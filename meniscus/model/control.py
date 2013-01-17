from sqlalchemy import Table, Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, declared_attr


class Persisted(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=Persisted)


class EventProducer(Base):
    """
    An event producer is a nicer way of describing a parsing template
    for a producer of events. Event producer definitions should be
    resuable and not specific to any one host. While this may not
    always be the case, it should be considered for each event producer
    described.
    """

    name = Column(String)
    pattern = Column(String)

    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern


class HostProfile(Base):
    """
    Host profiles are resuable collections of event producers with an
    associated, unique name for lookup.
    """
    _assigned_producers = Table(
        'profile_assigned_producer', Base.metadata,
        Column('event_producer_id', Integer,
               ForeignKey('eventproducer.id')),
        Column('host_profile_id', Integer,
               ForeignKey('hostprofile.id')))

    name = Column(String)
    event_producers = relationship('EventProducer',
                                   secondary=_assigned_producers)

    def __init__(self, name, event_producers):
        self.name = name
        self.event_producers = event_producers


class Host(Base):
    """
    Hosts represent a single, addressible entity in a logical tennat
    environment.
    """

    hostname = Column(String)
    ip_address = Column(String)

    profile_id = Column(Integer, ForeignKey('hostprofile.id'))
    profile = relationship('HostProfile')

    def __init__(self, hostname, ip_address, profile):
        self.hostname = hostname
        self.ip_address = ip_address
        self.profile = profile


class Tennant(Base):
    """
    Tennants are users of the environemnts being monitored for
    application events.
    """
    _registered_hosts = Table(
        'registered_hosts', Base.metadata,
        Column('tennant_id', Integer,
               ForeignKey('tennant.id')),
        Column('host_id', Integer,
               ForeignKey('host.id')))

    name = Column(String)
    hosts = relationship('Host', secondary=_registered_hosts)

    def __init__(self, name, hosts):
        self.name = name
        self.hosts = hosts
