"""
The Tenant Resources module provides RESTful operations for managing
Tenants and their configurations.  This includes the creating and updating
of new Tenants, creation, update and deletion of Event Producer definitions,
and the management of Tokens.
"""
import falcon

from meniscus import api
from meniscus.api.validator_init import get_validator
from meniscus.data.model import tenant_util
from meniscus.openstack.common.timeutils import parse_isotime
from meniscus.openstack.common.timeutils import isotime


MESSAGE_TOKEN = 'MESSAGE-TOKEN'
MIN_TOKEN_TIME_LIMIT_HRS = 3


def _tenant_not_found():
    """
    sends an http 404 response to the caller
    """
    api.abort(falcon.HTTP_404, 'Unable to locate tenant.')


def _producer_not_found():
    """
    sends an http 404 response to the caller
    """
    api.abort(falcon.HTTP_404, 'Unable to locate event producer.')


def _message_token_is_invalid():
    """
    sends an http 404 response to the caller
    """
    api.abort(falcon.HTTP_404)


def _token_time_limit_not_reached():
    """
    sends an http 409 response to the caller
    """
    api.abort(
        falcon.HTTP_409,
        'Message tokens can only be changed once every {0} hours'
        .format(MIN_TOKEN_TIME_LIMIT_HRS))


class TenantResource(api.ApiResource):
    """
    The tenant Resource allows for the creation of new tenants in the system.
    """

    @api.handle_api_exception(operation_name='TenantResource POST')
    @falcon.before(get_validator('tenant'))
    def on_post(self, req, resp, validated_body):
        """
        Create a new tenant when a HTTP POST is received
        """

        body = validated_body['tenant']
        tenant_id = str(body['tenant_id'])

        tenant_name = body.get('tenant_name', tenant_id)

        #validate that tenant does not already exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)
        if tenant:
            api.abort(falcon.HTTP_400, 'Tenant with tenant_id {0} '
                      'already exists'.format(tenant_id))

        tenant_util.create_tenant(tenant_id=tenant_id, tenant_name=tenant_name)

        resp.status = falcon.HTTP_201
        resp.set_header('Location', '/v1/{0}'.format(tenant_id))


class UserResource(api.ApiResource):
    """
    User Resource allows for retrieval of existing tenants.
    """

    @api.handle_api_exception(operation_name='UserResource GET')
    def on_get(self, req, resp, tenant_id):
        """
        Retrieve a specified tenant when a HTTP GET is received
        """
        tenant = tenant_util.find_tenant(
            tenant_id=tenant_id, create_on_missing=True)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body({'tenant': tenant.format()})


class EventProducersResource(api.ApiResource):
    """
    The Event Producer resource allows for the creation of new Event Producers
    and retrieval of all Event Producers for a Tenant
    """

    @api.handle_api_exception(operation_name='Event Producers GET')
    def on_get(self, req, resp, tenant_id):
        """
        Retrieve a list of all Event Producers for a specified Tenant
        """
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body(
            {'event_producers': [p.format() for p in tenant.event_producers]})

    @api.handle_api_exception(operation_name='Event Producers POST')
    @falcon.before(get_validator('tenant'))
    def on_post(self, req, resp, tenant_id, validated_body):
        """
        Create a a new event Producer for a specified Tenant
        when an HTTP Post is received
        """
        body = validated_body['event_producer']

        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

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
        producer = tenant_util.find_event_producer(
            tenant, producer_name=event_producer_name)
        if producer:
            api.abort(
                falcon.HTTP_400,
                'Event producer with name {0} already exists with id={1}.'
                .format(producer.name, producer.get_id()))

        # Create the new profile for the host
        producer_id = tenant_util.create_event_producer(
            tenant,
            event_producer_name,
            event_producer_pattern,
            event_producer_durable,
            event_producer_encrypted,
            event_producer_sinks)

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/producers/{1}'
                        .format(tenant_id, producer_id))


class EventProducerResource(api.ApiResource):
    """
    EventProducer Resource allows for the retrieval and update of a
    specified Event Producer for a Tenant.
    """

    @api.handle_api_exception(operation_name='Event Producer GET')
    def on_get(self, req, resp, tenant_id, event_producer_id):
        """
        Retrieve a specified Event Producer from a Tenant
        when an HTTP GET is received
        """
        #verify the tenant exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists and belongs to the tenant
        event_producer = tenant_util.find_event_producer(
            tenant, producer_id=event_producer_id)
        if not event_producer:
            _producer_not_found()

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body(
            {'event_producer': event_producer.format()})

    @api.handle_api_exception(operation_name='Event Producer PUT')
    @falcon.before(get_validator('tenant'))
    def on_put(self, req, resp, tenant_id, event_producer_id, validated_body):
        """
        Make an update to a specified Event Producer's configuration
        when an HTTP PUT is received
        """

        body = validated_body['event_producer']

        #verify the tenant exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists and belongs to the tenant
        event_producer = tenant_util.find_event_producer(
            tenant, producer_id=event_producer_id)
        if not event_producer:
            _producer_not_found()

        #if a key is present, update the event_producer with the value
        if 'name' in body.keys() and event_producer.name != body['name']:
            #if the tenant already has a profile with this name then abort
            duplicate_producer = tenant_util.find_event_producer(
                tenant,  producer_name=body['name'])
            if duplicate_producer:
                api.abort(
                    falcon.HTTP_400,
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

        #save the tenant document
        tenant_util.save_tenant(tenant)

        resp.status = falcon.HTTP_200

    @api.handle_api_exception(operation_name='Event Producer DELETE')
    def on_delete(self, req, resp, tenant_id, event_producer_id):
        """
        Delete a specified Event Producer from a Tenant's configuration
        when an HTTP DELETE is received
        """
        #verify the tenant exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists and belongs to the tenant
        event_producer = tenant_util.find_event_producer(
            tenant, producer_id=event_producer_id)
        if not event_producer:
            _producer_not_found()

        tenant_util.delete_event_producer(tenant, event_producer)

        resp.status = falcon.HTTP_200


class TokenResource(api.ApiResource):
    """
    The Token Resource manages Tokens for a tenant
    and provides validation operations.
    """

    @api.handle_api_exception(operation_name='Token HEAD')
    def on_head(self, req, resp, tenant_id):
        """
        Validates a token for a specified tenant
        when an HTTP HEAD call is received
        """

        #get message token, or abort if token is not in header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        #verify the tenant exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        if not tenant.token.validate_token(message_token):
            _message_token_is_invalid()

        resp.status = falcon.HTTP_200

    @api.handle_api_exception(operation_name='Token GET')
    def on_get(self, req, resp, tenant_id):
        """
        Retrieves Token information for a specified Tenant
        when an HTTP GET call is received
        """

        #verify the tenant exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = api.format_response_body({'token': tenant.token.format()})

    def _validate_token_min_time_limit_reached(self, token):
        """
        Tokens are giving a minimum time limit between resets.  This private
        method validates that the time limit has been reached.
        """
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

    @api.handle_api_exception(operation_name='Token POST')
    @falcon.before(get_validator('tenant'))
    def on_post(self, req, resp, tenant_id, validated_body):
        """
        This method resets a token when an HTTP POST is received.  There is
        a minimum time limit that must be reached before resetting a token,
        unless the call is made  with the "invalidate_now: true" option.
        """

        body = validated_body['token']

        #verify the tenant exists
        tenant = tenant_util.find_tenant(tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        invalidate_now = body['invalidate_now']

        if invalidate_now:
            #immediately invalidate the token
            tenant.token.reset_token_now()

        else:
            self._validate_token_min_time_limit_reached(tenant.token)
            tenant.token.reset_token()

        #save the tenant document
        tenant_util.save_tenant(tenant)

        resp.status = falcon.HTTP_203
        resp.set_header('Location', '/v1/{0}/token'.format(tenant_id))
