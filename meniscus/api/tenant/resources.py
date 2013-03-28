import falcon

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.data.model.util import find_event_producer
from meniscus.data.model.util import find_host
from meniscus.data.model.util import find_host_profile
from meniscus.data.model.util import find_tenant
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.openstack.common.timeutils import parse_isotime
from meniscus.openstack.common.timeutils import isotime

MESSAGE_TOKEN = 'MESSAGE-TOKEN'
MIN_TOKEN_TIME_LIMIT_HRS = 3


def _tenant_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate tenant.')


def _tenant_id_not_provided():
    """
    sends an http 400 response to the caller when a a tenant id is not given
    """
    abort(falcon.HTTP_400, 'Malformed request, tenant_id cannot be empty')


def _host_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_400, 'Unable to locate host.')


def _hostname_not_provided():
    """
    sends an http 400 response to the caller when a a tenant id is not given
    """
    abort(falcon.HTTP_400, 'Malformed request, hostname cannot be empty')


def _host_profile_id_invalid():
    """
    sends an http 400 response to the caller
    """
    abort(
        falcon.HTTP_400,
        'Malformed request, invalid value for profile_id')


def _profile_not_found():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, 'Unable to locate host profile.')


def _profile_name_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, 'Malformed request, name cannot be empty')


def _producer_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate event producer.')


def _profile_producer_ids_invalid():
    """
    sends an http 400 response to the caller
    """
    abort(
        falcon.HTTP_400,
        'Malformed request, event_producer_ids must be a list of integers')


def _producer_name_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, 'Malformed request, name cannot be empty')


def _producer_pattern_not_provided():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400, 'Malformed request, pattern cannot be empty')


def _message_token_is_invalid():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404)


def _token_invalidate_now_malformed():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400,
          'Malformed request, invalidate_now must be a boolean ')


def _token_time_limit_not_reached():
    """
    sends an http 409 response to the caller
    """
    abort(falcon.HTTP_409,
          'Message tokens can only be changed once every {0} hours'
          .format(MIN_TOKEN_TIME_LIMIT_HRS))


def _encrypted_must_be_bool():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400,
          'Malformed request, encrypted must be true or false')


def _durable_must_be_bool():
    """
    sends an http 400 response to the caller
    """
    abort(falcon.HTTP_400,
          'Malformed request, durable must be true or false')


class VersionResource(ApiResource):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'v1': 'current'})


class TenantResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def _validate_req_body_on_post(self, body):
        if 'tenant_id' not in body.keys() or not body['tenant_id']:
            _tenant_id_not_provided()

    def on_post(self, req, resp):
        body = load_body(req)

        self._validate_req_body_on_post(body)

        tenant_id = str(body['tenant_id'])

        #validate that tenant does not already exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)
        if tenant:
            abort(falcon.HTTP_400, 'Tenant with tenant_id {0} '
                  'already exists'.format(tenant_id))

        #create new token for the tenant
        new_token = Token()
        new_tenant = Tenant(tenant_id, new_token)

        self.db.put('tenant', new_tenant.format())
        self.db.create_sequence(new_tenant.tenant_id)
        resp.status = falcon.HTTP_201
        resp.set_header('Location', '/v1/{0}'.format(tenant_id))


class UserResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):

        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'tenant': tenant.format()})

    def on_delete(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        self.db.delete('tenant', {'_id': tenant.get_id()})
        self.db.delete_sequence(tenant.tenant_id)
        resp.status = falcon.HTTP_200


class HostProfilesResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):
        #ensure the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)
        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200

        #jsonify a list of formatted profiles
        resp.body = format_response_body({
            'profiles': [p.format() for p in tenant.profiles]
        })

    def _validate_req_body_on_post(self, body):
        if 'name' not in body.keys() or not body['name']:
            _profile_name_not_provided()

        #validate that event_producer_ids is a list of integers
        if 'event_producer_ids' in body.keys() and body['event_producer_ids']:
            event_producer_ids = body['event_producer_ids']
            try:
                [int(p_id) for p_id in event_producer_ids]
            except (TypeError, ValueError):
                _profile_producer_ids_invalid()

    def on_post(self, req, resp, tenant_id):
        body = load_body(req)

        self._validate_req_body_on_post(body)

        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        profile_name = body['name']

        # Check if the tenant already has a profile with this name
        profile = find_host_profile(tenant, profile_name=profile_name)
        if profile:
            abort(falcon.HTTP_400,
                  'Profile with name {0} already exists with id={1}.'
                  .format(profile.name, profile.get_id()))

        # Create the new profile for the host
        new_host_profile = HostProfile(
            self.db.next_sequence_value(tenant.tenant_id), profile_name)

        if 'event_producer_ids' in body.keys():
            producer_ids = body['event_producer_ids']

            for producer_id in producer_ids:

                #abort if any of the event_producers being passed in are not
                # valid event_producers for this tenant
                if not find_event_producer(tenant, producer_id=producer_id):
                    _producer_not_found()

            #update the list of event_producers
            new_host_profile.event_producers = producer_ids

        tenant.profiles.append(new_host_profile)
        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/profiles/{1}'
                        .format(tenant_id, new_host_profile.get_id()))


class HostProfileResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id, profile_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the profile exists and belongs to the tenant
        profile = find_host_profile(tenant, profile_id=profile_id)
        if not profile:
            _profile_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'profile': profile.format()})

    def _validate_req_body_on_put(self, body):
        # if the request includes name field, validate it is not empty
        if 'name' in body.keys():
            if not body['name']:
                _profile_name_not_provided()

        #validate that event_producer_ids is a list of integers
        if 'event_producer_ids' in body.keys() and body['event_producer_ids']:
            event_producer_ids = body['event_producer_ids']
            try:
                [int(p_id) for p_id in event_producer_ids]
            except (TypeError, ValueError):
                _profile_producer_ids_invalid()

    def on_put(self, req, resp, tenant_id, profile_id):
        #load the message
        body = load_body(req)

        self._validate_req_body_on_put(body)

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)
        if not tenant:
            _tenant_not_found()

        #verify the profile exists and belongs to the tenant
        profile = find_host_profile(tenant, profile_id=profile_id)
        if not profile:
            _profile_not_found()

        #if attributes are present in message, update the profile
        if 'name' in body.keys() and body['name'] != profile.name:

            #if the tenant already has a profile with this name then abort
            duplicate_profile = find_host_profile(tenant,
                                                  profile_name=body['name'])
            if duplicate_profile:
                abort(falcon.HTTP_400,
                      'Profile with name {0} already exists with id={1}.'
                      .format(duplicate_profile.name,
                              duplicate_profile.get_id()))

            profile.name = body['name']

        if 'event_producer_ids' in body.keys():
            producer_ids = body['event_producer_ids']

            for producer_id in producer_ids:

                #abort if any of the event_producers being passed in are not
                # valid event_producers for this tenant

                if not find_event_producer(tenant, producer_id=producer_id):
                    _producer_not_found()

            #update the list of event_producers
            profile.event_producers = producer_ids

        self.db.update('tenant', tenant.format_for_save())
        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, tenant_id, profile_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the profile exists and belongs to the tenant
        profile = find_host_profile(tenant, profile_id=profile_id)
        if not profile:
            _profile_not_found()

        #remove any references to the profile being deleted
        tenant.profiles.remove(profile)
        for host in tenant.hosts:
            if host.profile == profile.get_id():
                host.profile = None

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200


class EventProducersResource(ApiResource):
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'event_producers':
                                         [p.format()
                                          for p in tenant.event_producers]})

    def _validate_req_body_on_post(self, body):
        if 'name' not in body.keys() or not body['name']:
            _producer_name_not_provided()

        if 'pattern' not in body.keys() or not body['pattern']:
            _producer_pattern_not_provided()

        if 'durable' in body.keys():
            if body['durable'] not in [True, False]:
                _durable_must_be_bool()

        if 'encrypted' in body.keys():
            if body['encrypted'] not in [True, False]:
                _encrypted_must_be_bool()

    def on_post(self, req, resp, tenant_id):
        body = load_body(req)

        self._validate_req_body_on_post(body)

        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        event_producer_name = body['name']
        event_producer_pattern = body['pattern']

        #if durable or encrypted aren't specified, set to False
        if 'durable' in body.keys():
            event_producer_durable = body['durable']
        else:
            event_producer_durable = False

        if 'encrypted' in body.keys():
            event_producer_encrypted = body['encrypted']
        else:
            event_producer_encrypted = False

        # Check if the tenant already has an event producer with this name
        producer = find_event_producer(tenant,
                                       producer_name=event_producer_name)
        if producer:
            abort(falcon.HTTP_400,
                  'Event producer with name {0} already exists with id={1}.'
                  .format(producer.name, producer.get_id()))

        # Create the new profile for the host
        new_event_producer = EventProducer(
            self.db.next_sequence_value(tenant.tenant_id),
            event_producer_name,
            event_producer_pattern,
            event_producer_durable,
            event_producer_encrypted)

        tenant.event_producers.append(new_event_producer)
        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/producers/{1}'
                        .format(tenant_id, new_event_producer.get_id()))


class EventProducerResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id, event_producer_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists and belongs to the tenant
        event_producer = find_event_producer(tenant,
                                             producer_id=event_producer_id)
        if not event_producer:
            _producer_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body(
            {'event_producer': event_producer.format()})

    def _validate_req_body_on_put(self, body):
        if 'name' in body.keys():
            if not body['name']:
                _producer_name_not_provided()

        if 'pattern' in body.keys():
            if not body['pattern']:
                _producer_pattern_not_provided()

        if 'durable' in body.keys():
            if body['durable'] not in [True, False]:
                _durable_must_be_bool()

        if 'encrypted' in body.keys():
            if body['encrypted'] not in [True, False]:
                _encrypted_must_be_bool()

    def on_put(self, req, resp, tenant_id, event_producer_id):
        body = load_body(req)

        self._validate_req_body_on_put(body)

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists and belongs to the tenant
        event_producer = find_event_producer(tenant,
                                             producer_id=event_producer_id)
        if not event_producer:
            _producer_not_found()

        #if a key is present, update the event_producer with the value
        if 'name' in body.keys() and event_producer.name != body['name']:
            #if the tenant already has a profile with this name then abort
            duplicate_producer = \
                find_event_producer(tenant,  producer_name=body['name'])
            if duplicate_producer:
                abort(falcon.HTTP_400,
                      'EventProducer with name {0} already exists with id={1}.'
                      .format(duplicate_producer.name,
                              duplicate_producer.get_id()))
            event_producer.name = body['name']

        if 'pattern' in body.keys():
            event_producer.pattern = str(body['pattern'])

        if 'durable' in body.keys():
            event_producer.durable = body['durable']

        if 'encrypted' in body.keys():
            event_producer.encrypted = body['encrypted']

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, tenant_id, event_producer_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists and belongs to the tenant
        event_producer = find_event_producer(tenant,
                                             producer_id=event_producer_id)
        if not event_producer:
            _producer_not_found()

        #remove any references to the event producer being deleted
        tenant.event_producers.remove(event_producer)
        for profile in tenant.profiles:
            if event_producer.get_id() in profile.event_producers:
                profile.event_producers.remove(event_producer.get_id())

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200


class HostsResource(ApiResource):

    def __init__(self, db_session):
        self.db = db_session

    def on_get(self, req, resp, tenant_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body(
            {'hosts': [h.format() for h in tenant.hosts]})

    def _validate_req_body_on_post(self, body):
        if 'hostname' not in body.keys() or not body['hostname']:
            _hostname_not_provided()

        if 'profile_id' in body.keys() and body['profile_id']:
            try:
                int(body['profile_id'])
            except (TypeError, ValueError):
                _host_profile_id_invalid()

    def on_post(self, req, resp, tenant_id):
        body = load_body(req)

        self._validate_req_body_on_post(body)

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        hostname = body['hostname']

        # Check if the tenant already has a host with this hostname
        for host in tenant.hosts:
            if host.hostname == hostname:
                abort(falcon.HTTP_400,
                      'Host with hostname {0} already exists with id={1}'
                      .format(hostname, host.get_id()))

        ip_address_v4 = None
        if 'ip_address_v4' in body.keys():
            ip_address_v4 = body['ip_address_v4']

        ip_address_v6 = None
        if 'ip_address_v6' in body.keys():
            ip_address_v6 = body['ip_address_v6']

        profile_id = None
        #if profile id is not in post message, then use a null profile
        if 'profile_id' in body.keys():
            if body['profile_id']:
                profile_id = body['profile_id']

        #if profile id is in post message, then make sure it is valid profile
        if profile_id:
            #verify the profile exists and belongs to the tenant
            profile = find_host_profile(tenant, profile_id=profile_id)
            if not profile:
                _profile_not_found()

        # Create the new host definition
        new_host = Host(
            self.db.next_sequence_value(tenant.tenant_id),
            hostname, ip_address_v4,
            ip_address_v6, profile_id)

        tenant.hosts.append(new_host)
        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/hosts/{1}'
                        .format(tenant_id, new_host.get_id()))


class HostResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id, host_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the hosts exists and belongs to the tenant
        host = find_host(tenant, host_id=host_id)
        if not host:
            _host_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'host': host.format()})

    def _validate_req_body_on_put(self, body):
        if 'hostname' in body.keys():
            if not body['hostname']:
                _hostname_not_provided()

        if 'profile_id' in body.keys() and body['profile_id']:
            try:
                int(body['profile_id'])
            except (TypeError, ValueError):
                _host_profile_id_invalid()

    def on_put(self, req, resp, tenant_id, host_id):
        body = load_body(req)

        self._validate_req_body_on_put(body)

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the hosts exists and belongs to the tenant
        host = find_host(tenant, host_id=host_id)
        if not host:
            _host_not_found()

        if 'hostname' in body.keys() and host.hostname != body['hostname']:
            # Check if the tenant already has a host with this hostname
            hostname = str(body['hostname'])
            for duplicate_host in tenant.hosts:
                if duplicate_host.hostname == hostname:
                    abort(falcon.HTTP_400,
                          'Host with hostname {0} already exists with'
                          ' id={1}'.format(hostname, duplicate_host.get_id()))
            host.hostname = hostname

        if 'ip_address_v4' in body.keys():
            host.ip_address_v4 = body['ip_address_v4']

        if 'ip_address_v6' in body.keys():
            host.ip_address_v6 = body['ip_address_v6']

        if 'profile_id' in body.keys():
            if body['profile_id']:
                host.profile = int(body['profile_id'])
            else:
                host.profile = None

            if host.profile:
                #verify the profile exists and belongs to the tenant
                profile = find_host_profile(tenant, profile_id=host.profile)
                if not profile:
                    _profile_not_found()

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, tenant_id, host_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the hosts exists and belongs to the tenant
        host = find_host(tenant, host_id=host_id)
        if not host:
            _host_not_found()

        #delete the host
        tenant.hosts.remove(host)
        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200


class TokenResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_head(self, req, resp, tenant_id):

        #get message token, or abort if token is not in header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        if not tenant.token.validate_token(message_token):
            _message_token_is_invalid()

        resp.status = falcon.HTTP_200

    def on_get(self, req, resp, tenant_id):

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'token': tenant.token.format()})

    def _validate_req_body_on_post(self, body):
        #if invalidate_now is included in request,
        # verify the value is True or False
        if 'token' in body.keys() and 'invalidate_now' in body['token']:
            invalidate_now = body['token']['invalidate_now']
            if invalidate_now not in [True, False]:
                _token_invalidate_now_malformed()

    def _validate_token_min_time_limit_reached(self, token):
        #get the token create time and the current time as datetime objects
        token_created = parse_isotime(token.last_changed)
        current_time = parse_isotime(isotime(subsecond=True))

        #get a datetime.timedelta object that represents the difference
        time_diff = current_time - token_created
        hours_diff = time_diff.total_seconds() / 3600

        #if the time limit has not been reached, abort and alert the caller
        if hours_diff < MIN_TOKEN_TIME_LIMIT_HRS:
            _token_time_limit_not_reached()

    def on_post(self, req, resp, tenant_id):

        body = dict()
        if req.stream:
            body = load_body(req)
            self._validate_req_body_on_post(body)

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        invalidate_now = False

        if 'token' in body.keys() and 'invalidate_now' in body['token']:
            invalidate_now = body['token']['invalidate_now']

        if invalidate_now:
            #immediately invalidate the token
            tenant.token.reset_token_now()

        else:
            self._validate_token_min_time_limit_reached(tenant.token)
            tenant.token.reset_token()

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_203
        resp.set_header('Location', '/v1/{0}/token'.format(tenant_id))
