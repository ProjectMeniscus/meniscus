from RFC5424 import *

import time
import cProfile

HAPPY_PATH_MESSAGE = '<46>1 2012-12-11T15:48:23.217459-06:00 tohru rsyslogd 6611 12512  [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start'

class PerformanceTest:
   def test_performance(self):
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
    PerformanceTest().test_performance()

if __name__ == '__main__':
    #cProfile.run('main()')
	main()
