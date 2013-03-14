import falcon

from meniscus.api import ApiResource, format_response_body


class VersionResource(ApiResource):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'v1': 'current'})
