import falcon

from meniscus.api.datastore_init import db_handler
from meniscus.api.tenant.resources import EventProducerResource
from meniscus.api.tenant.resources import EventProducersResource
from meniscus.api.tenant.resources import HostProfileResource
from meniscus.api.tenant.resources import HostResource
from meniscus.api.tenant.resources import HostProfilesResource
from meniscus.api.tenant.resources import HostsResource
from meniscus.api.tenant.resources import TenantResource
from meniscus.api.tenant.resources import TokenResource
from meniscus.api.tenant.resources import UserResource
from meniscus.api.version.resources import VersionResource


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
token = TokenResource(db_handler())

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
api.add_route('/v1/{tenant_id}/token', token)
