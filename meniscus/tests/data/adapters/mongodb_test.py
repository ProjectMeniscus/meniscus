import unittest
import os

from meniscus.config import init_config, get_config

from meniscus.data.datastore import datasource_handler


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenConnectingToLiveMongoDB())

    return suite


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

        test_objs = self.handler.find('test', {'name': 'test_2'})
        self.assertEqual(5, test_objs.count())

        self.handler.delete('test', {'name': 'test_2'})
        test_objs = self.handler.find('test', {'name': 'test_2'})
        self.assertEqual(0, test_objs.count())

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
