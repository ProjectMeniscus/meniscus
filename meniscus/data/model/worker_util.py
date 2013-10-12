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

