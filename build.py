import os
import os.path as path
import stat
import sys
import shutil
import tempfile
import subprocess
import urllib2
import tarfile

from pip.download import unpack_http_url
from pip.index import PackageFinder
from pip.req import InstallRequirement, RequirementSet
from pip.locations import build_prefix, src_prefix


def download(url, dl_location):
    u = urllib2.urlopen(url)
    localFile = open(dl_location, 'w')
    localFile.write(u.read())
    localFile.close()


def run(cmd, cwd=None):
    print('Exec: {}'.format(cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True)
    proc.wait()
    if proc.returncode != 0:
        print('Failed: {}'.format(proc.stdout.read()))


def define_dir(tmp_dir, name):
    fullname = path.join(tmp_dir, name)
    os.mkdir(fullname)
    return fullname


def package_finder():
    return PackageFinder(
        find_links=[],
        index_urls=["http://pypi.python.org/simple/"])


def install_req(name, hooks):
    finder = package_finder()
    req = InstallRequirement.from_line("pyev", None)
    found_req = finder.find_requirement(req, False)
    print(dir(found_req))
    dl_target = path.join(dl_dir, found_req.filename)
    unpact_target = path.join(build_dir, name)
    download(found_req.url, dl_target)
    tarchive = tarfile.open(dl_target, mode='r|gz')
    tarchive.extractall(build_dir)
    build_location = path.join(build_dir, found_req.filename.rstrip('.tar.gz'))
    print(build_location)
    run('python setup.py build --build-base={}'.format(build_location))
    run('python setup.py install --home={}'.format(dist_dir))



tmp_dir = tempfile.mkdtemp()

build_dir = define_dir(tmp_dir, 'build')
dist_dir = define_dir(tmp_dir, 'dist')
lib_dir = define_dir(dist_dir, 'lib')
define_dir(lib_dir, 'python')
dl_dir = define_dir(tmp_dir, 'dl')


install_req('pyev', {
    'unpack.after': lambda pkg_dir: os.chmod(path.join(pkg_dir, 'src/libev/configure'), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)})

#requirement_set.prepare_files(
#    finder, force_root_egg_info=False, bundle=False)
#requirement_set.install(install_options, global_options)

#print("")
#print("Installed")
#print("==================================")
#for package in requirement_set.successfully_installed:
#    print(package.name)
#print("")

#run('pip install -t {} -b {} -r tools/pip-requires'.format(dist_dir, build_dir))

print('Cleaning {}'.format(tmp_dir))
#shutil.rmtree(tmp_dir)
