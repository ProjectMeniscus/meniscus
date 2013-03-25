from oslo.config import cfg
from meniscus.config import get_config
from meniscus.config import init_config


# cache configuration options
_cache_group = cfg.OptGroup(name='cache', title='Cache Options')
get_config().register_group(_cache_group)

_CACHE_OPTIONS = [
    cfg.ListOpt('default_expires',
                default=900,
                help="""default time to keep items in cache"""
                ),
    cfg.StrOpt('config_expires',
               default=0,
               help="""Default time to keep worker config items in cache."""
               ),
    cfg.StrOpt('cache_config',
               default='cache-config',
               help="""The name of the cache to store worker config values"""
               ),
    cfg.StrOpt('cache_tenant',
               default='cache-tenant',
               help="""The name of the cache to store worker config values"""
    ),
    cfg.StrOpt('cache_token',
               default='cache-token',
               help="""The name of the cache to store worker config values"""
    )
]

get_config().register_opts(_CACHE_OPTIONS, group=_cache_group)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

DEFAULT_EXPIRES = conf.cache.default_expires
CONFIG_EXPIRES = conf.cache.config_expires
CACHE_CONFIG = conf.cache.cache_config
CACHE_TENANT = conf.cache.cache_tenant
CACHE_TOKEN = conf.cache.cache_token

