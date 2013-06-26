import falcon

from meniscus.api import (abort, ApiResource, format_response_body,
                          handle_api_exception)
from meniscus.api.correlation import correlator
import meniscus.api.correlation.correlation_exceptions as errors
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.validator_init import get_validator
from meniscus.sinks import dispatch


class PublishMessageResource(ApiResource):

    @handle_api_exception(operation_name='Publish Message POST')
    @falcon.before(get_validator('correlation'))
    def on_post(self, req, resp, tenant_id, validated_body):
        """
        This method is passed log event data by a tenant. The request will
        have a message token and a tenant id which must be validated either
        by the local cache or by a call to this workers coordinator.
        """

        #read message token from header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        #Validate the tenant's JSON event log data as valid JSON.
        message = validated_body['log_message']

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

        dispatch.persist_message(message)

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
