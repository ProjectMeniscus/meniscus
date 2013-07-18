
import newrelic.agent

from meniscus.ext.plugin import import_module
from meniscus.data.cache_handler import ConfigCache
from meniscus import env
from meniscus.openstack.common import log


log.setup('meniscus')
_LOG = env.get_logger(__name__)

newrelic.agent.initialize("/etc/meniscus/newrelic.ini")

# Adding a hook into environment variables let's us override this
DEFAULT_PERSONALITY_MODULE = env.get('WORKER_PERSONA',
                                     'meniscus.personas.pairing.app')
config_cache = ConfigCache()


def bootstrap_api(global_config, **local_conf):

    #if the configuration exists in the cache,
    # retrieve the personality module
    config = config_cache.get_config()

    if config:
        personality_module = config.personality_module
        _LOG.info('loading personality module from config: {0}'
                  .format(personality_module))
    else:
        personality_module = DEFAULT_PERSONALITY_MODULE
        _LOG.info('loading default personality module: {0}'
                  .format(personality_module))

    #load the personality module as a plug in
    plugin_mod = import_module(personality_module)

    #start up the api from the specified personality_module
    return plugin_mod.start_up()
