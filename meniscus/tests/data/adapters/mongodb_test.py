import unittest
import os

from mock import MagicMock, patch

from meniscus.config import init_config, get_config
from meniscus.data.datastore import datasource_handler
from meniscus.data.adapters import mongodb
from meniscus.data.adapters.mongodb import MongoClient


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenConnectingToLiveMongoDB())
    suite.addTest(WhenTestingMongoDataSourceHandler())
    return suite


class WhenTestingMongoDataSourceHandler(unittest.TestCase):
    def setUp(self):
        self.conf = MagicMock()

        self.conf.servers = ['localhost:9200']
        self.conf.username = 'mongodb'
        self.conf.password = 'pass'
        self.mongo_handler = mongodb.NamedDatasourceHandler(self.conf)

    def test_constructor(self):
        self.assertEqual(self.mongo_handler.mongo_servers, self.conf.servers)
        self.assertEqual(self.mongo_handler.username, self.conf.username)
        self.assertEqual(self.mongo_handler.password, self.conf.password)

    def test_check_connection(self):
        self.mongo_handler.status = None
        with self.assertRaises(mongodb.DatabaseHandlerError):
            self.mongo_handler._check_connection()

        self.mongo_handler.status = mongodb.STATUS_CLOSED
        with self.assertRaises(mongodb.DatabaseHandlerError):
            self.mongo_handler._check_connection()

        #test that a status of  STATUS_CONNECTED  does not raise an exception
        handler_error_raised = False
        try:
            self.mongo_handler.status = mongodb.STATUS_CONNECTED
            self.mongo_handler._check_connection()
        except mongodb.DatabaseHandlerError:
            handler_error_raised = True
        self.assertFalse(handler_error_raised)

    def test_connection(self):
        connection = MagicMock(return_value=MagicMock())
        with patch('meniscus.data.adapters.mongodb.MongoClient', connection):
            self.mongo_handler.connect()
        connection.assert_called_once_with(self.mongo_handler.mongo_servers,
                                           slave_okay=True)
        self.assertEquals(self.mongo_handler.status, mongodb.STATUS_CONNECTED)

    def test_close_connection(self):
        self.mongo_handler.status = mongodb.STATUS_CLOSED
        connection = MagicMock(return_value=MagicMock())
        with patch('meniscus.data.adapters.mongodb.MongoClient', connection):
            self.mongo_handler.connect()
        self.mongo_handler.close()
        self.assertEquals(self.mongo_handler.status, mongodb.STATUS_CLOSED)

    def test_create_sequence_existing_sequence(self):
        self.mongo_handler.status = mongodb.STATUS_CONNECTED
        sequence = 'sequence01'
        create_sequence = MagicMock()
        self.mongo_handler.find_one = create_sequence
        self.mongo_handler.create_sequence(sequence)
        create_sequence.assert_called_once_with('counters', {'name': sequence})

    def test_create_sequence_new_sequence(self):
        self.mongo_handler.status = mongodb.STATUS_CONNECTED
        sequence = 'sequence01'
        create_sequence = MagicMock()
        self.mongo_handler.find_one = MagicMock(return_value=None)
        self.mongo_handler.put = create_sequence
        self.mongo_handler.create_sequence(sequence)
        create_sequence.assert_called_once_with('counters', {'name': sequence,
                                                             'seq': 1})

    def test_delete_sequence(self):
        self.mongo_handler.status = mongodb.STATUS_CONNECTED
        sequence = 'sequence01'
        delete_sequence = MagicMock()
        self.mongo_handler.delete = delete_sequence
        self.mongo_handler.delete_sequence(sequence)
        delete_sequence.assert_called_once_with('counters', {'name': sequence})


class WhenConnectingToLiveMongoDB(unittest.TestCase):

    def setUp(self):
        init_config(['--config-file', 'meniscus.cfg'])
        conf = get_config()
        self.handler = datasource_handler(conf)
        self.handler.connect()

    def tearDown(self):
        self.handler.close()

    @unittest.skipIf('RUN_INTEGRATION' not in os.environ or
                     os.environ['RUN_INTEGRATION'] is False,
                     'Integration tests are not enabled. Enable them by '
                     'setting the environment variable "RUN_INTEGRATION"'
                     'to true.')
    def test_mongodb_adapter(self):
        self.handler.put('test', {'name': 'test_1', 'value': 1})
        self.handler.put('test', {'name': 'test_2', 'value': 2})
        self.handler.put('test', {'name': 'test_2', 'value': 3})
        self.handler.put('test', {'name': 'test_2', 'value': 4})
        self.handler.put('test', {'name': 'test_2', 'value': 5})
        self.handler.put('test', {'name': 'test_2', 'value': 6})

        test_obj = self.handler.find_one('test', {'name': 'test_1'})
        self.assertEqual(1, test_obj['value'])

        obj_id = test_obj['_id']
        test_obj['value'] = 10
        self.handler.update('test', test_obj)

        test_obj = self.handler.find_one('test', {'name': 'test_1'})
        self.assertEqual(10, test_obj['value'])
        self.assertEqual(obj_id, test_obj['_id'])

        self.handler.delete('test', {'name': 'test_1'})
        test_obj = self.handler.find_one('test', {'name': 'test_1'})
        self.assertFalse(test_obj)

        test_objects = self.handler.find('test', {'name': 'test_2'})
        self.assertEqual(5, test_objects.count())

        self.handler.delete('test', {'name': 'test_2'})
        test_objects = self.handler.find('test', {'name': 'test_2'})
        self.assertEqual(0, test_objects.count())

    @unittest.skipIf('RUN_INTEGRATION' not in os.environ or
                     os.environ['RUN_INTEGRATION'] is False,
                     'Integration tests are not enabled. Enable them by '
                     'setting the environment variable "RUN_INTEGRATION"'
                     'to true.')
    def test_mongodb_sequences(self):
        self.handler.create_sequence('test')
        seq_val = self.handler.next_sequence_value('test')
        self.assertEqual(1, seq_val)
        seq_val = self.handler.next_sequence_value('test')
        self.assertEqual(2, seq_val)
        self.handler.delete_sequence('test')

        seq_doc = self.handler.find_one('sequence', {'name': 'test'})
        self.assertFalse(seq_doc)


if __name__ == '__main__':
    unittest.main()