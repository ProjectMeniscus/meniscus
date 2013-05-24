import falcon

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.api.correlation import correlator
import meniscus.api.correlation.correlation_exceptions as errors
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.storage.persistence import persist_message


class PublishMessageResource(ApiResource):

    def _validate_req_body_on_post(self, body):
        """
        This method validates the on_post request body
        """
        try:
            correlator.validate_event_message_body(body)

        except errors.MessageValidationError as ex:
            abort(falcon.HTTP_400, ex.message)

    def on_post(self, req, resp, tenant_id):
        """
        This method is passed log event data by a tenant. The request will
        have a message token and a tenant id which must be validated either
        by the local cache or by a call to this workers coordinator.
        """

        #read message token from header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        #Validate the tenant's JSON event log data as valid JSON.
        message = load_body(req)
        self._validate_req_body_on_post(message)

        tenant_identification = correlator.TenantIdentification(
            tenant_id, message_token)

        try:
            tenant = tenant_identification.get_validated_tenant()
            message = correlator.add_correlation_info_to_message(
                tenant, message)

        except errors.MessageAuthenticationError as ex:
            abort(falcon.HTTP_401, ex.message)
        except errors.ResourceNotFoundError as ex:
            abort(falcon.HTTP_404, ex.message)
        except errors.CoordinatorCommunicationError:
            abort(falcon.HTTP_500)

        persist_message(message)

        #if message is durable, return durable job info
        if message['meniscus']['correlation']['durable']:
            durable_job_id = message['meniscus']['correlation']['job_id']
            job_status_uri = "http://{0}/v1/job/{1}/status" \
                .format("meniscus_uri", durable_job_id)

            resp.status = falcon.HTTP_202
            resp.body = format_response_body(
                {
                    "job_id": durable_job_id,
                    "job_status_uri": job_status_uri
                }
            )

        else:
            resp.status = falcon.HTTP_204
