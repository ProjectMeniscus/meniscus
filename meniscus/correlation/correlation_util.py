
from uuid import uuid4

from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.data.cache_handler import ConfigCache
from meniscus.data.cache_handler import TenantCache
from meniscus.data.cache_handler import TokenCache
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant_util import find_event_producer
from meniscus.openstack.common import timeutils


def _build_request_uri(coordinator_uri, tenant_id, token=None):
    if token:
        return "{0}/tenant/{1}/token".format(coordinator_uri, tenant_id)
    else:
        return "{0}/tenant/{1}".format(coordinator_uri, tenant_id)


def _build_token_header(message_token, hostname):
    return {MESSAGE_TOKEN: message_token, "hostname": hostname}


def _save_tenant_and_token(tenant_id, tenant):
    #load caches
    tenant_cache = TenantCache()
    token_cache = TokenCache()

    #save token and tenant information to cache
    token_cache.set_token(tenant_id, tenant.token)
    tenant_cache.set_tenant(tenant)


def _get_config_from_cache():
    config_cache = ConfigCache()
    return config_cache.get_config()


def _add_correlation_info_to_message(tenant, src_message):
    #match the producer by the message pname
    producer = find_event_producer(
        tenant, producer_name=src_message['pname'])

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
        correlation_dict["destinations"][sink] = {
            'transaction_id': None,
            'transaction_time': None
        }

    #todo(sgonzales) persist message and create job
    if producer.durable:
        durable_job_id = str(uuid4())
        correlation_dict.update({'job_id': durable_job_id})

    src_message.update({
        "meniscus": {
            "tenant": tenant.tenant_id,
            "correlation": correlation_dict
        }
    })

    return src_message


def _convert_message_cee(src_message):
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

    return cee_message