"""
The Status Resources module provides RESTful operations for managing
Worker status.  This includes the updating of a worker's status as well as the
retrieval of the status of a specified worker node, or all workers.
"""
import falcon

from meniscus import api
from meniscus.api.validator_init import get_validator
from meniscus.data.model.worker import SystemInfo
from meniscus.data.model import worker_util


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    api.abort(falcon.HTTP_404, 'Unable to locate worker.')


class WorkerStatusResource(api.ApiResource):
    """
    A resource for updating and retrieving data for a single worker node
    """

    @api.handle_api_exception(operation_name='WorkerStatus PUT')
    @falcon.before(get_validator('worker_status'))
    def on_put(self, req, resp, worker_id, validated_body):
        """
        updates a worker's status
        """

        #load validated json payload in body
        body = validated_body['worker_status']

        #find the worker in db
        worker = worker_util.find_worker(worker_id)

        if worker is None:
            _worker_not_found()

        if 'status' in body:
            worker.status = body['status']

        if 'system_info' in body:
            worker.system_info = SystemInfo(**body['system_info'])

        worker_util.save_worker(worker)
        resp.status = falcon.HTTP_200

    @api.handle_api_exception(operation_name='WorkerStatus GET')
    def on_get(self, req, resp, worker_id):
        """
        Retrieve the status of a specified worker node
        """
        #find the worker in db
        worker = worker_util.find_worker(worker_id)

        if worker is None:
            _worker_not_found()

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body({'status': worker.get_status()})


class WorkersStatusResource(api.ApiResource):
    """
    A resource for retrieving data about all worker nodes in a meniscus cluster
    """

    @api.handle_api_exception(operation_name='WorkersStatus GET')
    def on_get(self, req, resp):
        """
        Retrieve the status of all workers in the meniscus cluster
        """

        workers = worker_util.retrieve_all_workers()

        workers_status = [
            worker.get_status()
            for worker in workers]

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body({'status': workers_status})
