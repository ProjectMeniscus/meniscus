from meniscus.api.datastore_init import db_handler
from meniscus.queue import celery
from meniscus import env


LOG = env.get_logger(__name__)


@celery.task(acks_late=True, max_retries=0,
             ignore_result=True, serializer="json")
def persist_message(message):
    """Takes a message and persists it to the datastore."""
    try:
        _sink = db_handler()
        _sink.put('logs', message)
    except Exception as ex:
        LOG.exception(ex)
        persist_message.retry()
