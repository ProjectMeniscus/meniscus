import falcon

from meniscus.api import ApiResource
from meniscus.api.callback import callback_methods

TYPE_HEADER = 'TYPE'
ROUTES = 'ROUTES'


class CallbackResource(ApiResource):
    def on_head(self, req, resp):
        #get message token, or abort if token is not in header
        type_header = req.get_header(TYPE_HEADER, required=True)

        if ROUTES in type_header :
            callback_methods.get_routes_from_coordinator()

        resp.status = falcon.HTTP_200
