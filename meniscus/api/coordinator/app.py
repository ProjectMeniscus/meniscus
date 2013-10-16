from multiprocessing import Process

import falcon

from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.status.resources import (
    WorkerStatusResource, WorkersStatusResource)
from meniscus.api.tenant.resources import (
    EventProducerResource, EventProducersResource,
    UserResource, TenantResource, TokenResource)

from meniscus.api.version.resources import VersionResource
from meniscus import env
from meniscus.openstack.common import log
from meniscus.queue import celery


log.setup('meniscus')
_LOG = env.get_logger(__name__)

#Common Resource(s)
versions = VersionResource()

#Coordinator Resources
worker_registration = WorkerRegistrationResource()
workers_status = WorkersStatusResource()
worker_status = WorkerStatusResource()

#Tenant Resources
tenant = TenantResource()
user = UserResource()
event_producers = EventProducersResource()
event_producer = EventProducerResource()
token = TokenResource()

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
api.add_route('/v1/tenant/{tenant_id}/producers', event_producers)
api.add_route('/v1/tenant/{tenant_id}/producers/{event_producer_id}',
              event_producer)
api.add_route('/v1/tenant/{tenant_id}/token', token)

celery_proc = Process(target=celery.worker_main)
celery_proc.start()
_LOG.info(
    'Celery started as process: {}'.format(celery_proc.pid)
)
