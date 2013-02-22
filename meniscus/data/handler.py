from oslo.config import cfg
from meniscus.config import get_config

# Handler configuration options
datasource_group = cfg.OptGroup(name='datasource', title='Datasource Configuration Options')
get_config().register_group(datasource_group)

HANDLER_OPTIONS = [
   cfg.StrOpt('handler_name',
               default='memory',
               help="""Sets the name of the handler to load for
                       datasource interactions. e.g. mongodb
                    """
               ),
   cfg.BoolOpt('verbose',
               default=False,
               help="""Sets whether or not the datasource handlers
                       should be verbose in their logging output.
                    """
               )
]

get_config().register_opts(HANDLER_OPTIONS, group=datasource_group)

# Connection status values
STATUS_NEW = 'NEW'
STATUS_CONNECTED = 'CONNTECTED'
STATUS_CLOSED = 'CLOSED'


class DatabaseHandlerError(Exception):

    def __init__(self, msg):
        self.msg = msg


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

    def find(self, object_name, query_filter=dict()):
        raise NotImplementedError

    def find_one(self, object_name, query_filter=dict()):
        raise NotImplementedError

    def put(self, object_name, document=dict()):
        raise NotImplementedError

    def delete(self, object_name, query_filter=dict()):
        raise NotImplementedError


# Handler registration
_DATASOURCE_HANDLERS = DatasourceHandlerManager()

def datasource_handler(conf):
    handler_def = _DATASOURCE_HANDLERS.get(conf.datasource.handler_name)
    return handler_def(conf)


def register_handler(handler_name, handler_def):
    _DATASOURCE_HANDLERS.register(handler_name, handler_def)
