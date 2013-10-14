import unittest
from mock import MagicMock, patch
from meniscus.data.adapters import elasticsearch
from meniscus.data.adapters.elasticsearch import pyes


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingFormatMethods())
    suite.addTest(WhenTestingEsDataSourceHandler)

    return suite


class WhenTestingFormatMethods(unittest.TestCase):
    def setUp(self):
        self.unformatted_terms = {
            "tenant_id": "abcd1234",
            "log_level": "DEBUG"
        }
        self.expected_format = [
            {
                'term': {
                    "tenant_id": "abcd1234"
                }
            },
            {
                'term': {
                    "log_level": "DEBUG"
                }
            }
        ]

        self.positive_terms = {
            "appname": "apache",
            "tenant_id": "abcd1234"
        }
        self.negative_terms = {
            "log_level": "DEBUG"
        }
        self.expected_search = {
            'bool': {
                'must_not': [
                    {
                        'term': {
                            'log_level': 'DEBUG'
                        }
                    }
                ],
                'must': [
                    {
                        'term': {
                            'tenant_id': 'abcd1234'
                        }
                    },
                    {
                        'term': {
                            'appname': 'apache'
                        }
                    }
                ]
            }
        }

    def test_format_terms(self):
        formatted_terms = elasticsearch.format_terms(self.unformatted_terms)
        self.assertEqual(formatted_terms, self.expected_format)

    def test_format_search(self):
        formatted_search = elasticsearch.format_search(
            self.positive_terms, self.negative_terms)

        self.assertEqual(formatted_search, self.expected_search)


class WhenTestingEsDataSourceHandler(unittest.TestCase):
    def setUp(self):
        self.conf = MagicMock()
        self.conf.servers = ['localhost:9200']
        self.conf.bulk_size = None
        self.conf.ttl = 45

        self.bulk_conf = MagicMock()
        self.bulk_conf.servers = ['localhost:9200']
        self.bulk_conf.bulk_size = 100
        self.bulk_conf.ttl = 30

        self.es_handler = elasticsearch.NamedDatasourceHandler(self.conf)
        self.es_bulk_handler = elasticsearch.NamedDatasourceHandler(
            self.bulk_conf)

    def test_constructor(self):
        #test es_handler constructor with no bulk off
        self.assertEqual(self.es_handler.es_servers, self.conf.servers)
        self.assertEqual(self.es_handler.bulk_size, self.conf.bulk_size)
        self.assertEqual(self.es_handler.bulk, False)
        self.assertEqual(self.es_handler.ttl, self.conf.ttl)
        self.assertEquals(self.es_handler.status, elasticsearch.STATUS_NEW)

        #test es_handler constructor with bulk on
        self.assertEqual(self.es_bulk_handler.es_servers,
                         self.bulk_conf.servers)
        self.assertEqual(self.es_bulk_handler.bulk_size,
                         self.bulk_conf.bulk_size)
        self.assertEqual(self.es_bulk_handler.bulk, True)
        self.assertEqual(self.es_bulk_handler.ttl, self.bulk_conf.ttl)
        self.assertEquals(self.es_bulk_handler.status,
                          elasticsearch.STATUS_NEW)

    def test_check_connection(self):
        self.es_handler.status = elasticsearch.STATUS_NEW
        with self.assertRaises(elasticsearch.DatabaseHandlerError):
            self.es_handler._check_connection()

        self.es_handler.status = elasticsearch.STATUS_CLOSED
        with self.assertRaises(elasticsearch.DatabaseHandlerError):
            self.es_handler._check_connection()

        #test that a status of  STATUS_CONNECTED  does not raise an exception
        handler_error_raised = False
        try:
            self.es_handler.status = elasticsearch.STATUS_CONNECTED
            self.es_handler._check_connection()
        except elasticsearch.DatabaseHandlerError:
            handler_error_raised = True
        self.assertFalse(handler_error_raised)

    def test_connection(self):
        connection = MagicMock(return_value=None)
        with patch.object(pyes.ES, '__init__', connection):
            self.es_handler.connect()
        connection.assert_called_once_with(
            self.es_handler.es_servers,
            bulk_size=None
        )
        self.assertEquals(
            self.es_handler.status,
            elasticsearch.STATUS_CONNECTED)

        connection = MagicMock(return_value=None)
        with patch.object(pyes.ES, '__init__', connection):
            self.es_bulk_handler.connect()
        connection.assert_called_once_with(
            self.es_bulk_handler.es_servers,
            bulk_size=self.es_bulk_handler.bulk_size
        )
        self.assertEquals(
            self.es_bulk_handler.status,
            elasticsearch.STATUS_CONNECTED)

    def test_close(self):
        self.es_handler.close()
        self.assertEqual(self.es_handler.connection, None)
        self.assertEqual(self.es_handler.status, elasticsearch.STATUS_CLOSED)

    def test_put(self):
        index_method = MagicMock()
        connection = MagicMock()
        connection.index = index_method
        self.es_handler.connection = connection
        self.es_handler.status = elasticsearch.STATUS_CONNECTED

        test_uuid = "7eaf874c-ea3a-4098-9617-35de9392d3b1"

        #test with default document and ttl
        with patch(
                'meniscus.data.adapters.elasticsearch.uuid.uuid4',
                MagicMock(return_value=test_uuid)):
            object_name = 'syslog'
            index_name = 'tenant_id'
            self.es_handler.put(object_name, index=index_name)
            index_method.assert_called_once_with(
                dict(), index_name, object_name, test_uuid,
                bulk=self.es_handler.bulk, ttl=self.es_handler.ttl)

        #test with assigned document and ttl values
        index_method = MagicMock()
        connection = MagicMock()
        connection.index = index_method
        self.es_handler.connection = connection
        self.es_handler.status = elasticsearch.STATUS_CONNECTED

        test_ttl = "120d"
        test_document = {"log": "test_data"}
        with patch(
                'meniscus.data.adapters.elasticsearch.uuid.uuid4',
                MagicMock(return_value=test_uuid)):
            object_name = 'syslog'
            index_name = 'tenant_id'
            self.es_handler.put(
                object_name, document=test_document,
                index=index_name, ttl=test_ttl)
            index_method.assert_called_once_with(
                test_document, index_name, object_name, test_uuid,
                bulk=self.es_handler.bulk, ttl=test_ttl)

    def test_create_index(self):
        create_index_method = MagicMock()
        connection = MagicMock()
        connection.indices.create_index_if_missing = create_index_method
        self.es_handler.connection = connection

        index = "dc2bb3e0-3116-11e3-aa6e-0800200c9a66"

        self.es_handler.create_index(index)
        create_index_method.assert_called_once_with(index=index)

    def test_put_ttl_mapping(self):
        put_mapping_method = MagicMock()
        connection = MagicMock()
        connection.indices.put_mapping = put_mapping_method
        self.es_handler.connection = connection

        index = "dc2bb3e0-3116-11e3-aa6e-0800200c9a66"
        doc_type = "default"

        self.es_handler.put_ttl_mapping(doc_type=doc_type, index=index)
        put_mapping_method.assert_called_once_with(
            doc_type=doc_type,
            mapping={"_ttl": {"enabled": True}},
            indices=[index])
