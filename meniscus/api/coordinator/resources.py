
import falcon

from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.data.model.worker import Worker
from meniscus.api.coordinator import coordinator_flow
from meniscus.api.coordinator import watchlist_flow


class WorkerWatchlistResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_put(self, req, resp, worker_id):
        """
        tracks worker failure in watchlist table
        """
        # process the non-responsive worker
        watchlist_flow.process_watchlist_item(self.db, worker_id)

        resp.status = falcon.HTTP_202


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


class WorkerRoutesResource(ApiResource):
    """
    configuration: listing of all workers downstream of the worker
    passes configuration to a worker based on the workers personality
    """
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, worker_id):
        """
        Gets configuration: list of downstream personalities in the grid
        """
        routes = coordinator_flow.get_routes(self.db, worker_id)

        resp.status = falcon.HTTP_200
        resp.body = format_response_body(routes)
