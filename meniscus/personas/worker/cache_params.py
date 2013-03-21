from meniscus.config import get_config
from meniscus.config import init_config
from oslo.config.cfg import ConfigFilesNotFoundError

try:
    init_config()
    conf = get_config()

    DEFAULT_EXPIRES = conf.cache.default_expires
    CONFIG_EXPIRES = conf.cache.config_expires
    CACHE_CONFIG = conf.cache.cache_config
    CACHE_TENANT = conf.cache.cache_tenant
    CACHE_TOKEN = conf.cache.cache_token

except ConfigFilesNotFoundError:

    DEFAULT_EXPIRES = 900
    CONFIG_EXPIRES = 0
    CACHE_CONFIG = 'cache-config'
    CACHE_TENANT = 'cache-tenant'
    CACHE_TOKEN = 'cache-token'
