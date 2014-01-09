from multiprocessing import Process
from datetime import timedelta

import falcon

from meniscus.api.tenant.resources import EventProducerResource
from meniscus.api.tenant.resources import EventProducersResource
from meniscus.api.tenant.resources import UserResource
from meniscus.api.tenant.resources import TenantResource
from meniscus.api.tenant.resources import TokenResource
from meniscus.api.version.resources import VersionResource
from meniscus.data.datastore import COORDINATOR_DB, get_data_handler
from meniscus import env
from meniscus.personas.common import publish_stats
from meniscus.queue import celery


_LOG = env.get_logger(__name__)


def start_up():
    #Common Resource(s)
    versions = VersionResource()

    #Tenant Resources
    tenant = TenantResource()
    user = UserResource()
    event_producers = EventProducersResource()
    event_producer = EventProducerResource()
    token = TokenResource()

    # Create API
    application = api = falcon.API()

    # Version Routing
    api.add_route('/', versions)

    # Tenant Routing
    api.add_route('/v1/tenant', tenant)
    api.add_route('/v1/tenant/{tenant_id}', user)
    api.add_route('/v1/tenant/{tenant_id}/producers', event_producers)
    api.add_route('/v1/tenant/{tenant_id}/producers/{event_producer_id}',
                  event_producer)
    api.add_route('/v1/tenant/{tenant_id}/token', token)

    celery.conf.CELERYBEAT_SCHEDULE = {
        'worker_stats': {
            'task': 'stats.publish',
            'schedule': timedelta(seconds=publish_stats.WORKER_STATUS_INTERVAL)
        },
    }

    #include blank argument to celery in order for beat to start correctly
    celery_proc = Process(target=celery.worker_main, args=[['', '--beat']])
    celery_proc.start()
    _LOG.info(
        'Celery started as process: {}'.format(celery_proc.pid)
    )

    return application
