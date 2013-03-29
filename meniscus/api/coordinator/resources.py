
import falcon

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.api.personalities import PERSONALITIES
from meniscus.data.model.worker import Worker


def _personality_not_valid():
    """
    sends an http 400 invalid personality request
    """
    abort(falcon.HTTP_400, 'invalid personality.')


def _registration_not_valid():
    """
    sends an http 400 invalid registration request
    """
    abort(falcon.HTTP_400, 'invalid registration request.')


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    abort(falcon.HTTP_404, 'unable to locate worker.')


class WorkerConfigurationResource(ApiResource):
    """
    configuration: listing of all workers downstream of the worker
    passes configuration to a worker based on the workers personality
    """

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, worker_id):
        """
        Gets configuration e.g. list of downstream personalities in the grid
        """
        worker_dict = self.db.find_one(
            'worker', {'worker_id': worker_id})
        if not worker_dict:
            _worker_not_found()

        worker = Worker(**worker_dict)
        downstream = PERSONALITIES.get(worker.personality).get('downstream')
        downstream_workers = self.db.find(
            'worker', {'personality': downstream})

        pipeline = [
            Worker(worker).get_pipeline_info()
            for worker in downstream_workers]

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'pipeline_workers': pipeline})


class WorkerRegistrationResource(ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    def _format_registration_response(self, worker):
        """
        returns response for a successfully registered worker request
        """
        return {'personality_module': 'meniscus.personas.{0}.app'
                .format(worker['personality']),
                'worker_id': worker['worker_id'],
                'worker_token': worker['worker_token']}

    def _validate_req_body_on_post(self, body):
        """
        validate request body
        """
        if not 'worker_registration' in body.keys():
            _registration_not_valid()
        worker_registration = body['worker_registration']
        if worker_registration.get('personality') not in PERSONALITIES:
            _personality_not_valid()

    def on_post(self, req, resp):
        """
        receives json req to register worker responds with a 202 for success
        """

        #load json payload in body
        body = load_body(req)

        self._validate_req_body_on_post(body)

        #instantiate new worker object
        new_worker = Worker(**body['worker_registration'])

        #persist the new worker
        self.db.put('worker', new_worker.format())

        resp.status = falcon.HTTP_202
        resp.body = format_response_body(
            new_worker.get_registration_identity())

    def _validate_req_body_on_put(self, body):
        """
        validate request body
        """
        if not 'worker_status' in body:
            _registration_not_valid()

    def on_put(self, req, resp, worker_id):
        """
        updates a worker's status
        """
        #load json payload in body
        body = load_body(req)
        self._validate_req_body_on_put(body)

        #find the worker in db
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})

        if not worker_dict:
            _worker_not_found()

        worker = Worker(worker_dict)

        self.db.update('worker', worker.format_for_save())
        resp.status = falcon.HTTP_200
