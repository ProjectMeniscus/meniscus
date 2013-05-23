from meniscus.api.correlation.syslog import MessageHandler
from meniscus.api.storage import persistence

class WorkerSyslogHandler(MessageHandler):


    def message_complete(self, last_message_part):
        full_message = self.msg + last_message_part
        syslog_message = self.msg_head.as_dict()
        syslog_message['message'] = full_message.decode('utf-8')
        persistence.persist_message(syslog_message)
        self.msg_head = None
        self.msg = b''

