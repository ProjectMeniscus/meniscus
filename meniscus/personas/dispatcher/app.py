from datetime import timedelta
from multiprocessing import Process

import falcon

from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher
from meniscus import env
from meniscus.queue import celery
from meniscus.sinks import hdfs

_LOG = env.get_logger(__name__)


def start_up():

    application = api = falcon.API()
    api.add_route('/', VersionResource())

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    celery.conf.CELERYBEAT_SCHEDULE = {
        'hdfs': {
            'task': 'hdfs.send',
            'schedule': timedelta(seconds=hdfs.FREQUENCY)
        },
    }

    #include blank argument to celery in order for beat to start correctly
    Process(target=celery.worker_main, args=[['', '--beat']]).start()
    return application
