
import falcon

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import load_body
from meniscus.api.tenant.resources import MESSAGE_TOKEN

from correlation_exceptions import CoordinatorCommunicationError
from correlation_exceptions import MessageAuthenticationError
from correlation_exceptions import MessageValidationError
from correlation_exceptions import ResourceNotFoundError
from correlation_process import CorrelationMessage
from correlation_process import TenantIdentification
from correlation_process import validate_event_message_body


def _host_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'hostname not found for this tenant')


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

        #read message token from header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        tenant_validator = TenantIdentification(
            self.cache, tenant_id, message_token)

        try:
            tenant = tenant_validator.get_validated_tenant()
            message = CorrelationMessage(tenant, body)
            message.process_message()

        except MessageAuthenticationError as ex:
            abort(falcon.HTTP_401, ex.message)
        except ResourceNotFoundError as ex:
            abort(falcon.HTTP_404, ex.message)
        except CoordinatorCommunicationError:
            abort(falcon.HTTP_500)

        #todo(sgonzales) provide job json in response body
        if message.durable:
            resp.status = falcon.HTTP_202

        else:
            resp.status = falcon.HTTP_204

