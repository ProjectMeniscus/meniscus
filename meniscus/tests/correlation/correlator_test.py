import httplib
import unittest

from mock import MagicMock
from mock import patch
import requests
from meniscus.correlation import correlator

from meniscus.correlation import errors
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.data.model.worker import WorkerConfiguration


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingCorrelationPipeline())
    return suite


class WhenTestingCorrelationPipeline(unittest.TestCase):
    def setUp(self):
        self.tenant_id = '5164b8f4-16fb-4376-9d29-8a6cbaa02fa9'
        self.message_token = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.producers = [
            EventProducer(432, 'producer1', 'syslog', durable=True),
            EventProducer(433, 'producer2', 'syslog', durable=False)
        ]
        self.invalid_message_token = 'yyy7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           '2013-03-19T18:16:48.411029Z')
        self.tenant = Tenant(self.tenant_id, self.token,
                             event_producers=self.producers)
        self.get_token = MagicMock(return_value=self.token)
        self.get_tenant = MagicMock(return_value=self.tenant)
        self.get_none = MagicMock(return_value=None)
        self.src_msg = {
            'HOST': 'tohru',
            '_SDATA': {
                'meniscus': {
                    'token': self.message_token,
                    'tenant': self.tenant_id
                }
            },
            'PRIORITY': 'info',
            'MESSAGE': '127.0.0.1 - - [12/Jul/2013:19:40:58 +0000] '
                       '\'GET /test.html HTTP/1.1\' 404 466 \'-\' '
                       '\'curl/7.29.0\'',
            'FACILITY': 'local1',
            'MSGID': '345',
            'ISODATE': '2013-07-12T14:17:00+00:00',
            'PROGRAM': 'apache',
            'DATE': '2013-07-12T14:17:00.134+00:00',
            'PID': '234'
        }
        self.malformed_sys_msg = {
            'HOST': 'tohru',
            '_SDATA': {
                'meniscus': {
                    'token': '',
                    'tenant': ''
                }
            },
            'PRIORITY': 'info',
            'MESSAGE': '127.0.0.1 - - [12/Jul/2013:19:40:58 +0000] '
                       '\'GET /test.html HTTP/1.1\' 404 466 \'-\' '
                       '\'curl/7.29.0\'',
            'FACILITY': 'local1',
            'MSGID': '345',
            'ISODATE': '2013-07-12T14:17:00+00:00',
            'PROGRAM': 'apache',
            'DATE': '2013-07-12T14:17:00.134+00:00',
            'PID': '234'
        }
        self.cee_msg = {
            'host': 'tohru',
            'pri': 'info',
            'msg': '127.0.0.1 - - [12/Jul/2013:19:40:58 +0000] '
                   '\'GET /test.html HTTP/1.1\' 404 466 \'-\' '
                   '\'curl/7.29.0\'',
            'msgid': '345',
            'time': '2013-07-12T14:17:00+00:00',
            'pname': 'apache',
            'pid': '234',
            'ver': '1',
            'native': {'meniscus': {
                'token': 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                'tenant': '5164b8f4-16fb-4376-9d29-8a6cbaa02fa9'}}
        }
        self.config = WorkerConfiguration(
            personality='worker',
            hostname='worker01',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)
        self.tenant_found = MagicMock(return_value=self.tenant)

    def test_correlate_syslog_message_exception(self):
        http_request = MagicMock(side_effect=requests.RequestException)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
            patch('meniscus.correlation.correlator.http_request',
                  http_request):

            with self.assertRaises(errors.CoordinatorCommunicationError):
                correlator.correlate_syslog_message(self.src_msg)

    def test_correlate_syslog_message_success(self):
        http_request = MagicMock(side_effect=requests.RequestException)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request):

            with self.assertRaises(errors.CoordinatorCommunicationError):
                correlator.correlate_http_message(self.tenant_id,
                                                  self.message_token,
                                                  self.src_msg)

    def test_format_message_cee_message_failure_empty_string(self):
        with self.assertRaises(errors.MessageValidationError):
            correlator.correlate_syslog_message({})

    def test_format_message_cee_message(self):
        _validate_token_from_cache_func = MagicMock()
        with patch('meniscus.correlation.correlator.'
                   '_validate_token_from_cache',
                   _validate_token_from_cache_func):

            correlator._format_message_cee(self.src_msg)
            _validate_token_from_cache_func.assert_called_once_with(
                self.tenant_id, self.message_token, self.cee_msg)

    # Tests for _validate_token_from_cache
    def test_validate_token_from_cache_throws_auth_exception_from_cache(self):
        with patch.object(correlator.cache_handler.TokenCache, 'get_token',
                          self.get_token):
            with self.assertRaises(errors.MessageAuthenticationError):
                correlator._validate_token_from_cache(
                    self.tenant_id, self.invalid_message_token, self.src_msg)

    def test_validate_token_from_cache_calls_get_tenant_from_cache(self):
        get_tenant_from_cache_func = MagicMock()
        with patch.object(correlator.cache_handler.TokenCache, 'get_token',
                          self.get_token), \
            patch('meniscus.correlation.correlator._get_tenant_from_cache',
                  get_tenant_from_cache_func):

            correlator._validate_token_from_cache(
                self.tenant_id, self.message_token, self.src_msg)
            get_tenant_from_cache_func.assert_called_once_with(
                self.tenant_id, self.message_token, self.src_msg)

    def test_validate_token_from_cache_calls_validate_token_coordinator(self):
        validate_token_from_coordinator_func = MagicMock()
        with patch.object(correlator.cache_handler.TokenCache, 'get_token',
                          self.get_none), \
                patch('meniscus.correlation.correlator.'
                      '_validate_token_with_coordinator',
                      validate_token_from_coordinator_func):

            correlator._validate_token_from_cache(
                self.tenant_id, self.message_token, self.src_msg)
            validate_token_from_coordinator_func.assert_called_once_with(
                self.tenant_id, self.message_token, self.src_msg)

    # Tests for _get_tenant_from_cache
    def test_get_tenant_from_cache_calls_get_tenant_from_coordinator(self):
        get_tenant_from_coordinator_func = MagicMock()
        with patch.object(correlator.cache_handler.TenantCache, 'get_tenant',
                          self.get_none), \
                patch('meniscus.correlation.correlator.'
                      '_get_tenant_from_coordinator',
                      get_tenant_from_coordinator_func):

            correlator._get_tenant_from_cache(self.tenant_id,
                                              self.message_token,
                                              self.src_msg)
            get_tenant_from_coordinator_func.assert_called_once_with(
                self.tenant_id, self.message_token, self.src_msg)

    def test_get_tenant_from_cache_calls_add_correlation_info_to_message(self):
        add_correlation_info_to_message_func = MagicMock()
        with patch.object(correlator.cache_handler.TenantCache, 'get_tenant',
                          self.get_tenant), \
                patch('meniscus.correlation.correlator.'
                      '_add_correlation_info_to_message',
                      add_correlation_info_to_message_func):

            correlator._get_tenant_from_cache(self.tenant_id,
                                              self.message_token,
                                              self.src_msg)
            add_correlation_info_to_message_func.assert_called_once_with(
                self.tenant, self.src_msg)

    # Tests for _validate_token_with_coordinator
    def test_validate_token_with_coordinator_throws_communication_error(self):
        http_request = MagicMock(side_effect=requests.RequestException)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config),\
            patch('meniscus.correlation.correlator.http_request',
                  http_request):

            with self.assertRaises(errors.CoordinatorCommunicationError):
                correlator._validate_token_with_coordinator(
                    self.tenant_id, self.message_token, self.src_msg)

    def test_validate_token_with_coordinator_throws_auth_error(self):
        response = MagicMock()
        response.status_code = httplib.NOT_FOUND
        http_request = MagicMock(return_value=response)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request):

            with self.assertRaises(errors.MessageAuthenticationError):
                correlator._validate_token_with_coordinator(
                    self.tenant_id, self.invalid_message_token, self.src_msg)

    def test_validate_token_with_coordinator_calls_get_tenant(self):
        response = MagicMock()
        response.status_code = httplib.OK
        http_request = MagicMock(return_value=response)
        get_tenant_from_coordinator_func = MagicMock()
        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
            patch('meniscus.correlation.correlator.http_request',
                  http_request),\
            patch('meniscus.correlation.correlator.'
                  '_get_tenant_from_coordinator',
                  get_tenant_from_coordinator_func):
            correlator._validate_token_with_coordinator(self.tenant_id,
                                                        self.message_token,
                                                        self.src_msg)
        get_tenant_from_coordinator_func.assert_called_once_with(
            self.tenant_id, self.message_token, self.src_msg)

    # Tests for _get_tenant_from_coordinator
    def test_get_tenant_from_coordinator_throws_communication_error(self):
        http_request = MagicMock(
            side_effect=requests.RequestException)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request):

            with self.assertRaises(errors.CoordinatorCommunicationError):
                correlator._get_tenant_from_coordinator(self.tenant_id,
                                                        self.message_token,
                                                        self.src_msg)

    def test_get_tenant_from_coordinator_throws_auth_error(self):
        response = MagicMock()
        response.status_code = httplib.NOT_FOUND
        http_request = MagicMock(return_value=response)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request):

            with self.assertRaises(errors.ResourceNotFoundError):
                correlator._get_tenant_from_coordinator(
                    self.tenant_id, self.invalid_message_token, self.src_msg)

    def test_get_tenant_from_coordinator_throws_resource_not_found_error(self):
        response = MagicMock()
        response.status_code = httplib.BAD_REQUEST
        http_request = MagicMock(return_value=response)

        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request):

            with self.assertRaises(errors.CoordinatorCommunicationError):
                correlator._get_tenant_from_coordinator(
                    self.tenant_id, self.invalid_message_token, self.src_msg)

    def test_get_tenant_from_coordinator_calls_get_tenant(self):
        response = MagicMock()
        response.status_code = httplib.OK
        http_request = MagicMock(return_value=response)
        add_correlation_info_to_message_func = MagicMock()
        with patch.object(correlator, '_get_config_from_cache',
                          self.get_config), \
                patch('meniscus.correlation.correlator.http_request',
                      http_request), \
                patch('meniscus.correlation.correlator.tenant_util.'
                      'load_tenant_from_dict',
                      self.tenant_found), \
                patch('meniscus.correlation.correlator.'
                      '_add_correlation_info_to_message',
                      add_correlation_info_to_message_func):
            correlator._get_tenant_from_coordinator(self.tenant_id,
                                                    self.message_token,
                                                    self.src_msg)
        add_correlation_info_to_message_func.assert_called_once_with(
            self.tenant, self.src_msg)

    #Tests for _add_correlation_info_to_message
    def test_add_correlation_info_to_message(self):
        route_message_func = MagicMock()
        with patch('meniscus.correlation.correlator.sinks.route_message',
                   route_message_func):
            correlator._add_correlation_info_to_message(
                self.tenant, self.cee_msg)
        route_message_func.assert_called_once_with(self.cee_msg)

if __name__ == '__main__':
    unittest.main()
