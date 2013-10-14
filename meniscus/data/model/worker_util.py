"""
The worker_util module provides an abstraction of database operations used
with instances fo the Worker class
"""

from meniscus.data.datastore import COORDINATOR_DB, datasource_handler
from meniscus.data.model.worker import Worker

_db_handler = datasource_handler(COORDINATOR_DB)


def create_worker(worker):
    """
    add new worker to db
    """
    _db_handler.put('worker', worker.format())


def find_worker(worker_id):
    """
    returns worker object based on worker id
    """
    worker_dict = _db_handler.find_one('worker', {'worker_id': worker_id})
    if worker_dict:
        return Worker(**worker_dict)
    return None


def save_worker(worker):
    """
    Updates an existing worker document
    """
    _db_handler.update('worker', worker.format_for_save())


def retrieve_all_workers():
    """
    Retreive all worker documents from the db and
    return a list of Worker objects
    """
    return [
        Worker(**worker_dict) for worker_dict in _db_handler.find('worker')
    ]
