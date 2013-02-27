import falcon

from meniscus.api.tenant.resources import VersionResource
from meniscus.api.coordinator.resources import NodeConfigurationResource
#
# from config import config
# from sqlalchemy import create_engine, MetaData
# from sqlalchemy.orm import scoped_session, sessionmaker
# from meniscus.model.tenant import Base
#
# """
# Locally scoped db session
# """
# _session = scoped_session(sessionmaker())
# _engine = None
#
#
# def db_session():
#     return _session
#
#
# def _engine_from_config(configuration):
#     configuration = dict(configuration)
#     url = configuration.pop('url')
#
#     return create_engine(url, **configuration)
#
#
# def init_tenant_model():
#     _engine = _engine_from_config(config['sqlalchemy'])
#     Base.metadata.create_all(_engine)
#     _session.bind = _engine
#
#
# # Initialize the data model
# init_tenant_model()
#
# Resources
versions = VersionResource()
node_cfg = NodeConfigurationResource()


# Routing
application = api = falcon.API()

api.add_route('/', versions)
api.add_route('/v1/', node_cfg)
