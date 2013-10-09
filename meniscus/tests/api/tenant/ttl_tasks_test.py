import unittest

from mock import MagicMock, patch
with patch('meniscus.data.datastore.datasource_handler', MagicMock()):
    from meniscus.api.tenant import ttl_tasks


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingTtlTasks())
    return suite


class WhenTestingTtlTasks(unittest.TestCase):

    def setUp(self):
        self.tenant_id = "dc2bb3e0-3116-11e3-aa6e-0800200c9a66"
        self.doc_type = "default"
        self.db_handler = MagicMock()
        self.create_index_method = MagicMock()
        self.db_handler.create_index = self.create_index_method

    def test_create_index(self):
        delay_call = MagicMock()
        ttl_tasks.create_ttl_mapping = MagicMock()
        ttl_tasks.create_ttl_mapping.delay = delay_call

        with patch('meniscus.api.tenant.ttl_tasks._db_handler',
                   self.db_handler):
            ttl_tasks.create_index(self.tenant_id)
        self.create_index_method.assert_called_once_with(index=self.tenant_id)
        delay_call.assert_called_once_with(self.tenant_id, "default")

    def test_create_ttl_mapping(self):
        pass


if __name__ == "__main__":
    unittest.main()