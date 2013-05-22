from multiprocessing import Process

import falcon

from portal.env import get_logger
from portal.server import SyslogServer

from meniscus.api.callback.resources import CallbackResource
from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher
from meniscus.personas.worker import syslog_handler


_LOG = get_logger('meniscus.personas.worker.app')


def start_up():
    # Routing
    application = api = falcon.API()
    api.add_route('/v1', VersionResource())
    api.add_route('/v1/callback', CallbackResource())

    # Getting the status out - this may require a little more finesse...
    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    server = SyslogServer(
        ("0.0.0.0", 5140), syslog_handler.MessageHandler())
    Process(target=server.start).start()

    return application
