import json
import falcon

from meniscus.api.callback.resources import CallbackResource
from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher

from multiprocessing import Process

from portal.env import get_logger
from portal.server import SyslogServer
from portal.input.rfc5424 import SyslogMessageHandler


_LOG = get_logger('portal.tests.server_test')


class MessageHandler(SyslogMessageHandler):

    def __init__(self):
        self.msg = b''
        self.msg_head = None
        self.msg_count = 0

    def message_head(self, message_head):
        self.msg_count += 1
        self.msg_head = message_head

    def message_part(self, message_part):
        self.msg += message_part

    def message_complete(self, last_message_part):
        message_dict = self.msg_head.as_dict()
        message_dict['message'] = (
            self.msg + last_message_part).decode('utf-8')
        _LOG.debug('Message: {}'.format(json.dumps(message_dict)))
        self.msg_head = None
        self.msg = b''


def start_up():
    # Routing
    application = api = falcon.API()
    api.add_route('/v1', VersionResource())
    api.add_route('/v1/callback', CallbackResource())

    # Getting the status out - this may require a little more finesse...
    register_worker_online = WorkerStatusPublisher('online')
    #register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    #publish_stats_service.run()

    server = SyslogServer(("0.0.0.0", 5140), MessageHandler())
    Process(target=server.start).start()

    return application
