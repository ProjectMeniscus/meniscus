from meniscus.api.datastore_init import db_handler


def persist_message(message):
    """Takes a message dict and persists it to the configured database."""
    _sink = db_handler()
    _sink.put('logs', message)
