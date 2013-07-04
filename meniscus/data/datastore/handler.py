
# Connection status values
STATUS_NEW = 'NEW'
STATUS_CONNECTED = 'CONNECTED'
STATUS_CLOSED = 'CLOSED'


class DatabaseHandlerError(Exception):

    def __init__(self, msg):
        self.msg = msg
        super(DatabaseHandlerError, self).__init__(self.msg)


class DatasourceHandlerManager():

    def __init__(self):
        self.registered_handlers = dict()

    def register(self, handler_name, handler_def):
        self.registered_handlers[handler_name] = handler_def

    def get(self, handler_name):
        return self.registered_handlers[handler_name]


class DatasourceHandler():

    datasource_status = STATUS_NEW

    def status(self):
        return self.datasource_status

    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def create_sequence(self, sequence_name):
        raise NotImplementedError

    def delete_sequence(self, sequence_name):
        raise NotImplementedError

    def next_sequence(self, sequence_name):
        raise NotImplementedError

    def find(self, object_name, query_filter=None):
        if query_filter is None:
            query_filter = dict()
        raise NotImplementedError

    def find_one(self, object_name, query_filter=None):
        if query_filter is None:
            query_filter = dict()
        raise NotImplementedError

    def put(self, object_name, document=None):
        if document is None:
            document = dict()
        raise NotImplementedError

    def update(self, object_name, document=None, id=None):
        if document is None:
            document = dict()
        raise NotImplementedError

    def delete(self, object_name, query_filter=None, limit_one=False):
        if query_filter is None:
            query_filter = dict()
        raise NotImplementedError
