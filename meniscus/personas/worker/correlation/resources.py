import httplib

import falcon
import requests
from uuid import uuid4

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import load_body
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.utils.request import http_request
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_event_producer_for_host
from meniscus.data.model.util import find_tenant_in_cache
from meniscus.data.model.util import find_token_in_cache
from meniscus.data.model.util import load_tenant_from_dict
from meniscus.data.model.util import persist_tenant_to_cache
from meniscus.data.model.util import persist_token_to_cache
from meniscus.openstack.common import jsonutils
from meniscus.personas.worker.cache_params import CACHE_CONFIG


def _tenant_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate tenant.')


def _host_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, "malformed request, host cannot be empty")


def _producer_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, "malformed request, procname cannot be empty")


def _time_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, "malformed request, time cannot be empty")


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


class PublishMessageResource(ApiResource):

    def __init__(self, cache):
        self.cache = cache

    def _validate_req_body_on_post(self, body):
        """
        This method validates the on_post request body
        """
    # validate host with tenant
        if 'host' not in body.keys() or not body['host']:
            _host_not_provided()

        if 'pname' not in body.keys() or not body['pname']:
            _producer_not_provided()

        if 'time' not in body.keys() or not body['time']:
            _time_not_provided()

        return True

    def _get_tenant_from_coordinator(self, tenant_id):
        """
        This method calls to the coordinator to validate the message
        token and tenant
        """

        config = jsonutils.loads(self.cache.cache_get(
            'worker_configuration', CACHE_CONFIG))

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

    def _validate_token_with_coordinator(
            self, tenant_id, message_token):
        """
        This method calls to the coordinator to validate the message token
        """

        config = jsonutils.loads(self.cache.cache_get(
            'worker_configuration', CACHE_CONFIG))

        token_header = {
            MESSAGE_TOKEN: message_token,
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

            return True

        except requests.ConnectionError:
            _coordinator_connection_failure()

        return False

    def on_post(self, req, resp, tenant_id):
        """
        This method is passed log event data by a tenant. The request will
        have a message token and a tenant id which must be validated either
        by the local cache or by a call to this workers coordinator.
        """
        #Validate the tenant's JSON event log data as valid JSON.
        body = load_body(req)
        self._validate_req_body_on_post(body)
        message_dict = body

        #read message token from header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        #check if the token is in the cache
        token = find_token_in_cache(self.cache, tenant_id)
        if token:
            #validate token
            if not token.validate_token(message_token):
                _unauthorized_message()

            #get the tenant object from cache
            tenant = find_tenant_in_cache(self.cache, tenant_id)

            #if tenant is not in cache, ask the coordinator
            if not tenant:
                tenant = self._get_tenant_from_coordinator(tenant_id)
                persist_tenant_to_cache(self.cache, tenant)
        else:
            self._validate_token_with_coordinator(tenant_id, message_token)
            persist_token_to_cache(self.cache, tenant_id, token)

            #get tenant from coordinator
            tenant = self._get_tenant_from_coordinator(tenant_id)
            persist_tenant_to_cache(self.cache, tenant)

        host = find_host(tenant, host_name=body['hostname'])

        if not host:
            _host_not_found()

        #initialize correlation dictionary with default values
        correlation_dict = {
            'host_id': host.get_id(),
            'ep_id': None,
            'pattern': None
        }

        producer = find_event_producer_for_host(tenant, host, body['procname'])

        if producer:
            correlation_dict.update({
                'ep_id': producer.get_id(),
                'pattern': producer.pattern
            })

            if producer.durable:
                job_id = str(uuid4())
                correlation_dict.update({'job_id': job_id})
                #todo(sgonzales) persist message and create job

        message_dict.update({
            "profile": "http://projectmeniscus.org/cee/profiles/base",
            "meniscus": {
                "correlation": correlation_dict
            }
        })

        #todo(sgonzales) provide job json in response body
        if producer and producer.durable:
            resp.status = falcon.HTTP_202

        else:
            resp.status = falcon.HTTP_204

        #todo(sgonzales) pass message to normalization worker
