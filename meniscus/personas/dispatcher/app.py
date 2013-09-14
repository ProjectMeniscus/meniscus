from datetime import timedelta
from multiprocessing import Process

import falcon

from meniscus.api.version.resources import VersionResource
from meniscus import env
from meniscus.personas.common import publish_stats
from meniscus.queue import celery
from meniscus.sinks import hdfs


_LOG = env.get_logger(__name__)


def start_up():

    application = api = falcon.API()
    api.add_route('/', VersionResource())

    celery.conf.CELERYBEAT_SCHEDULE = {
        'hdfs': {
            'task': 'hdfs.send',
            'schedule': timedelta(seconds=hdfs.FREQUENCY)
        },
        'worker_stats': {
            'task': 'stats.publish',
            'schedule': timedelta(seconds=publish_stats.WORKER_STATUS_INTERVAL)
        },
    }

    #include blank argument to celery in order for beat to start correctly
    celery_proc = Process(target=celery.worker_main, args=[['', '--beat']])
    celery_proc.start()
    _LOG.info(
        'Celery started as process: {}'.format(celery_proc.pid)
    )
    return application
