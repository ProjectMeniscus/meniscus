from meniscus.storage import default_store, short_term_store
from meniscus.sinks import DEFAULT_SINK, SECONDARY_SINKS

from meniscus.queue import celery


@celery.task
def persist_message(message):
    message_sinks = message['meniscus']['correlation']['sinks']

    if DEFAULT_SINK in message_sinks:
        default_store.persist_message.delay(message)

    if (set(message_sinks) & set(SECONDARY_SINKS)):
        short_term_store.persist_message.delay(message)
