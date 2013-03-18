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

except ConfigFilesNotFoundError:

    DEFAULT_EXPIRES = 900
    CONFIG_EXPIRES = 0
    CACHE_CONFIG = 'cache_config'
    CACHE_TENANT = 'cache_tenant'
