import unittest

from mock import MagicMock
from mock import patch
import falcon

import meniscus.api.correlation.correlation_exceptions as errors
from meniscus.api.correlation.resources import correlator
from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.data.model.tenant import Tenant


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPublishMessage())
    return suite


class WhenTestingPublishMessage(unittest.TestCase):
    def setUp(self):
        self.resource = PublishMessageResource()
        self.body = {
            "host": "host",
            "pname": "pname",
            "time": "2013-03-19T18:16:48.411029Z"
        }

        self.validate_body = MagicMock(
            side_effect=errors.MessageValidationError)
        self.req = MagicMock()
        self.req.get_header.return_value = \
            'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.resp = MagicMock()
        self.tenant_id = '1234'
        self.token = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.tenant = Tenant(self.tenant_id, self.token)

    def test_validate_body_throws_validation_error(self):
        with patch('meniscus.api.correlation.resources.correlator.'
                   'validate_event_message_body', self.validate_body):
            with self.assertRaises(falcon.HTTPError):
                self.resource._validate_req_body_on_post(self.body)

    def test_throws_falcon_error_for_message_auth_error_on_post(self):
        with patch('meniscus.api.correlation.resources.load_body',
                   MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()),\
            patch.object(correlator.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(side_effect=errors.MessageAuthenticationError)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_throws_falcon_error_for_resource_not_found_error_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(correlator.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(side_effect=errors.ResourceNotFoundError)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_throws_falcon_error_for_coordinator_comm_error_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(correlator.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(side_effect=errors.CoordinatorCommunicationError)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_returns_204_for_non_durable_message_on_post(self):
        message = {
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

        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(correlator.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(return_value=message)),\
            patch('meniscus.api.correlation.resources.persist_message',
                  MagicMock()):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
            self.assertEquals(self.resp.status, falcon.HTTP_204)

    def test_returns_202_for_durable_message_on_post(self):
        message = {
            "profile": "http://projectmeniscus.org/cee/profiles/base",
            "ver": "1",
            "msgid": "-",
            "pri": "46",
            "pid": "-",
            "meniscus": {
                "tenant": "5164b8f4-16fb-4376-9d29-8a6cbaa02fa9",
                "correlation": {
                    "host_id": "1",
                    "durable": True,
                    "ep_id": None,
                    "pattern": None,
                    "encrypted": False,
                    "job_id": "5497b8f4-16fb-4376-9d29-8a6cbaa0223bc"
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
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(correlator.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(return_value=message)), \
            patch('meniscus.api.correlation.resources.persist_message',
                  MagicMock()):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
            self.assertEquals(self.resp.status, falcon.HTTP_202)
            self.assertTrue("job_id" in self.resp.body)
            self.assertTrue("job_status_uri" in self.resp.body)

if __name__ == '__main__':
    unittest.main()
