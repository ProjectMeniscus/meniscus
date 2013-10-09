from meniscus.data.datastore import datasource_handler, DEFAULT_SINK
from meniscus import env
from meniscus.queue import celery

_LOG = env.get_logger(__name__)

_db_handler = datasource_handler(DEFAULT_SINK)


@celery.task(acks_late=True, max_retries=None, ignore_result=True)
def create_index(tenant_id):
    _db_handler.create_index(index=tenant_id)
    create_ttl_mapping.delay(tenant_id, "default")


@celery.task(acks_late=True, max_retries=None, ignore_result=True)
def create_ttl_mapping(tenant_id, producer_pattern):
    _db_handler.put_ttl_mapping(doc_type=producer_pattern, index=tenant_id)
