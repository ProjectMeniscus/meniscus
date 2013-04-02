
from oslo.config import cfg
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.model.util import load_tenant_from_dict
from meniscus.data.model.util import load_token_from_dict
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.openstack.common import jsonutils
from meniscus.proxy import NativeProxy


# cache configuration options
_cache_group = cfg.OptGroup(name='cache', title='Cache Options')
get_config().register_group(_cache_group)

_CACHE_OPTIONS = [
    cfg.IntOpt('default_expires',
               default=900,
               help="""default time to keep items in cache"""
               ),
    cfg.IntOpt('config_expires',
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


class Cache(object):
    def __init__(self):
        self.cache = NativeProxy()

    def clear(self):
        raise NotImplementedError


class ConfigCache(Cache):
    def clear(self):
        self.cache.cache_clear(CACHE_CONFIG)

    def set_config(self, worker_config):
        if self.cache.cache_exists('worker_configuration', CACHE_CONFIG):
            self.cache.cache_update(
                'worker_configuration',
                jsonutils.dumps(worker_config.format()),
                CONFIG_EXPIRES, CACHE_CONFIG)
        else:
            self.cache.cache_set(
                'worker_configuration',
                jsonutils.dumps(worker_config.format()),
                CONFIG_EXPIRES, CACHE_CONFIG)

    def get_config(self):
        if self.cache.cache_exists('worker_configuration', CACHE_CONFIG):
            config = jsonutils.loads(
                self.cache.cache_get('worker_configuration', CACHE_CONFIG))
            worker_config = WorkerConfiguration(**config)
            return worker_config
        return None

    def delete_config(self):
        if self.cache.cache_exists('worker_configuration', CACHE_CONFIG):
            self.cache.cache_del('worker_configuration', CACHE_CONFIG)

    def set_pipeline(self, pipeline_workers):
        if self.cache.cache_exists('pipeline_workers', CACHE_CONFIG):
            self.cache.cache_update(
                'pipeline_workers',
                jsonutils.dumps(pipeline_workers),
                CONFIG_EXPIRES, CACHE_CONFIG)
        else:
            self.cache.cache_set(
                'pipeline_workers',
                jsonutils.dumps(pipeline_workers),
                CONFIG_EXPIRES, CACHE_CONFIG)

    def get_pipeline(self):
        if self.cache.cache_exists('pipeline_workers', CACHE_CONFIG):
            pipeline_workers = jsonutils.loads(
                self.cache.cache_get('pipeline_workers', CACHE_CONFIG))
            return pipeline_workers
        return None

    def delete_pipeline(self):
        if self.cache.cache_exists('pipeline_workers', CACHE_CONFIG):
            self.cache.cache_del('pipeline_workers', CACHE_CONFIG)


class TenantCache(Cache):

    def clear(self):
            self.cache.cache_clear(CACHE_TENANT)

    def set_tenant(self, tenant):
        if self.cache.cache_exists(tenant.tenant_id, CACHE_TENANT):
            self.cache.cache_update(
                tenant.tenant_id, jsonutils.dumps(tenant.format()),
                DEFAULT_EXPIRES, CACHE_TENANT)
        else:
            self.cache.cache_set(
                tenant.tenant_id, jsonutils.dumps(tenant.format()),
                DEFAULT_EXPIRES, CACHE_TENANT)

    def get_tenant(self, tenant_id):
        if  self.cache.cache_exists(tenant_id, CACHE_TENANT):
            tenant_dict = jsonutils.loads(
                self.cache.cache_get(tenant_id, CACHE_TENANT))
            tenant = load_tenant_from_dict(tenant_dict)
            return tenant

        return None

    def delete_tenant(self, tenant_id):
        if  self.cache.cache_exists(tenant_id, CACHE_TENANT):
            self.cache.cache_del(tenant_id, CACHE_TENANT)


class TokenCache(Cache):

    def clear(self):
        self.cache.cache_clear(CACHE_TOKEN)

    def set_token(self, tenant_id, token):

        if self.cache.cache_exists(tenant_id, CACHE_TOKEN):
            self.cache.cache_update(
                tenant_id, jsonutils.dumps(token.format()),
                DEFAULT_EXPIRES, CACHE_TOKEN)
        else:
            self.cache.cache_set(
                tenant_id, jsonutils.dumps(token.format()),
                DEFAULT_EXPIRES, CACHE_TOKEN)

    def get_token(self, tenant_id):
        if self.cache.cache_exists(tenant_id, CACHE_TOKEN):
            token_dict = jsonutils.loads(
                self.cache.cache_get(tenant_id, CACHE_TOKEN))
            token = load_token_from_dict(token_dict)
            return token
        return None

    def delete_token(self, tenant_id):
        if self.cache.cache_exists(tenant_id, CACHE_TOKEN):
            self.cache.cache_del(tenant_id, CACHE_TOKEN)
