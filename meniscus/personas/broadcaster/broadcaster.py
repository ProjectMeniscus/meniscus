from multiprocessing import Process

from oslo.config import cfg
from meniscus.api.utils.request import http_request
from meniscus.api.utils.retry import retry
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.cache_handler import BroadcastCache


# cache configuration options
_BROADCAST_GROUP = cfg.OptGroup(name='broadcast',
                                title='Broadcast Settings')
get_config().register_group(_BROADCAST_GROUP)

_CACHE_OPTIONS = [
    cfg.IntOpt('broadcast_message_interval',
               default=60,
               help="""default time to broadcast messages"""
    )
]

get_config().register_opts(_CACHE_OPTIONS, group=_BROADCAST_GROUP)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

BROADCAST_MESSAGE_INTERVAL = conf.status_update.broadcast_message_interval

ROUTES = 'ROUTES'

# Constants for retry methods
TRIES = 0
BACKOFF = 1


class Broadcaster(object):
    def __init__(self, ):
        self.process = Process(
            target=self._broadcast_route_messages)

    def run(self):
        self.process.start()

    @retry(tries=TRIES, delay=BROADCAST_MESSAGE_INTERVAL, backoff=BACKOFF)
    def _broadcast_route_messages(self):
        cache = BroadcastCache()
        uri_targets = cache.get_targets(ROUTES)

        # Get route messages from cache and notify the workers
        if len(uri_targets):
            type_header = {
                "TYPE": ROUTES
            }

            for uri in uri_targets:
                try:
                    http_request(uri,
                                 add_headers=type_header,
                                 http_verb='HEAD')
                except Exception:
                    # Swallow exception for now
                    pass
