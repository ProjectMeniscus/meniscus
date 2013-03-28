import falcon

from meniscus.api import ApiResource
from meniscus.api import format_response_body


class VersionResource(ApiResource):
    """ Return the current version of the Pairing API """

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'v1': 'current'})
