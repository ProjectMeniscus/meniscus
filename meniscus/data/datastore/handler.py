
# Connection status values
STATUS_NEW = 'NEW'
STATUS_CONNECTED = 'CONNECTED'
STATUS_CLOSED = 'CLOSED'


class DatabaseHandlerError(Exception):

    def __init__(self, msg):
        self.msg = msg
        super(DatabaseHandlerError, self).__init__(self.msg)


class DatasourceHandlerManager(object):

    def __init__(self):
        self.registered_handlers = dict()

    def register(self, handler_name, handler_def):
        self.registered_handlers[handler_name] = handler_def

    def get(self, handler_name):
        return self.registered_handlers[handler_name]


class DatasourceHandler(object):

    datasource_status = STATUS_NEW

    def status(self):
        return self.status

    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
