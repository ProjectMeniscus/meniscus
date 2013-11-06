import unittest
import json

from mock import MagicMock
from mock import patch

from meniscus.correlation import receiver
from meniscus.storage import dispatch


class WhenTestingCorrelationInputServer(unittest.TestCase):
    def setUp(self):
        self.conf = MagicMock()
        self.conf.worker_id = '12345'
        self.tenant_id = '5164b8f4-16fb-4376-9d29-8a6cbaa02fa9'
        self.token = '87324559-33aa-4534-bfd1-036472a32f2e'
        self.src_msg = {
            "profile": "http://projectmeniscus.org/cee/profiles/base",
            "version": "1",
            "messageid": "-",
            "priority": "46",
            "processid": "-",
            "hostname": "tohru",
            "appname": "rsyslogd",
            "timestamp": "2013-04-02T14:12:04.873490-05:00",
            "message": "start",
            "sd": {
                "meniscus": {
                    "tenant": "5164b8f4-16fb-4376-9d29-8a6cbaa02fa9",
                    "token": "87324559-33aa-4534-bfd1-036472a32f2e"
                }
            },
            "native": {
                "origin": {
                    "x-info": "http://www.rsyslog.com",
                    "swVersion": "7.2.5",
                    "x-pid": "12662",
                    "software": "rsyslogd"
                }
            }
        }
        self.correlated_message = {
            "profile": "http://projectmeniscus.org/cee/profiles/base",
            "ver": "1",
            "msgid": "-",
            "pri": "46",
            "pid": "-",
            "meniscus": {
                "tenant": "5164b8f4-16fb-4376-9d29-8a6cbaa02fa9",
                "correlation": {
                    "host_id": "1",
                    "durable": False,
                    "ep_id": None,
                    "pattern": None,
                    "encrypted": False
                }
            },
            "host": "tohru",
            "pname": "rsyslogd",
            "time": "2013-04-02T14:12:04.873490-05:00",
            "msg": "start",
            "native": {
                "origin": {
                    "x-info": "http://www.rsyslog.com",
                    "swVersion": "7.2.5",
                    "x-pid": "12662",
                    "software": "rsyslogd"
                }
            }
        }
        zmq_reciever = MagicMock()
        zmq_reciever.get.return_value = json.dumps(self.src_msg)
        self.server = receiver.CorrelationInputServer(zmq_reciever)

    def test_process_msg(self):
        correlate_func = MagicMock(return_value=self.correlated_message)
        normalizer_func = MagicMock()
        with patch('meniscus.correlation.correlator.correlate_src_message',
                   correlate_func), \
             patch('meniscus.correlation.receiver.normalize_message',
                   normalizer_func),\
            patch('meniscus.correlation.receiver.should_normalize',
                  MagicMock(return_value=True)):
            self.server.process_msg()
            correlate_func.assert_called_once_with(self.src_msg)
            normalizer_func.apply_async.assert_called_once_with(
                (self.correlated_message,),
                link=dispatch.persist_message.subtask())

    def test_new_correlation_input_server(self):
        server = receiver.new_correlation_input_server()
        self.assertIsInstance(server, receiver.CorrelationInputServer)


if __name__ == '__main__':
    unittest.main()
