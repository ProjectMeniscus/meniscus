from multiprocessing import Process
from datetime import timedelta

import falcon

from portal.server import SyslogServer, start_io

from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.version.resources import VersionResource
from meniscus.api.correlation import syslog
from meniscus import env
from meniscus.personas.common import publish_stats
from meniscus.queue import celery

import newrelic.agent

_LOG = env.get_logger(__name__)

@newrelic.agent.function_trace()
def start_up():

    application = api = falcon.API()
    api.add_route('/', VersionResource())

    #http correlation endpoint
    api.add_route('/v1/tenant/{tenant_id}/publish', PublishMessageResource())

    #syslog correlation endpoint
    server = SyslogServer(
        ("0.0.0.0", 5140), syslog.MessageHandler())
    server.start()
    Process(target=start_io).start()

    celery.conf.CELERYBEAT_SCHEDULE = {
        'worker_stats': {
            'task': 'stats.publish',
            'schedule': timedelta(seconds=publish_stats.WORKER_STATUS_INTERVAL)
        },
    }

    #include blank argument to celery in order for beat to start correctly
    Process(target=celery.worker_main, args=[['', '--beat']]).start()
    return application
