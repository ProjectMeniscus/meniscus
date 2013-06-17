import falcon
from meniscus.api import ApiResource, handle_api_exception, load_body
from meniscus.api.pairing.pairing_process import PairingProcess
from meniscus.api.validator_init import get_validator


class PairingConfigurationResource(ApiResource):
    """
    Webhook callback for the system package coordinator to
    configure the worker for pairing with its coordinator
    """

    @handle_api_exception(operation_name='PairingConfiguration POST')
    @falcon.before(get_validator('pairing_configuration'))
    def on_post(self, req, resp, validated_body):
        body = validated_body['pairing_configuration']

        api_secret = body['api_secret']
        coordinator_uri = body['coordinator_uri']
        personality = body['personality']

        #start pairing on a separate process
        pairing_process = PairingProcess(
            api_secret, coordinator_uri, personality)
        pairing_process.run()

        resp.status = falcon.HTTP_200
