import falcon

from meniscus.api.callback.resources import CallbackResource
from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher

from multiprocessing import Process

from portal.env import get_logger
from portal.server import JsonStreamServer
from portal.input.jsonstream import JsonMessageHandler

from meniscus.api.datastore_init import db_handler


_LOG = get_logger('portal.tests.server_test')


class JsonHandler(JsonMessageHandler):

    def __init__(self, db_handler):
        self.msg_count = 0
        self.db_handler = db_handler

    def header(self, key, value):
        # Don't really care about headers in this case... that's for later
        #_LOG.debug('Header: {} = {}'.format(key, value))
        pass

    def body(self, body):
        #_LOG.debug('Body: {}'.format(body))
        self.db_handler.put('logs', body)


def start_up():
    versions = VersionResource()
    callback = CallbackResource()

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/v1/callback', callback)

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    server = JsonStreamServer(
        ("127.0.0.1", 9001), JsonHandler(db_handler()))
    Process(target=server.start).start()

    return application
