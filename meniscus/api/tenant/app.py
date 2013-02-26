import falcon

from meniscus.api.tenant.resources import *
from meniscus.data.handler import datasource_handler
from meniscus.config import init_config, get_config


init_config(['--config-file', 'meniscus.cfg'])
conf = get_config()
_handler = datasource_handler(conf)
_handler.connect()


def db_handler():
    return _handler


# Resources
versions = VersionResource()
tenant = TenantResource(db_handler())
user = UserResource(db_handler())
profiles = HostProfilesResource(db_handler())
profile = HostProfileResource(db_handler())
event_producers = EventProducersResource(db_handler())
event_producer = EventProducerResource(db_handler())
hosts = HostsResource(db_handler())
host = HostResource(db_handler())


# Routing
application = api = falcon.API()

api.add_route('/', versions)
api.add_route('/v1', tenant)
api.add_route('/v1/{tenant_id}', user)
api.add_route('/v1/{tenant_id}/profiles', profiles)
api.add_route('/v1/{tenant_id}/profiles/{profile_id}', profile)
api.add_route('/v1/{tenant_id}/producers', event_producers)
api.add_route('/v1/{tenant_id}/producers/{event_producer_id}', event_producer)
api.add_route('/v1/{tenant_id}/hosts', hosts)
api.add_route('/v1/{tenant_id}/hosts/{host_id}', host)
