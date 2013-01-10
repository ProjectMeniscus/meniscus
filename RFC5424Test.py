from datetime import datetime
from RFC5424 import *

import unittest

HAPPY_PATH_MESSAGE = '<46>1 2012-12-11T15:48:23.217459-06:00 tohru rsyslogd 6611 12512  [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start'
PARTIAL_MESSAGE = '<46>1 - - - - - - start'

HAPPY_PATH_SD = '[origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start'

class FromTextToStructuredData(unittest.TestCase):
    
    def test_parsing_structured_data(self):
        parser = MessageTailParser(HAPPY_PATH_SD)
        
        try:
            message = parser.parse(SyslogMessage())
        except ParserError as pe:
            self.fail(pe.msg)

        for sd in message.structured_data:      
            for param in sd:
                if param == 'software':
                    self.assertEqual(sd[param], 'rsyslogd')
                elif param == 'swVersion':
                    self.assertEqual(sd[param], '7.2.2')
                elif param == 'x-pid':
                    self.assertEqual(sd[param], '12297')
                elif param == 'x-info':
                    self.assertEqual(sd[param], 'http://www.rsyslog.com')
                else:
                    self.fail('Unexpected structred data element: {0}="{1}"'.format(param, sd[param]))
        return


class FromTextToSyslogMessage(unittest.TestCase):
    
    def test_parsing_full_message(self):
        parser = RFC5424MessageParser()
        
        try:
            message = parser.parse(HAPPY_PATH_MESSAGE)
        except ParserError as pe:
            self.fail(pe.msg)

        self.assertEqual(message.version, '1')
        self.assertEqual(message.priority, '46')
        self.assertEqual(message.application, 'rsyslogd')
        self.assertEqual(message.process_id, '6611')
        self.assertEqual(message.timestamp, datetime(2012, 12, 11, 9, 42, 23, 217459))
        self.assertEqual(message.message_id, '12512')
        self.assertEqual(message.message, 'start')

        self.assertEqual(len(message.structured_data), 2)

    def test_parsing_partial_message(self):
        parser = RFC5424MessageParser()
        message = parser.parse(PARTIAL_MESSAGE)

        self.assertEqual(message.version, '1')
        self.assertEqual(message.priority, '46')
        self.assertEqual(message.application, '-')
        self.assertEqual(message.process_id, '-')
        self.assertEqual(message.message_id, '-')
        self.assertEqual(message.message, 'start')
        
        self.assertEqual(len(message.structured_data), 0)
    
def main():
    unittest.main()

if __name__ == '__main__':
    main()
