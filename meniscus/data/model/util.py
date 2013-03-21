from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.openstack.common import jsonutils
from meniscus.personas.worker.cache_params import CACHE_TENANT
from meniscus.personas.worker.cache_params import CACHE_TOKEN
from meniscus.personas.worker.cache_params import DEFAULT_EXPIRES


def find_tenant(ds_handler, tenant_id):
    """
    Retrieves a dictionary describing a tenant object and its Hosts, Profiles,
    and eventProducers and maps them to a tenant object
    """

    # get the tenant dictionary form the data source
    tenant_dict = ds_handler.find_one('tenant', {'tenant_id': tenant_id})

    if tenant_dict:
        tenant = load_tenant_from_dict(tenant_dict)
        return tenant

    return None


def persist_tenant_to_cache(cache, tenant):
    tenant_id = tenant.get_id()

    if cache.cache_exists(tenant_id, CACHE_TENANT):
        cache.cache_update(
            tenant_id, jsonutils.dumps(tenant.format()),
            CACHE_TENANT, DEFAULT_EXPIRES)
    else:
        cache.cache_set(
            tenant_id, jsonutils.dumps(tenant.format()),
            CACHE_TENANT, DEFAULT_EXPIRES)


def find_tenant_in_cache(cache, tenant_id):
    """
    Retrieves a dictionary describing a tenant object and its Hosts, Profiles,
    and eventProducers and maps them to a tenant object
    """

    if cache.cache_exists(tenant_id, CACHE_TENANT):
        tenant_dict = jsonutils.loads(cache.cache_get(tenant_id, CACHE_TENANT))
        tenant = load_tenant_from_dict(tenant_dict)
        return tenant

    return None


def load_tenant_from_dict(tenant_dict):
    #Create a list of Host objects from the dictionary
    hosts = [Host(
        h['id'], h['hostname'], h['ip_address_v4'],
        h['ip_address_v6'], h['profile']) for h in tenant_dict['hosts']]

    #Create a list of Profile objects from the dictionary
    profiles = [HostProfile(p['id'], p['name'], p['event_producers'])
                for p in tenant_dict['profiles']]

    #Create a list of EventProducer objects from the dictionary
    event_producers = [EventProducer(
        e['id'], e['name'], e['pattern'], e['durable'], e['encrypted'])
        for e in tenant_dict['event_producers']]

    token = load_token_from_dict(tenant_dict['token'])

    #Create the parent tenant object
    tenant = Tenant(tenant_dict['tenant_id'], token, hosts, profiles,
                    event_producers, tenant_dict['_id'])

    #return tenant object
    return tenant


def persist_token_to_cache(cache, tenant_id, token):

    if cache.cache_exists(tenant_id, CACHE_TOKEN):
        cache.cache_update(
            tenant_id, jsonutils.dumps(token.format()),
            CACHE_TOKEN, DEFAULT_EXPIRES)
    else:
        cache.cache_set(
            tenant_id, jsonutils.dumps(token.format()),
            CACHE_TOKEN, DEFAULT_EXPIRES)


def find_token_in_cache(cache, tenant_id):
    if cache.cache_exists(tenant_id, CACHE_TOKEN):
        token_dict = jsonutils.loads(cache.cache_get(tenant_id, CACHE_TOKEN))
        token = load_token_from_dict(token_dict)
        return token
    return None


def load_token_from_dict(token_dict):
    token = Token(token_dict['valid'],
                  token_dict['previous'],
                  token_dict['last_changed'])
    return token


def find_host(tenant, host_id=None, host_name=None):
    """
    searches the given tenant for a host matching either the id or hostname
    """
    if host_id:
        host_id = int(host_id)
        for host in tenant.hosts:
            if host_id == host.get_id():
                return host
    if host_name:
        for host in tenant.hosts:
            if host_name == host.hostname:
                return host
    return None


def find_host_profile(tenant, profile_id=None, profile_name=None):
    """
    searches the given tenant for a profile matching either the id or name
    """
    if profile_id:
        profile_id = int(profile_id)
        for profile in tenant.profiles:
            if profile_id == profile.get_id():
                return profile
    if profile_name:
        for profile in tenant.profiles:
            if profile_name == profile.name:
                return profile

    return None


def find_event_producer(tenant, producer_id=None, producer_name=None):
    """
    searches the given tenant for a producer matching either the id or name
    """
    if producer_id:
        producer_id = int(producer_id)
        for producer in tenant.event_producers:
            if producer_id == producer.get_id():
                return producer

    if producer_name:
        for producer in tenant.event_producers:
            if producer_name == producer.name:
                return producer

    return None


def find_event_producer_for_host(tenant, host, producer_name):
    #if the host does not have a profile assigned, return None
    if not host.profile:
        return None

    #get the profile
    profile = find_host_profile(tenant, profile_id=host.profile)

    #if the profile does not have event producers assigned, return None
    if not profile.event_producers:
        return None

    ##find the producer by name
    producer = find_event_producer(tenant, producer_name=producer_name)

    #if the producer is not found, return None
    if not producer:
        return None

    if producer.get_id() in profile.event_producers:
        return producer

    return None
