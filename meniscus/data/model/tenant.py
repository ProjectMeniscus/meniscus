from uuid import uuid4
from meniscus.openstack.common.timeutils import isotime
from meniscus.sinks import DEFAULT_SINK


class EventProducer(object):
    """
An event producer is a nicer way of describing a parsing template
for a producer of events. Event producer definitions should be
reusable and not specific to any one host. While this may not
always be the case, it should be considered for each event producer
described.
"""

    def __init__(self, _id, name, pattern, durable=False,
                 encrypted=False, sinks=None):

        if not sinks:
            self.sinks = [DEFAULT_SINK,]
        else:
            self.sinks = sinks

        self._id = _id
        self.name = name
        self.pattern = pattern
        self.durable = durable
        self.encrypted = encrypted

    def get_id(self):
        return self._id

    def format(self):
        return {'id': self._id, 'name': self.name, 'pattern': self.pattern,
                'durable': self.durable, 'encrypted': self.encrypted,
                'sinks': self.sinks}


class HostProfile(object):
    """
Host profiles are reusable collections of event producers with an
associated, unique name for lookup.
"""

    def __init__(self, _id, name, event_producer_ids=None):
        if event_producer_ids is None:
            event_producer_ids = []

        self._id = _id
        self.name = name
        self.event_producers = event_producer_ids

    def get_id(self):
        return self._id

    def format(self):
        return {'id': self._id,
                'name': self.name,
                'event_producer_ids': self.event_producers}


class Host(object):
    """
Hosts represent a single, addressable entity in a logical tenant
environment.
"""

    def __init__(self, _id, hostname, ip_address_v4=None, ip_address_v6=None,
                 profile_id=None):
        self._id = _id
        self.hostname = hostname
        self.ip_address_v4 = ip_address_v4
        self.ip_address_v6 = ip_address_v6
        self.profile = profile_id

    def get_id(self):
        return self._id

    def format(self):

        return {'id': self._id,
                'hostname': self.hostname,
                'ip_address_v4': self.ip_address_v4,
                'ip_address_v6': self.ip_address_v6,
                'profile_id': self.profile}


class Token(object):

    def __init__(self, valid=None, previous=None, last_changed=None):
        if not valid:
            valid = str(uuid4())
        if not last_changed:
            last_changed = isotime(subsecond=True)

        self.valid = valid
        self.previous = previous
        self.last_changed = last_changed

    def reset_token(self):
        self.previous = self.valid
        self.valid = str(uuid4())
        self.last_changed = isotime(subsecond=True)

    def reset_token_now(self):
        self.__init__()

    def validate_token(self, message_token):
        if not message_token:
            return False

        if message_token == self.valid or message_token == self.previous:
            return True

        return False

    def format(self):
        return {'valid': self.valid,
                'previous': self.previous,
                'last_changed': self.last_changed,
                }


class Tenant(object):
    """
Tenants are users of the environments being monitored for
application events.
"""

    def __init__(self, tenant_id, token, hosts=None, profiles=None,
                 event_producers=None,  _id=None, tenant_name=None):
        if hosts is None:
            hosts = list()

        if profiles is None:
            profiles = list()

        if event_producers is None:
            event_producers = list()

        if tenant_name is None:
            tenant_name = tenant_id

        self._id = _id
        self.tenant_id = str(tenant_id)
        self.token = token
        self.hosts = hosts
        self.profiles = profiles
        self.event_producers = event_producers
        self.tenant_name = tenant_name

    def get_id(self):
        return self._id

    def format(self):
        return {'tenant_id': self.tenant_id,
                'tenant_name': self.tenant_name,
                'hosts': [h.format() for h in self.hosts],
                'profiles': [p.format() for p in self.profiles],
                'event_producers':
                [p.format() for p in self.event_producers],
                'token': self.token.format()}

    def format_for_save(self):
        tenant_dict = self.format()
        tenant_dict['_id'] = self._id
        return tenant_dict
