from config import config

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

from meniscus.model.control import Base, Tenant, Host

"""
Locally scoped db session
"""
_Session = scoped_session(sessionmaker())
_engine = None


def db_session():
    return _Session


def _engine_from_config(configuration):
    configuration = dict(configuration)
    url = configuration.pop('url')
    
    return create_engine(url, **configuration)


def init_model():
    _engine = _engine_from_config(config['sqlalchemy'])
    Base.metadata.create_all(_engine)
    _Session.bind = _engine
