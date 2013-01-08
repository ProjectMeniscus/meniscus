from datetime import datetime
from enum import Enum

import re

class SDToken:
   SD_END = 1
   SD_NAME = 2
   SD_PARAM_NAME = 3
   SD_PARAM_VALUE = 4
   MSG = 5

   def __init__(self, type, value, source, start, end):
      self.type = type
      self.value = value
      self.source = source
      self.start = start
      self.end = end

   def __repr__(self):
      return 'Token(Tokens.{0}, {1}, {2}, {3}, {4})'.format(self.type, repr(self.value), repr(self.source), self.start, self.end)

   def matches(self, type):
      return self.type is type
      
   def error(self, msg):
      return ParserError(msg)

class SDTokenizer:
   TOKEN_RE = re.compile('\s*(?:(\])|\[(\w+)|([^"][^=]+)=|"([^\\"]*(?:\\.[^\\"]*)*)"|(.*))', re.X)

   def __init__(self, source):
      self.iter = self.tokenize(source)

   def __iter__(self):
      return self

   def next(self):
      return next(self.iter)

   def tokenize(self, source):
      for match in self.TOKEN_RE.finditer(source):
         if match.group(SDToken.SD_END):
            yield SDToken(SDToken.SD_END, match.group(SDToken.SD_END), source, match.start(SDToken.SD_END), match.end(SDToken.SD_END))
         elif match.group(SDToken.SD_NAME):
            yield SDToken(SDToken.SD_NAME, match.group(SDToken.SD_NAME), source, match.start(SDToken.SD_NAME), match.end(SDToken.SD_NAME))
         elif match.group(SDToken.SD_PARAM_NAME):
            yield SDToken(SDToken.SD_PARAM_NAME, match.group(SDToken.SD_PARAM_NAME), source, match.start(SDToken.SD_PARAM_NAME), match.end(SDToken.SD_PARAM_NAME))
         elif match.group(SDToken.SD_PARAM_VALUE):
            yield SDToken(SDToken.SD_PARAM_VALUE, match.group(SDToken.SD_PARAM_VALUE), source, match.start(SDToken.SD_PARAM_VALUE), match.end(SDToken.SD_PARAM_VALUE))
         else:
            yield SDToken(SDToken.MSG, match.group(SDToken.MSG), source, match.start(SDToken.SD_PARAM_VALUE), match.end(SDToken.SD_PARAM_VALUE))

class MessageTailParser:
   def __init__(self, source):
      self.tokenizer = SDTokenizer(source)
      self.lookahead = None
      self.next_token()

   def next_token(self):
      token = self.lookahead
      self.lookahead = next(self.tokenizer)
     
      return token

   def parse(self, syslog_message):
      token = self.next_token()
      
      if token.matches(SDToken.SD_NAME):
         sd = self.parse_structured_data(token.value)
         syslog_message.structured_data.append(sd)
         token = self.next_token()
         
      if not token.matches(SDToken.MSG):
         raise token.error("Expected syslog message content")
         
      syslog_message.message = token.value

      return syslog_message

   def parse_structured_data(self, name):
      structured_data = StructuredData(name)
      
      while not self.lookahead.matches(SDToken.SD_END):
         token = self.next_token()
         
         if not token.matches(SDToken.SD_PARAM_NAME):
            raise token.error("Expected structured data parameter name")

         name = token.value

         token = self.next_token()

         if not token.matches(SDToken.SD_PARAM_VALUE):
            raise token.error("Expected structured data parameter value")

         structured_data.parameters[name] = token.value

      token = self.next_token()

      if not token.matches(SDToken.SD_END):
         raise token.error("Expected structured data closing token")

      return structured_data
		 
     
class SyslogMessage:
   def __init__(self):
      self.structured_data = []
      self.priority = None
      self.timestamp = None
      self.hostname = None
      self.application = None
      self.process_id = None
      self.message = None
      self.message_id = None
      self.version = None

   def __repr__(self):
      return 'SyslogMessage({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8})'.format(
         self.priority,
         repr(self.timestamp),
         self.hostname,
         self.application,
         self.process_id,
         self.message,
         self.message_id,
         self.version,
         repr(self.structured_data))
      
class StructuredData:
   def __init__(self, name):
      self.parameters = {}
      self.name = name

   def __repr__(self):
      return 'StructuredData({0}, {1})'.format(self.name, repr(self.parameters))

MESSAGE_HEAD_PATTERN = re.compile('<(\d{1,3})>(\d)\s+(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d.\d+-\d\d:\d\d)\s+(-|[^\s\[]+)\s+(-|[^\s\[]+)\s+(-|[^\s\[]+)\s+(-|[^\s\[]+)\s+(.+)')

class ParserError:
   def __init__(self, msg):
      self.msg = msg

class MessageParser:
   def parse(self, data):
      match = MESSAGE_HEAD_PATTERN.match(data)

      if not match:
         raise ParserError('String is not a syslog message')

      groupCount = len(match.groups())

      if groupCount is not 8:
         raise ParserError('String is probably not a syslog message. Found {0}'.format(groupCount))

      message = SyslogMessage()

      message.priority = match.group(1)
      message.version = match.group(2)
      message.timestamp = match.group(3)
      message.hostname = match.group(4)
      message.application = match.group(5)
      message.process_id = match.group(6)
      message.message_id = match.group(7)
      message.content = match.group(8)

      return message

parser = MessageParser()


sd = MessageTailParser('[origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start').parse(SyslogMessage())

print sd

try:
   message = parser.parse('<46>1 2012-12-11T15:48:23.217459-06:00 tohru rsyslogd 6611 12512  [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] [origin software="rsyslogd" swVersion="7.2.2" x-pid="12297" x-info="http://www.rsyslog.com"] start');
   print message
except ParserError as error:
   print error.msg
