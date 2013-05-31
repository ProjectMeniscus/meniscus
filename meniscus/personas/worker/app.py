from multiprocessing import Process

import falcon

from portal.env import get_logger
from portal.server import SyslogServer

from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher
from meniscus.api.correlation import syslog
from meniscus.queue import celery

_LOG = get_logger(__name__)


def start_up():

    application = api = falcon.API()
    api.add_route('/', VersionResource())

    #http correlation endpoint
    api.add_route('/v1/tenant/{tenant_id}/publish', PublishMessageResource())

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    #syslog correlation endpoint
    server = SyslogServer(
        ("0.0.0.0", 5140), syslog.MessageHandler())
    Process(target=server.start).start()

    Process(target=celery.worker_main).start()
    return application
