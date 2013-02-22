import falcon

from meniscus.api.tenant.resources import *

from config import config
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker


"""
Locally scoped db session
"""
_session = scoped_session(sessionmaker())
_engine = None


def db_session():
    return _session


def _engine_from_config(configuration):
    configuration = dict(configuration)
    url = configuration.pop('url')
    
    return create_engine(url, **configuration)


def init_tenant_model():
    _engine = _engine_from_config(config['sqlalchemy'])
    Base.metadata.create_all(_engine)
    _session.bind = _engine


# Initialize the data model
init_tenant_model()

# Resources
versions = VersionResource()
tenant = TenantResource(db_session())
user = UserResource(db_session())
profiles = HostProfilesResource(db_session())
profile = HostProfileResource(db_session())
event_producers = EventProducersResource(db_session())
event_producer = EventProducerResource(db_session())
hosts = HostsResource(db_session())
host = HostResource(db_session())


# Routing
application = api = falcon.API()

api.add_route('/', versions)
api.add_route('/v1', tenant)
api.add_route('/v1/{tenant_id}', user)
api.add_route('/v1/{tenant_id}/profiles', profiles)
api.add_route('/v1/{tenant_id}/profiles/{profile_id}', profile)
api.add_route('/v1/{tenant_id}/producers', event_producers)
api.add_route('/v1/{tenant_id}/producers/{event_producer_id}', event_producer)
api.add_route('/v1/{tenant_id}/hosts', hosts)
api.add_route('/v1/{tenant_id}/hosts/{host_id}', host)
