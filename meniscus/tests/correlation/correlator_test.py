import httplib
import unittest

from mock import MagicMock
from mock import patch
import requests
from meniscus.correlation import correlator

import meniscus.correlation.errors as exception
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.sinks import VALID_SINKS


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingTenantIdentification())
    suite.addTest(WhenTestingCorrelationMessage())
    suite.addTest(WhenTestingCorrelationUtilities())
    return suite


class WhenCorrelateSrcMessage(unittest.TestCase):
    def setUp(self):
        self.tenant_id = '5164b8f4-16fb-4376-9d29-8a6cbaa02fa9'
        self.token = '87324559-33aa-4534-bfd1-036472a32f2e'
        self.credentials = {'tenant_id': self.tenant_id,
                            'message_token': self.token}
        self.src_msg = {
            "HOST": "tohru",
            "_SDATA": {
                "meniscus": {
                    "token": self.token,
                    "tenant": self.tenant_id
                }
            },
            "PRIORITY": "info",
            "MESSAGE": "127.0.0.1 - - [12/Jul/2013:19:40:58 +0000] "
                       "\"GET /test.html HTTP/1.1\" 404 466 \"-\" "
                       "\"curl/7.29.0\"",
            "FACILITY": "local1",
            "MSGID": "345",
            "ISODATE": "2013-07-12T14:17:00+00:00",
            "PROGRAM": "apache",
            "DATE": "2013-07-12T14:17:00.134+00:00",
            "PID": "234"
        }

    def test_extract_message_credentials_valid(self):
        result = correlator.extract_message_credentials(self.src_msg)
        self.assertDictEqual(result, self.credentials)

    def test_extract_message_credentials_msg_failure(self):
        with self.assertRaises(exception.MessageValidationError):
            correlator.extract_message_credentials({})


    # def test_correlate__message(self):
    #     validate_tenant_func = MagicMock()
    #     extract_creds_func = MagicMock()
    #     with patch(correlator, 'extract_message_credentials',
    #                extract_creds_func), \
    #             patch.object(correlator, 'validate_tenant',
    #                          validate_tenant_func):
    #
    #         correlator.correlate_src_message(self.src_msg)
    #     validate_tenant_func.assert_called_once_with()
    #     extract_creds_func.assert_called_once()


class WhenTestingTenantIdentification(unittest.TestCase):
    def setUp(self):
        self.timestamp = "2013-03-19T18:16:48.411029Z"
        self.producers = [
            EventProducer(432, 'producer1', 'syslog', durable=True),
            EventProducer(433, 'producer2', 'syslog', durable=False)
        ]
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           "2013-03-19T18:16:48.411029Z")
        self.tenant_id = '1234'
        self.tenant = Tenant(self.tenant_id, self.token,
                             event_producers=self.producers)
        self.tenant_found = MagicMock(return_value=self.tenant)

        self.cache = MagicMock()
        self.valid_message_token = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.invalid_message_token = 'yyy7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.get_token = MagicMock(return_value=self.token)
        self.get_tenant = MagicMock(return_value=self.tenant)
        self.get_none = MagicMock(return_value=None)
        self.config = WorkerConfiguration(
            personality='worker',
            hostname='worker01',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)
        self.src_msg = {
            "HOST": "tohru",
            "_SDATA": {
                "meniscus": {
                    "token": self.token,
                    "tenant": self.tenant
                }
            },
            "PRIORITY": "info",
            "MESSAGE": "127.0.0.1 - - [12/Jul/2013:19:40:58 +0000] "
                       "\"GET /test.html HTTP/1.1\" 404 466 \"-\" "
                       "\"curl/7.29.0\"",
            "FACILITY": "local1",
            "MSGID": "345",
            "ISODATE": "2013-07-12T14:17:00+00:00",
            "PROGRAM": "apache",
            "DATE": "2013-07-12T14:17:00.134+00:00",
            "PID": "234"
        }

    def test_get_validated_tenant_throws_auth_exception_from_cache(self):
        with patch.object(correlator.TokenCache, 'get_token', self.get_token):
            with self.assertRaises(exception.MessageAuthenticationError):
                correlator.validate_token(self.tenant_id,
                                           self.invalid_message_token,
                                           {})

    # def test_correlate__message(self):
    #     validate_tenant_func = MagicMock()
    #     extract_creds_func = MagicMock()
    #     with patch(correlator, 'extract_message_credentials',
    #                extract_creds_func), \
    #             patch.object(correlator, 'validate_tenant',
    #                          validate_tenant_func):
    #
    #         correlator.correlate_src_message(self.src_msg)
    #     validate_tenant_func.assert_called_once_with(self.src_msg)
    #     extract_creds_func.assert_called_once(self.tenant_id,
    #                                           self.valid_message_token,
    #                                           self.src_msg)

    # def test_get_validated_tenant_from_cache(self):
    #     add_corr_to_msg_func = MagicMock()
    #     with patch.object(
    #             correlator.TokenCache, 'get_token', self.get_token), \
    #         patch.object(
    #             correlator.TenantCache, 'get_tenant', self.get_tenant), \
    #         patch.object(util, '_add_correlation_info_to_message',
    #                      add_corr_to_msg_func):
    #             correlator.validate_tenant(self.tenant_id,
    #                                        self.valid_message_token,
    #                                        self.src_msg)
    #             add_corr_to_msg_func.assert_called_once_with()


    # def test_get_validated_tenant_from_coordinator_returns_tenant(self):
    #     tenant_identify = correlator.TenantIdentification(
    #         self.tenant_id, self.valid_message_token)
    #
    #     with patch.object(
    #             correlator.TokenCache, 'get_token', self.get_token), \
    #         patch.object(correlator.TenantCache, 'get_tenant', self.get_none),\
    #         patch.object(
    #             correlator.TenantIdentification,
    #             '_get_tenant_from_coordinator',
    #             self.get_tenant):
    #         tenant = tenant_identify.get_validated_tenant()
    #     self.assertIsInstance(tenant, Tenant)

    # def test_get_coord_validated_tenant_from_coordinator_returns_tenant(self):
    #     tenant_identify = correlator.TenantIdentification(
    #         self.tenant_id, self.valid_message_token)
    #
    #     with patch.object(correlator.TokenCache, 'get_token', self.get_none), \
    #         patch.object(correlator.TenantIdentification,
    #                      '_validate_token_with_coordinator', MagicMock()), \
    #         patch.object(
    #             correlator.TenantIdentification,
    #             '_get_tenant_from_coordinator',
    #             self.get_tenant):
    #
    #         tenant = tenant_identify.get_validated_tenant()
    #
    #     self.assertIsInstance(tenant, Tenant)

    def test_validate_token_with_coordinator_throws_communication_error(self):
        http_request = MagicMock(
            side_effect=requests.RequestException)

        with patch.object(
                util, '_get_config_from_cache', self.get_config),\
            patch('meniscus.correlation.'
                  'correlator.http_request', http_request):

            with self.assertRaises(requests.RequestException):
                correlator.validate_token_with_coordinator(
                    self.tenant_id, self.valid_message_token, self.src_msg)

    def test_validate_token_with_coordinator_throws_auth_error(self):
        response = MagicMock()
        response.status_code = httplib.NOT_FOUND
        http_request = MagicMock(return_value=response)

        with patch.object(util, '_get_config_from_cache', self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request):

            with self.assertRaises(exception.MessageAuthenticationError):
                correlator.validate_token_with_coordinator(
                    self.tenant_id, self.invalid_message_token, self.src_msg)

    # def test_validate_token_with_coordinator_calls_get_tenant(self):
    #     response = MagicMock()
    #     response.status_code = httplib.OK
    #     http_request = MagicMock(return_value=response)
    #     get_tenant_from_coor_func = MagicMock()
    #     with patch.object(util, '_get_config_from_cache', self.get_config), \
    #         patch('meniscus.correlation.correlator.http_request',
    #               http_request),\
    #         patch(correlator, 'get_tenant_from_coordinator',
    #               get_tenant_from_coor_func):
    #         correlator.validate_token_with_coordinator(
    #             self.tenant_id, self.valid_message_token, self.src_msg)
    #     get_tenant_from_coor_func.assert_called_once_with(
    #         self.tenant_id, self.valid_message_token, self.src_msg)

    def test_get_tenant_from_coordinator_exception_on_http_request(self):
        http_request = MagicMock(
            side_effect=requests.RequestException)

        with patch.object(util, '_get_config_from_cache', self.get_config), \
            patch('meniscus.correlation.correlator.http_request',
                  http_request):

            with self.assertRaises(requests.RequestException):
                correlator.get_tenant_from_coordinator(
                    self.tenant_id, self.valid_message_token, self.src_msg)

    def test_get_tenant_from_coordinator_exception_for_no_tenant_found(self):
        response = MagicMock()
        response.status_code = httplib.NOT_FOUND
        http_request = MagicMock(return_value=response)

        with patch.object(util, '_get_config_from_cache', self.get_config), \
            patch('meniscus.correlation.correlator.http_request',
                  http_request):

            with self.assertRaises(exception.ResourceNotFoundError):
                correlator.get_tenant_from_coordinator(
                    self.tenant_id, self.valid_message_token, self.src_msg)

    def test_get_tenant_from_coordinator_exception_on_bad_response_code(self):
        response = MagicMock()
        response.status_code = httplib.UNAUTHORIZED
        http_request = MagicMock(return_value=response)

        with patch.object(util, '_get_config_from_cache', self.get_config), \
            patch('meniscus.correlation.correlator.http_request',
                  http_request):

            with self.assertRaises(exception.CoordinatorCommunicationError):
                correlator.get_tenant_from_coordinator(
                    self.tenant_id, self.valid_message_token, self.src_msg)

    # def test_get_tenant_from_coordinator_calls_add_correlation_func(self):
    #     add_correlation_func = MagicMock()
    #     response = MagicMock()
    #     response.status_code = httplib.OK
    #     http_request = MagicMock(return_value=response)
    #
    #     with patch.object(util, '_get_config_from_cache', self.get_config), \
    #         patch('meniscus.correlation.correlator.http_request',
    #               http_request), \
    #         patch('meniscus.correlation.correlator.load_tenant_from_dict',
    #               self.tenant_found):
    #         patch(util._add_correlation_info_to_message, add_correlation_func)
    #
    #         correlator.get_tenant_from_coordinator(self.tenant_id,
    #                                                self.valid_message_token,
    #                                                self.src_msg)
    #
    #     add_correlation_func.assert_called_once_with(self.tenant_found,
    #                                                  self.src_msg)



class WhenTestingCorrelationUtilities(unittest.TestCase):
    def setUp(self):
        self.tenant_id = '1234'
        self.message_token = '4321'
        self.coordinator_uri = 'http://192.168.1.2/v1'
        self.request_uri_tenant = 'http://192.168.1.2/v1/tenant/1234'
        self.request_uri_token = 'http://192.168.1.2/v1/tenant/1234/token'
        self.hostname = 'hostname'
        self.token_header = {MESSAGE_TOKEN: self.message_token,
                             'hostname': self.hostname}
        self.producers = [
            EventProducer(432, 'producer1', 'syslog', durable=True,
                          sinks=VALID_SINKS),
            EventProducer(433, 'producer2', 'syslog', durable=False)
        ]
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           "2013-03-19T18:16:48.411029Z")
        self.tenant_id = '1234'
        self.tenant_name = 'TenantName'
        self.tenant = Tenant(self.tenant_id, self.token,
                             event_producers=self.producers,
                             tenant_name=self.tenant_name)
        self.destination = {
            'transaction_id': None,
            'transaction_time': None
        }
        self.config = WorkerConfiguration(
            personality='worker',
            hostname='worker01',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)

    def test_build_request_uri_token_None(self):
        uri = util._build_request_uri(self.coordinator_uri, self.tenant_id)
        self.assertEqual(uri, self.request_uri_tenant)

    def test_build_request_uri_token_true(self):
        uri = util._build_request_uri(
            self.coordinator_uri, self.tenant_id, True)
        self.assertEqual(uri, self.request_uri_token)

    def test_build_token_header(self):
        header = util._build_token_header(self.message_token, self.hostname)
        self.assertDictEqual(header, self.token_header)

    def test_get_config_from_cache(self):
        with patch.object(util.ConfigCache, 'get_config', self.get_config):
            self.assertEqual(util._get_config_from_cache(), self.config)


class WhenTestingCorrelationMessage(unittest.TestCase):
    def setUp(self):
        self.tenant_id = '5164b8f4-16fb-4376-9d29-8a6cbaa02fa9'
        self.token = '87324559-33aa-4534-bfd1-036472a32f2e'
        self.src_msg = {
            "HOST": "tohru",
            "_SDATA": {
                "meniscus": {
                    "token": self.token,
                    "tenant": self.tenant_id
                }
            },
            "PRIORITY": "info",
            "MESSAGE": "127.0.0.1 - - [12/Jul/2013:19:40:58 +0000] "
                       "\"GET /test.html HTTP/1.1\" 404 466 \"-\" "
                       "\"curl/7.29.0\"",
            "FACILITY": "local1",
            "MSGID": "345",
            "ISODATE": "2013-07-12T14:17:00+00:00",
            "PROGRAM": "apache",
            "DATE": "2013-07-12T14:17:00.134+00:00",
            "PID": "234"
        }
        self.producers = [
            EventProducer(432, 'producer1', 'syslog', durable=True,
                          sinks=VALID_SINKS),
            EventProducer(433, 'producer2', 'syslog', durable=False)
        ]
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           "2013-03-19T18:16:48.411029Z")
        self.tenant_id = '1234'
        self.tenant_name = 'TenantName'
        self.tenant = Tenant(self.tenant_id, self.token,
                             event_producers=self.producers,
                             tenant_name=self.tenant_name)
        self.destination = {
            'transaction_id': None,
            'transaction_time': None
        }

    def test_process_message_durable(self):
        message = {
            "host": "host1",
            "pname": "producer1",
            "time": "2013-03-19T18:16:48.411029Z"
        }

        message = util._add_correlation_info_to_message(
            self.tenant, message)
        self.assertTrue(message['meniscus']['correlation']['durable'])
        self.assertTrue('host' in message.keys())
        self.assertTrue('pname' in message.keys())
        self.assertTrue('time' in message.keys())
        self.assertTrue('meniscus' in message.keys())
        self.assertTrue('correlation' in message['meniscus'].keys())
        meniscus_dict = message['meniscus']['correlation']
        self.assertTrue('tenant_name' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['tenant_name'], self.tenant_name)
        self.assertTrue('ep_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['ep_id'], 432)
        self.assertTrue('pattern' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['pattern'], 'syslog')
        self.assertTrue('job_id' in meniscus_dict.keys())
        self.assertTrue('durable' in meniscus_dict.keys())
        self.assertTrue('encrypted' in meniscus_dict.keys())
        self.assertTrue('@timestamp' in meniscus_dict.keys())
        self.assertTrue(meniscus_dict['durable'])
        for sink in VALID_SINKS:
            self.assertEqual(
                meniscus_dict['destinations'][sink],
                self.destination)

    def test_process_message_not_durable(self):
        message = {
            "host": "host1",
            "pname": "producer2",
            "time": "2013-03-19T18:16:48.411029Z"
        }

        message = util._add_correlation_info_to_message(self.tenant, message)
        self.assertFalse(message['meniscus']['correlation']['durable'])
        self.assertTrue('host' in message.keys())
        self.assertTrue('pname' in message.keys())
        self.assertTrue('time' in message.keys())
        self.assertTrue('meniscus' in message.keys())
        self.assertTrue('correlation' in message['meniscus'].keys())
        meniscus_dict = message['meniscus']['correlation']
        self.assertTrue('tenant_name' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['tenant_name'], self.tenant_name)
        self.assertTrue('ep_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['ep_id'], 433)
        self.assertTrue('@timestamp' in meniscus_dict.keys())
        self.assertTrue('pattern' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['pattern'], 'syslog')
        self.assertFalse('job_id' in meniscus_dict.keys())

    def test_process_message_default(self):
        message = {
            "host": "host1",
            "pname": "producer99",
            "time": "2013-03-19T18:16:48.411029Z"
        }

        message = correlator._add_correlation_info_to_message(self.tenant,
                                                              message)
        self.assertFalse(message['meniscus']['correlation']['durable'])
        self.assertTrue('host' in message.keys())
        self.assertTrue('pname' in message.keys())
        self.assertTrue('time' in message.keys())
        self.assertTrue('meniscus' in message.keys())
        self.assertTrue('correlation' in message['meniscus'].keys())
        meniscus_dict = message['meniscus']['correlation']
        self.assertTrue('tenant_name' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['tenant_name'], self.tenant_name)
        self.assertTrue('ep_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['ep_id'], None)
        self.assertTrue('pattern' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['pattern'], 'default')
        self.assertFalse('job_id' in meniscus_dict.keys())

    def test_convert_to_cee(self):
        cee_message = util._convert_message_cee(self.src_msg)
        self.assertEquals(cee_message['ver'], self.src_msg.get('VERSION', "1"))
        self.assertEquals(cee_message['msgid'], self.src_msg['MSGID'])
        self.assertEquals(cee_message['pid'], self.src_msg['PID'])
        self.assertEquals(cee_message['pri'], self.src_msg['PRIORITY'])
        self.assertEquals(cee_message['host'], self.src_msg['HOST'])
        self.assertEquals(cee_message['pname'], self.src_msg['PROGRAM'])
        self.assertEquals(cee_message['time'], self.src_msg['ISODATE'])
        self.assertEquals(cee_message['msg'], self.src_msg['MESSAGE'])



if __name__ == '__main__':
    unittest.main()
