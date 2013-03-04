import falcon
import json

from meniscus.api import ApiResource, load_body, abort


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


def _validate_worker_request(body):
    """
    validate requests
    """

    if body['event']['type'] != 'worker.registration' or \
            not body['event']['callback']:
        _registration_not_valid()
    return True


def _register_worker(body):
    """
    registers worker in mongodb
    """

    is_valid_request = _validate_worker_request(body)

    if is_valid_request:
        #register worker in mongodb
        pass
    #queue configuration callback for new worker
    return True


class VersionResource(ApiResource):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


class WorkerRegistrationResource(ApiResource):

    def on_post(self, req, resp):
        body = load_body(req)
        is_registered = _register_worker(body)

        if is_registered:
            resp.status = falcon.HTTP_202
        else:
            _registration_not_valid()


class WorkerConfigurationResource(ApiResource):

    def on_get(self, req, resp):

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

    pass