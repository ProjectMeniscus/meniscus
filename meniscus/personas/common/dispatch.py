from portal.output.json import ObjectJsonWriter


class DispatchException(Exception):
    """Raised when dispatch is unable to send message."""
    pass


class Dispatch(object):
    def __init__(self):
        self.writer = ObjectJsonWriter()

    def dispatch_message(self, message, sock):
        headers = dict()
        try:
            self.writer.write(headers, message, sock)
        except Exception as ex:
            #TODO(dmend) Log this
            raise DispatchException()
