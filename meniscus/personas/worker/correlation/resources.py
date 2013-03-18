import httplib
import falcon
import requests

from meniscus.api import ApiResource, load_body, abort
from meniscus.api.utils.request import http_request
from meniscus.openstack.common import jsonutils
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_event_producer_for_host
from meniscus.data.model.util import load_tenant_from_dict
from meniscus.personas.worker.cache_params import CACHE_CONFIG
from meniscus.personas.worker.cache_params import CACHE_TENANT
from meniscus.personas.worker.cache_params import DEFAULT_EXPIRES
from meniscus.proxy import NativeProxy


MSG_TOKEN = 'MESSAGE-TOKEN'


def _tenant_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate tenant.')


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

    def _validate_req_body_on_post(self, body):
        """
        This method validates the on_post request body
        """
    # validate host with tenant
        if 'hostname' not in body.keys() or not body['hostname']:
            _hostname_not_provided()

        if 'procname' not in body.keys() or not body['procname']:
            _producer_not_provided()

    def _get_validated_tenant_from_cache(
            self, cache, tenant_id, message_token):
        """
        This method is called to validate the message token and tenant in the
        cache if it is exists.
        """

        if cache.cache_exists(tenant_id, CACHE_TENANT):
            tenant_info = jsonutils.loads(
                cache.cache_get(tenant_id, CACHE_TENANT))

            # Message token not valid abort
            if tenant_info['message_token'] != message_token:
                _unauthorized_message()

            # extract tenant object from cache
            tenant = load_tenant_from_dict(tenant_info['tenant_object'])
            return tenant

        return None

    def _get_validated_tenant_from_coordinator(
            self, cache, tenant_id, message_token):
        """
        This method calls to the coordinator to validate the message
        token and tenant
        """

        # build head from cache to validate message token and tenant id
        config = jsonutils.loads(cache.cache_get(
            'worker_configuration', CACHE_CONFIG))

        token_header = {
            "MESSAGE-TOKEN": message_token,
            "WORKER-ID": config['worker_id'],
            "WORKER-TOKEN": config['worker_token']
        }

        request_uri = "{0}/{1}/token".format(
            config['coordinator_uri'], tenant_id)

        try:
            resp = http_request(request_uri, token_header,
                                http_verb='HEAD')

            if resp.status_code == httplib.NOT_FOUND:
                _tenant_not_found()

            if resp.status_code != httplib.OK:
                _unauthorized_message()
        except requests.ConnectionError:
            _coordinator_connection_failure()

        token_header = {
            "WORKER-ID": config['worker_id'],
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
                return tenant

            else:
                _tenant_not_found()

        except requests.ConnectionError:
            _coordinator_connection_failure()

    def on_post(self, req, resp, tenant_id):
        """
        This method is passed log event data by a tenant. The request will
        have a message token and a tenant id which must be validated either
        by the local cache or by a call to this workers coordinator.
        """
        #Validate the tenant's JSON event log data as valid JSON.
        body = load_body(req)
        self._validate_req_body_on_post(body)

        message_token = req.get_header(MSG_TOKEN)

        cache = NativeProxy()

        #attempt to retrieve valid tenant and message token from cache
        tenant = self._get_validated_tenant_from_cache(
            cache, tenant_id, message_token)

        #if no valid tenant request from coordinator
        if not tenant:
            tenant = self._get_validated_tenant_from_coordinator(
                cache, tenant_id, message_token)

            #cache the tenant info
            tenant_cache = {
                'message_token': message_token,
                'tenant_object': tenant.format()}

            cache.cache_set(tenant_id,jsonutils.dumps(tenant_cache),
                            CACHE_TENANT, DEFAULT_EXPIRES)

        host = find_host(tenant, host_name=body['hostname'])

        if not host:
            _host_not_found()

        producer = find_event_producer_for_host(tenant, host, body['procname'])

        if not producer:
            #todo use default producer
            pass

        if producer.durable:
            resp.status = falcon.HTTP_202
            #todo identify uuid and meniscus uri

        else:
            resp.status = falcon.HTTP_204
