import falcon

from meniscus.api import ApiResource
from meniscus.api import load_body
from meniscus.data.cache_handler import BroadcastCache


class BroadcastResource(ApiResource):
    def on_put(self, req, resp):
        """
        Take a broadcast message from a Coordinator and stuff it
        in the cache for the broadcaster process to handle
        """
        body = load_body(req)
        broadcast_msg_dict = body['broadcast']

        cache = BroadcastCache()
        cache.set_message_and_targets(broadcast_msg_dict['type'],
                                      broadcast_msg_dict['targets'])

        resp.status = falcon.HTTP_202
