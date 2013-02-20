from sqlalchemy import Table, Column, String
from sqlalchemy import Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, declared_attr


class Persisted(object):
    
    id = Column(Integer, primary_key=True)
    
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()


Base = declarative_base(cls=Persisted)


class EventProducer(Base):
    """
    An event producer is a nicer way of describing a parsing template
    for a producer of events. Event producer definitions should be
    reusable and not specific to any one host. While this may not
    always be the case, it should be considered for each event producer
    described.
    """

    name = Column(String)
    pattern = Column(String)
    durable = Column(Boolean)
    encrypted = Column(Boolean)
    owner_id = Column(Integer, ForeignKey('tenant.id'))

    def __init__(self, owner_id, name, pattern, durable,
                 encrypted):

        self.owner_id = owner_id
        self.name = name
        self.pattern = pattern
        self.durable = durable
        self.encrypted = encrypted

    def format(self):
        return {'id': self.id, 'name': self.name, 'pattern': self.pattern,
                'durable': self.durable, 'encrypted': self.encrypted}


class HostProfile(Base):
    """
    Host profiles are reusable collections of event producers with an
    associated, unique name for lookup.
    """
    _assigned_producers = Table(
        'profile_assigned_producer', Base.metadata,
        Column('event_producer_id', Integer,
               ForeignKey('eventproducer.id')),
        Column('host_profile_id', Integer,
               ForeignKey('hostprofile.id')))

    name = Column(String)
    owner_id = Column(Integer, ForeignKey('tenant.id'))
    event_producers = relationship('EventProducer',
                                   secondary=_assigned_producers)

    def __init__(self, owner_id, name, event_producers=None):
        if not event_producers:
            event_producers = []

        self.owner_id = owner_id
        self.name = name
        self.event_producers = event_producers

    def format(self):
        return {'id': self.id,
                'name': self.name,
                'event_producers':
                [ep.format() for ep in self.event_producers]}


class Host(Base):
    """
    Hosts represent a single, addressable entity in a logical tenant
    environment.
    """

    hostname = Column(String)
    ip_address = Column(String)
    profile_id = Column(Integer, ForeignKey('hostprofile.id'))
    profile = relationship('HostProfile', uselist=False)

    def __init__(self, hostname, ip_address, profile=None):
        self.hostname = hostname
        self.ip_address = ip_address
        self.profile = profile

    def format(self):
        if self.profile:
            profile = self.profile.format()
        else:
            profile = None
        return {'id': self.id,
                'hostname': self.hostname,
                'ip_address': self.ip_address,
                'profile': profile}


class Tenant(Base):
    """
    Tenants are users of the environments being monitored for
    application events.
    """
    _registered_hosts = Table(
        'registered_hosts', Base.metadata,
        Column('tenant_id', Integer,
               ForeignKey('tenant.id')),
        Column('host_id', Integer,
               ForeignKey('host.id')))

    tenant_id = Column(String)
    hosts = relationship('Host', secondary=_registered_hosts)
    profiles = relationship('HostProfile')
    event_producers = relationship('EventProducer')

    def __init__(self, tenant_id, hosts=[], profiles=[], event_producers=[]):
        self.tenant_id = tenant_id
        self.hosts = hosts
        self.profiles = profiles
        self.event_producers = event_producers

    def format(self):
        return {'id': self.id,
                'tenant_id': self.tenant_id}
