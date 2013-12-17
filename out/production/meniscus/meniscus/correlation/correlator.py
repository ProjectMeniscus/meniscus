import httplib

import requests

from meniscus.correlation import errors
from meniscus.correlation import correlation_util as util
from meniscus.api.utils.request import http_request
from meniscus.data.cache_handler import TenantCache
from meniscus.data.cache_handler import TokenCache
from meniscus.data.model.tenant_util import load_tenant_from_dict
from meniscus.queue import celery
from meniscus.storage import dispatch
from meniscus import env


_LOG = env.get_logger(__name__)


@celery.task()
def correlate_src_syslog_message(src_message):
    """
    entry point for correlating syslog message processing
    """
    try:
        # get message credentials to identify and validate source of message
        _format_message_cee(src_message)

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise correlate_src_syslog_message.retry(ex=ex)
    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_src_http_message.retry(ex=ex)



@celery.task()
def correlate_src_http_message(tenant_id, message_token, src_message):
    """
    entry point for correlating http message processing
    """
    try:
        #validate the tenant and the message token
        _validate_token(tenant_id, message_token, src_message)

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise correlate_src_http_message.retry(ex=ex)
    except errors.CoordinatorCommunicationError as ex:
        _LOG.exception(ex.message)
        raise correlate_src_http_message.retry(ex=ex)


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
    _validate_token(tenant_id, message_token, cee_message)


def _validate_token(tenant_id, message_token, src_message):
    """
    returns a validated tenant object from cache or from coordinator
    """
    tenant_cache = TenantCache()
    token_cache = TokenCache()
    token = token_cache.get_token(tenant_id)

    if token:
        #validate token
        if not token.validate_token(message_token):
            raise errors.MessageAuthenticationError(
                'Message not authenticated, check your tenant id '
                'and or message token for validity')

        #get the tenant object from cache
        tenant = tenant_cache.get_tenant(tenant_id)

        #finish up with correlation
        util._add_correlation_info_to_message(tenant, src_message)

        #if tenant is not in cache, ask the coordinator
        if not tenant:
            get_tenant_from_coordinator(tenant_id, message_token, src_message)
    else:
        # token not in cache, get it from coordinator
        _validate_token_with_coordinator(tenant_id, message_token, src_message)


def _validate_token_with_cache(token, tenant_id, message_token, src_message):



@celery.task()
def _validate_token_with_coordinator(tenant_id, message_token, src_message):
    """
    This method calls to the coordinator to validate the message token
    """

    config = util._get_config_from_cache()

    try:
        resp = http_request(
            util._build_request_uri(config.coordinator_uri, tenant_id, True),
            util._build_token_header(message_token, config.hostname),
            http_verb='HEAD')

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise errors.CoordinatorCommunicationError

    if resp.status_code != httplib.OK:
        raise errors.MessageAuthenticationError(
            'Message not authenticated, check your tenant id '
            'and or message token for validity')

    #get tenant from coordinator
    get_tenant_from_coordinator(tenant_id, message_token, src_message)


def get_tenant_from_coordinator(tenant_id, message_token, src_message):
    """
    This method calls to the coordinator to retrieve tenant
    """

    config = util._get_config_from_cache()

    try:
        resp = http_request(util._build_request_uri(config.coordinator_uri,
                                                    tenant_id),
                            util._build_token_header(message_token,
                                                     config.hostname),
                            http_verb='GET')

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise errors.CoordinatorCommunicationError

    if resp.status_code == httplib.OK:
        response_body = resp.json()

        #load new tenant data from response body
        tenant = load_tenant_from_dict(response_body['tenant'])

        # save tenant data to cache
        util._save_tenant_and_token(tenant_id, tenant)

        # add correlation to message
        util._add_correlation_info_to_message(tenant, src_message)

    elif resp.status_code == httplib.NOT_FOUND:
        message = 'unable to locate tenant.'
        _LOG.debug(message)
        raise errors.ResourceNotFoundError(message)
    else:
        #coordinator responds, but coordinator datasink could be unreachable
        raise errors.CoordinatorCommunicationError
