from datetime import datetime
import re

"""
A parser for the syslog rfc5424
"""


class ParserError(Exception):
    """
        Simple exception class for the parser
    """
    def __init__(self, msg):
        super(ParserError, self).__init__()
        self.msg = msg


class TailToken(object):
    """
        Tail tokens are used to describe the unique grammar components of
        structured data.
    """
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
        return 'Token(Tokens.{0}, {1},'\
            ' {2}, {3}, {4})'.format(self.type,
                                     repr(self.value),
                                     repr(self.source))

    def matches(self, type):
        return self.type is type

    def error(self, msg):
        return ParserError(msg)


class TailTokenizer(object):

    TOKEN_RE = re.compile('''
                          \s*
                          (?:(\])|\[(\w+)
                          |([^"][^=]+)=
                          |"([^\\"]*(?:\\.[^\\"]*)*)"
                          |(.*))''', re.X)

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


class MessageTailParser(object):

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
                raise token.error('Expected structured data param '
                                  'name. Got: {0}'.format(token))

            name = token.value

            token = self.tokenizer.next_token()

            if not token.matches(TailToken.SD_PARAM_VALUE):
                raise token.error('Expected structured data param '
                                  'value. Got: {0}'.format(token))

            structured_data[name] = token.value

        token = self.tokenizer.next_token()

        if not token.matches(TailToken.SD_END):
            raise token.error('Expected structured data closing '
                              'token. Got: {0}'.format(token))

        return structured_data


class SyslogMessage(object):

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
        super(StructuredData, self).__init__()
        self.name = name

    def __repr__(self):
        return 'StructuredData({0}, {1})'.format(self.name, dict(self))


class RFC5424MessageParser(object):

    PRIORITY = 1
    VERSION = 2
    EMPTY_DATETIME = 3
    YEAR = 4
    MONTH = 5
    DAY = 6
    HOURS = 7
    MINUTES = 8
    SECONDS = 9
    FRACTIONAL_SECONDS = 10
    EMPTY_TIMEZONE = 11
    TZ_OFFSET_SIGN = 12
    TZ_OFFSET_HOURS = 13
    TZ_OFFSET_MINUTES = 14
    HOSTNAME = 15
    APPLICATION_NAME = 16
    PROCESS_ID = 17
    MESSAGE_ID = 18
    MESSAGE_TAIL = 19

    HEAD_REGEX = re.compile('''
                            <(\d{1,3})>(\d)\s+
                            (?:(-)|(\d+)-(\d+)-(\d+)
                            T
                            (\d+):(\d+):(\d+)(.\d+)
                            (?:(Z)|([+-])(\d+):(\d+)))\s+
                            (-|[^\s\[]+)\s+
                            (-|[^\s\[]+)\s+
                            (-|[^\s\[]+)\s+
                            (-|[^\s\[]+)\s+
                            (?:-\s+)?(.+)
                            ''', re.X)

    def parse(self, data):
        match = self.HEAD_REGEX.match(data)

        if not match:
            raise ParserError('String is not a syslog message')

        groupCount = len(match.groups())

        if groupCount != 19:
            raise ParserError('String is probably not a syslog message. '
                              'Found {0}'.format(groupCount))

        message = SyslogMessage()

        message.priority = match.group(self.PRIORITY)
        message.version = match.group(self.VERSION)

        if not match.group(self.EMPTY_DATETIME):
            message.timestamp = self.parse_datetime(match)
        else:
            message.timestamp = datetime.now()

        message.hostname = match.group(self.HOSTNAME)
        message.application = match.group(self.APPLICATION_NAME)
        message.process_id = match.group(self.PROCESS_ID)
        message.message_id = match.group(self.MESSAGE_ID)

        MessageTailParser(match.group(self.MESSAGE_TAIL)).parse(message)

        return message

    def parse_datetime(self, match):
        year = int(match.group(self.YEAR))
        month = int(match.group(self.MONTH))
        day = int(match.group(self.DAY))
        hours = int(match.group(self.HOURS))
        minutes = int(match.group(self.MINUTES))
        seconds = int(match.group(self.SECONDS))

        fractional_seconds = float(match.group(self.FRACTIONAL_SECONDS))
        microseconds = int(1000000 * fractional_seconds)

        if not match.group(self.EMPTY_TIMEZONE):
            # Timezone offset specified
            sign = match.group(self.TZ_OFFSET_SIGN) == '-' and -1 or 1
            hours = hours + sign * int(match.group(self.TZ_OFFSET_HOURS))
            minutes = minutes + sign * int(match.group(self.TZ_OFFSET_HOURS))

        return datetime(year, month, day, hours, minutes,
                        seconds, microseconds)


PARSER = RFC5424MessageParser()


def parse_rfc5424(self, msg):
    return PARSER.parse(msg)
