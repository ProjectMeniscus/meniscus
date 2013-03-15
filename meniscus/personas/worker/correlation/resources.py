import httplib
import falcon
import json
import requests

from meniscus.api import ApiResource, load_body, abort
from meniscus.data.model.util import find_tenant
from meniscus.data.model.tenant import Tenant
from meniscus.proxy import NativeProxy
from meniscus.api.utils.request import http_request

MSG_TOKEN = 'MESSAGE-TOKEN'

def _tenant_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'The tenant id specified was not found')


def _coordinator_connection_failure():
    """
    sends an http 500 response to the caller if fails to connect to
    coordinator
    """
    abort(falcon.HTTP_500)


def _unauthorized_message():
    """
    sends an http 401 response to the caller
    """
    abort(falcon.HTTP_401, 'Message not authenticated, check your tenant id '
                           'and or message token for validity')


class PublishResource():

    def __init__(self, db_handler):
        self.db = db_handler

    def _get_tenant_from_cache(self, tenant_id):
        """
        check cache for tenant if it is available
        """
        cache = NativeProxy()
        #todo: not sure if whole tenants are cached or just tenant ids
        #todo: will do discovery later
        #todo: refactor of json.loads on cache
        tenant_list = json.loads(cache.cache_get('tenants'))
        if tenant_id in tenant_list:
            return True
        else:
            return False

    def _get_tenant_from_coordinator(self, tenant_id, req):
        """
        contact the Coordinator API to verify the tenant id
        """
        # call to coordinator
        cache = NativeProxy()
        config = json.loads(cache.cache_get('worker_configuration'))
        coordinator_uri = config['coordinator_uri']

        token_header = {"WORKER-TOKEN": config['worker_token'],
                        "WORKER-ID": config['worker_id']}
        request_uri = "{0}/{1}/publish".format(
            coordinator_uri, tenant_id)

        try:
            resp = http_request(request_uri, token_header,
                                http_verb='POST')
            if resp.status_code == httplib.NOT_FOUND:
                #todo: look to see if coordinator should send or not
                _unauthorized_message()
        except requests.ConnectionError:
            _coordinator_connection_failure()


        #if the coordinator issues a response, cache the worker routes
        #and return true
        if resp.status_code == httplib.OK:
            routes = resp.json()

    def on_post(self, req, resp, tenant_id):

        #Validate the tenant's JSON event log data as valid JSON.
        body = load_body(req)
        message_token = req.get_header(MSG_TOKEN)

        #validate that tenant is cache locally
        tenant = self._get_tenant_from_cache(tenant_id)

        #call to coordinator api
        if not tenant:
            self._get_tenant_from_coordinator(tenant_id, message_token)


        if not tenant:
            _tenant_not_found()



        resp.status = falcon.HTTP_202
