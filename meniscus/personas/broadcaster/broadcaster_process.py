from multiprocessing import Process
from time import sleep

import requests

from oslo.config import cfg
from meniscus.api.utils.request import http_request
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.cache_handler import BroadcastCache


# cache configuration options
_BROADCAST_GROUP = cfg.OptGroup(name='broadcast_settings',
                                title='Broadcast Settings')
get_config().register_group(_BROADCAST_GROUP)

_BROADCAST_OPTIONS = [
    cfg.IntOpt('broadcast_message_interval',
               default=60,
               help="""default time to broadcast messages"""
               )
]

get_config().register_opts(_BROADCAST_OPTIONS, group=_BROADCAST_GROUP)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

BROADCAST_MESSAGE_INTERVAL = conf.broadcast_settings.broadcast_message_interval

ROUTES = 'ROUTES'


class BroadcasterProcess(object):
    def __init__(self, run_once=False):
        self.process = Process(
            target=self._broadcast_route_messages,
            kwargs={
                'message_interval':  BROADCAST_MESSAGE_INTERVAL
            })
        self.run_once = run_once

    def run(self):
        """
        launch the subprocess
        """
        self.process.start()

    def kill(self):
        """
        kill the subprocess
        """
        self.process.terminate()

    def _broadcast_route_messages(self, message_interval):
        cache = BroadcastCache()

        while True:
            sleep(message_interval)
            uri_targets = cache.get_targets(ROUTES)
            cache.delete_message(ROUTES)

            # Get route messages from cache and notify the workers
            if uri_targets:
                type_header = {
                    "TYPE": ROUTES
                }

                for uri in uri_targets:
                    try:
                        http_request(uri,
                                     add_headers=type_header,
                                     http_verb='HEAD')
                    except requests.RequestException:
                        # Swallow exception for non-responsive worker
                        pass

            if self.run_once:
                break
