import unittest

from mock import MagicMock

from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.util import find_event_producer
from meniscus.data.model.util import find_event_producer_for_host
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_host_profile
from meniscus.data.model.util import find_tenant
from meniscus.data.model.util import load_tenant_from_dict
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingFindMethods())


class WhenTestingFindMethods(unittest.TestCase):

    def setUp(self):

        self.tenant = {
            "tenant_id": "12345",
            "tenant_name": "TenantName",
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
            ],
            "token": {
                "valid": "c8a4db32-635a-46b6-94ed-04b1bd533f41",
                "previous": None,
                "last_changed": "2013-03-19T18:16:48.411029Z"
            }
        }
        self.ds_handler = MagicMock()
        self.ds_handler.find_one.return_value = self.tenant
        self.ds_handler_empty = MagicMock()
        self.ds_handler_empty.find_one.return_value = None
        self.tenant_cache = MagicMock()
        self.tenant_cache.cache_get.return_value = jsonutils.dumps(self.tenant)
        self.tenant_cache.cache_exists.return_value = True
        self.tenant_cache.cache_update = MagicMock()
        self.token_cache = MagicMock()
        self.token_cache.cache_get.return_value = jsonutils.dumps(
            self.tenant['token'])
        self.token_cache.cache_exists.return_value = True
        self.cache_empty = MagicMock()
        self.cache_empty.cache_exists.return_value = False
        self.cache_empty.cache_set = MagicMock()

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

    def test_find_event_producer_for_host_no_profile_returns_none(self):
        tenant = load_tenant_from_dict(self.tenant)
        test_host = find_host(tenant, host_name='ws-n01')
        test_host.profile = None
        test_producer = find_event_producer_for_host(
            tenant, test_host, 'producer_name_none')
        self.assertEqual(test_producer, None)

    def test_find_event_producer_for_host_no_producers_for_profile(self):
        tenant = load_tenant_from_dict(self.tenant)
        test_host = find_host(tenant, host_name='ws-n01')
        test_profile = find_host_profile(tenant, profile_id=122)
        test_profile.event_producers = list()
        test_producer = find_event_producer_for_host(
            tenant, test_host, 'producer_name_none')
        self.assertEqual(test_producer, None)

    def test_find_event_producer_for_host_no_producer_found(self):
        tenant = load_tenant_from_dict(self.tenant)
        test_host = find_host(tenant, host_name='ws-n01')
        tenant.event_producers = list()
        test_producer = find_event_producer_for_host(
            tenant, test_host, 'producer_name_none')
        self.assertEqual(test_producer, None)

    def test_find_event_producer_for_host_producer_not_in_profile(self):
        tenant = load_tenant_from_dict(self.tenant)
        test_host = find_host(tenant, host_name='ws-n01')
        test_profile = find_host_profile(tenant, profile_id=122)
        test_profile.event_producers = [124]
        test_producer = find_event_producer_for_host(
            tenant, test_host, 'apache')
        self.assertEqual(test_producer, None)

    def test_find_event_producer_for_host_success_returns_producer(self):
        tenant = load_tenant_from_dict(self.tenant)
        test_host = find_host(tenant, host_name='ws-n01')
        test_producer = find_event_producer_for_host(
            tenant, test_host, 'apache')
        self.assertIsInstance(test_producer, EventProducer)


if __name__ == '__main__':
    unittest.main()
