import falcon

from meniscus.api import (abort, ApiResource, format_response_body,
                          handle_api_exception, load_body)
from meniscus.api.validator_init import get_validator
from meniscus.data.model.worker import Worker


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    abort(falcon.HTTP_404, 'unable to locate worker.')


class WorkerStatusResource(ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    @handle_api_exception(operation_name='WorkerStatus PUT')
    @falcon.before(get_validator('worker_status'))
    def on_put(self, req, resp, worker_id, validated_body):
        """
        updates a worker's status
        """

        #load validated json payload in body
        body = validated_body

        #find the worker in db
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})

        if not worker_dict:
            _worker_not_found()

        worker = Worker(**worker_dict)

        if 'status' in body:
            worker.status = body['status']

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
