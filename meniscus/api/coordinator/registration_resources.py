import falcon
import uuid

from meniscus.api import ApiResource, load_body, format_response_body
from meniscus.data.model.coordinator import Worker
from meniscus.api import abort

#CONSTANTS FOR Worker Registration on_get
_VALID_HEADER = 'X-Auth-Roles'
_VALID_ROLE = 'meniscus_role'


def _header_not_valid():
    """
    sends an http 400 invalid header
    """
    abort(falcon.HTTP_400, 'unauthorized request.')


def _role_not_valid():
    """
    sends an http 400 invalid role
    """
    abort(falcon.HTTP_400, 'roles do not have access to this resource.')


def _registration_not_valid():
    """
    sends an http 400 invalid registration request
    """
    abort(falcon.HTTP_400, 'invalid registration request.')


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
        return {'personality_module': 'meniscus.personas.{0}'
                .format(worker['personality']),
                'worker_id': worker['worker_id'],
                'worker_token': worker['worker_token']}

    def _validate_worker_body(self, body):
        """
        validate json
        """
        if not 'worker_registration' in body.keys():
            _registration_not_valid()

    def _register_worker(self, body):
        """
        registers worker in db if worker exists update
        """
        #check if keys are there
        self._validate_worker_body(body)

        # worker_id = str(uuid.uuid4())
        # worker_token = str(uuid.uuid4())

        #instantiate new worker object
        new_worker = Worker(str(uuid.uuid4()), str(uuid.uuid4()))

        #set network layer stats
        new_worker.set_worker_network_layer_stats(
            body['worker_registration']['hostname'],
            body['worker_registration']['callback'],
            body['worker_registration']['ip_address_v4'],
            body['worker_registration']['ip_address_v6'])

        #set worker personality stats
        new_worker.set_worker_personality_stats(
            body['worker_registration']['personality'],
            body['worker_registration']['status'],
            body['worker_registration']['system_info'])

        self.db.put('worker', new_worker.format())
        return self._format_registration_response(new_worker.format())

    def on_post(self, req, resp):
        """
        receives json req to register worker responds with a 202 for success
        """

        #load json payload in body
        body = load_body(req)

        #Register worker and store in confirmation
        confirmation = self._register_worker(body)

        resp.status = falcon.HTTP_202
        resp.body = format_response_body(confirmation)

    def _update_worker(self, req, worker_id):
        """
        finds worker based on worker_id parameter, updates the worker
        with the new status
        """
        #load json payload in body
        body = load_body(req)

        #find the worker in db
        worker = self.db.find_one('worker', {'worker_id': worker_id})

        #update worker status taken from json body
        updated_worker = Worker(worker['worker_id'], worker['worker_token'])

        updated_worker.set_worker_network_layer_stats(worker['hostname'],
                                                      worker['callback'],
                                                      worker['ip_address_v4'],
                                                      worker['ip_address_v6'])

        updated_worker.set_worker_personality_stats(worker['personality'],
                                                    body['worker_status'],
                                                    worker['system_info'])
        mongo_worker = updated_worker.format_for_save(worker['_id'])
        self.db.update('worker', mongo_worker)

    def on_put(self, req, resp, worker_id):
        """
        update worker on_put. calls _update_worker() passing in the worker_id
        and the request with the new worker_status
        """
        self._update_worker(req, worker_id)
        resp.status = falcon.HTTP_200

    def on_get(self, req, resp):
        """
        Validate roles header
        """
        roles = req.get_header(_VALID_HEADER)

        if not roles:
            _header_not_valid()

        has_access = False

        for role in roles:
            if role == _VALID_ROLE:
                has_access = True
                break

        if has_access:
            resp.status = falcon.HTTP_200
        else:
            _role_not_valid()

