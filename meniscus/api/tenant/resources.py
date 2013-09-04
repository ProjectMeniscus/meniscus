
import falcon

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import handle_api_exception

from meniscus.data.model.util import find_event_producer
from meniscus.data.model.util import find_tenant
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.openstack.common.timeutils import parse_isotime
from meniscus.openstack.common.timeutils import isotime
from meniscus.api.validator_init import get_validator

MESSAGE_TOKEN = 'MESSAGE-TOKEN'
MIN_TOKEN_TIME_LIMIT_HRS = 3


def _tenant_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate tenant.')


def _producer_not_found():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404, 'Unable to locate event producer.')


def _message_token_is_invalid():
    """
    sends an http 404 response to the caller
    """
    abort(falcon.HTTP_404)


def _token_time_limit_not_reached():
    """
    sends an http 409 response to the caller
    """
    abort(falcon.HTTP_409,
          'Message tokens can only be changed once every {0} hours'
          .format(MIN_TOKEN_TIME_LIMIT_HRS))


class TenantResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    @handle_api_exception(operation_name='TenantResource POST')
    @falcon.before(get_validator('tenant'))
    def on_post(self, req, resp, validated_body):

        body = validated_body['tenant']
        tenant_id = str(body['tenant_id'])

        tenant_name = body.get('tenant_name', tenant_id)

        #validate that tenant does not already exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)
        if tenant:
            abort(falcon.HTTP_400, 'Tenant with tenant_id {0} '
                  'already exists'.format(tenant_id))

        #create new token for the tenant
        new_token = Token()
        new_tenant = Tenant(tenant_id, new_token, tenant_name=tenant_name)

        self.db.put('tenant', new_tenant.format())
        self.db.create_sequence(new_tenant.tenant_id)
        resp.status = falcon.HTTP_201
        resp.set_header('Location', '/v1/{0}'.format(tenant_id))


class UserResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    @handle_api_exception(operation_name='UserResource GET')
    def on_get(self, req, resp, tenant_id):
        tenant = find_tenant(self.db,
                             tenant_id=tenant_id,
                             create_on_missing=True)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'tenant': tenant.format()})

    @handle_api_exception(operation_name='UserResource DELETE')
    def on_delete(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        self.db.delete('tenant', {'_id': tenant.get_id()})
        self.db.delete_sequence(tenant.tenant_id)
        resp.status = falcon.HTTP_200


class EventProducersResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    @handle_api_exception(operation_name='Event Producers GET')
    def on_get(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'event_producers':
                                         [p.format()
                                          for p in tenant.event_producers]})

    @handle_api_exception(operation_name='Event Producers POST')
    @falcon.before(get_validator('tenant'))
    def on_post(self, req, resp, tenant_id, validated_body):
        body = validated_body['event_producer']

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

        if 'sinks' in body.keys():
            event_producer_sinks = body['sinks']
        else:
            event_producer_sinks = None

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
            event_producer_encrypted,
            event_producer_sinks)

        tenant.event_producers.append(new_event_producer)
        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/producers/{1}'
                        .format(tenant_id, new_event_producer.get_id()))


class EventProducerResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    @handle_api_exception(operation_name='Event Producer GET')
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

    @handle_api_exception(operation_name='Event Producer PUT')
    @falcon.before(get_validator('tenant'))
    def on_put(self, req, resp, tenant_id, event_producer_id, validated_body):

        body = validated_body['event_producer']

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

        if 'pattern' in body:
            event_producer.pattern = str(body['pattern'])

        if 'durable' in body:
            event_producer.durable = body['durable']

        if 'encrypted' in body:
            event_producer.encrypted = body['encrypted']

        if 'sinks' in body:
            event_producer.sinks = body['sinks']

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200

    @handle_api_exception(operation_name='Event Producer DELETE')
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

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_200


class TokenResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    @handle_api_exception(operation_name='Token HEAD')
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

    @handle_api_exception(operation_name='Token GET')
    def on_get(self, req, resp, tenant_id):

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'token': tenant.token.format()})

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

        return True

    @handle_api_exception(operation_name='Token POST')
    @falcon.before(get_validator('tenant'))
    def on_post(self, req, resp, tenant_id, validated_body):

        body = validated_body['token']

        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        invalidate_now = body['invalidate_now']

        if invalidate_now:
            #immediately invalidate the token
            tenant.token.reset_token_now()

        else:
            self._validate_token_min_time_limit_reached(tenant.token)
            tenant.token.reset_token()

        self.db.update('tenant', tenant.format_for_save())

        resp.status = falcon.HTTP_203
        resp.set_header('Location', '/v1/{0}/token'.format(tenant_id))
