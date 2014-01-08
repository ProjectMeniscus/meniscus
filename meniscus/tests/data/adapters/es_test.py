import unittest
from mock import MagicMock, patch
from meniscus.data.adapters import es
from meniscus.data.adapters.es import elasticsearch


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingEsDataSourceHandler)

    return suite


class WhenTestingEsDataSourceHandler(unittest.TestCase):
    def setUp(self):
        self.conf = MagicMock()
        self.conf = MagicMock()
        self.conf.servers = ['localhost:9200']
        self.conf.bulk_size = 100
        self.conf.ttl = 30
        self.es_handler = es.NamedDatasourceHandler(self.conf)
        self.mock_index = "dc2bb3e0-3116-11e3-aa6e-0800200c9a66"
        self.mock_mapping = {
            "mapping": {
                "properties": {
                    "field": {
                        "type": "date",
                        "format": "dateOptionalTime"
                    }
                }
            }
        }

    def test_constructor(self):
        #test es_handler constructor with no bulk off
        self.assertEqual(
            self.es_handler.es_servers,
            [{'host': 'localhost', 'port': '9200'}]
        )
        self.assertEqual(self.es_handler.bulk_size, self.conf.bulk_size)
        self.assertEqual(self.es_handler.ttl, self.conf.ttl)
        self.assertEquals(self.es_handler.status, es.STATUS_NEW)

    def test_check_connection(self):
        self.es_handler.status = es.STATUS_NEW
        with self.assertRaises(es.DatabaseHandlerError):
            self.es_handler._check_connection()

        self.es_handler.status = es.STATUS_CLOSED
        with self.assertRaises(es.DatabaseHandlerError):
            self.es_handler._check_connection()

        #test that a status of  STATUS_CONNECTED  does not raise an exception
        handler_error_raised = False
        try:
            self.es_handler.status = es.STATUS_CONNECTED
            self.es_handler._check_connection()
        except es.DatabaseHandlerError:
            handler_error_raised = True
        self.assertFalse(handler_error_raised)

    def test_connection(self):
        connection = MagicMock(return_value=None)
        with patch.object(elasticsearch.Elasticsearch, '__init__', connection):
            self.es_handler.connect()
        connection.assert_called_once_with(
            hosts=self.es_handler.es_servers
        )
        self.assertEquals(
            self.es_handler.status,
            es.STATUS_CONNECTED)

    def test_close(self):
        self.es_handler.close()
        self.assertEqual(self.es_handler.connection, None)
        self.assertEqual(self.es_handler.status, es.STATUS_CLOSED)

    def test_create_index(self):
        create_index_method = MagicMock()
        connection = MagicMock()
        connection.indices.create = create_index_method
        self.es_handler.connection = connection

        self.es_handler.create_index(self.mock_index)
        create_index_method.assert_called_once_with(
            index=self.mock_index, body=None)

    def test_create_index_mapping(self):
        create_index_method = MagicMock()
        connection = MagicMock()
        connection.indices.create = create_index_method
        self.es_handler.connection = connection
        self.es_handler.create_index(
            self.mock_index, mapping=self.mock_mapping)
        create_index_method.assert_called_once_with(
            index=self.mock_index, body=self.mock_mapping)

    def test_put_mapping(self):
        put_mapping_method = MagicMock()
        connection = MagicMock()
        connection.indices.put_mapping = put_mapping_method
        self.es_handler.connection = connection
        doc_type = "default"
        self.es_handler.put_mapping(
            index=self.mock_index, doc_type=doc_type,
            mapping=self.mock_mapping)
        put_mapping_method.assert_called_once_with(
            index=self.mock_index,
            doc_type=doc_type,
            body=self.mock_mapping
        )
