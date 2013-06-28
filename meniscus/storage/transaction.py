import time

from meniscus.data.datastore import datasource_handler, SHORT_TERM_SINK
from meniscus.queue import celery

_db_handler = datasource_handler(SHORT_TERM_SINK)


class Transaction(object):

    def _lock_records(self):
        raise NotImplementedError

    def _retrieve_locked_records(self):
        raise NotImplementedError

    def _process_locked_records(self):
        raise NotImplementedError

    def _release_lock(self):
        raise NotImplementedError

    def process_transaction(self):
        raise NotImplementedError


class BatchMessageTransaction(Transaction):

    def __init__(self, sink_name, transaction_id, expire_seconds):
        self.db_handler = _db_handler
        self.transaction_field_base = "meniscus.correlation.destinations"
        self.transaction_field = "{0}.{1}".format(
            self.transaction_field_base, sink_name)
        self.id_field = "{0}.transaction_id".format(self.transaction_field)
        self.time_field = "{0}.transaction_time".format(self.transaction_field)

        self.transaction_id = transaction_id
        self.transaction_time = time.time()
        self.threshold_time = self.transaction_time - expire_seconds
        self.expire_seconds = expire_seconds
        self.locked_records = None

    def _lock_records(self):

        lock_fields = {
            self.id_field: self.transaction_id,
            self.time_field: self.transaction_time
        }

        update_filter = {
            "$and": [
                {self.transaction_field: {"$exists": True}},
                {
                    "$or": [
                        {self.time_field: {"$lt": self.threshold_time}},
                        {self.time_field: None}
                    ]
                }
            ]
        }

        self.db_handler.set_field("logs", lock_fields, update_filter)

    def _retrieve_locked_records(self):

        query_filter = {self.id_field: self.transaction_id}
        fields = {"_id": False}

        self.locked_records = self.db_handler.find(
            'logs', query_filter, fields)

    def _process_locked_records(self):
        raise NotImplementedError

    def _release_lock(self):

        _release_lock_task.delay(
            self.transaction_field, self.id_field, self.transaction_id)

    def process_transaction(self):
        self._lock_records()
        self._retrieve_locked_records()

        if self.locked_records.count():
            self._process_locked_records()
            self._release_lock()


@celery.task(name="transaction.release",
             max_retries=5, interval_start=30)
def _release_lock_task(transaction_field, id_field, transaction_id):
    db_handler = _db_handler
    remove_field = {transaction_field: ""}
    update_filter = {id_field: transaction_id}
    try:
        db_handler.remove_field("logs", remove_field, update_filter)
    except:
        _release_lock_task.retry()
