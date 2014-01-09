from elasticsearch import Elasticsearch, ElasticsearchException
from oslo.config import cfg
from meniscus.data.handlers import base
from meniscus import config
from meniscus import env


_LOG = env.get_logger(__name__)


#Register options for Elasticsearch
elasticsearch_group = cfg.OptGroup(
    name="elasticsearch",
    title='Elasticsearch Configuration Options')

config.get_config().register_group(elasticsearch_group)

elasticsearch_options = [
    cfg.ListOpt('servers',
                default=['localhost:9200'],
                help="""hostname:port for db servers
                    """
                ),
    cfg.IntOpt('bulk_size',
               default=100,
               help="""Amount of records to transmit in bulk
                    """
               ),
    cfg.StrOpt('ttl',
               default="30d",
               help="""default time to live for documents
                    inserted into the default store
                    """
               )
]

config.get_config().register_opts(
    elasticsearch_options, group=elasticsearch_group)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)


class ElasticsearchHandlerError(base.DataHandlerError):
    pass


class ElasticsearchHandler(base.DataHandlerBase):

    def __init__(self, conf):
        """
        Initialize a data handler for elasticsearch
        from settings in the meniscus config.
        es_servers: a list[] of {"host": "hostname", "port": "port"} for
        elasticsearch servers
        bulk_size: hom may records are held before performing a bulk flush
        ttl: the default length of time a document should live when indexed
        status: the status of the current es connection
        """
        self.es_servers = [{
            "host": server.split(":")[0],
            "port": server.split(":")[1]
            } for server in conf.servers
        ]

        if conf.bulk_size < 1:
            raise ElasticsearchHandlerError(
                "bulk size must be at least 1, bulk size given is {0}".format(
                    conf.bulk_size)
            )
        self.bulk_size = conf.bulk_size

        self.ttl = conf.ttl
        self.status = ElasticsearchHandler.STATUS_NEW

    def _check_connection(self):
        """
        Check that a pyES connection has been created,
        if not, raise an exception
        """
        if self.status != ElasticsearchHandler.STATUS_CONNECTED:
            raise ElasticsearchHandlerError('Database not connected.')

    def connect(self):
        """
        Create a connection to elasticsearch.  if a bulk size has been set
        the connection will be configured for bulk indexing.
        """
        self.connection = Elasticsearch(hosts=self.es_servers)
        self.status = ElasticsearchHandler.STATUS_CONNECTED

    def close(self):
        """
        Close the connection to elasticsearch
        """
        self.connection = None
        self.status = ElasticsearchHandler.STATUS_CLOSED

    def create_index(self, index, mapping=None):
        """
        Creates a new index on the elasticsearch cluster.
        :param index: the name of the index to create
        :param default_mapping: Whether or not to apply the default
        mapping to the index
        """
        self._check_connection()
        self.connection.indices.create(index=index, body=mapping)

    def put_mapping(self, index, doc_type, mapping):
        """
        Create a mapping for a doc_type on a specified index
        """
        self._check_connection()
        self.connection.indices.put_mapping(
            index=index, doc_type=doc_type, body=mapping)


def get_handler():
    """
    factory method that returns an instance of ElasticsearchHandler
    """
    conf = config.get_config()
    es_handler = ElasticsearchHandler(conf.elasticsearch)
    es_handler.connect()
    return es_handler
