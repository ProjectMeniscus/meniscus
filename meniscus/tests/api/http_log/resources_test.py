import unittest

from mock import MagicMock
from mock import patch
import falcon
import falcon.testing as testing
from meniscus.correlation import correlator

import meniscus.correlation.errors as errors
with patch('meniscus.data.datastore.datasource_handler', MagicMock()):
    from meniscus.api.http_log.resources import PublishMessageResource
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

        self.tenant = tenant.Tenant(
            self.tenant_id, self.token, event_producers=self.producers)
        self.message = {
            "log_message":  {
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

    def test_returns_202_for_non_durable_message(self):
        correlate_http_msg_func = MagicMock()
        with patch('meniscus.correlation.correlator.correlate_http_message',
                   correlate_http_msg_func):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                    MESSAGE_TOKEN: self.token
                },
                body=jsonutils.dumps(self.message))
            correlate_http_msg_func.assert_called_once()

        self.assertEquals(falcon.HTTP_204, self.srmock.status)


if __name__ == '__main__':
    unittest.main()
