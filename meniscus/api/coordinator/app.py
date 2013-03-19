import falcon

from meniscus.api.coordinator.configuration_resources \
    import WorkerConfigurationResource
from meniscus.api.coordinator.registration_resources \
    import WorkerRegistrationResource
from meniscus.api.tenant.resources import VersionResource, \
    TenantResource, UserResource, HostProfilesResource, HostProfileResource, \
    EventProducersResource, EventProducerResource, HostsResource, HostResource

from meniscus.api.datastore_init import db_handler


#Common Resource(s)
versions = VersionResource()

#Coordinator Resources
worker_configuration = WorkerConfigurationResource(db_handler())
worker_registration = WorkerRegistrationResource(db_handler())

#Tenant Resources
tenant = TenantResource(db_handler())
user = UserResource(db_handler())
profiles = HostProfilesResource(db_handler())
profile = HostProfileResource(db_handler())
event_producers = EventProducersResource(db_handler())
event_producer = EventProducerResource(db_handler())
hosts = HostsResource(db_handler())
host = HostResource(db_handler())

# Create API
application = api = falcon.API()

# Common Routing
api.add_route('/', versions)

# Coordinator Routing
api.add_route('/v1/pairing', worker_registration)
api.add_route('/v1/worker/{worker_id}/configuration', worker_configuration)
api.add_route('/v1/worker/{worker_id}/status', worker_registration)

# Tenant Routing
api.add_route('/v1', tenant)
api.add_route('/v1/{tenant_id}', user)
api.add_route('/v1/{tenant_id}/profiles', profiles)
api.add_route('/v1/{tenant_id}/profiles/{profile_id}', profile)
api.add_route('/v1/{tenant_id}/producers', event_producers)
api.add_route('/v1/{tenant_id}/producers/{event_producer_id}',
              event_producer)
api.add_route('/v1/{tenant_id}/hosts', hosts)
api.add_route('/v1/{tenant_id}/hosts/{host_id}', host)

