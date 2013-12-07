import httplib

import requests

from meniscus.correlation import errors
from meniscus.correlation import correlation_util as util
from meniscus.api.utils.request import http_request
from meniscus.data.cache_handler import TenantCache
from meniscus.data.cache_handler import TokenCache
from meniscus.data.model.tenant_util import load_tenant_from_dict
from meniscus.queue import celery
from meniscus import env


_LOG = env.get_logger(__name__)


def correlate_src_message(src_message):
    credentials = _extract_message_credentials(src_message)

    #validate the tenant and the message token
    _validate_tenant(credentials['tenant_id'], credentials['message_token'],
                     src_message)

    #TODO EXIT POINT add to method chain
    # cee_message = _convert_message_cee(src_message)
    # add_correlation_info_to_message(tenant, cee_message)
    #
    # return cee_message


def _extract_message_credentials(src_message):
    #remove meniscus tenant id and message token
    # from the syslog structured data
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

    return {'tenant_id': tenant_id, 'message_token': message_token}


def _validate_tenant(tenant_id, message_token, src_message):
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

            tenant = _get_tenant_from_coordinator(tenant_id,
                                                  message_token,
                                                  src_message)
    else:
        _validate_token_with_coordinator()

        #get tenant from coordinator
        tenant = _get_tenant_from_coordinator()
        token_cache.set_token(tenant_id, tenant.token)
        tenant_cache.set_tenant(tenant)

    return tenant


@celery.task()
def _validate_token_with_coordinator(tenant_id, message_token, src_message):
    """
    This method calls to the coordinator to validate the message token
    """

    config = util._get_config_from_cache()

    try:
        resp = http_request(util._build_request_uri(config.coordinator_uri,
                                                    tenant_id, True),
                            util._build_token_header(message_token,
                                                     config.hostname),
                            http_verb='HEAD')

    except requests.RequestException as ex:
        _LOG.exception(ex.message)
        raise _validate_token_with_coordinator.retry(ex=ex)

    if resp.status_code != httplib.OK:
        raise errors.MessageAuthenticationError(
            'Message not authenticated, check your tenant id '
            'and or message token for validity')

    return True


@celery.task()
def _get_tenant_from_coordinator(tenant_id, message_token, src_message):
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
        raise _get_tenant_from_coordinator.retry(ex=ex)

    if resp.status_code == httplib.OK:
        response_body = resp.json()
        tenant = load_tenant_from_dict(response_body['tenant'])
        util._save_tenant_and_token(tenant_id, tenant)
        #TODO continue with chain of methods

    elif resp.status_code == httplib.NOT_FOUND:
        message = 'unable to locate tenant.'
        _LOG.debug(message)
        raise errors.ResourceNotFoundError(message)
    else:
    #TODO not sure where the fall through is here
        raise errors.CoordinatorCommunicationError



