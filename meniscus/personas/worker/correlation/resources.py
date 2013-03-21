
import falcon
from uuid import uuid4

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import load_body
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_event_producer_for_host

from correlation_exceptions import CoordinatorCommunicationError
from correlation_exceptions import MessageAuthenticationError
from correlation_exceptions import MessageValidationError
from correlation_exceptions import ResourceNotFoundError
from validation import TenantIdentification
from validation import validate_event_message_body


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
        try:
            validate_event_message_body(body)

        except MessageValidationError as ex:
            abort(falcon.HTTP_400, ex.message)

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

        tenant_validator = TenantIdentification(
            self.cache, tenant_id, message_token)

        try:
            tenant = tenant_validator.get_validated_tenant()

        except MessageAuthenticationError as ex:
            abort(falcon.HTTP_401, ex.message)
        except ResourceNotFoundError as ex:
            abort(falcon.HTTP_404, ex.message)
        except CoordinatorCommunicationError:
            abort(falcon.HTTP_500)

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
