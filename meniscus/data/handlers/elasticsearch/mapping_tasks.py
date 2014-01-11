"""
The mapping_tasks module is used for configuring elasticsearch indexes and
doc_types with field mappings using async tasks that retry on failure
"""

from meniscus.data.handlers import elasticsearch
from meniscus import env
from meniscus.queue import celery


_LOG = env.get_logger(__name__)

_es_handler = elasticsearch.get_handler()


@celery.task(acks_late=True, max_retries=None, ignore_result=True)
def create_index(tenant_id):
    """
    A celery task to create a new index in elasticsearch, and then create
    a default field mapping.  The task will retry any failed attempts to
    create the index
    """
    try:
        _es_handler.create_index(index=tenant_id, mapping=DEFAULT_MAPPING)
    except Exception as ex:
        _LOG.exception(ex.message)
        create_index.retry()


@celery.task(acks_late=True, max_retries=None, ignore_result=True)
def create_ttl_mapping(tenant_id, producer_pattern):
    """
    A celery task to create a new mapping on a specified index/doc_type
    that enables time to live.  The task will retry until successful.
    """
    try:
        _es_handler.put_mapping(
            index=tenant_id, doc_type=producer_pattern, mapping=TTL_MAPPING)
    except Exception as ex:
        _LOG.exception(ex.message)
        create_ttl_mapping.retry()


#the default ttl time for an index if one is not specified in the document
DEFAULT_TTL = 7776000000

#es mapping for enabling TTL
TTL_MAPPING = {
    "_ttl": {
        "enabled": True,
        "default": DEFAULT_TTL
    }
}

#default es mapping for log messages
DEFAULT_MAPPING = {
    "mappings": {
        "default": {
            "_ttl": {
                "enabled": True,
                "default": DEFAULT_TTL
            },
            "properties": {
                "host": {
                    "type": "string"
                },
                "meniscus": {
                    "properties": {
                        "correlation": {
                            "properties": {
                                "@timestamp": {
                                    "type": "date",
                                    "format": "dateOptionalTime"
                                },
                                "destinations": {
                                    "properties": {
                                        "elasticsearch": {
                                            "type": "object"
                                        }
                                    }
                                },
                                "durable": {
                                    "type": "boolean"
                                },
                                "encrypted": {
                                    "type": "boolean"
                                },
                                "pattern": {
                                    "type": "string"
                                },
                                "sinks": {
                                    "type": "string"
                                },
                                "tenant_name": {
                                    "type": "string"
                                }
                            }
                        },
                        "tenant": {
                            "type": "string"
                        }
                    }
                },
                "msg": {
                    "type": "string"
                },
                "msgid": {
                    "type": "string"
                },
                "pid": {
                    "type": "string"
                },
                "pname": {
                    "type": "string"
                },
                "pri": {
                    "type": "string"
                },
                "time": {
                    "type": "date",
                    "format": "dateOptionalTime"
                },
                "ver": {
                    "type": "string"
                }
            }
        }
    }
}
