from celery import Celery

import meniscus.config as config
from oslo.config import cfg

# Celery configuration options
_CELERY_GROUP = cfg.OptGroup(name='celery', title='Celery Options')
config.get_config().register_group(_CELERY_GROUP)

_CELERY = [
    cfg.StrOpt('BROKER_URL',
               default="librabbitmq://guest@localhost//",
               help="""url to the broker behind celery"""
               ),
    cfg.IntOpt('CELERYD_CONCURRENCY',
               default=10,
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
except config.cfg.ConfigFilesNotFoundError:
    #TODO(sgonzales) Log config error
    pass

celery_conf = config.get_config().celery


celery = Celery('meniscus',
                broker='librabbitmq://guest@localhost//')

celery.conf.BROKER_URL = celery_conf.BROKER_URL
celery.conf.CELERYD_CONCURRENCY = celery_conf.CELERYD_CONCURRENCY
celery.conf.CELERY_DISABLE_RATE_LIMITS = celery_conf.CELERY_DISABLE_RATE_LIMITS
celery.conf.CELERY_TASK_SERIALIZER = celery_conf.CELERY_TASK_SERIALIZER
