import abc


class DataHandlerError(Exception):
    """
    base class to be used for data handler errors
    """
    def __init__(self, msg):
        self.msg = msg
        super(DataHandlerError, self).__init__(self.msg)


class DataHandlerBase:
    """
    Abstract Base Class for implementing data drivers
    """
    __metaclass__ = abc.ABCMeta

    STATUS_NEW = 'NEW'
    STATUS_CONNECTED = 'CONNECTED'
    STATUS_CLOSED = 'CLOSED'

    def status(self):
        return self.status

    @abc.abstractmethod
    def connect(self):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError
