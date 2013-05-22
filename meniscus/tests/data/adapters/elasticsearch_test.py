import unittest
import os

from meniscus.config import init_config, get_config

from meniscus.data import adapters
from meniscus.data.handler import datasource_handler

from meniscus.data.adapters.elasticsearch import format_search


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenConnectingToLiveES())

    return suite


class WhenBuildingQueryObjects(unittest.TestCase):

    def test_should_format_one_term_queries(self):
        expected = {
            'bool': {
                'must': [
                    {
                        'term': {
                            'test': 'value'
                        }
                    }
                ]
            }
        }

        actual = format_search(positive_terms={'test': 'value'})
        self.assertEqual(expected, actual)

    def test_should_format_multi_term_queries(self):
        expected = {
            'bool': {
                'must': [
                    {
                        'term': {
                            'test': 'value'
                        }
                    },
                    {
                        'term': {
                            'value': 'test'
                        }
                    }
                ]
            }
        }

        actual = format_search(positive_terms={
            'test': 'value',
            'value': 'test'
        })
        self.assertEqual(expected, actual)


class WhenConnectingToLiveES(unittest.TestCase):

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
    def test_elasticsearch_adapter(self):
        self.handler.put('test', {'name': 'test_1', 'value': 1})
        self.handler.put('test', {'name': 'test_2', 'value': 2})
        self.handler.put('test', {'name': 'test_2', 'value': 3})
        self.handler.put('test', {'name': 'test_2', 'value': 4})
        self.handler.put('test', {'name': 'test_2', 'value': 5})
        self.handler.put('test', {'name': 'test_2', 'value': 6})

        test_obj = self.handler.find_one('test', {'name': 'test_1'})
        self.assertEqual(1, test_obj['value'])

        obj_id = test_obj._meta.id
        test_obj['value'] = 10
        self.handler.update('test', test_obj, obj_id)

        test_obj = self.handler.find_one('test', {'name': 'test_1'})
        self.assertEqual(10, test_obj['value'])
        self.assertEqual(obj_id, test_obj._meta.id)

        self.handler.delete('test', {'name': 'test_1'})
        test_obj = self.handler.find_one('test', {'name': 'test_1'})
        self.assertFalse(test_obj)

        test_objs = self.handler.find('test', {'name': 'test_2'})
        self.assertEqual(5, test_objs.count())

        self.handler.delete('test', {'name': 'test_2'})
        test_objs = self.handler.find('test', {'name': 'test_2'})
        self.assertEqual(0, test_objs.count())


if __name__ == '__main__':
    unittest.main()
