import imp
import sys
import os.path

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
        pathname = os.path.join(*fullname.split('.'))
        
        for path in self.plugin_paths:
            target = os.path.join(path, pathname)

            if os.path.isdir(target):
                target = os.path.join(target, '__init__.py')
            else:
                target += '.py'
                
            if os.path.exists(target):
                return SecureLoader(fullname, target)

        return None
            

class SecureLoader():

    def __init__(self, module_name, target):
        self.module_name = module_name
        self.load_target = target

    def load_module(self, fullname):
        if fullname != self.module_name:
            raise PluginError('Requesting a module that the loader is unaware of')

        return imp.load_source(fullname, self.load_target)


PLUGIN_FINDER = PluginFinder()

def plug_into(*args):
    for path in args:
        PLUGIN_FINDER.add_path(path)

    if PLUGIN_FINDER not in sys.meta_path:
        sys.meta_path.append(PLUGIN_FINDER)
