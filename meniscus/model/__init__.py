from pecan import conf

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

from meniscus.model.control import Base, Tenant, Host

"""
Locally scoped db session
"""
_Session = scoped_session(sessionmaker())


def db_session():
    return _Session


def _engine_from_config(configuration):
    configuration = dict(configuration)
    url = configuration.pop('url')
    return create_engine(url, **configuration)


def init_model():
    conf.sqlalchemy.engine = _engine_from_config(conf.sqlalchemy)
    Base.metadata.create_all(conf.sqlalchemy.engine)


def start():
    session = db_session()
    session.bind = conf.sqlalchemy.engine


def start_read_only():
    start()


def commit():
    db_session().commit()


def rollback():
    db_session().rollback()


def clear():
    db_session().remove()
