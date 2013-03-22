import httplib
from mock import MagicMock
from mock import patch
import unittest

import falcon
import requests

from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.personas.worker.correlation.resources \
    import PublishMessageResource


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPublishMessage())
    return suite


class WhenTestingPublishMessage(unittest.TestCase):
    def setUp(self):

        self.cache = MagicMock()
        self.resource = PublishMessageResource(self.cache)
        self.timestamp = "2013-03-19T18:16:48.411029Z"
        self.profiles = [HostProfile(123, 'profile1',
                                     event_producer_ids=[432, 433]),
                         HostProfile(456, 'profile2',
                                     event_producer_ids=[432, 433])]
        self.producers = [EventProducer(432, 'producer1', 'syslog'),
                          EventProducer(433, 'producer2', 'syslog')]
        self.hosts = [Host(765, 'host1', ip_address_v4='192.168.1.1',
                           profile_id=123),
                      Host(766, 'host2', ip_address_v4='192.168.2.1',
                           profile_id=456)]
        self.token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                           'bbd6302e-8d93-47dc-a49a-8fb0d39e5192',
                           "2013-03-19T18:16:48.411029Z")
        self.tenant_id = '1234'
        self.tenant = Tenant(self.tenant_id, self.token,
                             profiles=self.profiles,
                             event_producers=self.producers,
                             hosts=self.hosts)
        self.tenant_not_found = MagicMock(return_value=None)
        self.tenant_found = MagicMock(return_value=self.tenant)

    def test_validate_req_body_throws_exception_host_not_provided(self):
        body = {
            "host": "",
            "pname": "pname",
            "time": "2013-03-19T18:16:48.411029Z"
        }
