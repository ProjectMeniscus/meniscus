from meniscus.queue import celery
from meniscus.api.normalization.lognorm import get_normalizer
from meniscus import env
import json


_LOG = env.get_logger(__name__)

normalizer = get_normalizer()


@celery.task(acks_late=True, max_retries=None, serializer="json")
def normalize_message(message):
    """Takes a message and normalizes it."""
    if message['message'] and type(message['message']) == 'string':
        message['message'] = json.loads(
            normalizer.normalize(message['message']))
    return message
