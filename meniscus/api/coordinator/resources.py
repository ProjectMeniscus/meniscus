import json
import falcon
import uuid

from meniscus.api import ApiResource, load_body
from meniscus.data.model.coordinator import Worker
from meniscus.api import abort

## TODO: Please consider the following return code for bad requests
## http://tools.ietf.org/html/rfc2616#section-10.4.1

def _header_not_valid():
    """
    sends an http 401 invalid header
    """
    abort(falcon.HTTP_401, 'unauthorized request.')


def _role_not_valid():
    """
    sends an http 403 invalid role
    """
    abort(falcon.HTTP_403, 'roles do not have access to this resource.')


def _registration_not_valid():
    """
    sends an http 401 invalid registration request
    """
    abort(falcon.HTTP_401, 'invalid registration request.')


def _personality_not_valid():
    """
    sends an http 401 invalid registration request
    """
    abort(falcon.HTTP_401, 'invalid personality.')


def _worker_not_found():
    """
    sends an http 401 invalid registration request
    """
    abort(falcon.HTTP_401, 'unable to locate worker.')


def _configuration_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate configuration.')



class VersionResource(ApiResource):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


class WorkerRegistrationResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def _format_registration_response(self, worker):
        ## TODO: Avoid string concats - use .format and interpolation
        return {'personality_module': 'meniscus.persona.'
                                      + worker['personality'],
                'worker_id': worker['worker_id'],
                'worker_token': worker['worker_token']}

    def _validate_worker_body(self, body):
        """
        validate json
        """
        if not 'worker_registration' in body.keys():
            _registration_not_valid()
        # TODO: Returns are unnecessarry if the function will raise an error
        return True

    def _register_worker(self, body):
        """
        registers worker in db if worker exists update
        """
        #check if keys are there
        self._validate_worker_body(body)

        #mongodb does not return confirmation,
        #compartmentalized this chunk in case of having to search for
        worker_id = str(uuid.uuid4())
        worker_token = str(uuid.uuid4())

        new_worker = Worker(worker_id,
                            worker_token,
                            body['worker_registration']['hostname'],
                            body['worker_registration']['callback'],
                            body['worker_registration']['ip_address_v4'],
                            body['worker_registration']['ip_address_v6'],
                            body['worker_registration']['personality'],
                            body['worker_registration']['status'],
                            body['worker_registration']['system_info'])

        ## TODO: When this call returns, the db operation should be considered successful
        ## See: http://api.mongodb.org/python/current/api/pymongo/collection.html
        self.db.put('worker', new_worker.format())

        registered_worker = self.db.find_one(
            'worker', {'worker_id': new_worker.worker_id})
        confirmation = self._format_registration_response(registered_worker)
        return confirmation

    def on_post(self, req, resp):
        """
        receives json req to register worker responds with a 203 for success
        """

        #load json payload in body
        body = load_body(req)
        #try to register and return success or die
        confirmation = self._register_worker(body)

        ## TODO: Over-zealous checking of returns
        if confirmation:
            resp.status = falcon.HTTP_203
            resp.body = json.dumps(confirmation)
        else:
            _registration_not_valid()

    def _update_worker(self, req, worker_id):
        body = load_body(req)
        worker = self.db.find_one('worker', {'worker_id': worker_id})
        updated_worker = Worker(worker['worker_id'],
                                worker['worker_token'],
                                worker['hostname'],
                                worker['callback'],
                                worker['ip_address_v4'],
                                worker['ip_address_v6'],
                                worker['personality'],
                                body['worker_status'],
                                worker['system_info'])
        mongo_worker = updated_worker.format_for_save(worker['_id'])
        self.db.update('worker', mongo_worker)

    def on_put(self, req, resp, worker_id):
        self._update_worker(req, worker_id)
        resp.status = falcon.HTTP_200

    def on_get(self, req, resp):

        ## TODO: Constants should live in global scope and be prefixed with a '_' if they're not to be exported
        VALID_HEADER = 'X-Auth-Roles'
        VALID_ROLE = 'meniscus_role'

        roles = req.get_header(VALID_HEADER)

        if not roles:
            _header_not_valid()

        has_access = False

        for role in roles:
            if role == VALID_ROLE:
                has_access = True
                break

        if has_access:
            resp.status = falcon.HTTP_200
        else:
            _role_not_valid()

## TODO: Refactor into worker_configuration_api.py or something similar

class WorkerConfigurationResource(ApiResource):
    """
    configuration: listing of all workers downstream of the worker
    passes configuration to a worker based on the workers personality
    """
    #tuple of personalities
    PERSONALITIES = {'COR': 'worker.correlation',
                     'NORM': 'worker.normalization',
                     'STORE': 'worker.storage'}

    def __init__(self, db_handler):
        self.db = db_handler

    def _find_workers(self, personality):
        """
        finds all workers with personality parameter
        """
        worker_list = self.db.find('worker', {'personality': personality})
        return worker_list

    def _get_configuration(self, personality_type):
        """
        gets required configuration based on personality type
        correlation -> normalization,
        normalization -> storage,
        storage -> *data_node
        * = To be defined later
        """
        if personality_type == self.PERSONALITIES['COR']:
            return self._find_workers(self.PERSONALITIES['NORM'])
        elif personality_type == self.PERSONALITIES['NORM']:
            return self._find_workers(self.PERSONALITIES['STORE'])
        elif personality_type == self.PERSONALITIES['STORE']:
            #too be filled in with unique configuration probably storage nodes
            return {}
        else:
            _personality_not_valid()

    def _format_configuration(self, configuration):
        ## TODO: prefer list(), dict()... etc. over empty literals
        worker_list = []

        for worker in configuration:
            worker_list.append({'hostname': worker['hostname'],
                                'ip_address_v4': worker['ip_address_v4'],
                                'ip_address_v6': worker['ip_address_v6'],
                                'personality': worker['personality']})
        return {'pipeline_workers': worker_list}

    def on_get(self, req, resp, worker_id):
        """
        Gets configuration e.g. list of downstream personalities in the grid
        """

        ## TODO: consider other line breaks instead of using '\'
        reg_worker = \
            self.db.find_one('worker', {'worker_id': worker_id})
        if not reg_worker:
            _worker_not_found()

        configuration = self._get_configuration(reg_worker['personality'])
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(self._format_configuration(configuration))

