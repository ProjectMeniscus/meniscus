import unittest

from mock import MagicMock, patch

from meniscus.data import mapping_tasks


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
        self.put_mapping_method = MagicMock()
        self.db_handler.put_mapping = self.put_mapping_method

    def test_create_ttl_mapping(self):
        with patch('meniscus.data.mapping_tasks._db_handler',
                   self.db_handler):
            mapping_tasks.create_ttl_mapping(self.tenant_id, self.doc_type)
            self.put_mapping_method.assert_called_once_with(
                index=self.tenant_id, doc_type=self.doc_type,
                mapping=mapping_tasks.TTL_MAPPING
            )

    def test_create_index(self):
        delay_call = MagicMock()

        with patch('meniscus.data.mapping_tasks._db_handler',
                   self.db_handler), \
                patch('meniscus.data.mapping_tasks.create_ttl_mapping',
                      MagicMock()):
            mapping_tasks.create_index(self.tenant_id)
        self.create_index_method.assert_called_once_with(
            index=self.tenant_id, mapping=mapping_tasks.DEFAULT_MAPPING)


if __name__ == "__main__":
    unittest.main()
