import uuid

import pyes
from pyes.connection_http import update_connection_pool
from oslo.config import cfg

from meniscus.config import get_config
from meniscus.data.datastore.handler import (
    DatabaseHandlerError, DatasourceHandler, STATUS_CONNECTED, STATUS_CLOSED)


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


class NamedDatasourceHandler(DatasourceHandler):

    def __init__(self, conf):
        self.es_servers = conf.servers
        self.index = conf.index
        self.username = conf.username
        self.password = conf.password
        self.bulk_size = conf.bulk_size

    def _check_connection(self):
        if self.status != STATUS_CONNECTED:
            raise DatabaseHandlerError('Database not connected.')
        self.connection.flush()

    def connect(self):
        update_connection_pool(125)
        bulk_size = None
        if self.bulk_size > 0:
            bulk_size = self.bulk_size
        self.connection = pyes.ES(self.es_servers, bulk_size=bulk_size)

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

    def delete(self, object_name, query_filter=None, limit_one=False):
        if query_filter is None:
            query_filter = dict()

        self.connection.delete_by_query(
            [self.index], [object_name], format_search(query_filter))
