from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from meniscus.model.tenant import Tenant, Host, HostProfile, EventProducer


def _empty_condition(): pass


def find_tenant(db_session, id=None, tenant_id=None,
                when_not_found=_empty_condition,
                when_multiple_found=_empty_condition):
    try:
        if id:
            return db_session.query(Tenant).filter_by(id=id).one()
        elif tenant_id:
            return db_session.query(Tenant).filter_by(tenant_id=tenant_id).one()
    except NoResultFound:
        when_not_found()
    except MultipleResultsFound:
        when_multiple_found()

    return None


def find_host(db_session, id, when_not_found=_empty_condition,
              when_multiple_found=_empty_condition):
    try:
        return db_session.query(Host).filter_by(id=id).one()
    except NoResultFound:
        when_not_found()
    except MultipleResultsFound:
        when_multiple_found()


def find_host_profile(db_session, id=None, name=None,
                      when_not_found=_empty_condition,
                      when_multiple_found=_empty_condition):
    try:
        if id:
            return db_session.query(HostProfile).filter_by(id=id).one()
        elif name:
            return db_session.query(HostProfile).filter_by(name=name).one()
    except NoResultFound:
        when_not_found()
    except MultipleResultsFound:
        when_multiple_found()


def find_event_producer(db_session, id=None, name=None,
                        when_not_found=_empty_condition,
                        when_multiple_found=_empty_condition):
    try:

        if id:
            return db_session.query(EventProducer).filter_by(id=id).one()
        elif name:
            return db_session.query(EventProducer).filter_by(name=name).one()
    except NoResultFound:
        when_not_found()
    except MultipleResultsFound:
        when_multiple_found()
