from oslo.config import cfg
from meniscus.api.utils.request import http_request
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.cache_handler import ConfigCache
from meniscus.openstack.common import jsonutils
from meniscus.queue import celery
from meniscus.data.model.worker import SystemInfo
from meniscus import env


_LOG = env.get_logger(__name__)

# cache configuration options
_STATUS_UPDATE_GROUP = cfg.OptGroup(name='status_update',
                                    title='Status Update Settings')
get_config().register_group(_STATUS_UPDATE_GROUP)

_CACHE_OPTIONS = [
    cfg.IntOpt('worker_status_interval',
               default=60,
               help="""default time to update the worker status"""
               )
]

get_config().register_opts(_CACHE_OPTIONS, group=_STATUS_UPDATE_GROUP)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

WORKER_STATUS_INTERVAL = conf.status_update.worker_status_interval


@celery.task(name="stats.publish")
def publish_worker_stats():
    """
    Publishes worker stats to the Coordinator(s) at set times
    """
    try:
        cache = ConfigCache()
        config = cache.get_config()

        request_uri = "{0}/worker/{1}/status".format(
            config.coordinator_uri, config.hostname)

        req_body = {
            'worker_status': {
                'status': 'online',
                'system_info': SystemInfo().format()
            }
        }

        http_request(url=request_uri, json_payload=jsonutils.dumps(req_body),
                     http_verb='PUT')
    except Exception as ex:
        _LOG.info(ex.message)
