from oslo.config import cfg
from meniscus import config
from meniscus.data.datastore import handler
from meniscus import env
from meniscus.ext.plugin import import_module


_LOG = env.get_logger(__name__)

COORDINATOR_DB = 'coordinator_db'
DEFAULT_SINK = 'default_sink'
SHORT_TERM_STORE = 'short_term_store'


#Register data handler options for coordinator db
coordinator_db_group = cfg.OptGroup(
    name=COORDINATOR_DB, title='Coordinator DB Configuration Options')
config.get_config().register_group(coordinator_db_group)

coordinator_db_options = [
    cfg.StrOpt('adapter_name',
               default='mongodb',
               help="""Sets the name of the handler to load for
                       datasource interactions. e.g. mongodb
                    """
               ),
    cfg.ListOpt('servers',
                default='localhost:27017',
                help="""hostanme:port for db servers
                    """
                ),
    cfg.StrOpt('database',
               default='test',
               help="""database name
                    """
               ),
    cfg.StrOpt('index',
               default=None,
               help="""datasource index
                    """
               ),
    cfg.StrOpt('username',
               default='test',
               help="""db username
                    """
               ),
    cfg.StrOpt('password',
               default='test',
               help="""db password
                    """
               )
]

config.get_config().register_opts(
    coordinator_db_options, group=coordinator_db_group)


#Register data handler options for short term store
short_term_store_group = cfg.OptGroup(
    name=SHORT_TERM_STORE,
    title='Short Term Store Configuration Options')

config.get_config().register_group(short_term_store_group)

short_term_store_options = [
    cfg.StrOpt('adapter_name',
               default='mongodb',
               help="""Sets the name of the handler to load for
                       datasource interactions. e.g. mongodb
                    """
               ),
    cfg.ListOpt('servers',
                default='localhost:27017',
                help="""hostanme:port for db servers
                    """
                ),
    cfg.StrOpt('database',
               default='test',
               help="""database name
                    """
               ),
    cfg.StrOpt('index',
               default=None,
               help="""datasource index
                    """
               ),
    cfg.StrOpt('username',
               default='test',
               help="""db username
                    """
               ),
    cfg.StrOpt('password',
               default='test',
               help="""db password
                    """
               )
]

config.get_config().register_opts(
    short_term_store_options, group=short_term_store_group)


#Register data handler options for default sink
default_sink_group = cfg.OptGroup(
    name=DEFAULT_SINK,
    title='Deafault_Sink Configuration Options')

config.get_config().register_group(default_sink_group)

default_sink_options = [
    cfg.StrOpt('adapter_name',
               default='elasticsearch',
               help="""Sets the name of the handler to load for
                       datasource interactions. e.g. mongodb
                    """
               ),
    cfg.ListOpt('servers',
                default='localhost:9200',
                help="""hostanme:port for db servers
                    """
                ),
    cfg.IntOpt('bulk_size',
               default='0',
               help="""Amount of records to transmit in bulk
                    """
               ),
    cfg.StrOpt('database',
               default=None,
               help="""database name
                    """
               ),
    cfg.StrOpt('index',
               default='logs',
               help="""datasource index
                    """
               ),
    cfg.StrOpt('username',
               default=None,
               help="""db username
                    """
               ),
    cfg.StrOpt('password',
               default=None,
               help="""db password
                    """
               )
]

config.get_config().register_opts(
    default_sink_options, group=default_sink_group)


try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

conf = config.get_config()

# Handler registration
_DATASOURCE_HANDLERS = handler.DatasourceHandlerManager()

#create coordinator_db handler
coordinator_db_module = import_module(
    'meniscus.data.adapters.{0}'.format(conf.coordinator_db.adapter_name))
coordinator_db_handler = coordinator_db_module.NamedDatasourceHandler(
    conf.coordinator_db)
_DATASOURCE_HANDLERS.register(COORDINATOR_DB, coordinator_db_handler)


#create short_term_store handler
short_term_store_module = import_module(
    'meniscus.data.adapters.{0}'.format(conf.short_term_store.adapter_name))
short_term_store_handler = short_term_store_module.NamedDatasourceHandler(
    conf.short_term_store)
_DATASOURCE_HANDLERS.register(SHORT_TERM_STORE, short_term_store_handler)


#create default_sink handler
default_sink_module = import_module(
    'meniscus.data.adapters.{0}'.format(conf.default_sink.adapter_name))
default_sink_handler = default_sink_module.NamedDatasourceHandler(
    conf.default_sink)
_DATASOURCE_HANDLERS.register(DEFAULT_SINK, default_sink_handler)


def datasource_handler(handler_name):
    handler = _DATASOURCE_HANDLERS.get(handler_name)
    handler.connect()
    return handler
