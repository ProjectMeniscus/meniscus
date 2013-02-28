import json
import falcon

from meniscus.api import ApiResource, load_body


class VersionResource(ApiResource):
    """ Return the current version of the Worker API """

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


class ConfigurationResource(ApiResource):
    """
    Webhook callback for the Coordinator to send the
    latest configuration settings
    """

    # TODO: This is a placeholder, to be finished yet
    def on_post(self, req, resp):
        body = load_body(req)
        resp.status = falcon.HTTP_202