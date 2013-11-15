import platform

from oslo.config import cfg

from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.cache_handler import ConfigCache
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.ext.plugin import import_module
from meniscus import env
from meniscus.openstack.common import log


log.setup('meniscus')
_LOG = env.get_logger(__name__)

# default configuration options
_node_group = cfg.OptGroup(name='node', title='Node')
get_config().register_group(_node_group)

_NODE_OPTIONS = [
    cfg.StrOpt('personality',
               default='worker',
               help="""The personality to load"""
               ),
    cfg.StrOpt('coordinator_uri',
               default='http://localhost:8080/v1',
               help="""The URI of the Coordinator (can be a load balancer)"""
               )
]

get_config().register_opts(_NODE_OPTIONS, group=_node_group)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

PERSONALITY = conf.node.personality
COORDINATOR_URI = conf.node.coordinator_uri

config_cache = ConfigCache()


def bootstrap_api():
    # Persist the coordinator_uri and personality to ConfigCache
    config = WorkerConfiguration(PERSONALITY, platform.node(),
                                 COORDINATOR_URI)
    config_cache.set_config(config)

    personality_module = 'meniscus.personas.{0}.app'.format(PERSONALITY)
    _LOG.info('loading default personality module: {0}'
        .format(personality_module))

    #load the personality module as a plug in
    plugin_mod = import_module(personality_module)

    #start up the api from the specified personality_module
    return plugin_mod.start_up()

application = bootstrap_api()
