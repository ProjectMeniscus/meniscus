from meniscus.api.correlation.syslog import MessageHandler
from meniscus.api.datastore_init import db_handler

class WorkerSyslogHandler(MessageHandler):


    def message_complete(self, last_message_part):
        full_message = self.msg + last_message_part
        syslog_message = self.msg_head.as_dict()
        syslog_message['message'] = full_message.decode('utf-8')
        self._persist_message(syslog_message)
        self.msg_head = None
        self.msg = b''

    def _persist_message(self, message):
        """Takes a message dict and persists it to the configured database."""
        _sink = db_handler()
        _sink.put('logs', message)
