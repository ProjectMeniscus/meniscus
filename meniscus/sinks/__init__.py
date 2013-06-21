from meniscus.sinks import default, hdfs

def persist_message(message):

    sinks = message['meniscus']['sinks']

    if 'hdfs' in sinks:
        hdfs.persist_message.delay(message)

    default.persist_message.delay(message)