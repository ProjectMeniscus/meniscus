from meniscus.sinks import (
    default_sink, DEFAULT_SINK, SECONDARY_SINKS, short_term_sink)


def persist_message(message):
    message_sinks = message['meniscus']['correlation']['sinks']

    if DEFAULT_SINK in message_sinks:
        default_sink.persist_message.delay(message)

    if (set(message_sinks) & set(SECONDARY_SINKS)):
        short_term_sink.persist_message.delay(message)
