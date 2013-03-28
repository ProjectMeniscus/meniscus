import falcon
from meniscus.api.pairing.pairing_process import PairingProcess
from meniscus.api import ApiResource, load_body, format_response_body


class PairingConfigurationResource(ApiResource):
    """
    Webhook callback for the system package coordinator to
    configure the worker for pairing with its coordinator
    """

    def on_post(self, req, resp):
        body = load_body(req)

        api_secret = body['api_secret']
        coordinator_uri = body['coordinator_uri']
        personality = body['personality']

        #start pairing on a separate process
        pairing_process = PairingProcess(
            api_secret, coordinator_uri, personality)
        pairing_process.run()

        resp.status = falcon.HTTP_200
