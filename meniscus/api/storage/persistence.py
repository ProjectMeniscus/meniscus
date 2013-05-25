from meniscus.api.datastore_init import db_handler
from meniscus.queue import celery
from pyes.connection_http import NoServerAvailable


@celery.task(acks_late=True, ignore_result=True, serializer="json")
def persist_message(message):
    """Takes a message dict and persists it to the configured database."""
    try:
        _sink = db_handler()
        _sink.put('logs', message)
    except NoServerAvailable:
        persist_message.retry()
