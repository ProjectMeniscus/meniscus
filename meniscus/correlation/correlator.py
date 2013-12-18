"""
This Module is a pipeline of correlation related methods used to validate
and format incoming messages:

Case 1 - Syslog: Entry point - correlate_src_syslog_message

    calls method to format syslog message to CEE
    before following the same pipeline as the HTTP entry point

Case 2 - HTTP: Entry point - correlate_src_http_message

    attempts to validate token from cache otherwise from coordinator

    if validated from cache, validate tenant from cache
    else validated from coordinator, get and save tenant from coordinator

    once validated correlate message and persist message to datasink
"""
#TODO: add normalization description

import httplib
import requests

from uuid import uuid4

from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.utils.request import http_request
from meniscus.correlation import errors
from meniscus.data import cache_handler
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant_util import find_event_producer
from meniscus.data.model.tenant_util import load_tenant_from_dict
from meniscus.openstack.common import timeutils
from meniscus.queue import celery
from meniscus.storage import dispatch
from meniscus import env
from meniscus.normalization import normalizer
_LOG = env.get_logger(__name__)


@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def correlate_syslog_message(message):
    """
    entry point for correlating syslog message processing
    """
    try:
        # get message credentials to identify and validate source of message
        _format_message_cee(message)

    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_syslog_message.retry()


@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def correlate_http_message(tenant_id, message_token, message):
    """
    entry point for correlating http message processing
    """
    try:
        #validate the tenant and the message token
        _validate_token_from_cache(tenant_id, message_token, message)

    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_http_message.retry()


def _format_message_cee(message):
    """
    extracts credentials from syslog message and formats to CEE
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

    # validate token
    _validate_token_from_cache(tenant_id, message_token, cee_message)


def _validate_token_from_cache(tenant_id, message_token, message):
    """
    validate token from cache:
    If token valid, get tenant from cache.
    If token invalid, validate token with coordinator
    """

    token_cache = cache_handler.TokenCache()
    token = token_cache.get_token(tenant_id)

    if token:
        #validate token
        if not token.validate_token(message_token):
            raise errors.MessageAuthenticationError(
                'Message not authenticated, check your tenant id '
                'and or message token for validity')

        # get tenant from cache
        _get_tenant_from_cache(tenant_id, message_token, message)
    else:
        # token not in cache, get it from coordinator
        _validate_token_with_coordinator(tenant_id, message_token, message)


def _get_tenant_from_cache(tenant_id, message_token, message):
    """
    get tenant from cache and then calls correlation or
    get tenant from coordinator
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
    call coordinator to validate the message token then get tenant
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
    _get_tenant_from_coordinator(tenant_id, message_token, message)


def _get_tenant_from_coordinator(tenant_id, message_token, message):
    """
    This method calls to the coordinator to retrieve tenant
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
        tenant = load_tenant_from_dict(response_body['tenant'])

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
    #match the producer by the message pname
    producer = find_event_producer(tenant, producer_name=message['pname'])

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

    # if durable, update correlation dict with new durable job id
    if producer.durable:
        durable_job_id = str(uuid4())
        correlation_dict.update({'job_id': durable_job_id})

    message['native'].pop('meniscus', None)
    message.update({'meniscus': {'tenant': tenant.tenant_id,
                                 'correlation': correlation_dict}})

    if normalizer.should_normalize(message):
        # send the message to normalization then to
        # the data dispatch
        normalizer.normalize_message.apply_async(
            (message,),
            link=dispatch.persist_message.subtask())
    else:
        dispatch.persist_message(message)
        # except Exception:
        # _LOG.exception('unable to place persist_message task on queue')


def _save_tenant_to_cache(tenant_id, tenant):
    #load caches
    tenant_cache = cache_handler.TenantCache()
    token_cache = cache_handler.TokenCache()

    #save token and tenant information to cache
    token_cache.set_token(tenant_id, tenant.token)
    tenant_cache.set_tenant(tenant)


def _get_config_from_cache():
    config_cache = cache_handler.ConfigCache()
    return config_cache.get_config()
