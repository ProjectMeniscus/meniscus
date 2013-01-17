from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from meniscus.model import db_session
from meniscus.model.control import Base, Tenant, Host

def _empty_condition():
    pass


def find_tenant(name, when_not_found=_empty_condition,
                 when_multiple_found=_empty_condition):
    try:
        return db_session().query(Tenant).filter_by(name=name).one()
    except NoResultFound:
        when_not_found()
    except MultipleResultsFound:
        when_multiple_found()


def find_host_by_id(host_id, when_not_found=_empty_condition,
                    when_multiple_found=_empty_condition):
    try:
        return db_session().query(Host).filter_by(id=host_id).first()
    except NoResultFound:
        when_not_found()
    except MultipleResultsFound:
        when_multiple_found()
