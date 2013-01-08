from RFC5424 import *

import time
import unittest

HAPPY_PATH_MESSAGE = '<46>1 2012-12-11T15:48:23.217459-06:00 tohru rsyslogd 6611 12512  [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start'
PARTIAL_MESSAGE = '<46>1 2012-12-11T15:48:23.217459-06:00 - - - - - start'

HAPPY_PATH_SD = '[origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start'

class FromTextToStructuredData(unittest.TestCase):
   def testParsingStruturedData(self):
      parser = MessageTailParser(HAPPY_PATH_SD)
      message = parser.parse(SyslogMessage())

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
   def testParsingFullMessage(self):
      parser = RFC5424MessageParser()
      message = parser.parse(HAPPY_PATH_MESSAGE)

      self.assertEqual(message.version, '1')
      self.assertEqual(message.priority, '46')
      self.assertEqual(message.application, 'rsyslogd')
      self.assertEqual(message.process_id, '6611')
      self.assertEqual(message.timestamp, '2012-12-11T15:48:23.217459-06:00')
      self.assertEqual(message.message_id, '12512')
      self.assertEqual(message.message, 'start')

      self.assertEqual(len(message.structured_data), 2)

   def testParsingPartialMessage(self):
      parser = RFC5424MessageParser()
      message = parser.parse(PARTIAL_MESSAGE)

      self.assertEqual(message.version, '1')
      self.assertEqual(message.priority, '46')
      self.assertEqual(message.application, '-')
      self.assertEqual(message.process_id, '-')
      self.assertEqual(message.timestamp, '2012-12-11T15:48:23.217459-06:00')
      self.assertEqual(message.message_id, '-')
      self.assertEqual(message.message, 'start')
      
      self.assertEqual(len(message.structured_data), 0)

class PerformanceTest(unittest.TestCase):
   def testPerformance(self):
      start = time.time()
      iterations = 0

      parser = RFC5424MessageParser()
         
      while iterations < 100000:
         parser.parse(HAPPY_PATH_MESSAGE)
         iterations += 1

      secondsTaken = time.time() - start
      passesPerSecond = iterations / secondsTaken
      
      print 'Performed {0} parsing passes. Time taken: {1} seconds. Averge number of operations per second: {2}'.format(iterations, secondsTaken, passesPerSecond)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
