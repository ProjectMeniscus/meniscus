import imp
import sys
import os.path
import importlib


"""
This is a simple plugin layer that uses the sys.meta_path list along
with custom finder and loader definitions to hook into the Python
import process. For more information, please see:
http://www.python.org/dev/peps/pep-0302/
"""


# Constants; because they make the code look nice.
_MODULE_PATH_SEP = '.'
_NAME = '__name__'
_PATH = '__path__'


class PluginError(ImportError):

    def __init__(self, msg):
        self.msg = msg


class PluginFinder():

    def __init__(self, paths=list()):
        self.plugin_paths = paths

    def add_path(self, new_path):
        if new_path not in self.plugin_paths:
            self.plugin_paths.append(new_path)

    def find_module(self, fullname, path=None):
        pathname = os.path.join(*fullname.split(_MODULE_PATH_SEP))

        for path in self.plugin_paths:
            target = os.path.join(path, pathname)
            is_pkg = False

            # If the target references a directory, try to load it as
            # a module by referencing the __init__.py file, otherwise
            # append .py and attempt to resolve it.
            if os.path.isdir(target):
                target = os.path.join(target, '__init__.py')
                is_pkg = True
            else:
                target += '.py'

            if os.path.exists(target):
                return SecureLoader(fullname, target, is_pkg)

        return None


class SecureLoader():

    def __init__(self, module_name, target, is_pkg):
        self.module_name = module_name
        self.load_target = target
        self.is_pkg = is_pkg

    def _read_code(self):
        fin = open(self.load_target, 'r')
        code = fin.read()
        fin.close()
        return code

    def load_module(self, fullname):
        if fullname != self.module_name:
            raise PluginError('Requesting a module that the loader is '
                              'unaware of.')

        if fullname in sys.modules:
            return sys.modules[fullname]

        code = self._read_code()
        module = imp.new_module(fullname)
        module.__file__ = self.load_target
        module.__loader__ = self

        if self.is_pkg:
            module.__path__ = []
            module.__package__ = fullname
        else:
            module.__package__ = fullname.rpartition('.')[0]

        exec(code, module.__dict__)
        sys.modules[fullname] = module
        return module


PLUGIN_FINDER = PluginFinder()


"""
Injects a custom finder object into the sys.meta_path list in order to
allow for the loading of additional modules that may not be in the path
given to the interpreter at boot.
"""


def _inject():
    if PLUGIN_FINDER not in sys.meta_path:
        sys.meta_path.append(PLUGIN_FINDER)


"""
This function ensures that the directory hooks have been placed in the
sys.meta_path list before passing the module name being required to
the importlib call of the same name.
"""


def import_module(module_name):
    _inject()
    return importlib.import_module(module_name)


"""
Adds all arguments passed as plugin directories to search when loading
modules.
"""


def plug_into(*args):
    for path in args:
        PLUGIN_FINDER.add_path(path)
