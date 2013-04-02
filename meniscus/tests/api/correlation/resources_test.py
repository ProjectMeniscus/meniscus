import unittest

from mock import MagicMock
from mock import patch
import falcon

import meniscus.api.correlation.correlation_exceptions as errors
import meniscus.api.correlation.correlation_process as process
from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.data.model.tenant import Tenant


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPublishMessage())
    return suite


class WhenTestingPublishMessage(unittest.TestCase):
    def setUp(self):
        self.cache = MagicMock()
        self.resource = PublishMessageResource(self.cache)
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
        with patch('meniscus.api.correlation.resources.'
                   'validate_event_message_body', self.validate_body):
            with self.assertRaises(falcon.HTTPError):
                self.resource._validate_req_body_on_post(self.body)

    def test_throws_falcon_error_for_message_auth_error_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()),\
            patch.object(process.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch.object(process.CorrelationMessage,
                         'process_message',
                         MagicMock(side_effect=
                         errors.MessageAuthenticationError)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_throws_falcon_error_for_resource_not_found_error_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(process.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch.object(process.CorrelationMessage,
                         'process_message',
                         MagicMock(side_effect=
                         errors.ResourceNotFoundError)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_throws_falcon_error_for_coordinator_comm_error_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(process.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch.object(process.CorrelationMessage,
                         'process_message',
                         MagicMock(side_effect=
                         errors.CoordinatorCommunicationError)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_returns_204_for_non_durable_message_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(process.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch.object(process.CorrelationMessage,
                         'process_message',
                         MagicMock()), \
            patch.object(process.CorrelationMessage,
                         'is_durable',
                         MagicMock(return_value=False)):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
            self.assertEquals(self.resp.status, falcon.HTTP_204)

    def test_returns_202_for_durable_message_on_post(self):
        with patch('meniscus.api.correlation.resources.'
                   'load_body', MagicMock(return_value=self.body)), \
            patch.object(PublishMessageResource,
                         '_validate_req_body_on_post', MagicMock()), \
            patch.object(process.TenantIdentification,
                         'get_validated_tenant',
                         MagicMock(return_value=self.tenant)), \
            patch.object(process.CorrelationMessage,
                         'process_message',
                         MagicMock()), \
            patch.object(process.CorrelationMessage,
                         'is_durable',
                         MagicMock(return_value=True)):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
            self.assertEquals(self.resp.status, falcon.HTTP_202)
            self.assertTrue("job_id" in self.resp.body)
            self.assertTrue("job_status_uri" in self.resp.body)

if __name__ == '__main__':
    unittest.main()
