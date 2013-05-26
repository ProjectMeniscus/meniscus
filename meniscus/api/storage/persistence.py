
#from meniscus.api.datastore_init import db_handler
import eventlet
from meniscus.queue import celery
datastore_init = eventlet.import_patched('meniscus.api.datastore_init')


@celery.task(acks_late=True, max_retries=0,
             ignore_result=True, serializer="json")
def persist_message(message):
    """Takes a message dict and persists it to the configured database."""
    #try:
    _sink = datastore_init.db_handler()
    _sink.close()
    _sink.connect()
    _sink.put('logs', message)
    _sink.close()
    #except:
     #   persist_message.retry()
