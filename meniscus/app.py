from meniscus.proxy import NativeProxy
from meniscus.ext.plugin import plug_into, import_module

DEFAULT_PERSONALITY_MODULE = 'meniscus.personas.worker.pairing'
cache = NativeProxy()


def bootstrap_api():
    personality_module = None
    #check if uwsgi was imported

    #if the configuration exists in the cache,
    # retrieve the personality module
    if cache.cache_exists('configuration'):
        cached_config = cache.cache_get('configuration')
        personality_module = cached_config['personality_module']

    #if no personality module was pulled form the cache, use the default
    if not personality_module:
        personality_module = DEFAULT_PERSONALITY_MODULE

    #plug into the meniscus directory, and load the personality module
    plug_into(
        '/var/lib/meniscus')
    plugin_mod = import_module( personality_module)

    #start up the api from the specified personality_module
    return plugin_mod.start_up()

application = bootstrap_api()
