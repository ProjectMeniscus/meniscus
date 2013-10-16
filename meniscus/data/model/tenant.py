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
            self.sinks = [DEFAULT_SINK]
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


class Token(object):
    """
    Token is an object used to authenticate messages from a tenant.
    """

    def __init__(self, valid=None, previous=None, last_changed=None):
        if not valid:
            valid = str(uuid4())
        if not last_changed:
            last_changed = isotime(subsecond=True)

        self.valid = valid
        self.previous = previous
        self.last_changed = last_changed

    def reset_token(self):
        """
        Resets a token by creating a new valid token,
        and saves the current token as previous.
        """
        self.previous = self.valid
        self.valid = str(uuid4())
        self.last_changed = isotime(subsecond=True)

    def reset_token_now(self):
        """
        Completely resets token values leaving no previous token.
        """
        self.__init__()

    def validate_token(self, message_token):
        """
        Validates a token as True if the message_token matches
        the current valid token or the previous token.
        """
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

    def __init__(self, tenant_id, token, event_producers=None,
                 _id=None, tenant_name=None):

        if event_producers is None:
            event_producers = list()

        if tenant_name is None:
            tenant_name = tenant_id

        self._id = _id
        self.tenant_id = str(tenant_id)
        self.token = token
        self.event_producers = event_producers
        self.tenant_name = tenant_name

    def get_id(self):
        return self._id

    def format(self):
        return {'tenant_id': self.tenant_id,
                'tenant_name': self.tenant_name,
                'event_producers':
                [p.format() for p in self.event_producers],
                'token': self.token.format()}

    def format_for_save(self):
        tenant_dict = self.format()
        tenant_dict['_id'] = self._id
        return tenant_dict
