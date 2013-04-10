import falcon

from meniscus.api.callback.resources import CallbackResource
from meniscus.api.coordinator.resources import WorkerRoutesResource
from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.status.resources import WorkerUpdateResource
from meniscus.api.status.resources import WorkerStatusResource
from meniscus.api.status.resources import WorkersStatusResource
from meniscus.api.tenant.resources import EventProducerResource
from meniscus.api.tenant.resources import EventProducersResource
from meniscus.api.tenant.resources import HostProfileResource
from meniscus.api.tenant.resources import HostProfilesResource
from meniscus.api.tenant.resources import HostResource
from meniscus.api.tenant.resources import HostsResource
from meniscus.api.tenant.resources import UserResource
from meniscus.api.tenant.resources import TenantResource
from meniscus.api.tenant.resources import TokenResource
from meniscus.api.version.resources import VersionResource

from meniscus.api.datastore_init import db_handler


#Common Resource(s)
versions = VersionResource()
callback = CallbackResource()

#Coordinator Resources
worker_routes = WorkerRoutesResource(db_handler())
worker_registration = WorkerRegistrationResource(db_handler())
worker_update = WorkerUpdateResource(db_handler())
workers_status = WorkersStatusResource(db_handler())
worker_status = WorkerStatusResource(db_handler())

#Tenant Resources
tenant = TenantResource(db_handler())
user = UserResource(db_handler())
profiles = HostProfilesResource(db_handler())
profile = HostProfileResource(db_handler())
event_producers = EventProducersResource(db_handler())
event_producer = EventProducerResource(db_handler())
hosts = HostsResource(db_handler())
host = HostResource(db_handler())
token = TokenResource(db_handler())

# Create API
application = api = falcon.API()

# Common Routing
api.add_route('/', versions)
api.add_route('/v1/callback', callback)

# Coordinator Routing
api.add_route('/v1/pairing', worker_registration)
api.add_route('/v1/worker/{worker_id}/routes', worker_routes)
api.add_route('/v1/worker/{worker_id}/registration', worker_registration)

api.add_route('/v1/worker/{worker_id}/status', worker_update)
api.add_route('/v1/status', workers_status)
api.add_route('/v1/status/{worker_id}', worker_status)

# Tenant Routing
api.add_route('/v1/tenant', tenant)
api.add_route('/v1/tenant/{tenant_id}', user)
api.add_route('/v1/tenant/{tenant_id}/profiles', profiles)
api.add_route('/v1/tenant/{tenant_id}/profiles/{profile_id}', profile)
api.add_route('/v1/tenant/{tenant_id}/producers', event_producers)
api.add_route('/v1/tenant/{tenant_id}/producers/{event_producer_id}',
              event_producer)
api.add_route('/v1/tenant/{tenant_id}/hosts', hosts)
api.add_route('/v1/tenant/{tenant_id}/hosts/{host_id}', host)
api.add_route('/v1/tenant/{tenant_id}/token', token)
