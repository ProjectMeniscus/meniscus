

class EventProducer():
    """
An event producer is a nicer way of describing a parsing template
for a producer of events. Event producer definitions should be
reusable and not specific to any one host. While this may not
always be the case, it should be considered for each event producer
described.
"""

    def __init__(self, _id, name, pattern, durable=False,
                 encrypted=False):
        self._id = _id
        self.name = name
        self.pattern = pattern
        self.durable = durable
        self.encrypted = encrypted

    def get_id(self):
        return self._id

    def format(self):
        return {'id': self._id, 'name': self.name, 'pattern': self.pattern,
                'durable': self.durable, 'encrypted': self.encrypted}


class HostProfile():
    """
Host profiles are reusable collections of event producers with an
associated, unique name for lookup.
"""

    def __init__(self, _id, name, event_producer_ids=[]):
        if not event_producer_ids:
            event_producer_ids = []

        self._id = _id
        self.name = name
        self.event_producers = event_producer_ids

    def get_id(self):
        return self._id

    def format(self):
        return {'id': self._id,
                'name': self.name,
                'event_producers': self.event_producers}


class Host():
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
                'profile': self.profile}


class Tenant():
    """
Tenants are users of the environments being monitored for
application events.
"""

    def __init__(self, tenant_id, hosts=[], profiles=[], event_producers=[],
                 _id=None):
        self._id = _id
        self.tenant_id = tenant_id
        self.hosts = hosts
        self.profiles = profiles
        self.event_producers = event_producers

    def get_id(self):
        return self._id

    def format(self):
        return {'tenant':
                    {'tenant_id': self.tenant_id,
                     'hosts': [h.format() for h in self.hosts],
                     'profiles': [p.format() for p in self.profiles],
                     'event_producers':
                         [p.format() for p in self.event_producers]}
        }

    def format_for_save(self):
        tenant_dict = self.format()
        tenant_dict['tenant']['_id'] = self._id
        return tenant_dict