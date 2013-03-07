import json
import falcon
from meniscus.api.utils.request import http_request
from meniscus.api import ApiResource, load_body


class VersionResource(ApiResource):
    """ Return the current version of the Pairing API """

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


class PairingConfigurationResource(ApiResource):
    """
    Webhook callback for the system package coordinator to
    configure the worker for pairing with its coordinator
    """

    def on_post(self, req, resp):
        body = load_body(req)

        api_secret = body['api_secret']
        coordinator_uri = body['coordinator_uri']
        personality = body['personality']

        resp.status = falcon.HTTP_200
