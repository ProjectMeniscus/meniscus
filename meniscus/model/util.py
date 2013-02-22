from meniscus.model.tenant import Tenant, Host, HostProfile, EventProducer


def _empty_condition():
    raise NotImplementedError


def find_tenant(ds_handler, tenant_id):
    """
    Retrieves a dictionary describing a tenant object and its Hosts, Profiles,
    and eventProducers and maps them to a tenant object
    """

    # get the tenant dictionary form the data source
    tenant_dict = ds_handler.find_one('tenant', {'tenant_id': tenant_id})

    if not tenant_dict:
        return None

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

    #Create the parent tenant object
    tenant = Tenant(tenant_dict['tenant_id'], hosts, profiles, event_producers,
                    tenant_dict['_id'])

    return tenant


def find_host(tenant, host_id):
    for host in tenant.hosts:
        if host_id == host.get_id():
            return host

    return None


def find_host_profile(tenant, profile_id):
    for profile in tenant.profiles:
        if profile_id == profile.get_id():
            return profile

    return None


def find_event_producer(tenant, producer_id):
    for producer in tenant.event_producers:
        if producer_id == producer.get_id():
            return producer

    return None
