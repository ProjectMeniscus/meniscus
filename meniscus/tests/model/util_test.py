from meniscus.model.tenant import Tenant, Host, HostProfile, EventProducer
from meniscus.model.util import *
from mock import MagicMock
import unittest


class WhenTestingFindMethods(unittest.TestCase):

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
        self.assertIsInstance(tenant, Tenant)

    def test_find_tenant_returns_none(self):
        tenant = find_tenant(self.ds_handler_empty, '12345')
        self.assertEquals(tenant, None)

    def test_find_host_by_id_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        host = find_host(tenant, host_id=121)
        self.assertIsInstance(host, Host)

    def test_find_host_by_id_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        host = find_host(tenant, host_id=130)
        self.assertEquals(host, None)

    def test_find_host_by_name_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        host = find_host(tenant, host_name='ws-n01')
        self.assertIsInstance(host, Host)

    def test_find_host_by_name_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        host = find_host(tenant, host_name='not_name')
        self.assertEquals(host, None)

    def test_find_profile_by_id_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        profile = find_host_profile(tenant, profile_id=122)
        self.assertIsInstance(profile, HostProfile)

    def test_find_profile_by_id_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        profile = find_host_profile(tenant, profile_id=130)
        self.assertEquals(profile, None)

    def test_find_profile_by_name_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        profile = find_host_profile(tenant, profile_name='test')
        self.assertIsInstance(profile, HostProfile)

    def test_find_profile_by_name_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        profile = find_host_profile(tenant, profile_name='not_name')
        self.assertEquals(profile, None)

    def test_find_event_producer_by_id_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        producer = find_event_producer(tenant, producer_id=123)
        self.assertIsInstance(producer, EventProducer)

    def test_find_event_producer_by_id_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        producer = find_event_producer(tenant, producer_id=130)
        self.assertEquals(producer, None)

    def test_find_event_producer_by_name_returns_instance(self):
        tenant = find_tenant(self.ds_handler, '12345')
        producer = find_event_producer(tenant, producer_name='system.auth')
        self.assertIsInstance(producer, EventProducer)

    def test_find_event_producer_by_name_returns_none(self):
        tenant = find_tenant(self.ds_handler, '12345')
        producer = find_event_producer(tenant, producer_name='not_name')
        self.assertEquals(producer, None)

if __name__ == '__main__':
    unittest.main()