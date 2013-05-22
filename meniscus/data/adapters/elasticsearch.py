import pyes
import pprint
import uuid

from oslo.config import cfg
from meniscus.config import get_config
from meniscus.data.handler import (
    DatabaseHandlerError, DatasourceHandler, register_handler,
    STATUS_CONNECTED, STATUS_CLOSED
)


def format_terms(terms):
    formatted_terms = list()
    for term_key in terms:
        formatted_terms.append({
            'term': {
                term_key: terms[term_key]
            }
        })
    return formatted_terms


def format_search(positive_terms=None, negative_terms=None):
    query = dict()
    if positive_terms:
        query['must'] = format_terms(positive_terms)
    if negative_terms:
        query['must_not'] = format_terms(negative_terms)
    return {'bool': query}


# Elasticsearch configuration options
_es_group = cfg.OptGroup(name='elasticsearch', title=' ElasticSearch Options')
get_config().register_group(_es_group)

_ES_OPTIONS = [
    cfg.ListOpt('es_servers',
                default=['localhost:27017'],
                help="""ES servers to connect to."""
                ),
    cfg.StrOpt('index',
               default='test',
               help="""ES index  to use."""
               )
]

get_config().register_opts(_ES_OPTIONS, group=_es_group)


class PyesDatasourceHandler(DatasourceHandler):

    def __init__(self, conf):
        self.es_servers = conf.elasticsearch.es_servers
        self.index = conf.elasticsearch.index
        self.username = None
        self.password = None

    def _check_connection(self):
        if self.status != STATUS_CONNECTED:
            raise DatabaseHandlerError('Database not connected.')
        self.connection.flush()

    def connect(self):
        self.connection = pyes.ES(self.es_servers)

        if self.username and self.password:
            #Todo:{JHopper)Add Authentication
            pass

        self.status = STATUS_CONNECTED

    def close(self):
        self.connection = None
        self.status = STATUS_CLOSED

    def find(self, object_name, query_filter=None):
        if query_filter is None:
            query_filter = dict()
        self._check_connection()
        return self.connection.search(
            format_search(query_filter), [self.index], [object_name])

    def find_one(self, object_name, query_filter=None):
        if query_filter is None:
            query_filter = dict()
        self._check_connection()
        query = format_search(query_filter)
        cursor = self.connection.search(
            query, [self.index], [object_name])
        return cursor[0] if len(cursor) > 0 else None

    def put(self, object_name, document=None):
        if document is None:
            document = dict()
        self._check_connection()
        _id = uuid.uuid4()
        self.connection.index(document, self.index, object_name, _id)
        return _id

    def update(self, object_name, document=None, id=None):
        if document is None:
            document = dict()
        self._check_connection()

        if not id:
            raise DatabaseHandlerError(
                'An ID must be specified. Please set the funciton arg '
                '"doc_id" when calling this function.')

        self.connection.update(
            document, self.index, object_name, id)

    def delete(self, object_name, query_filter=dict(), limit_one=False):
        self.connection.delete_by_query(
            [self.index], [object_name], format_search(query_filter))


def register_elasticsaerch():
    """Registers this handler and makes it available for use"""
    register_handler('elasticsearch', PyesDatasourceHandler)
