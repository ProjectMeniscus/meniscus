
import falcon

from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.data.model.worker import Worker
from meniscus.api.coordinator import coordinator_flow


class WorkerRegistrationResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_post(self, req, resp):
        """
        receives json req to register worker responds with a 202 for success
        """

        #load json payload in body
        body = load_body(req)
        coordinator_flow.validate_worker_registration_req_body(body)

        #instantiate new worker object
        new_worker = Worker(**body['worker_registration'])

        #persist the new worker
        coordinator_flow.add_worker(self.db, new_worker)

        resp.status = falcon.HTTP_202
        resp.body = format_response_body(
            new_worker.get_registration_identity())
