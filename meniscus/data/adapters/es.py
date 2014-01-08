import uuid
import elasticsearch

from meniscus.data.datastore.handler import (
    DatabaseHandlerError, DatasourceHandler,
    STATUS_CONNECTED, STATUS_CLOSED, STATUS_NEW)


class NamedDatasourceHandler(DatasourceHandler):

    def __init__(self, conf):
        """
        Initialize a data handler for elasticsearch
        from settings in the meniscus config.
        es_servers: a list[] of hostname:port of elasticsearch servers
        bulk_size: hom may records are held before performing a bulk flush
        bulk: enable bulk indexing if bulk_size > 0
        ttl: the default length of time a document should live when indexed
        status: the status of the current es connection
        """
        self.es_servers = [{
            "host": server.split(":")[0],
            "port": server.split(":")[1]} for server in conf.servers]

        if conf.bulk_size < 1:
            raise elasticsearch.ElasticsearchException(
                "bulk size must be at least 1, bulk size given is {0}".format(
                    conf.bulk_size)
            )
        self.bulk_size = conf.bulk_size

        self.ttl = conf.ttl
        self.status = STATUS_NEW

    def _check_connection(self):
        """
        Check that a pyES connection has been created,
        if not, raise an exception
        """
        if self.status != STATUS_CONNECTED:
            raise DatabaseHandlerError('Database not connected.')

    def connect(self):
        """
        Create a connection to elasticsearch.  if a bulk size has been set
        the connection will be configured for bulk indexing.
        """
        bulk_size = None
        if self.bulk_size > 0:
            bulk_size = self.bulk_size

        self.connection = elasticsearch.Elasticsearch(hosts=self.es_servers)
        self.status = STATUS_CONNECTED

    def close(self):
        """
        Close the connection to elasticsearch
        """
        self.connection = None
        self.status = STATUS_CLOSED

    def create_index(self, index, mapping=None):
        """
        Creates a new index on the elasticsearch cluster.
        :param index: the name of the index to create
        :param default_mapping: Whether or not to apply the default
        mapping to the index
        """

        self.connection.indices.create(index=index, body=mapping)

    def put_mapping(self, index, doc_type, mapping):
        """
        Create a mapping for a doc_type on a specified index
        """
        self.connection.indices.put_mapping(
            index=index, doc_type=doc_type, body=mapping)
