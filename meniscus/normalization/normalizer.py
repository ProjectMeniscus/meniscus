from meniscus.queue import celery
from meniscus.normalization.lognorm import get_normalizer
from meniscus import env
import json


_LOG = env.get_logger(__name__)

normalizer = get_normalizer()


def should_normalize(message):
    should_normalize = ('pattern' in message and
                        message['pattern'] != 'syslog')
    can_normalize = ('msg' in message and
                     type(message['msg']) == str)
    return should_normalize and can_normalize


@celery.task(acks_late=True, max_retries=None, serializer="json")
def normalize_message(message):
    """Takes a message and normalizes it."""
    message['msg'] = json.loads(
        normalizer.normalize(message['msg']).as_json())
    return message
