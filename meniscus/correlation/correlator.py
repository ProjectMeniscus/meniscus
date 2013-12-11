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

_LOG = env.get_logger(__name__)


@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def correlate_syslog_message(src_message):
    """
    entry point for correlating syslog message processing
    """
    try:
        # get message credentials to identify and validate source of message
        _format_message_cee(src_message)

    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_syslog_message.retry(ex=ex)



@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def correlate_http_message(tenant_id, message_token, src_message):
    """
    entry point for correlating http message processing
    """
    try:
        #validate the tenant and the message token
        _validate_token_from_cache(tenant_id, message_token, src_message)

    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_http_message.retry(ex=ex)


def _format_message_cee(src_message):
    """
    extracts credentials from syslog message and formats to CEE
    """
    try:
        meniscus_sd = src_message['_SDATA'].pop('meniscus')
        tenant_id = meniscus_sd['tenant']
        message_token = meniscus_sd['token']

    #if there is a key error then the syslog message did
    #not contain necessary credential information
    except KeyError:
        message = 'tenant_id or message token not provided'
        _LOG.debug('Message validation failed: {0}'.format(message))
        raise errors.MessageValidationError(message)

    # format to CEE
    cee_message = dict()

    cee_message['time'] = src_message.get('ISODATE', '-')
    cee_message['host'] = src_message.get('HOST', '-')
    cee_message['pname'] = src_message.get('PROGRAM', '-')
    cee_message['pri'] = src_message.get('PRIORITY', '-')
    cee_message['ver'] = src_message.get('VERSION', "1")
    cee_message['pid'] = src_message.get('PID', '-')
    cee_message['msgid'] = src_message.get('MSGID', '-')
    cee_message['msg'] = src_message.get('MESSAGE', '-')
    cee_message['native'] = src_message.get('sd')

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

        # get tenant
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
    call coordinator to validate the message token
    then get tenant
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

    #get tenant
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
        message = 'unable to locate tenant.'
        _LOG.debug(message)
        raise errors.ResourceNotFoundError(message)
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

    message.update({"meniscus": {"tenant": tenant.tenant_id,
                                 "correlation": correlation_dict}})

    dispatch.persist_message(message)

    #TODO: do something with this
    #
    # #if message is durable, return durable job info
    # if message['meniscus']['correlation']['durable']:
    #     durable_job_id = message['meniscus']['correlation']['job_id']
    #     job_status_uri = "http://{0}/v1/job/{1}/status" \
    #         .format("meniscus_uri", durable_job_id)
    #
    #     resp.status = falcon.HTTP_202
    #     resp.body = format_response_body(
    #         {
    #             "job_id": durable_job_id,
    #             "job_status_uri": job_status_uri
    #         }
    #     )


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
