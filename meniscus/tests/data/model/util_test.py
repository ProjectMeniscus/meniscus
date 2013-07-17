import unittest

from mock import MagicMock

from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.util import find_event_producer
from meniscus.data.model.util import find_tenant
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
            "event_producers": [
                {
                    "id": 123,
                    "name": "apache",
                    "pattern": "apache2.cee",
                    "durable": False,
                    "encrypted": False,
                    "sinks": ["elasticsearch"]
                },
                {
                    "id": 124,
                    "name": "system.auth",
                    "pattern": "auth_log.cee",
                    "durable": False,
                    "encrypted": False,
                    "sinks": ["elasticsearch", "hdfs"]
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
        self.ds_handler_no_tenant = MagicMock()
        self.ds_handler_no_tenant.put = MagicMock()
        self.ds_handler_no_tenant.find_one.side_effect = [None, self.tenant]
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

    def test_find_tenant_creates_new_tenant_on_no_tenant_found(self):

        tenant = find_tenant(self.ds_handler_no_tenant,
                             'unknown_tenant',
                             create_on_missing=True)
        self.assertIsInstance(tenant, Tenant)
        self.ds_handler_no_tenant.put.assert_called_once()

    def test_find_tenant_returns_none(self):
        tenant = find_tenant(self.ds_handler_empty, '12345')
        self.assertEquals(tenant, None)

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
