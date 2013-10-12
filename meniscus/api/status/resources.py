import falcon

from meniscus import api
from meniscus.api.validator_init import get_validator
from meniscus.data.model.worker import SystemInfo
from meniscus.data.model.worker import Worker


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    api.abort(falcon.HTTP_404, 'Unable to locate worker.')


class WorkerStatusResource(api.ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    @api.handle_api_exception(operation_name='WorkerStatus PUT')
    @falcon.before(get_validator('worker_status'))
    def on_put(self, req, resp, worker_id, validated_body):
        """
        updates a worker's status
        """

        #load validated json payload in body
        body = validated_body['worker_status']

        #find the worker in db
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})

        if not worker_dict:
            _worker_not_found()

        worker = Worker(**worker_dict)

        if 'status' in body:
            worker.status = body['status']

        if 'system_info' in body:
            worker.system_info = SystemInfo(**body['system_info'])

        self.db.update('worker', worker.format_for_save())
        resp.status = falcon.HTTP_200

    @api.handle_api_exception(operation_name='WorkerStatus GET')
    def on_get(self, req, resp, worker_id):
        #find the worker in db
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})

        if not worker_dict:
            _worker_not_found()

        worker = Worker(**worker_dict)

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body({'status': worker.get_status()})


class WorkersStatusResource(api.ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    @api.handle_api_exception(operation_name='WorkersStatus GET')
    def on_get(self, req, resp):

        workers = self.db.find('worker')

        workers_status = [
            Worker(**worker).get_status()
            for worker in workers]

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body({'status': workers_status})
