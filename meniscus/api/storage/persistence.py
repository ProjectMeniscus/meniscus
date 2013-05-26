import eventlet
eventlet.monkey_patch()

from meniscus.api.datastore_init import db_handler
from meniscus.queue import celery


@celery.task(acks_late=True, max_retries=0,
             ignore_result=True, serializer="json")
def persist_message(message):
    """Takes a message dict and persists it to the configured database."""
    #try:
    _sink = db_handler()
    _sink.close()
    _sink.connect()
    _sink.put('logs', message)
    _sink.close()
    #except:
     #   persist_message.retry()
