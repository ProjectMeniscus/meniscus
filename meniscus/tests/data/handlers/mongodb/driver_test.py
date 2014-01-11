import unittest
from mock import MagicMock, patch
from meniscus.data.handlers.mongodb import driver as mongodb


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingMongoDataSourceHandler())
    return suite


class WhenTestingMongoDataSourceHandler(unittest.TestCase):
    def setUp(self):
        self.conf = MagicMock()

        self.conf.servers = ['localhost:9200']
        self.conf.username = 'mongodb'
        self.conf.password = 'pass'
        self.mongo_handler = mongodb.MongoDBHandler(self.conf)

    def test_constructor(self):
        self.assertEqual(self.mongo_handler.mongo_servers, self.conf.servers)
        self.assertEqual(self.mongo_handler.username, self.conf.username)
        self.assertEqual(self.mongo_handler.password, self.conf.password)

    def test_check_connection(self):
        self.mongo_handler.status = None
        with self.assertRaises(mongodb.MongoDBHandlerError):
            self.mongo_handler._check_connection()

        self.mongo_handler.status = self.mongo_handler.STATUS_CLOSED
        with self.assertRaises(mongodb.MongoDBHandlerError):
            self.mongo_handler._check_connection()

        #test that a status of  STATUS_CONNECTED  does not raise an exception
        handler_error_raised = False
        try:
            self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
            self.mongo_handler._check_connection()
        except mongodb.MongoDBHandlerError:
            handler_error_raised = True
        self.assertFalse(handler_error_raised)

    def test_connection(self):
        connection = MagicMock(return_value=MagicMock())
        with patch(
                'meniscus.data.handlers.mongodb.driver.MongoClient',
                connection):
            self.mongo_handler.connect()
        connection.assert_called_once_with(self.mongo_handler.mongo_servers,
                                           slave_okay=True)
        self.assertEquals(
            self.mongo_handler.status, self.mongo_handler.STATUS_CONNECTED)

    def test_close_connection(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CLOSED
        connection = MagicMock(return_value=MagicMock())
        with patch(
                'meniscus.data.handlers.mongodb.driver.MongoClient',
                connection):
            self.mongo_handler.connect()
        self.mongo_handler.close()
        self.assertEquals(
            self.mongo_handler.status, self.mongo_handler.STATUS_CLOSED)

    def test_create_sequence_existing_sequence(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        sequence = 'sequence01'
        create_sequence = MagicMock()
        self.mongo_handler.find_one = create_sequence
        self.mongo_handler.create_sequence(sequence)
        create_sequence.assert_called_once_with('counters', {'name': sequence})

    def test_create_sequence_new_sequence(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        sequence = 'sequence01'
        create_sequence = MagicMock()
        self.mongo_handler.find_one = MagicMock(return_value=None)
        self.mongo_handler.put = create_sequence
        self.mongo_handler.create_sequence(sequence)
        create_sequence.assert_called_once_with('counters', {'name': sequence,
                                                             'seq': 1})

    def test_delete_sequence(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        sequence = 'sequence01'
        delete_sequence = MagicMock()
        self.mongo_handler.delete = delete_sequence
        self.mongo_handler.delete_sequence(sequence)
        delete_sequence.assert_called_once_with('counters', {'name': sequence})

    def test_next_sequence_value(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        sequence_name = 'sequence01'
        next_sequence_value = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database['counters'].find_and_modify \
            = next_sequence_value
        self.mongo_handler.next_sequence_value(sequence_name)
        next_sequence_value.assert_called_once_with(
            {'name': sequence_name}, {'$inc': {'seq': 1}})

    def test_find_no_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        find = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].find = find
        self.mongo_handler.find(object_name)
        find.assert_called_once_with({}, None)

    def test_find_with_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        query_filter = {"filter": "test"}
        find = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].find = find
        self.mongo_handler.find(object_name, query_filter)
        find.assert_called_once_with(query_filter, None)

    def test_find_one_no_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        find_one = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].find_one = find_one
        self.mongo_handler.find_one(object_name)
        find_one.assert_called_once_with({})

    def test_find_one_with_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        query_filter = {"filter": "test"}
        find_one = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].find_one = find_one
        self.mongo_handler.find_one(object_name, query_filter)
        find_one.assert_called_once_with(query_filter)

    def test_put_no_document(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        insert = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].insert = insert
        self.mongo_handler.put(object_name)
        insert.assert_called_once_with({})

    def test_put_with_document(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        document = {"document": "test"}
        insert = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].insert = insert
        self.mongo_handler.put(object_name, document)
        insert.assert_called_once_with(document)

    def test_update_with_document(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        document = {"_id": "test"}
        save = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].save = save
        self.mongo_handler.update(object_name, document)
        save.assert_called_once_with(document)

    def test_set_field_no_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        update_fields = {}
        set_field = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].update = set_field
        self.mongo_handler.set_field(object_name, update_fields)
        set_field.assert_called_once_with(
            {}, {"$set": update_fields}, multi=True)

    def test_set_field_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        query_filter = {'filter01': 'test'}
        update_fields = {'field': 'test'}
        set_field = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].update = set_field
        self.mongo_handler.set_field(object_name, update_fields, query_filter)
        set_field.assert_called_once_with({'filter01': 'test'},
                                          {'$set': {'field': 'test'}},
                                          multi=True)

    def test_remove_field_no_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        update_fields = {'field': 'test'}
        remove_field = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].update = remove_field
        self.mongo_handler.remove_field(object_name, update_fields)
        remove_field.assert_called_once_with(
            {}, {"$unset": update_fields}, multi=True)

    def test_remove_field_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        query_filter = {'filter01': 'test'}
        update_fields = {'field': 'test'}
        remove_field = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].update = remove_field
        self.mongo_handler.remove_field(object_name, update_fields,
                                        query_filter)
        remove_field.assert_called_once_with({'filter01': 'test'},
                                             {'$unset': {'field': 'test'}},
                                             multi=True)

    def test_find_one_no_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        remove = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].remove = remove
        self.mongo_handler.delete(object_name)
        remove.assert_called_once_with({}, True)

    def test_find_one_with_query_filter(self):
        self.mongo_handler.status = self.mongo_handler.STATUS_CONNECTED
        object_name = 'object01'
        query_filter = {"filter": "test"}
        remove = MagicMock()
        self.mongo_handler.database = MagicMock()
        self.mongo_handler.database[object_name].remove = remove
        self.mongo_handler.delete(object_name, query_filter)
        remove.assert_called_once_with({'filter': 'test'}, True)


class WhenTestingGetHandler(unittest.TestCase):
    def setUp(self):
        self.connect_method = MagicMock()

    def test_get_handler(self):
        with patch.object(
                mongodb.MongoDBHandler, 'connect', self.connect_method):
            handler = mongodb.get_handler()
            self.connect_method.assert_called_once_with()
            self.assertIsInstance(handler, mongodb.MongoDBHandler)


if __name__ == '__main__':
    unittest.main()
