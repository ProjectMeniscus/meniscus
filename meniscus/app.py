from meniscus.ext.plugin import import_module
from meniscus.data.cache_handler import ConfigCache


DEFAULT_PERSONALITY_MODULE = 'meniscus.personas.worker.pairing.app'
config_cache = ConfigCache()


def bootstrap_api():

    #if the configuration exists in the cache,
    # retrieve the personality module
    config = config_cache.get_config()

    if config:
        personality_module = config.personality_module
    else:
        personality_module = DEFAULT_PERSONALITY_MODULE

    #load the personality module as a plug in
    plugin_mod = import_module(personality_module)

    #start up the api from the specified personality_module
    return plugin_mod.start_up()

application = bootstrap_api()
