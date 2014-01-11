"""
The tenant_util module provides an abstraction of database operations used
with instances of the Tenant class and its member objects
"""

from meniscus.data.handlers import mongodb
from meniscus.data.handlers.elasticsearch import mapping_tasks
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import (
    load_tenant_from_dict, Tenant, Token)

_db_handler = mongodb.get_handler()


def find_tenant(tenant_id, create_on_missing=False):
    """
    Retrieves a dictionary describing a tenant object and its EventProducers
    and maps them to a tenant object.  If the "create_on_missing" param is set
    a new tenant will be created of the specified tenant is not found in the
    datastore
    """
    # get the tenant dictionary from the data source
    tenant = retrieve_tenant(tenant_id)

    if tenant is None:
    #if the create_on_missing parameter us set, create the new tenant,
    # then retrieve it from the data store and return
        if create_on_missing:
            create_tenant(tenant_id)
            tenant = retrieve_tenant(tenant_id)

    return tenant


def create_tenant(tenant_id, tenant_name=None):
    """
    Creates a new tenant and and persists to the datastore
    """
    #create new token for the tenant
    new_token = Token()
    new_tenant = Tenant(tenant_id, new_token, tenant_name=tenant_name)

    #save the new tenant to the datastore
    _db_handler.put('tenant', new_tenant.format())
    #create a new sequence for the tenant for creation of IDs on child objects
    _db_handler.create_sequence(new_tenant.tenant_id)

    #create an index for the tenant in the default sink
    # and enables time to live for the default doc_type
    mapping_tasks.create_index.delay(tenant_id)


def retrieve_tenant(tenant_id):
    """
    Retrieve the specified tenant form the datastore
    """
    tenant_dict = _db_handler.find_one('tenant', {'tenant_id': tenant_id})
    #return the tenant object
    if tenant_dict:
        return load_tenant_from_dict(tenant_dict)

    return None


def save_tenant(tenant):
    """
    Update an existing tenant in the datastore
    """
    _db_handler.update('tenant', tenant.format_for_save())


def create_event_producer(tenant, name, pattern, durable, encrypted, sinks):
    """
    Creates an Event Producer object, assigns it to a tenant, and updates the
    tenant in the datastore.
    """
    new_event_producer = EventProducer(
        _db_handler.next_sequence_value(tenant.tenant_id),
        name,
        pattern,
        durable,
        encrypted,
        sinks)
    #add the event_producer to the tenant
    tenant.event_producers.append(new_event_producer)
    #save the tenant's data
    save_tenant(tenant)

    #create a new mapping for the producer in the default
    # sink to enable time_to_live
    mapping_tasks.create_ttl_mapping.delay(
        tenant_id=tenant.tenant_id,
        producer_pattern=new_event_producer.pattern)

    #return the id of the newly created producer
    return new_event_producer.get_id()


def delete_event_producer(tenant, event_producer):
    """
    Removes a specified Event producer from the tenant object, and updates
    the tenant in the datastore
    """
    #remove any references to the event producer being deleted
    tenant.event_producers.remove(event_producer)
    #save the tenant document
    save_tenant(tenant)


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
