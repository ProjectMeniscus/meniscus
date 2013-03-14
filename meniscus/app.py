from meniscus.openstack.common import jsonutils
from meniscus.proxy import NativeProxy
from meniscus.ext.plugin import import_module

DEFAULT_PERSONALITY_MODULE = 'meniscus.personas.worker.pairing'
cache = NativeProxy()


def bootstrap_api():
    personality_module = None

    #if the configuration exists in the cache,
    # retrieve the personality module
    if cache.cache_exists('worker_configuration'):
        cached_config = jsonutils.loads(cache.cache_get('worker_configuration'))
        personality_module = cached_config['personality_module']

    #if no personality module was pulled form the cache, use the default
    if not personality_module:
        personality_module = DEFAULT_PERSONALITY_MODULE

    #load the personality module as a plug in
    plugin_mod = import_module(personality_module)

    #start up the api from the specified personality_module
    return plugin_mod.start_up()

application = bootstrap_api()
