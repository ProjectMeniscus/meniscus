from meniscus.queue import celery
from meniscus.normalization.lognorm import get_normalizer
from meniscus import env
import json


_LOG = env.get_logger(__name__)

normalizer = get_normalizer()


@celery.task(acks_late=True, max_retries=None, serializer="json")
def normalize_message(message):
    """Takes a message and normalizes it."""

    # If it's not the default syslog pattern, send it through the
    # normalizer
    should_normalize = ('pattern' in message and
                        message['pattern'] != 'syslog')
    can_normalize = ('msg' in message and
                     type(message['msg']) == 'string')
    if should_normalize and can_normalize:
        message['msg'] = json.loads(
            normalizer.normalize(message['msg']))
    return message
