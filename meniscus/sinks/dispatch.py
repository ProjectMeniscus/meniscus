from meniscus.queue import celery


@celery.task
def route_message(message):
    message_sinks = message['meniscus']['correlation']['sinks']
    #Todo: sgonzales Route message to sink using new design for bulk flush
