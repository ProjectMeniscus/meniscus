import httplib
import unittest

from mock import MagicMock
from mock import patch
import requests

import meniscus.api.correlation.correlation_exceptions as exception
from meniscus.api.correlation import correlator
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.sinks import VALID_SINKS


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingMessageBodyValidation())
    suite.addTest(WhenTestingCorrelationMessage())
    suite.addTest(WhenTestingTenantIdentification())
    return suite


class WhenTestingMessageBodyValidation(unittest.TestCase):
    def setUp(self):
        self.body_no_host = {
            "pname": "pname",
            "time": "2013-03-19T18:16:48.411029Z"
        }
        self.body_empty_host = {
            "host": "",
            "pname": "pname",
            "time": "2013-03-19T18:16:48.411029Z"
        }
        self.body_no_pname = {
            "host": "host",
            "time": "2013-03-19T18:16:48.411029Z"
        }
        self.body_empty_pname = {
            "host": "host",
            "pname": "",
            "time": "2013-03-19T18:16:48.411029Z"
        }
        self.body_no_time = {
            "host": "host",
            "pname": "pname"
        }
        self.body_empty_time = {
            "host": "host",
            "pname": "pname",
            "time": ""
        }
        self.body_valid = {
            "host": "host",
            "pname": "pname",
            "time": "2013-03-19T18:16:48.411029Z"
        }

    def test_should_raise_exception_for_no_host(self):
        body = self.body_no_host
        self.assertFalse('host' in body.keys())
        with self.assertRaises(exception.MessageValidationError):
            correlator.validate_event_message_body(body)

    def test_should_raise_exception_for_empty_host(self):
        body = self.body_empty_host
        self.assertFalse(body['host'])
        with self.assertRaises(exception.MessageValidationError):
            correlator.validate_event_message_body(body)

    def test_should_raise_exception_for_no_pname(self):
        body = self.body_no_pname
        self.assertFalse('pname' in body.keys())
        with self.assertRaises(exception.MessageValidationError):
            correlator.validate_event_message_body(body)

    def test_should_raise_exception_for_empty_pname(self):
        body = self.body_empty_pname
        self.assertFalse(body['pname'])
        with self.assertRaises(exception.MessageValidationError):
            correlator.validate_event_message_body(body)

    def test_should_raise_exception_for_no_time(self):
        body = self.body_no_time
        self.assertFalse('time' in body.keys())
        with self.assertRaises(exception.MessageValidationError):
            correlator.validate_event_message_body(body)

    def test_should_raise_exception_for_empty_time(self):
        body = self.body_empty_time
        self.assertFalse(body['time'])
        with self.assertRaises(exception.MessageValidationError):
            correlator.validate_event_message_body(body)

    def test_should_return_true_for_valid_body(self):
        body = self.body_valid
        self.assertTrue('host' in body.keys())
        self.assertTrue(body['host'])
        self.assertTrue('pname' in body.keys())
        self.assertTrue(body['pname'])
        self.assertTrue('time' in body.keys())
        self.assertTrue(body['time'])
        self.assertTrue(correlator.validate_event_message_body(body))


class WhenTestingCorrelationMessage(unittest.TestCase):
    def setUp(self):

        self.profiles = [
            HostProfile(123, 'profile1', event_producer_ids=[432, 433]),
            HostProfile(456, 'profile2', event_producer_ids=[432, 433])
        ]
        self.producers = [
            EventProducer(432, 'producer1', 'syslog', durable=True,
                          sinks=VALID_SINKS),
            EventProducer(433, 'producer2', 'syslog', durable=False)
        ]
        self.hosts = [
            Host(765, 'host1', ip_address_v4='192.168.1.1', profile_id=123),
            Host(766, 'host2', ip_address_v4='192.168.2.1', profile_id=456)]
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           "2013-03-19T18:16:48.411029Z")
        self.tenant_id = '1234'
        self.tenant_name = 'TenantName'
        self.tenant = Tenant(self.tenant_id, self.token,
                             profiles=self.profiles,
                             event_producers=self.producers,
                             hosts=self.hosts,
                             tenant_name=self.tenant_name)
        self.destination = {
            'transaction_id': None,
            'transaction_time': None
        }

    def test_process_message_throws_exception_host_not_found(self):
        message = {
            "host": "host99",
            "pname": "pname",
            "time": "2013-03-19T18:16:48.411029Z"
        }

        with self.assertRaises(exception.MessageValidationError):
            correlator.add_correlation_info_to_message(
                self.tenant, message)

    def test_process_message_durable(self):
        message = {
            "host": "host1",
            "pname": "producer1",
            "time": "2013-03-19T18:16:48.411029Z"
        }

        message = correlator.add_correlation_info_to_message(
            self.tenant, message)
        self.assertTrue(message['meniscus']['correlation']['durable'])
        self.assertTrue('host' in message.keys())
        self.assertTrue('pname' in message.keys())
        self.assertTrue('time' in message.keys())
        self.assertTrue('meniscus' in message.keys())
        self.assertTrue('correlation' in message['meniscus'].keys())
        meniscus_dict = message['meniscus']['correlation']
        self.assertTrue('host_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['host_id'], 765)
        self.assertTrue('tenant_name' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['tenant_name'], self.tenant_name)
        self.assertTrue('ep_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['ep_id'], 432)
        self.assertTrue('pattern' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['pattern'], 'syslog')
        self.assertTrue('job_id' in meniscus_dict.keys())
        self.assertTrue('durable' in meniscus_dict.keys())
        self.assertTrue('encrypted' in meniscus_dict.keys())
        self.assertTrue('correlation_timestamp' in meniscus_dict.keys())
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

        message = correlator.add_correlation_info_to_message(
            self.tenant, message)
        self.assertFalse(message['meniscus']['correlation']['durable'])
        self.assertTrue('host' in message.keys())
        self.assertTrue('pname' in message.keys())
        self.assertTrue('time' in message.keys())
        self.assertTrue('meniscus' in message.keys())
        self.assertTrue('correlation' in message['meniscus'].keys())
        meniscus_dict = message['meniscus']['correlation']
        self.assertTrue('host_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['host_id'], 765)
        self.assertTrue('tenant_name' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['tenant_name'], self.tenant_name)
        self.assertTrue('ep_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['ep_id'], 433)
        self.assertTrue('correlation_timestamp' in meniscus_dict.keys())
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

        message = correlator.add_correlation_info_to_message(
            self.tenant, message)
        self.assertFalse(message['meniscus']['correlation']['durable'])
        self.assertTrue('host' in message.keys())
        self.assertTrue('pname' in message.keys())
        self.assertTrue('time' in message.keys())
        self.assertTrue('meniscus' in message.keys())
        self.assertTrue('correlation' in message['meniscus'].keys())
        meniscus_dict = message['meniscus']['correlation']
        self.assertTrue('host_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['host_id'], 765)
        self.assertTrue('tenant_name' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['tenant_name'], self.tenant_name)
        self.assertTrue('ep_id' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['ep_id'], None)
        self.assertTrue('correlation_timestamp' in meniscus_dict.keys())
        self.assertTrue('pattern' in meniscus_dict.keys())
        self.assertEquals(meniscus_dict['pattern'], None)
        self.assertFalse('job_id' in meniscus_dict.keys())


class WhenTestingTenantIdentification(unittest.TestCase):
    def setUp(self):

        self.timestamp = "2013-03-19T18:16:48.411029Z"
        self.profiles = [
            HostProfile(123, 'profile1', event_producer_ids=[432, 433]),
            HostProfile(456, 'profile2', event_producer_ids=[432, 433])
        ]
        self.producers = [
            EventProducer(432, 'producer1', 'syslog', durable=True),
            EventProducer(433, 'producer2', 'syslog', durable=False)
        ]
        self.hosts = [
            Host(765, 'host1', ip_address_v4='192.168.1.1', profile_id=123),
            Host(766, 'host2', ip_address_v4='192.168.2.1', profile_id=456)]
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           "2013-03-19T18:16:48.411029Z")
        self.tenant_id = '1234'
        self.tenant = Tenant(self.tenant_id, self.token,
                             profiles=self.profiles,
                             event_producers=self.producers,
                             hosts=self.hosts)
        self.tenant_found = MagicMock(return_value=self.tenant)

        self.cache = MagicMock()
        self.valid_message_token = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.invalid_message_token = 'yyy7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.get_token = MagicMock(return_value=self.token)
        self.get_tenant = MagicMock(return_value=self.tenant)
        self.get_none = MagicMock(return_value=None)
        self.config = WorkerConfiguration(
            personality='correlation',
            personality_module='meniscus.personas.worker.correlation.app',
            worker_id='fgc7104e-8d93-47dc-a49a-8fb0d39e5192',
            worker_token='bbd6307f-8d93-47dc-a49a-8fb0d39e5192',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)

    def test_get_validated_tenant_throws_auth_exception_from_cache(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.invalid_message_token)

        with patch.object(correlator.TokenCache, 'get_token', self.get_token):

            with self.assertRaises(exception.MessageAuthenticationError):
                tenant_identify.get_validated_tenant()

    def test_get_validated_tenant_from_cache_returns_tenant(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)

        with patch.object(
                correlator.TokenCache, 'get_token', self.get_token), \
                patch.object(
                    correlator.TenantCache, 'get_tenant', self.get_tenant):

                tenant = tenant_identify.get_validated_tenant()

        self.assertIsInstance(tenant, Tenant)

    def test_get_validated_tenant_from_coordinator_returns_tenant(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)

        with patch.object(
                correlator.TokenCache, 'get_token', self.get_token), \
            patch.object(correlator.TenantCache, 'get_tenant', self.get_none),\
            patch.object(
                correlator.TenantIdentification,
                '_get_tenant_from_coordinator',
                self.get_tenant):
            tenant = tenant_identify.get_validated_tenant()
        self.assertIsInstance(tenant, Tenant)

    def test_get_coord_validated_tenant_from_coordinator_returns_tenant(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)

        with patch.object(correlator.TokenCache, 'get_token', self.get_none), \
            patch.object(correlator.TenantIdentification,
                         '_validate_token_with_coordinator', MagicMock()), \
            patch.object(
                correlator.TenantIdentification,
                '_get_tenant_from_coordinator',
                self.get_tenant):

            tenant = tenant_identify.get_validated_tenant()

        self.assertIsInstance(tenant, Tenant)

    def test_validate_token_with_coordinator_throws_communication_error(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)
        http_request = MagicMock(
            side_effect=requests.RequestException)

        with patch.object(
                correlator.ConfigCache, 'get_config', self.get_config),\
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request):

            with self.assertRaises(exception.CoordinatorCommunicationError):
                tenant_identify._validate_token_with_coordinator()

    def test_validate_token_with_coordinator_throws_auth_error(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.invalid_message_token)
        response = MagicMock()
        response.status_code = httplib.NOT_FOUND
        http_request = MagicMock(return_value=response)

        with patch.object(
                correlator.ConfigCache, 'get_config', self.get_config), \
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request):

            with self.assertRaises(exception.MessageAuthenticationError):
                tenant_identify._validate_token_with_coordinator()

    def test_validate_token_with_coordinator_returns_true(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)
        response = MagicMock()
        response.status_code = httplib.OK
        http_request = MagicMock(return_value=response)

        with patch.object(
                correlator.ConfigCache, 'get_config', self.get_config), \
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request):

            result = tenant_identify._validate_token_with_coordinator()
            self.assertTrue(result)

    def test_get_tenant_from_coordinator_exception_on_http_request(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)
        http_request = MagicMock(
            side_effect=requests.RequestException)

        with patch.object(correlator.ConfigCache,
                          'get_config', self.get_config), \
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request):

            with self.assertRaises(exception.CoordinatorCommunicationError):
                tenant_identify._get_tenant_from_coordinator()

    def test_get_tenant_from_coordinator_exception_for_no_tenant_found(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)
        response = MagicMock()
        response.status_code = httplib.NOT_FOUND
        http_request = MagicMock(return_value=response)

        with patch.object(
                correlator.ConfigCache, 'get_config', self.get_config),\
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request):

            with self.assertRaises(exception.ResourceNotFoundError):
                tenant_identify._get_tenant_from_coordinator()

    def test_get_tenant_from_coordinator_exception_on_bad_response_code(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)
        response = MagicMock()
        response.status_code = httplib.UNAUTHORIZED
        http_request = MagicMock(return_value=response)

        with patch.object(
                correlator.ConfigCache, 'get_config', self.get_config), \
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request):

            with self.assertRaises(exception.CoordinatorCommunicationError):
                tenant_identify._get_tenant_from_coordinator()

    def test_get_tenant_from_coordinator_returns_tenant(self):
        tenant_identify = correlator.TenantIdentification(
            self.tenant_id, self.valid_message_token)
        response = MagicMock()
        response.status_code = httplib.OK
        http_request = MagicMock(return_value=response)

        with patch.object(
                correlator.ConfigCache, 'get_config', self.get_config), \
            patch('meniscus.api.correlation.'
                  'correlator.http_request', http_request), \
            patch('meniscus.api.correlation.'
                  'correlator.load_tenant_from_dict',
                  self.tenant_found):

            tenant = tenant_identify._get_tenant_from_coordinator()

        self.assertIsInstance(tenant, Tenant)


if __name__ == '__main__':
    unittest.main()
