"""
This Module is a pipeline of correlation related methods used to validate and
format incoming messages. Entry points into the correlation pipeline have been
implemented as asynchronous tasks. This allows for failures due to network
communications or heavy load to be retried, and also allows for messages to be
persisted in case of a service restart.

There are 2 entry points into the pipeline, one for messages that are received
from a syslog parser, and another entry point for messages posted to the
http_log endpoint.

Case 1 - Syslog: Entry point - correlate_src_syslog_message

    calls method to format syslog message to CEE
    before following the same pipeline as the HTTP entry point

Case 2 - HTTP: Entry point - correlate_src_http_message

    Token Validation - messages contain a tenant_id and message token which
    are used to validate a message. Previously validated tokens are stored in
    a local cache for faster processing. Message validation is first attempted
    by looking up information in the local cache. If the cache does not contain
    the necessary information to validate the message, the the message
    validation is attempted by making http calls to the Tenant API hosted on
    the coordinator.

    Add Tenant Data to Message - After validating the message, configuration
    data from the tenant used for processing the message are added to the
    message dictionary

    Normalization or Storage - The data added to the message is used to decide
    whether the message should be queued for normalization or for storage.
"""

import httplib
import requests

from meniscus import env
from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.utils.request import http_request
from meniscus.correlation import errors
from meniscus.data import cache_handler
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model import tenant_util
from meniscus.normalization import normalizer
from meniscus.openstack.common import timeutils
from meniscus.queue import celery
from meniscus.storage import dispatch

_LOG = env.get_logger(__name__)


@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def correlate_syslog_message(message):
    """
    Entry point into correlation pipeline for messages received from the
    syslog parser after being converted to JSON. These messages must be
    converted into CEE format for processing.

    This entry point is implemented as a queued task. The parameters in the
    task decorator allow for the task to be retried indefinitely int he event
    of network failure (store & forward). Exceptions thrown from failed
    validation or a malformed message do not initiate a retry but instead
    allow the task to fail.
    """
    try:
        _format_message_cee(message)

    # Catch all CoordinationCommunicationErrors and retry the task.
    # All other Exceptions will fail the task.
    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_syslog_message.retry()


@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def correlate_http_message(tenant_id, message_token, message):
    """
    Entry point into correlation pipeline for messages received from the
    PublishMessage resource. These messages should already comply with CEE
    format as this is enforced when the message is posted to the endpoint.

    This entry point is implemented as a queued task. The parameters in the
    task decorator allow for the task to be retried indefinitely int he event
    of network failure (store & forward). Exceptions thrown from failed
    validation or a malformed message do not initiate a retry but instead allow
    the task to fail.
    """
    try:
        #enter the pipeline by beginning mesage validation
        _validate_token_from_cache(tenant_id, message_token, message)

    # Catch all CoordinationCommunicationErrors and retry the task.
    # All other Exceptions will fail the task.
    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_http_message.retry()


def _format_message_cee(message):
    """
    Format message as CEE and begin message validation. The incoming message
    originates a syslog message (RFC 5424) that has been received on the syslog
    endpoint and parsed into the following JSON format:

        {
            "PRIORITY": "{RFC 5424 PRI}",
            "VERSION": "{RFC 5424 VERSION}",
            "ISODATE": "{RFC 5424 TIMESTAMP}",
            "HOST": "{RFC 5424 HOSTNAME}",
            "PROGRAM": "{RFC 5424 APPNAME}",
            "PID": "{RFC 5424 PROCID}",
            "MSGID": "{RFC 5424 MSGID}",
            "SDATA": {
            "meniscus": {
            "tenant": "{tenantid}",
            "token": "{message-token}"
        },
            "any client_data": {}
        }
            "MESSAGE": "{RFC 5424 MSG}"
        }

        After conversion to CEE, the message will have the following format:

        {
            "pri": "{PRIORITY}",
            "ver": "{VERSION}",
            "time": "{ISODATE}",
            "host": "{HOST}",
            "pname": "{PROGRAM}",
            "pid": "{PID}",
            "msgid": "{MSGID}",
            "msg": "{MSG}",
            "native": "{_SDATA}"
        }
    """
    try:
        meniscus_sd = message['_SDATA']['meniscus']
        tenant_id = meniscus_sd['tenant']
        message_token = meniscus_sd['token']

    #if there is a key error then the syslog message did
    #not contain necessary credential information
    except KeyError:
        error_message = 'tenant_id or message token not provided'
        _LOG.debug('Message validation failed: {0}'.format(error_message))
        raise errors.MessageValidationError(error_message)

    # format to CEE
    cee_message = dict()

    cee_message['time'] = message.get('ISODATE', '-')
    cee_message['host'] = message.get('HOST', '-')
    cee_message['pname'] = message.get('PROGRAM', '-')
    cee_message['pri'] = message.get('PRIORITY', '-')
    cee_message['ver'] = message.get('VERSION', "1")
    cee_message['pid'] = message.get('PID', '-')
    cee_message['msgid'] = message.get('MSGID', '-')
    cee_message['msg'] = message.get('MESSAGE', '-')
    cee_message['native'] = message.get('_SDATA', {})

    #send the new cee_message to be validated
    _validate_token_from_cache(tenant_id, message_token, cee_message)


def _validate_token_from_cache(tenant_id, message_token, message):
    """
    validate token from cache:
        Attempt to validate the message against the local cache.
        If successful, send off to retrieve the tenant information.
        If the token does not exist in the cache, send off to validate with
        the coordinator.
    """

    token_cache = cache_handler.TokenCache()
    token = token_cache.get_token(tenant_id)

    if token:
        #validate token
        if not token.validate_token(message_token):
            raise errors.MessageAuthenticationError(
                'Message not authenticated, check your tenant id '
                'and or message token for validity')

        # hand off the message to retrieve tenant information
        _get_tenant_from_cache(tenant_id, message_token, message)
    else:
        # hand off the message to validate the token with the coordinator
        _validate_token_with_coordinator(tenant_id, message_token, message)


def _get_tenant_from_cache(tenant_id, message_token, message):
    """
    Retrieve tenant information from local cache. If tenant data exists in
    local cache, hand off message to be packed with correlation data. If the
    tenant data is not in cache, hand off message for tenant data to be
    retrieved from coordinator
    """
    tenant_cache = cache_handler.TenantCache()
    #get the tenant object from cache
    tenant = tenant_cache.get_tenant(tenant_id)

    if not tenant:
        _get_tenant_from_coordinator(tenant_id, message_token, message)
    else:
        _add_correlation_info_to_message(tenant, message)


def _validate_token_with_coordinator(tenant_id, message_token, message):
    """
    Call coordinator to validate the message token. If token is validated,
    persist the token in the local cache for future lookups, and hand off
    message to retrieve tenant information.
    """

    config = _get_config_from_cache()
    try:
        resp = http_request(
            '{0}/tenant/{1}/token'.format(config.coordinator_uri, tenant_id),
            {MESSAGE_TOKEN: message_token, 'hostname': config.hostname},
            http_verb='HEAD')

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise errors.CoordinatorCommunicationError

    if resp.status_code != httplib.OK:
        raise errors.MessageAuthenticationError(
            'Message not authenticated, check your tenant id '
            'and or message token for validity')

    # hand off the message to validate the tenant with the coordinator
    _get_tenant_from_coordinator(tenant_id, message_token, message)


def _get_tenant_from_coordinator(tenant_id, message_token, message):
    """
    This method retrieves tenant data from the coordinator, and persists the
    tenant data in the local cache for future lookups. The message is then
    handed off to be packed with correlation data.
    """

    config = _get_config_from_cache()

    try:
        resp = http_request(
            '{0}/tenant/{1}'.format(config.coordinator_uri, tenant_id),
            {MESSAGE_TOKEN: message_token, 'hostname': config.hostname},
            http_verb='GET')

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise errors.CoordinatorCommunicationError

    if resp.status_code == httplib.OK:
        response_body = resp.json()

        #load new tenant data from response body
        tenant = tenant_util.load_tenant_from_dict(response_body['tenant'])

        # update the cache with new tenant info
        _save_tenant_to_cache(tenant_id, tenant)

        # add correlation to message
        _add_correlation_info_to_message(tenant, message)

    elif resp.status_code == httplib.NOT_FOUND:
        error_message = 'unable to locate tenant.'
        _LOG.debug(error_message)
        raise errors.ResourceNotFoundError(error_message)
    else:
        #coordinator responds, but coordinator datasink could be unreachable
        raise errors.CoordinatorCommunicationError


def _add_correlation_info_to_message(tenant, message):
    """
    Pack the message with correlation data. The message will be update by
    adding a dictionary named "meniscus" that contains tenant specific
    information used in processing the message.
    """
    #match the producer by the message pname
    producer = tenant_util.find_event_producer(tenant,
                                               producer_name=message['pname'])

    #if the producer is not found, create a default producer
    if not producer:
        producer = EventProducer(_id=None, name="default", pattern="default")

    #create correlation dictionary
    correlation_dict = {
        'tenant_name': tenant.tenant_name,
        'ep_id': producer.get_id(),
        'pattern': producer.pattern,
        'durable': producer.durable,
        'encrypted': producer.encrypted,
        '@timestamp': timeutils.utcnow(),
        'sinks': producer.sinks,
        "destinations": dict()
    }

    #configure sink dispatch
    for sink in producer.sinks:
        correlation_dict["destinations"][sink] = {'transaction_id': None,
                                                  'transaction_time': None}

    # After successful correlation remove meniscus information from structured
    # data so that the client's token is scrubbed form the message.
    message['native'].pop('meniscus', None)
    message.update({'meniscus': {'tenant': tenant.tenant_id,
                                 'correlation': correlation_dict}})

    # If the message data indicates that the message has normalization rules
    # that apply, Queue the message for normalization processing
    if normalizer.should_normalize(message):
        #Todo: (stevendgonzales) Examine whether or not to remove
        #Todo: persist_message as a linked subtask(callback) of the
        #Todo: normalization task instead Queue the task based on routing
        #Todo: determined at the end of the normalization process.
        # send the message to normalization then to the data dispatch
        normalizer.normalize_message.apply_async(
            (message,),
            link=dispatch.persist_message.subtask())
    else:
        # Queue the message for indexing/storage
        dispatch.persist_message(message)


def _save_tenant_to_cache(tenant_id, tenant):
    """
    saves validated tenant and token to cache to reduce validation calls to the
    coordinator
    """
    tenant_cache = cache_handler.TenantCache()
    token_cache = cache_handler.TokenCache()

    #save token and tenant information to cache
    token_cache.set_token(tenant_id, tenant.token)
    tenant_cache.set_tenant(tenant)


def _get_config_from_cache():
    config_cache = cache_handler.ConfigCache()
    return config_cache.get_config()