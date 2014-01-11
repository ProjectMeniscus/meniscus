from pymongo import MongoClient, errors
from oslo.config import cfg
from meniscus.data.handlers import base
from meniscus import config
from meniscus import env


_LOG = env.get_logger(__name__)

#Register options for MongoDB
mongodb_group = cfg.OptGroup(
    name="mongodb", title='MongoDB Configuration Options')
config.get_config().register_group(mongodb_group)

mongodb_options = [
    cfg.ListOpt('servers',
                default=['localhost:27017'],
                help="""hostname:port for db servers
                    """
                ),
    cfg.StrOpt('database',
               default='test',
               help="""database name
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
    mongodb_options, group=mongodb_group)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)


class MongoDBHandlerError(base.DataHandlerError):
    pass


class MongoDBHandler(base.DataHandlerBase):

    def __init__(self, conf):
        self.mongo_servers = conf.servers
        self.database_name = conf.database
        self.username = conf.username
        self.password = conf.password
        self.connection = None
        self.status = MongoDBHandler.STATUS_NEW

    def _check_connection(self):
        """
        Check that a pyMongo connection has been created,
        if not, raise an exception
        """
        if self.status != self.STATUS_CONNECTED:
            raise MongoDBHandlerError('Database not connected.')

    def connect(self):
        """
        Create a connection to mongodb
        """
        try:
            self.connection = MongoClient(self.mongo_servers, slave_okay=True)
            self.database = self.connection[self.database_name]

            if self.username and self.password:
                self.database.authenticate(self.username, self.password)

            self.status = MongoDBHandler.STATUS_CONNECTED
        except errors.PyMongoError as ex:
            _LOG.exception(ex)
            raise MongoDBHandlerError("failure connecting")

    def close(self):
        """
        Close the connection to mongodb
        """
        self.connection.close()
        self.status = MongoDBHandler.STATUS_CLOSED

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

    def find(self, object_name, query_filter=None, projection=None):
        if query_filter is None:
            query_filter = dict()

        self._check_connection()
        return self.database[object_name].find(query_filter, projection)

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
        if document is None or '_id' not in document:
            raise MongoDBHandlerError(
                'The document must have a field "_id" in its root in '
                'order to perform an update operation.')

        self._check_connection()
        self.database[object_name].save(document)

    def set_field(self, object_name, update_fields, query_filter=None):
        '''
        Updates the given field with a new value for all documents that match
        the query filter

        :param object_name: represents the mongo collection
        :param update_fields: dict of fields to update and their new values
        :param query_filter: represents field/value to query by

        '''
        if query_filter is None:
            query_filter = dict()
        self._check_connection()

        set_statement = {"$set": update_fields}

        self.database[object_name].update(
            query_filter, set_statement, multi=True)

    def remove_field(self, object_name, update_fields, query_filter=None):
        '''
        Updates the given field with a new value for all documents that match
        the query filter

        :param object_name: represents the mongo collection
        :param update_fields: dict of fields to remove from the collection
        :param value: the new value for the field
        :param query_filter: represents field/value to query by

        '''
        if query_filter is None:
            query_filter = dict()
        self._check_connection()

        set_statement = {"$unset": update_fields}

        self.database[object_name].update(
            query_filter, set_statement, multi=True)

    def delete(self, object_name, query_filter=None, limit_one=False):
        if query_filter is None:
            query_filter = dict()
        self.database[object_name].remove(query_filter, True)


def get_handler():
    """
    factory method that returns an instance of MongoDBHandler
    """
    conf = config.get_config()
    mongo_handler = MongoDBHandler(conf.mongodb)
    try:
        mongo_handler.connect()
    except MongoDBHandlerError as ex:
        _LOG.exception(ex)
    return mongo_handler
