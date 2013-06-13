import unittest

from mock import MagicMock
from mock import patch
import falcon
import falcon.testing as testing

import meniscus.api.correlation.correlation_exceptions as errors
from meniscus.api.correlation.resources import correlator
from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.data.model import tenant
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPublishMessage())
    return suite


class WhenTestingPublishMessage(testing.TestBase):
    def before(self):
        self.resource = PublishMessageResource()
        self.tenant_id = '1234'
        self.token = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.host_name = 'tohru'
        self.producer_durable = 'durable'
        self.producer_non_durable = 'non_durable'
        self.pattern = "http://projectmeniscus.org/cee/profiles/base"
        self.producers = [
            tenant.EventProducer(1, self.producer_durable,
                                 self.pattern, durable=True),
            tenant.EventProducer(2, self.producer_non_durable, self.pattern)
        ]
        self.profiles = [tenant.HostProfile(1, 'myprofile', [1, 2])]
        self.hosts = [tenant.Host(1, 'tohru', profile_id=1)]
        self.bad_host_name = 'badhostname'

        self.tenant = tenant.Tenant(
            self.tenant_id, self.token, profiles=self.profiles,
            hosts=self.hosts, event_producers=self.producers)
        self.message = {
            "log_message":  {
                "profile": self.pattern,
                "ver": "1",
                "msgid": "-",
                "pri": "46",
                "pid": "-",
                "host": self.host_name,
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
        }

        self.req = MagicMock()
        self.req.get_header.return_value = \
            'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.resp = MagicMock()

        self.test_route = '/v1/tenant/{tenant_id}/publish'
        self.api.add_route(self.test_route, self.resource)

    def test_returns_400_for_no_message_token_header(self):
        self.simulate_request(
            self.test_route,
            method='POST',
            headers={
                'content-type': 'application/json'
            },
            body=jsonutils.dumps(self.message))
        self.assertEquals(falcon.HTTP_400, self.srmock.status)

    def test_returns_401_for_MessageAuthenticationError(self):
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant',
                          MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(side_effect=errors.MessageAuthenticationError)):

            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                    MESSAGE_TOKEN: self.token
                },
                body=jsonutils.dumps(self.message))

        self.assertEquals(falcon.HTTP_401, self.srmock.status)

    def test_returns_404_for_ResourceNotFoundError(self):
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant',
                          MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(side_effect=errors.ResourceNotFoundError)):

            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                    MESSAGE_TOKEN: self.token
                },
                body=jsonutils.dumps(self.message))

        self.assertEquals(falcon.HTTP_404, self.srmock.status)

    def test_returns_500_for_CoordinatorCommunicationError(self):
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant',
                          MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.correlator.'
                  'add_correlation_info_to_message',
                  MagicMock(side_effect=errors.CoordinatorCommunicationError)):

            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                    MESSAGE_TOKEN: self.token
                },
                body=jsonutils.dumps(self.message))

        self.assertEquals(falcon.HTTP_500, self.srmock.status)

    def test_returns_204_for_non_durable_message(self):
        self.message['log_message']['pname'] = self.producer_non_durable
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant',
                          MagicMock(return_value=self.tenant)),\
            patch('meniscus.api.correlation.resources.persist_message',
                  MagicMock()):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                    MESSAGE_TOKEN: self.token
                },
                body=jsonutils.dumps(self.message))
        self.assertEquals(falcon.HTTP_204, self.srmock.status)

    def test_returns_202_for_non_durable_message(self):
        self.message['log_message']['pname'] = self.producer_durable
        with patch.object(correlator.TenantIdentification,
                          'get_validated_tenant',
                          MagicMock(return_value=self.tenant)), \
            patch('meniscus.api.correlation.resources.persist_message',
                  MagicMock()):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                    MESSAGE_TOKEN: self.token
                },
                body=jsonutils.dumps(self.message))
        self.assertEquals(falcon.HTTP_202, self.srmock.status)


if __name__ == '__main__':
    unittest.main()
