import httplib
import falcon
import requests

from meniscus.api import ApiResource, load_body, abort
from meniscus.api.utils.request import http_request
from meniscus.openstack.common import jsonutils
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_event_producer_for_host
from meniscus.data.model.util import load_tenant_from_dict
from meniscus.proxy import NativeProxy


MSG_TOKEN = 'MESSAGE-TOKEN'


def _hostname_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, "malformed request, hostname cannot be empty")


def _producer_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, "malformed request, procname cannot be empty")


def _host_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'hostname not found for this tenant')


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

    def on_post(self, req, resp, tenant_id):

        #Validate the tenant's JSON event log data as valid JSON.
        body = load_body(req)
        message_token = req.get_header(MSG_TOKEN)

        # call to coordinator
        cache = NativeProxy()

        #attempt to validate message token from the cache
        if cache.cache_exists(tenant_id):
            tenant_info = jsonutils.loads(cache.cache_get(tenant_id))

            # Message token not valid abort
            if tenant_info['message_token'] != message_token:
                _unauthorized_message()

            # extract tenant object from cache
            tenant = load_tenant_from_dict(tenant_info['tenant_object'])

        else:
            # build head from cache to validate message token and tenant id
            config = jsonutils.loads(cache.cache_get('worker_configuration'))
            token_header = {"MESSAGE-TOKEN": message_token,
                            "WORKER-ID": config['worker_id'],
                            "WORKER-TOKEN": config['worker_token']
                            }
            request_uri = "{0}/{1}/token".format(
                config['coordinator_uri'], tenant_id)

            try:
                resp = http_request(request_uri, token_header,
                                    http_verb='HEAD')
                if resp.status_code != httplib.OK:
                    _unauthorized_message()
            except requests.ConnectionError:
                _coordinator_connection_failure()

            token_header = {"WORKER-ID": config['worker_id'],
                            "WORKER-TOKEN": config['worker_token']
                            }
            request_uri = "{0}/{1}".format(
                config['coordinator_uri'], tenant_id)

            try:
                resp = http_request(request_uri, token_header,
                                    http_verb='GET')
                if resp.status_code == httplib.OK:
                    response_body = resp.json()
                    tenant = load_tenant_from_dict(response_body['tenant'])
                else:
                    _coordinator_connection_failure()
            except requests.ConnectionError:
                _coordinator_connection_failure()

        # validate host with tenant
        if 'hostname' not in body.keys() or not body['hostname']:
            _hostname_not_provided()

        host = find_host(tenant, host_name=body['hostname'])

        if not host:
            _host_not_found()

        if 'procname' not in body.keys() or not body['procname']:
            _producer_not_provided()

        producer = find_event_producer_for_host(tenant, host, body['procname'])

        if not producer:
            #todo use default producer
            pass
        