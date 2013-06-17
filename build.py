import os
import os.path as path
import stat
import sys
import shutil
import tempfile
import subprocess
import urllib2
import tarfile
import logging
import zipfile

from pip.download import unpack_http_url
from pip.index import PackageFinder
from pip.req import InstallRequirement, RequirementSet
from pip.locations import build_prefix, src_prefix


PYTHONPATH = 'PYTHONPATH'


class BuildContext(object):

    def __init__(self, starting_dir, pkg_index):
        self.ctx_root = starting_dir
        self.build_dir = mkdir(path.join(self.ctx_root, 'build'))
        self.dist_dir = mkdir(path.join(self.ctx_root, 'dist'))
        self.home_dir = mkdir(path.join(self.dist_dir, 'lib'))
        self.python_dist = mkdir(path.join(self.home_dir, 'python'))
        self.files_dir = mkdir(path.join(self.ctx_root, 'files'))
        self.pkg_index = pkg_index


def mkdir(location):
    if not path.exists(location):
        os.mkdir(location)
    return location


def download(url, dl_location):
    u = urllib2.urlopen(url)
    localFile = open(dl_location, 'w')
    localFile.write(u.read())
    localFile.close()


def run_python(bctx, cmd, cwd=None):
    env = os.environ.copy()
    if PYTHONPATH in env:
        current_path = env[PYTHONPATH]
        env[PYTHONPATH] = '{}{}{}'.format(
            current_path,
            os.path_sep,
            bctx.python_dist)
    else:
        env[PYTHONPATH] = bctx.python_dist
    run(cmd, cwd, env)


def run(cmd, cwd=None, env=None):
    print('>>> Exec: {}'.format(cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        close_fds=True)

    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print(line.rstrip('\n'))

    if proc.returncode and proc.returncode != 0:
        print('Failed with return code: {}'.format(proc.returncode))


def install_req(name, bctx, stage_hooks=None):
    req = InstallRequirement.from_line(name, None)
    found_req = bctx.pkg_index.find_requirement(req, False)
    dl_target = path.join(bctx.files_dir, found_req.filename)

    # stages
    call_hook(name, 'download.before', stage_hooks, bctx=bctx, fetch_url=found_req.url)
    download(found_req.url, dl_target)
    call_hook(name, 'download.after', stage_hooks, bctx=bctx, archive=dl_target)

    call_hook(name, 'unpack.before', stage_hooks, bctx=bctx, archive=dl_target)

    if dl_target.endswith('.tar.gz') or dl_target.endswith('.tgz'):
        archive = tarfile.open(dl_target, mode='r|gz')
        build_location = path.join(bctx.build_dir, found_req.filename.rstrip('.tar.gz'))
    elif dl_target.endswith('.zip'):
        archive = zipfile.ZipFile(dl_target, mode='r')
        build_location = path.join(bctx.build_dir, found_req.filename.rstrip('.zip'))
    else:
        print('Unknown archive format: {}'.format(dl_target))
        raise Exception()

    archive.extractall(bctx.build_dir)
    call_hook(name, 'unpack.after', stage_hooks, bctx=bctx, build_location=build_location)

    # stages
    call_hook(name, 'build.before', stage_hooks, bctx=bctx, build_location=build_location)
    run_python(bctx, 'python setup.py build --build-base={}'.format(build_location), build_location)
    call_hook(name, 'build.after', stage_hooks, bctx=bctx, build_location=build_location)

    call_hook(name, 'install.before', stage_hooks, bctx=bctx, build_location=build_location)
    run_python(bctx, 'python setup.py install --home={}'.format(bctx.dist_dir), build_location)
    call_hook(name, 'install.after', stage_hooks, bctx=bctx, build_location=build_location)


def call_hook(name, stage, stage_hooks, **kwargs):
    if stage_hooks:
        if name in stage_hooks:
            hooks = stage_hooks[name]
            if stage in hooks:
                hook = hooks[stage]
                print('Calling hook {} for stage {}'.format(hook, stage))
                hook(kwargs)


def read_requires(filename):
    pkg_index = PackageFinder(
            find_links=[],
            index_urls=["http://pypi.python.org/simple/"])
    bctx = BuildContext(tempfile.mkdtemp(), pkg_index)

    lines = open(filename, 'r').read()
    if not lines:
        raise Exception()

    for line in lines.split('\n'):
        install_req(line, bctx, hooks)

    print('Cleaning {}'.format(bctx.ctx_root))
    #shutil.rmtree(bctx.ctx_root)


def fix_pyev(bctx, build_location):
    os.chmod(
        path.join(build_location, 'src/libev/configure'),
        stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


hooks = {
    'pyev' : {
        'unpack.after' : fix_pyev
    }
}

if len(sys.argv) > 1:
    read_requires(sys.argv[1])
#go('meniscus', hooks)

