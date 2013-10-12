import unittest

from mock import MagicMock, patch

from meniscus.data.model.tenant import EventProducer, Tenant
from meniscus.openstack.common import jsonutils

from meniscus.data.model import tenant_util


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingFindMethods())


class WhenTestingFindMethods(unittest.TestCase):

    def setUp(self):
        self.tenant_id = "12673247623548752387452378"
        self.tenant_dict = {
            "tenant_id": self.tenant_id,
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
        self.producer_id = "234"
        self.event_producer = EventProducer(
            _id=self.producer_id, name="nginx", pattern="nginx")
        self.ds_handler = MagicMock()
        self.ds_handler.find_one.return_value = self.tenant_dict
        self.tenant_obj = tenant_util.load_tenant_from_dict(self.tenant_dict)
        self.tenant_cache = MagicMock()
        self.tenant_cache.cache_get.return_value = jsonutils.dumps(
            self.tenant_dict)
        self.tenant_cache.cache_exists.return_value = True
        self.tenant_cache.cache_update = MagicMock()
        self.token_cache = MagicMock()
        self.token_cache.cache_get.return_value = jsonutils.dumps(
            self.tenant_dict['token'])
        self.token_cache.cache_exists.return_value = True
        self.cache_empty = MagicMock()
        self.cache_empty.cache_exists.return_value = False
        self.cache_empty.cache_set = MagicMock()

    def test_find_tenant_returns_instance(self):
        retrieve_tenant_call = MagicMock(return_value=self.tenant_obj)
        with patch('meniscus.data.model.tenant_util.retrieve_tenant',
                   retrieve_tenant_call):
            tenant = tenant_util.find_tenant('12345')
            self.assertIsInstance(tenant, Tenant)

    def test_find_tenant_returns_none(self):
        retrieve_tenant_call = MagicMock(return_value=None)
        with patch('meniscus.data.model.tenant_util.retrieve_tenant',
                   retrieve_tenant_call):
            tenant = tenant_util.find_tenant('12345')
            self.assertIsNone(tenant)

    def test_find_tenant_creates_new_tenant_on_no_tenant_found(self):
        retrieve_tenant_call = MagicMock(side_effect=[None, self.tenant_obj])
        create_tenant_call = MagicMock()
        with patch('meniscus.data.model.tenant_util.retrieve_tenant',
                   retrieve_tenant_call), patch(
                'meniscus.data.model.tenant_util.create_tenant',
                create_tenant_call):
            tenant = tenant_util.find_tenant(
                'unknown_tenant_id', create_on_missing=True)
            self.assertIsInstance(tenant, Tenant)
            create_tenant_call.assert_called_once_with('unknown_tenant_id')

    def test_create_tenant(self):
        ttl_create_index_call = MagicMock()
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler), patch(
                'meniscus.data.model.tenant_util.ttl_tasks.create_index.delay',
                ttl_create_index_call):
            tenant_util.create_tenant(self.tenant_id)
            self.ds_handler.put.assert_called_once()
            self.ds_handler.create_sequence.assert_called_once_with(
                self.tenant_id)
            ttl_create_index_call.assert_called_once_with(self.tenant_id)

    def test_retrieve_tenant_returns_tenant_obj(self):
        self.ds_handler.find_one = MagicMock(return_value=self.tenant_dict)
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant = tenant_util.retrieve_tenant(self.tenant_id)
            self.ds_handler.find_one.assert_called_once_with(
                'tenant', {'tenant_id': self.tenant_id})
            self.assertIsInstance(tenant, Tenant)

    def test_retrieve_tenant_returns_none_when_no_tenant_found(self):
        self.ds_handler.find_one = MagicMock(return_value=None)
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant = tenant_util.retrieve_tenant(self.tenant_id)
            self.ds_handler.find_one.assert_called_once_with(
                'tenant', {'tenant_id': self.tenant_id})
            self.assertIsNone(tenant)

    def test_save_tenant(self):
        self.ds_handler.update = MagicMock()
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant_util.save_tenant(self.tenant_obj)
            self.ds_handler.update.assert_called_once_with(
                'tenant', self.tenant_obj.format_for_save())

    def test_load_tenant_from_dict(self):
        tenant = tenant_util.load_tenant_from_dict(
            self.tenant_obj.format_for_save())
        self.assertIsInstance(tenant, Tenant)
        self.assertEqual(tenant.format_for_save(),
                         self.tenant_obj.format_for_save())

    def test_create_event_producer(self):
        self.ds_handler.next_sequence_value = MagicMock(
            return_value=self.producer_id)
        ttl_create_mapping_call = MagicMock()
        save_tenant_call = MagicMock()
        with patch(
                'meniscus.data.model.tenant_util._db_handler',
                self.ds_handler), \
            patch(
                'meniscus.data.model.tenant_util.'
                'ttl_tasks.create_ttl_mapping.delay',
                ttl_create_mapping_call), \
            patch(
                'meniscus.data.model.tenant_util.save_tenant',
                save_tenant_call):
            new_producer_id = tenant_util.create_event_producer(
                self.tenant_obj,
                self.event_producer.name,
                self.event_producer.pattern,
                self.event_producer.durable,
                self.event_producer.encrypted,
                self.event_producer.sinks
            )
            save_tenant_call.assert_called_once_with(self.tenant_obj)
            ttl_create_mapping_call.assert_called_once_with(
                tenant_id=self.tenant_obj.tenant_id,
                producer_pattern=self.event_producer.pattern)
            self.assertEqual(new_producer_id, self.producer_id)

    def test_delete_event_producer(self):
        save_tenant_call = MagicMock()
        with patch('meniscus.data.model.tenant_util.save_tenant',
                   save_tenant_call):
            producer_to_delete = self.tenant_obj.event_producers[0]
            tenant_util.delete_event_producer(
                self.tenant_obj, producer_to_delete)
            self.assertFalse(
                producer_to_delete in self.tenant_obj.event_producers)
            save_tenant_call.assert_called_once_with(self.tenant_obj)

    def test_find_event_producer_by_id_returns_instance(self):
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant = tenant_util.find_tenant('12345')
            producer = tenant_util.find_event_producer(tenant, producer_id=123)
            self.assertIsInstance(producer, EventProducer)

    def test_find_event_producer_by_id_returns_none(self):
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant = tenant_util.find_tenant('12345')
            producer = tenant_util.find_event_producer(tenant, producer_id=130)
            self.assertEquals(producer, None)

    def test_find_event_producer_by_name_returns_instance(self):
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant = tenant_util.find_tenant('12345')
            producer = tenant_util.find_event_producer(
                tenant, producer_name='system.auth')
            self.assertIsInstance(producer, EventProducer)

    def test_find_event_producer_by_name_returns_none(self):
        with patch('meniscus.data.model.tenant_util._db_handler',
                   self.ds_handler):
            tenant = tenant_util.find_tenant('12345')
            producer = tenant_util.find_event_producer(
                tenant, producer_name='not_name')
            self.assertEquals(producer, None)

if __name__ == '__main__':
    unittest.main()
