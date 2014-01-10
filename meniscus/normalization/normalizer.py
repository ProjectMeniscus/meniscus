from meniscus import env
from meniscus.queue import celery
from meniscus.normalization.lognorm import get_normalizer
from meniscus import sinks
import json


_LOG = env.get_logger(__name__)
_normalizer, loaded_normalizer_rules = get_normalizer()


def should_normalize(message):
    """Returns true only if the pattern is in the loaded rules
    list and there is a string msg in the message dictionary"""
    should_normalize = (
        message['meniscus']['correlation']['pattern'] in
        loaded_normalizer_rules)
    can_normalize = ('msg' in message)
    return should_normalize and can_normalize


@celery.task(acks_late=True, max_retries=None, serializer="json")
def normalize_message(message):
    """
    This code takes a message and normalizes it into a dictionary. This
    normalized dictionary is assigned to a field matching the pattern name
    of the normalization. This dictionary is then assigned to the message
    under the normalized field.
    """
    pattern = message['meniscus']['correlation']['pattern']
    normalized_doc = json.loads(
        _normalizer.normalize(message['msg']).as_json())
    message['normalized'] = {
        pattern: normalized_doc
    }
    sinks.route_message(message)
