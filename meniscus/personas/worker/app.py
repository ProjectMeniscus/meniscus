from multiprocessing import Process
from datetime import timedelta

import falcon
from portal.server import SyslogServer, start_io

from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.version.resources import VersionResource
from meniscus import config
from meniscus.api.correlation import syslog
from meniscus import env
from meniscus.personas.common import publish_stats
from meniscus.queue import celery


_LOG = env.get_logger(__name__)


def start_up():
    try:
        config.init_config()
    except config.cfg.ConfigFilesNotFoundError as ex:
        _LOG.exception(ex.message)

    conf = config.get_config()

    application = api = falcon.API()
    api.add_route('/', VersionResource())

    #http correlation endpoint
    api.add_route('/v1/tenant/{tenant_id}/publish', PublishMessageResource())

    #syslog correlation endpoint
    server = SyslogServer(
        ("0.0.0.0", 5140), syslog.MessageHandler(conf))
    server.start()

    syslog_server_proc = Process(target=start_io)
    syslog_server_proc.start()
    _LOG.info(
        'Syslog server started as process: {}'.format(syslog_server_proc.pid)
    )

    celery.conf.CELERYBEAT_SCHEDULE = {
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
