from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token


def find_tenant(ds_handler, tenant_id, create_on_missing=False):
    """
    Retrieves a dictionary describing a tenant object and its Hosts, Profiles,
    and eventProducers and maps them to a tenant object
    """
    # get the tenant dictionary form the data source
    tenant_dict = ds_handler.find_one('tenant', {'tenant_id': tenant_id})

    if tenant_dict:
        tenant = load_tenant_from_dict(tenant_dict)
        return tenant

    if create_on_missing:
        #create new token for the tenant
        new_token = Token()
        new_tenant = Tenant(tenant_id, new_token)

        ds_handler.put('tenant', new_tenant.format())
        ds_handler.create_sequence(new_tenant.tenant_id)

        tenant_dict = ds_handler.find_one('tenant', {'tenant_id': tenant_id})

        tenant = load_tenant_from_dict(tenant_dict)
        return tenant

    return None


def load_tenant_from_dict(tenant_dict):
    #Create a list of EventProducer objects from the dictionary
    event_producers = [EventProducer(
        e['id'], e['name'], e['pattern'],
        e['durable'], e['encrypted'], e['sinks'])

        for e in tenant_dict['event_producers']]

    token = load_token_from_dict(tenant_dict['token'])

    _id = None
    if "_id" in tenant_dict.keys():
        _id = tenant_dict['_id']

    #Create the parent tenant object
    tenant = Tenant(tenant_dict['tenant_id'], token,
                    event_producers=event_producers,
                    _id=_id, tenant_name=tenant_dict['tenant_name'])

    #Return tenant object
    return tenant


def load_token_from_dict(token_dict):
    token = Token(token_dict['valid'],
                  token_dict['previous'],
                  token_dict['last_changed'])
    return token


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
