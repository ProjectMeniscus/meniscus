from datetime import datetime

import re
import time


class ParserError:
    """
        Simple exception class for the parser
    """
    def __init__(self, msg):
        self.msg = msg


class TailToken:
    """
        Tail tokens are used to describe the unique grammar components of
        structured data.
    """
    _REPR_FORMAT = 'Token(Tokens.{0}, {1}, {2}, {3}, {4})'

    SD_END = 1
    SD_NAME = 2
    SD_PARAM_NAME = 3
    SD_PARAM_VALUE = 4
    MSG = 5
        
    def __init__(self, type, value, source):
        self.type = type
        self.value = value
        self.source = source

    def __repr__(self):
        return self._REPR_FORMAT.format(self.type,
                                        repr(self.value),
                                        repr(self.source))

    def matches(self, type):
        return self.type is type

    def error(self, msg):
        return ParserError(msg)


class TailTokenizer:

    TOKEN_RE = re.compile(
        '\s*(?:(\])|\[(\w+)|([^"][^=]+)=|"([^\\"]*(?:\\.[^\\"]*)*)"|(.*))',
        re.X)

    def __init__(self, source):
        self.iter = self.tokenize(source)
        self.lookahead = None
        self.next_token()

    def next_token(self):
        token = self.lookahead
        self.lookahead = next(self)
        return token

    def __iter__(self):
        return self

    def next(self):
        return next(self.iter)

    def tokenize(self, source):
        for match in self.TOKEN_RE.finditer(source):
            if match.group(TailToken.SD_END):
                yield TailToken(TailToken.SD_END,
                                match.group(TailToken.SD_END),
                                source)
            elif match.group(TailToken.SD_NAME):
                yield TailToken(TailToken.SD_NAME,
                                match.group(TailToken.SD_NAME),
                                source)
            elif match.group(TailToken.SD_PARAM_NAME):
                yield TailToken(TailToken.SD_PARAM_NAME,
                                match.group(TailToken.SD_PARAM_NAME),
                                source)
            elif match.group(TailToken.SD_PARAM_VALUE):
                yield TailToken(TailToken.SD_PARAM_VALUE,
                                match.group(TailToken.SD_PARAM_VALUE),
                                source)
            else:
                yield TailToken(TailToken.MSG,
                                match.group(TailToken.MSG),
                                source)


class MessageTailParser:

    def __init__(self, source):
        self.tokenizer = TailTokenizer(source)

    def parse(self, syslog_message):
        token = self.tokenizer.next_token()

        while token.matches(TailToken.SD_NAME):
            sd = self.parse_structured_data(token.value)
            syslog_message.structured_data.append(sd)
            token = self.tokenizer.next_token()

        if not token.matches(TailToken.MSG):
            raise token.error('Expected syslog message content. '
                              'Got: {0}'.format(token.type))

        syslog_message.message = token.value
        return syslog_message

    def parse_structured_data(self, name):
        structured_data = StructuredData(name)

        while not self.tokenizer.lookahead.matches(TailToken.SD_END):
            token = self.tokenizer.next_token()

            if not token.matches(TailToken.SD_PARAM_NAME):
                raise token.error('Expected structured data param name. '
                                  'Got: {0}'.format(token))

            name = token.value

            token = self.tokenizer.next_token()

            if not token.matches(TailToken.SD_PARAM_VALUE):
                raise token.error('Expected structured data param value. '
                                  'Got: {0}'.format(token))

            structured_data[name] = token.value

        token = self.tokenizer.next_token()

        if not token.matches(TailToken.SD_END):
            raise token.error('Expected structured data closing token. '
                              'Got: {0}'.format(token))

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
        return 'SyslogMessage({0}, {1}, {2}, {3}, {4}'\
            ', {5}, {6}, {7}, {8})'.format(self.priority,
                                           repr(self.timestamp),
                                           self.hostname,
                                           self.application,
                                           self.process_id,
                                           self.message_id,
                                           self.version,
                                           repr(self.structured_data),
                                           self.message)


class StructuredData(dict):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'StructuredData({0}, {1})'.format(self.name, dict(self))


class RFC5424MessageParser:

    HEAD_REGEX = re.compile('<(\d{1,3})>(\d)\s+'
                            '(-|\d\d\d\d-\d\d-\d\d'
                            'T'
                            '\d\d:\d\d:\d\d.\d+(?:Z|[+-]\d\d:\d\d))\s+'
                            '(-|[^\s\[]+)\s+'
                            '(-|[^\s\[]+)\s+'
                            '(-|[^\s\[]+)\s+'
                            '(-|[^\s\[]+)\s+'
                            '(?:-\s+)?(.+)')

    def parse(self, data):
        match = self.HEAD_REGEX.match(data)

        if not match:
            raise ParserError('String is not a syslog message')

        groupCount = len(match.groups())

        if groupCount != 8:
            raise ParserError('String is probably not a syslog message. '
                              'Found {0}'.format(groupCount))

        message = SyslogMessage()

        message.priority = match.group(1)
        message.version = match.group(2)
        message.timestamp = match.group(3)
        message.hostname = match.group(4)
        message.application = match.group(5)
        message.process_id = match.group(6)
        message.message_id = match.group(7)

        MessageTailParser(match.group(8)).parse(message)

        return message
    
    def parse_datetime(self, timestamp):
        parsed_datetime = None
        
        if timestamp == '-':
            parsed_datetime = datetime.now()
        elif timestamp[-1] == 'Z':
            parsed_datetime = datetime.strptime(ts,
                                                '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            parsed_datetime = datetime.strptime(ts[:-6], 
                                                '%Y-%m-%dT%H:%M:%S.%f')
            hours = int(ts[-5:-3])
            mins = int(ts[-2:])
            sign = ts[-6] == '-' and -1 or 1
            self.timestamp += timedelta(sign*(hours*3600+mins*60))
