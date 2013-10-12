import uuid

import pyes

from meniscus.data.datastore.handler import (
    DatabaseHandlerError, DatasourceHandler,
    STATUS_CONNECTED, STATUS_CLOSED, STATUS_NEW)


def format_terms(terms):
    """
    Formats a dictionary into a list of elasticsearch terms
    :param terms: a dictionary of fields/values
    :return: a list[] for dictionaries containing es terms
    """
    formatted_terms = list()
    for term_key in terms:
        formatted_terms.append({
            'term': {
                term_key: terms[term_key]
            }
        })
    return formatted_terms


def format_search(positive_terms=None, negative_terms=None):
    """
    Formats a search query with positive and negative terms
    :param positive_terms: a list formatted terms that must
    match in the documents being searched
    :param negative_terms: a list formatted terms that must
    not match in the documents being searched
    :return: a dictionary representing the search criteria for an es query
    """
    query = dict()
    if positive_terms:
        query['must'] = format_terms(positive_terms)
    if negative_terms:
        query['must_not'] = format_terms(negative_terms)
    return {'bool': query}


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
        self.es_servers = conf.servers
        self.bulk_size = conf.bulk_size
        self.bulk = self.bulk_size is not None
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
        self.connection = pyes.ES(self.es_servers, bulk_size=bulk_size)
        self.status = STATUS_CONNECTED

    def close(self):
        """
        Close the connection to elasticsearcgh
        """
        self.connection = None
        self.status = STATUS_CLOSED

    def put(self, object_name, document=None, index=None, ttl=None):
        """
        From the pyES documents

        index(doc, index, doc_type, id=None, parent=None,
              force_insert=False, op_type=None, bulk=False,
              version=None, querystring_args=None, ttl=None)

        Index a typed JSON document into a specific index and make it
        searchable.

        ^
        In this case the doctype is the object name. I've changed code in
        a layer higher to provide an object name based on the following
        format: object_name='tenant/{tenant_id}'
        """
        if document is None:
            document = dict()
        if ttl is None:
            ttl = self.ttl
        self._check_connection()
        _id = str(uuid.uuid4())

        self.connection.index(
            document, index, object_name, _id, bulk=self.bulk, ttl=ttl)
        return _id

    def create_index(self, index):
        """
        Creates a new index on the elasticsearch cluster.
        If the index is already created, errors will be ignored.
        """
        self.connection.indices.create_index_if_missing(self, index)

    def put_ttl_mapping(self, doc_type, index):
        """
        Create a mapping for a doc_type on a specified index that
        enables time_to_live functionality.
        """
        indices = [index]
        mapping = {"_ttl": {"enabled": True}}

        self.connection.indices.put_mapping(
            self, doc_type=doc_type, mapping=mapping, indices=indices)
