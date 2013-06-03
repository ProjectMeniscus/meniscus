import falcon

from meniscus.api import (abort, ApiResource, format_response_body,
                          handle_api_exception, load_body)
from meniscus.data.model.worker import Worker


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    abort(falcon.HTTP_404, 'unable to locate worker.')


def _status_not_valid():
    """
    sends an http 400 invalid registration request
    """
    abort(falcon.HTTP_400, 'status update does not contain required fields.')


class WorkerStatusResource(ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    def _validate_req_body_on_put(self, body):
        """
        validate request body
        """

        # at least one status key must be present
        check_body = (
            'worker_status' in body,
            'load_average' in body, 'disk_usage' in body)

        if not any(check_body):
            _status_not_valid()

    @handle_api_exception(operation_name='WorkerStatus PUT')
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

        worker = Worker(**worker_dict)

        if 'worker_status' in body:
            worker.status = body['worker_status']

        if 'disk_usage' in body:
            worker.system_info.disk_usage = body['disk_usage']

        if 'load_average' in body:
            worker.system_info.load_average = body['load_average']

        self.db.update('worker', worker.format_for_save())
        resp.status = falcon.HTTP_200

    @handle_api_exception(operation_name='WorkerStatus GET')
    def on_get(self, req, resp, worker_id):
        #find the worker in db
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})

        if not worker_dict:
            _worker_not_found()

        worker = Worker(**worker_dict)

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'status': worker.get_status()})


class WorkersStatusResource(ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    @handle_api_exception(operation_name='WorkersStatus GET')
    def on_get(self, req, resp):

        workers = self.db.find('worker')

        workers_status = [
            Worker(**worker).get_status()
            for worker in workers]

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'status': workers_status})
