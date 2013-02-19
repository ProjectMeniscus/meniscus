import pymongo

from oslo.config import cfg
from meniscus.config import get_config
from meniscus.data.adapters.handler import *

# MongoDB configuration options
mongodb_group = cfg.OptGroup(name='mongodb', title='MongoDB Options')
get_config().register_group(mongodb_group)

MONGODB_OPTIONS = [
    cfg.ListOpt('mongo_servers',
               default=['localhost:27017'],
               help='MongoDB servers to connect to.'
               ),
   cfg.StrOpt('username',
               default='',
               help="""MongoDB username to use when authenticating.
                       If this value is left unset, then authentication
                       against the MongoDB will not be utilized.
                    """,
               secret=True
               ),
   cfg.StrOpt('password',
               default='',
               help="""MongoDB password to use when authenticating.
                       If this value is left unset, then authentication
                       against the MongoDB will not be utilized.
                    """,
               secret=True
               )
]

get_config().register_opts(_MONGODB_OPTIONS, group=_mongodb_group)

class MongoDatasourceHandler(DatasourceHandler):

    def __init__(self, conf):
        self.mongo_servers = conf.mongo_servers
        self.username = conf.username
        self.password = conf.password
        
    def connect(self):
        self.connection = MongoClient(self.mongo_servers, slave_okay=True)
        self.status = STATUS_CONNECTED

    def close(self):
        self.connection.close()
        self.status = STATUS_CLOSED

    def get(self, object_name, object_id):
        raise NotImplementedError

    def put(self, object_name, update_object):
        raise NotImplementedError

    def delete(self, object_name, object_id):
        raise NotImplementedError


# Registers this handler and make it available for use
def register():
    register_handler('mongodb', MongoDatasourceHandler)
