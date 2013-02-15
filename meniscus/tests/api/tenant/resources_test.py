from datetime import datetime
from meniscus.api.tenant.resources import _format_event_producer 

import unittest

def suite():
    suite = unittest.TestSuite()
    suite-addTest(WhenFormattingResponses)

    return suite

class WhenFormattingResponses(unittest.TestCase):

    def test_format_event_producers(self):
        event_producer = { 'name' : 'Formatted Apache Log',
                           'pattern': 'apache_cee',
                           'should_never' : 'see_mee'}

        formatted_event_producer = _format_event_producer(
            event_producer)

        self.assertEqual(
            formatted_event_producer['name'], 'Formatted Apache Log')

        self.assertEqual(
            formatted_event_producer['pattern'], 'apache_cee')

        self.assertFalse('should_never' in formatted_event_producer)
           
            
