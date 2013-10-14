
import falcon

from meniscus import api
from meniscus.data.model.worker import Worker
from meniscus.data.model import worker_util
from meniscus.api.validator_init import get_validator


class WorkerRegistrationResource(api.ApiResource):
    """
    A Resource for registering of new worker nodes.
    """

    @api.handle_api_exception(operation_name='WorkerRegistration POST')
    @falcon.before(get_validator('worker_registration'))
    def on_post(self, req, resp, validated_body):
        """
        Registers a new worker when an HTTP POST is received
        and responds with a 202 for success
        """

        #load json payload in body
        body = validated_body['worker_registration']

        #instantiate new worker object
        new_worker = Worker(**body)

        #persist the new worker
        worker_util.create_worker(new_worker)

        resp.status = falcon.HTTP_202
        resp.body = api.format_response_body(
            {'worker_identity': new_worker.get_registration_identity()})
