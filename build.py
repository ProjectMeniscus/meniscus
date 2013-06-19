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

    def __init__(self, starting_dir, pkg_index, project_name):
        self.ctx_root = starting_dir
        self.etc = path.join(self.ctx_root, 'etc')
        self.usr = mkdir(path.join(self.ctx_root, 'usr'))
        self.usr_share = mkdir(path.join(self.usr, 'share'))
        self.build_dir = mkdir(path.join(self.ctx_root, 'build'))
        self.dist_dir = mkdir(path.join(self.usr_share, project_name))
        self.home_dir = mkdir(path.join(self.dist_dir, 'lib'))
        self.python_dist = mkdir(path.join(self.home_dir, 'python'))
        self.files_dir = mkdir(path.join(self.ctx_root, 'files'))
        self.pkg_index = pkg_index


def read(relative):
    contents = open(relative, 'r').read()
    return [l for l in contents.split('\n') if l != '']


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

    done = False
    while not done:
        line = proc.stdout.readline()
        if line:
            print(line.rstrip('\n'))
        else:
            done = True

    if proc.returncode and proc.returncode != 0:
        print('Failed with return code: {}'.format(proc.returncode))
        sys.exit(1)


def unpack(name, bctx, stage_hooks, filename, dl_target):
    if dl_target.endswith('.tar.gz') or dl_target.endswith('.tgz'):
        archive = tarfile.open(dl_target, mode='r|gz')
        build_location = path.join(bctx.build_dir, filename.rstrip('.tar.gz'))
    elif dl_target.endswith('.zip'):
        archive = zipfile.ZipFile(dl_target, mode='r')
        build_location = path.join(bctx.build_dir, filename.rstrip('.zip'))
    else:
        print('Unknown archive format: {}'.format(dl_target))
        raise Exception()

    archive.extractall(bctx.build_dir)
    return build_location


def install_req(name, bctx, stage_hooks=None):
    req = InstallRequirement.from_line(name, None)
    found_req = bctx.pkg_index.find_requirement(req, False)
    dl_target = path.join(bctx.files_dir, found_req.filename)

    # stages
    call_hook(name, 'download.before', stage_hooks, bctx=bctx, fetch_url=found_req.url)
    download(found_req.url, dl_target)
    call_hook(name, 'download.after', stage_hooks, bctx=bctx, archive=dl_target)

    call_hook(name, 'unpack.before', stage_hooks, bctx=bctx, archive=dl_target)
    build_location = unpack(name, bctx, stage_hooks, found_req.filename, dl_target)
    call_hook(name, 'unpack.after', stage_hooks, bctx=bctx, build_location=build_location)

    call_hook(name, 'build.before', stage_hooks, bctx=bctx, build_location=build_location)
    run_python(bctx, 'python setup.py build'.format(build_location), build_location)
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


def read_requires(filename, bctx, pkg_index, hooks):
    lines = open(filename, 'r').read()
    if not lines:
        raise Exception()

    for line in lines.split('\n'):
        if line and len(line) > 0:
            install_req(line, bctx, hooks)


def build(requirements_file, hooks, project_name, version):
    pkg_index = PackageFinder(
        find_links=[],
        index_urls=["http://pypi.python.org/simple/"])
    bctx = BuildContext(tempfile.mkdtemp(), pkg_index, project_name)
    read_requires(requirements_file, bctx, pkg_index, hooks)

    run_python(bctx, 'python setup.py build')
    run_python(bctx, 'python setup.py install --home={}'.format(bctx.dist_dir))

    print('Copying etc')
    local_etc = path.join('.', 'etc')
    shutil.copytree(local_etc, bctx.etc)

    print('Cleaning {}'.format(bctx.ctx_root))

    #shutil.rmtree(bctx.ctx_root)
    tar_filename = '{}_{}.tar.gz'.format(project_name, version)
    tar_fpath = path.join(bctx.ctx_root, tar_filename)
    tarchive = tarfile.open(tar_fpath, 'w|gz')
    tarchive.add(bctx.usr, arcname='usr')
    tarchive.add(bctx.etc, arcname='etc')
    tarchive.close()
    shutil.copyfile(tar_fpath, path.join('.', tar_filename))

def fix_pyev(bctx, build_location):
    os.chmod(
        path.join(build_location, 'src/libev/configure'),
        stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


hooks = {
    'pyev' : {
        'unpack.after' : fix_pyev
    }
}

requirements_file = 'tools/pip-requires'

if len(sys.argv) != 2:
    print('usage: build.py <project-name>')

version = read('VERSION')[0]

build(requirements_file, hooks, sys.argv[1], version)
