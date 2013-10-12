"""
The ttl_tasks module is used for configuring time to live settings on the
default sink.  Time to live items
"""

from meniscus.data.datastore import datasource_handler, DEFAULT_SINK
from meniscus import env
from meniscus.queue import celery

_LOG = env.get_logger(__name__)

_db_handler = datasource_handler(DEFAULT_SINK)


@celery.task(acks_late=True, max_retries=None, ignore_result=True)
def create_index(tenant_id):
    """
    A celery task to create a new index on the default_sink, and then create
    a default mapping to enable time to live.  The task will retry any failed
    attempts to create the index and then call a task to create the mapping.
    """
    _db_handler.create_index(index=tenant_id)
    create_ttl_mapping.delay(tenant_id, "default")


@celery.task(acks_late=True, max_retries=None, ignore_result=True)
def create_ttl_mapping(tenant_id, producer_pattern):
    """
    A celery task to create a new mapping on a specified index
    that enables time to live.  The task will retry until successful.
    """
    _db_handler.put_ttl_mapping(doc_type=producer_pattern, index=tenant_id)
