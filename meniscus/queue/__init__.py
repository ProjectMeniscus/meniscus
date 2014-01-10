from celery import Celery

from oslo.config import cfg

import meniscus.config as config
from meniscus import env


_LOG = env.get_logger(__name__)

# Celery configuration options
_CELERY_GROUP = cfg.OptGroup(name='celery', title='Celery Options')
config.get_config().register_group(_CELERY_GROUP)

_CELERY = [
    cfg.StrOpt('BROKER_URL',
               default="librabbitmq://guest@localhost//",
               help="""url to the broker behind celery"""
               ),
    cfg.IntOpt('CELERYD_CONCURRENCY',
               default=1,
               help="""Number of concurrent worker processes/threads"""
               ),
    cfg.BoolOpt('CELERY_DISABLE_RATE_LIMITS',
                default=True,
                help="""disable celery rate limit"""
                ),
    cfg.StrOpt('CELERY_TASK_SERIALIZER',
               default="json",
               help="""default serialization method to use"""
               )
]

config.get_config().register_opts(_CELERY, group=_CELERY_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)


celery_conf = config.get_config().celery


celery = Celery('meniscus', broker=celery_conf.BROKER_URL)

celery.conf.BROKER_URL = celery_conf.BROKER_URL
celery.conf.CELERYD_CONCURRENCY = celery_conf.CELERYD_CONCURRENCY
celery.conf.CELERY_DISABLE_RATE_LIMITS = celery_conf.CELERY_DISABLE_RATE_LIMITS
celery.conf.CELERY_TASK_SERIALIZER = celery_conf.CELERY_TASK_SERIALIZER
celery.conf.CELERYD_HIJACK_ROOT_LOGGER = False
