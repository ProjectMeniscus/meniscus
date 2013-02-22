from meniscus.model.tenant import Tenant, Host, HostProfile, EventProducer
from meniscus.model.util import *
from mock import MagicMock
import unittest


class WhenTestingFindTenant(unittest.TestCase):

    def setUp(self):
        self.ds_handler = MagicMock()
        self.ds_handler.find_one.return_value = {
            "tenant_id": "12345",
            "_id": "507f1f77bcf86cd799439011",
            "hosts": [
                {
                    "id": 121,
                    "hostname": "ws-n01",
                    "ip_address_v4": "127.0.0.1",
                    "ip_address_v6": "::1",
                    "profile": 122
                }
            ],
            "profiles": [
                {
                    "id": 122,
                    "name": "test",
                    "event_producers": [
                        123,
                        124
                    ]
                }
            ],
            "event_producers": [
                {
                    "id": 123,
                    "name": "apache",
                    "pattern": "apache2.cee",
                    "durable": False,
                    "encrypted": False
                },
                {
                    "id": 124,
                    "name": "system.auth",
                    "pattern": "auth_log.cee",
                    "durable": False,
                    "encrypted": False
                }
            ]
        }

        self.ds_handler_empty = MagicMock()
        self.ds_handler_empty.find_one.return_value = None

    def test_find_tenant_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        assert isinstance(tenant, Tenant)

    def test_find_tenant_returns_none(self):
        tenant = find_tenant(self.ds_handler_empty, '12345')
        assert tenant is None

    def test_find_host_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        host = find_host(tenant, 121)
        assert isinstance(host, Host)

    def test_find_host_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        host = find_host(tenant, 130)
        assert host is None

    def test_find_profile_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        profile = find_host_profile(tenant, 122)
        assert isinstance(profile, HostProfile)

    def test_find_profile_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        profile = find_host_profile(tenant, 130)
        assert profile is None

    def test_find_event_producer_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        producer = find_event_producer(tenant, 123)
        assert isinstance(producer, EventProducer)

    def test_find_event_producer_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        producer = find_event_producer(tenant, 130)
        assert producer is None

if __name__ == '__main__':
    unittest.main()