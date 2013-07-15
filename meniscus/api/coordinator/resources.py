
import falcon

from meniscus.api import (ApiResource, format_response_body,
                          handle_api_exception)
from meniscus.data.model.worker import Worker
from meniscus.api.coordinator import coordinator_flow
from meniscus.api.validator_init import get_validator


class WorkerRegistrationResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    @handle_api_exception(operation_name='WorkerRegistration POST')
    @falcon.before(get_validator('worker_registration'))
    def on_post(self, req, resp, validated_body):
        """
        receives json req to register worker responds with a 202 for success
        """

        #load json payload in body
        body = validated_body['worker_registration']

        #instantiate new worker object
        new_worker = Worker(**body)

        #persist the new worker
        coordinator_flow.add_worker(self.db, new_worker)

        resp.status = falcon.HTTP_202
        resp.body = format_response_body(
            {'worker_identity': new_worker.get_registration_identity()})
