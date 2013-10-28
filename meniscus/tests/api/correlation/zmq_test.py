import unittest
import json

from mock import MagicMock
from mock import patch

import meniscus.api.correlation.correlation_exceptions as errors
from meniscus.api.correlation import receiver

with patch('meniscus.data.datastore.datasource_handler', MagicMock()):
    from meniscus.api.correlation.receiver import correlator

def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingSyslogHandler())
    return suite


class WhenTestingSyslogHandler(unittest.TestCase):

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

        zmq_reciever = MagicMock()
        zmq_reciever.get.return_value = json.dumps(self.src_msg)

        self.server = receiver.ZeroMQInputServer(zmq_reciever)


    def test_getting_msg(self):
        msg = self.server.get_msg()
        self.assertEqual(self.src_msg, msg)

    def test_message_full(self):
        correlated_message = {
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
        correlate_function = MagicMock(return_value=correlated_message)
        normalizer_func = MagicMock()

        with patch('meniscus.api.correlation.zmq._correlate_src_message',
                   correlate_function),\
            patch('meniscus.api.correlation.zmq.normalize_message',
                  normalizer_func):
            self.server.process_msg()
            correlate_function.assert_called_once_with(self.src_msg)
            normalizer_func.apply_async.assert_called_once()

    def test_correlate_message(self):
        get_validated_tenant_func = MagicMock()
        add_correlation_func = MagicMock()
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant', get_validated_tenant_func), \
            patch('meniscus.api.correlation.zmq.correlator.'
                  'add_correlation_info_to_message', add_correlation_func):
            receiver._correlate_src_message(self.src_msg)
        get_validated_tenant_func.assert_called_once()
        add_correlation_func.assert_called_once()

    def test_convert_to_cee(self):
        cee_message = receiver._convert_message_cee(self.src_msg)

        self.assertEquals(cee_message['ver'], self.src_msg['version'])
        self.assertEquals(cee_message['msgid'], self.src_msg['messageid'])
        self.assertEquals(cee_message['pid'], self.src_msg['processid'])
        self.assertEquals(cee_message['pri'], self.src_msg['priority'])
        self.assertEquals(cee_message['host'], self.src_msg['hostname'])
        self.assertEquals(cee_message['pname'], self.src_msg['appname'])
        self.assertEquals(cee_message['time'], self.src_msg['timestamp'])
        self.assertEquals(cee_message['msg'], self.src_msg['message'])
        self.assertEquals(
            cee_message['native']['meniscus']['tenant'], self.tenant_id)
        self.assertEquals(
            cee_message['native']['meniscus']['token'], self.token)


if __name__ == '__main__':
    unittest.main()
