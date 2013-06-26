import unittest

from mock import MagicMock
from mock import patch
from portal.input.usyslog import SyslogMessageHead

import meniscus.api.correlation.correlation_exceptions as errors
from meniscus.api.correlation import syslog
with patch('meniscus.data.datastore.datasource_handler', MagicMock()):
    from meniscus.api.correlation.syslog import correlator


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingSyslogHandler())
    return suite


class WhenTestingSyslogHandler(unittest.TestCase):

    def setUp(self):
        self.router = MagicMock()
        self.tenant_id = '5164b8f4-16fb-4376-9d29-8a6cbaa02fa9'
        self.token = '87324559-33aa-4534-bfd1-036472a32f2e'
        self.syslog_handler = syslog.MessageHandler(self.router)
        self.syslog_message_head = SyslogMessageHead()

        self.syslog_message_head.priority = '46'
        self.syslog_message_head.version = '1'
        self.syslog_message_head.timestamp = '2013-04-02T14:12:04.873490-05:00'
        self.syslog_message_head.hostname = 'tohru'
        self.syslog_message_head.appname = 'rsyslogd'
        self.syslog_message_head.processid = '-'
        self.syslog_message_head.messageid = '-'
        self.syslog_message_head.sd = dict()

        self.syslog_message_head.create_sde('meniscus')
        self.syslog_message_head.set_sd_field('tenant')
        self.syslog_message_head.set_sd_value(self.tenant_id)
        self.syslog_message_head.set_sd_field('token')
        self.syslog_message_head.set_sd_value(self.token)
        self.message_part_1 = 'test sys'
        self.message_part_2 = 'log msg '
        self.message_part_3 = 'parser  '

    def test_message_head(self):
        count = self.syslog_handler.msg_count
        self.syslog_handler.message_head(self.syslog_message_head)
        self.assertEquals(self.syslog_message_head,
                          self.syslog_handler.msg_head)
        self.assertEquals(self.syslog_handler.msg_count, count + 1)

    def test_message_part(self):
        self.syslog_handler.message_part(self.message_part_1)
        self.assertEqual(self.syslog_handler.msg, self.message_part_1)
        self.syslog_handler.message_part(self.message_part_2)
        self.assertEqual(self.syslog_handler.msg,
                         self.message_part_1 + self.message_part_2)

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
        persist_message_func = MagicMock()

        self.syslog_handler.message_head(self.syslog_message_head)
        self.syslog_handler.message_part(self.message_part_1)
        self.syslog_handler.message_part(self.message_part_2)

        syslog_message = self.syslog_message_head.as_dict()
        syslog_message['message'] = (
            self.message_part_1 +
            self.message_part_2 +
            self.message_part_3
        ).decode('utf-8')

        with patch('meniscus.api.correlation.syslog._correlate_syslog_message',
                   correlate_function),\
            patch('meniscus.api.correlation.syslog.dispatch.persist_message',
                  persist_message_func):

            self.syslog_handler.message_complete(self.message_part_3)
            correlate_function.assert_called_once_with(syslog_message)
            persist_message_func.assert_called_once_with(
                correlated_message)
            self.assertIs(self.syslog_handler.msg_head, None)
            self.assertIs(self.syslog_handler.msg, b'')

    def test_exception(self):
        mock_env = MagicMock()

        mock_debug = MagicMock()
        mock_env.debug = mock_debug
        ex = Exception('test exception')
        with patch('meniscus.api.correlation.syslog._LOG', mock_env):
            self.syslog_handler.exception(ex)
            mock_debug.assert_called_once_with(
                'syslog parser error: test exception')

    def test_correlate_message_raises_validation_error(self):
        syslog_message = self.syslog_message_head.as_dict()
        syslog_message['message'] = (
            self.message_part_1 +
            self.message_part_2 +
            self.message_part_3
        ).decode('utf-8')

        #remove necessary authentication for test
        syslog_message['sd'].pop('meniscus')

        with self.assertRaises(errors.MessageValidationError):
            syslog._correlate_syslog_message(syslog_message)

    def test_correlate_message(self):
        syslog_message = self.syslog_message_head.as_dict()
        syslog_message['message'] = (
            self.message_part_1 +
            self.message_part_2 +
            self.message_part_3
        ).decode('utf-8')

        get_validated_tenant_func = MagicMock()
        add_correlation_func = MagicMock()
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant', get_validated_tenant_func), \
            patch('meniscus.api.correlation.syslog.correlator.'
                  'add_correlation_info_to_message', add_correlation_func):
            syslog._correlate_syslog_message(syslog_message)
        get_validated_tenant_func.assert_called_once()
        add_correlation_func.assert_called_once()

    def test_convert_to_cee(self):
        syslog_message = self.syslog_message_head.as_dict()
        syslog_message['message'] = (
            self.message_part_1 +
            self.message_part_2 +
            self.message_part_3
        ).decode('utf-8')

        cee_message = syslog._convert_message_cee(syslog_message)

        self.assertEquals(cee_message['ver'], syslog_message['version'])
        self.assertEquals(cee_message['msgid'], syslog_message['messageid'])
        self.assertEquals(cee_message['pid'], syslog_message['processid'])
        self.assertEquals(cee_message['pri'], syslog_message['priority'])
        self.assertEquals(cee_message['host'], syslog_message['hostname'])
        self.assertEquals(cee_message['pname'], syslog_message['appname'])
        self.assertEquals(cee_message['time'], syslog_message['timestamp'])
        self.assertEquals(cee_message['msg'], syslog_message['message'])
        self.assertEquals(
            cee_message['native']['meniscus']['tenant'], self.tenant_id)
        self.assertEquals(
            cee_message['native']['meniscus']['token'], self.token)


if __name__ == '__main__':
    unittest.main()
