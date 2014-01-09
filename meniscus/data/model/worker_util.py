"""
The worker_util module provides an abstraction of database operations used
with instances fo the Worker class
"""

from meniscus.data.handlers import mongodb
from meniscus.data.model.worker import Worker

_db_handler = mongodb.get_handler()


def create_worker(worker):
    """
    add new worker to db
    """
    _db_handler.put('worker', worker.format())


def find_worker(hostname):
    """
    returns worker object based on hostname
    """
    worker_dict = _db_handler.find_one('worker', {'hostname': hostname})
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
    Retrieve all worker documents from the db and
    return a list of Worker objects
    """
    return [
        Worker(**worker_dict) for worker_dict in _db_handler.find('worker')
    ]
