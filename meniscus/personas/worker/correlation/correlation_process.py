import httplib
from uuid import uuid4
import requests

from correlation_exceptions import CoordinatorCommunicationError
from correlation_exceptions import MessageAuthenticationError
from correlation_exceptions import MessageValidationError
from correlation_exceptions import ResourceNotFoundError
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.utils.request import http_request
from meniscus.data.model.util import find_event_producer_for_host
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_tenant_in_cache
from meniscus.data.model.util import find_token_in_cache
from meniscus.data.model.util import load_tenant_from_dict
from meniscus.data.model.util import persist_tenant_to_cache
from meniscus.data.model.util import persist_token_to_cache
from meniscus.openstack.common import jsonutils
from meniscus.personas.worker.cache_params import CACHE_CONFIG


def validate_event_message_body(body):
    """
    This method validates the on_post request body
    """
    # validate host with tenant
    if 'host' not in body.keys() or not body['host']:
        raise MessageValidationError("host cannot be empty")

    if 'pname' not in body.keys() or not body['pname']:
        raise MessageValidationError("pname cannot be empty")

    if 'time' not in body.keys() or not body['time']:
        raise MessageValidationError("time cannot be empty")

    return True


class CorrelationMessage(object):
    def __init__(self, tenant, message):
        self.tenant = tenant
        self.message = message
        self.durable = False
        self.job_id = None
        self.job_info = None

    def process_message(self):
        host = find_host(self.tenant, host_name=self.message['host'])

        if not host:
            raise MessageValidationError(
                "invalid host, host with name {0} cannot be located"
                .format(self.message['host']))

            #initialize correlation dictionary with default values
        correlation_dict = {
            'host_id': host.get_id(),
            'ep_id': None,
            'pattern': None
        }

        producer = find_event_producer_for_host(
            self.tenant, host, self.message['pname'])

        if producer:
            self.durable = producer.durable
            correlation_dict.update({
                'ep_id': producer.get_id(),
                'pattern': producer.pattern
            })

            if producer.durable:
                job_id = str(uuid4())
                correlation_dict.update({'job_id': job_id})
                #todo(sgonzales) persist message and create job

        self.message.update({
            "profile": "http://projectmeniscus.org/cee/profiles/base",
            "meniscus": {
                "correlation": correlation_dict
            }
        })

        #todo(sgonzales) pass message to normalization worker


class TenantIdentification(object):
    def __init__(self, cache, tenant_id, token):
        self.cache = cache
        self.tenant_id = tenant_id
        self.token = token

    def get_validated_tenant(self):

        #check if the token is in the cache
        token = find_token_in_cache(self.cache, self.tenant_id)
        if token:
            #validate token
            if not token.validate_token(self.token):
                raise MessageAuthenticationError(
                    'Message not authenticated, check your tenant id '
                    'and or message token for validity')

            #get the tenant object from cache
            tenant = find_tenant_in_cache(self.cache, self.tenant_id)

            #if tenant is not in cache, ask the coordinator
            if not tenant:
                tenant = self._get_tenant_from_coordinator()
                persist_tenant_to_cache(self.cache, tenant)
        else:
            self._validate_token_with_coordinator()
            persist_token_to_cache(self.cache, self.tenant_id, token)

            #get tenant from coordinator
            tenant = self._get_tenant_from_coordinator()
            persist_tenant_to_cache(self.cache, tenant)

        return tenant

    def _validate_token_with_coordinator(self):
        """
        This method calls to the coordinator to validate the message token
        """

        config = jsonutils.loads(self.cache.cache_get(
            'worker_configuration', CACHE_CONFIG))

        token_header = {
            MESSAGE_TOKEN: self.token,
            "WORKER-ID": config['worker_id'],
            "WORKER-TOKEN": config['worker_token']
        }

        request_uri = "{0}/{1}/token".format(
            config['coordinator_uri'], self.tenant_id)

        try:
            resp = http_request(request_uri, token_header,
                                http_verb='HEAD')

            if resp.status_code == httplib.NOT_FOUND:
                raise ResourceNotFoundError('Unable to locate tenant.')

            if resp.status_code != httplib.OK:
                raise MessageAuthenticationError(
                    'Message not authenticated, check your tenant id '
                    'and or message token for validity')

        except requests.ConnectionError:
            raise CoordinatorCommunicationError

        return True

    def _get_tenant_from_coordinator(self):
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
            config['coordinator_uri'], self.tenant_id)

        try:
            resp = http_request(request_uri, token_header,
                                http_verb='GET')

            if resp.status_code == httplib.OK:
                response_body = resp.json()
                tenant = load_tenant_from_dict(response_body['tenant'])
                return tenant

            else:
                raise ResourceNotFoundError('Unable to locate tenant.')

        except requests.ConnectionError:
            raise CoordinatorCommunicationError

