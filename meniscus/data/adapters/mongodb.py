from pymongo import MongoClient

from oslo.config import cfg
from meniscus.config import get_config
from meniscus.data.datastore.handler import (
    DatabaseHandlerError, DatasourceHandler,
    STATUS_CONNECTED, STATUS_CLOSED
)


# MongoDB configuration options
_mongodb_group = cfg.OptGroup(name='mongodb', title='MongoDB Options')
get_config().register_group(_mongodb_group)

_MONGODB_OPTIONS = [
    cfg.ListOpt('mongo_servers',
                default=['localhost:27017'],
                help="""MongoDB servers to connect to."""
                ),
    cfg.StrOpt('database',
               default='test',
               help="""MongoDB database to use."""
               ),
    cfg.StrOpt('username',
               default='',
               help="""MongoDB username to use when authenticating.
                       If this value is left unset, then authentication
                       against the MongoDB will not be utilized.""",
               secret=True
               ),
    cfg.StrOpt('password',
               default='',
               help="""MongoDB password to use when authenticating.
                       If this value is left unset, then authentication
                       against the MongoDB will not be utilized.""",
               secret=True
               )
]

get_config().register_opts(_MONGODB_OPTIONS, group=_mongodb_group)


## TODO: (JHop) Document this damn thing --> pymongo.errors.OperationFailure.
class NamedDatasourceHandler(DatasourceHandler):

    def __init__(self, conf):
        self.mongo_servers = conf.servers
        self.database_name = conf.database
        self.username = conf.username
        self.password = conf.password

    def _check_connection(self):
        if self.status != STATUS_CONNECTED:
            raise DatabaseHandlerError('Database not connected.')

    def connect(self):
        self.connection = MongoClient(self.mongo_servers, slave_okay=True)
        self.database = self.connection[self.database_name]

        if self.username and self.password:
            self.database.authenticate(self.username, self.password)

        self.status = STATUS_CONNECTED

    def close(self):
        self.connection.close()
        self.status = STATUS_CLOSED

    def create_sequence(self, sequence_name):
        self._check_connection()
        sequence = self.find_one('counters', {'name': sequence_name})

        if not sequence:
            self.put('counters', {'name': sequence_name, 'seq': 1})

    def delete_sequence(self, sequence_name):
        self._check_connection()
        self.delete('counters', {'name': sequence_name})

    def next_sequence_value(self, sequence_name):
        self._check_connection()
        return self.database['counters'].find_and_modify(
            {'name': sequence_name}, {'$inc': {'seq': 1}})['seq']

    def find(self, object_name, query_filter=None):
        if query_filter is None:
            query_filter = dict()
        self._check_connection()
        return self.database[object_name].find(query_filter)

    def find_one(self, object_name, query_filter=None):
        if query_filter is None:
            query_filter = dict()
        self._check_connection()
        return self.database[object_name].find_one(query_filter)

    def put(self, object_name, document=None):
        if document is None:
            document = dict()
        self._check_connection()
        self.database[object_name].insert(document)

    def update(self, object_name, document=None):
        if document is None:
            document = dict()
        self._check_connection()

        if '_id' not in document:
            raise DatabaseHandlerError(
                'The document must have a field "_id" in its root in '
                'order to perform an update operation.')

        self.database[object_name].save(document)

    def set_field(self, object_name, field, value, query_filter=None):
        '''
        Updates the given field with a new value for all documents that match
        the query filter

        :param object_name: represents the mongo collection
        :param field: the field to update (or create)
        nested field are accessed with a '.' { 'name.middle': 'middlename' }
        :param value: the new value for the field
        :param query_filter: represents field/value to query by

        '''
        if query_filter is None:
            query_filter = dict()
        self._check_connection()

        set_statement = {"$set": {field: value}}

        self.database[object_name].update(
            query_filter, set_statement, multi=True)

    def delete(self, object_name, query_filter=None, limit_one=False):
        if query_filter is None:
            query_filter = dict()
        self.database[object_name].remove(query_filter, True)
