from meniscus.api.datastore_init import db_handler
from meniscus.queue.resources import celery

@celery.task
def _persist_message(message):
    """Takes a message dict and persists it to the configured database."""
    _sink = db_handler()
    _sink.put('logs', message)


def persist_message(message):
     return   _persist_message.delay(message)
