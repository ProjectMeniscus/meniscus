import falcon
import meniscus.config as config

from meniscus.api.coordinator.resources import WorkerRegistrationResource
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
from meniscus.data.datastore import COORDINATOR_DB, datasource_handler
from meniscus import env


_LOG = env.get_logger(__name__)


def start_up():
    #Common Resource(s)
    versions = VersionResource()

    #Datastore adapter/session manager
    datastore = datasource_handler(COORDINATOR_DB)

    #Coordinator Resources
    worker_registration = WorkerRegistrationResource(datastore)
    workers_status = WorkersStatusResource(datastore)
    worker_status = WorkerStatusResource(datastore)

    #Tenant Resources
    tenant = TenantResource(datastore)
    user = UserResource(datastore)
    profiles = HostProfilesResource(datastore)
    profile = HostProfileResource(datastore)
    event_producers = EventProducersResource(datastore)
    event_producer = EventProducerResource(datastore)
    hosts = HostsResource(datastore)
    host = HostResource(datastore)
    token = TokenResource(datastore)

    # Create API
    application = api = falcon.API()

    # Common Routing
    api.add_route('/', versions)

    # Coordinator Routing
    api.add_route('/v1/pairing', worker_registration)

    api.add_route('/v1/worker/{worker_id}/status', worker_status)
    api.add_route('/v1/status', workers_status)

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

    return application
