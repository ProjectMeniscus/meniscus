import httplib
from multiprocessing import Process
import threading

import requests

from oslo.config import cfg
from meniscus.api.utils.request import http_request
from meniscus.api.utils.retry import retry
from meniscus.api.utils import sys_assist
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.cache_handler import ConfigCache
from meniscus.openstack.common import jsonutils

# cache configuration options
_STATUS_UPDATE_GROUP = cfg.OptGroup(name='status_update',
                                    title='Status Update Settings')
get_config().register_group(_STATUS_UPDATE_GROUP)

_CACHE_OPTIONS = [
    cfg.IntOpt('load_ave_interval',
               default=60,
               help="""default time to update worker load average"""
               ),
    cfg.IntOpt('disk_usage_interval',
               default=300,
               help="""Default time to update work disk usage."""
               )
]

get_config().register_opts(_CACHE_OPTIONS, group=_STATUS_UPDATE_GROUP)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

LOAD_AVERAGE_INTERVAL = conf.status_update.load_ave_interval
DISK_USAGE_INTERVAL = conf.status_update.disk_usage_interval


class WorkerStatsPublisher(object):
    def __init__(self,):

        self.process = Process(
            target=self._send_stats)
        self.exit = False

    def run(self):
        self.process.start()

    def kill(self):
        self.process.terminate()

    def _send_stats(self):
        """
        register the worker with the coordinator with an online status
        """
        load_ave_interval = LOAD_AVERAGE_INTERVAL
        disk_usage_interval = DISK_USAGE_INTERVAL
        time_lapsed = 0
        event = threading.Event()

        while True:

            event.wait(load_ave_interval)
            time_lapsed += load_ave_interval

            cache = ConfigCache()
            config = cache.get_config()
            if config:
                token_header = {
                    "WORKER-ID": config.worker_id,
                    "WORKER-TOKEN": config.worker_token
                }

                request_uri = "{0}/worker/{1}/status".format(
                    config.coordinator_uri, config.worker_id)

                req_body = {'load_average': sys_assist.get_load_average()}

                if time_lapsed == disk_usage_interval:
                    time_lapsed = 0
                    req_body.update(
                        {'disk_usage': sys_assist.get_disk_usage()})

                try:
                    http_request(request_uri, token_header,
                                 jsonutils.dumps(req_body),
                                 http_verb='PUT')

                except requests.RequestException:
                    pass


#constants for retry methods
TRIES = 6
DELAY = 60
BACKOFF = 2


class WorkerStatusPublisher(object):
    def __init__(self, status):
        kwargs = {'status': status}

        self.process = Process(
            target=self._register_worker_online, kwargs=kwargs)

    def run(self):
        self.process.start()

    @retry(tries=TRIES, delay=DELAY, backoff=BACKOFF)
    def _register_worker_online(self, status):
        """
        register the worker with the coordinator with an online status
        """
        cache = ConfigCache()
        config = cache.get_config()

        token_header = {"WORKER-TOKEN": config.worker_token}

        request_uri = "{0}/worker/{1}/status".format(
            config.coordinator_uri, config.worker_id)

        status = {"worker_status": status}

        try:
            resp = http_request(request_uri, token_header,
                                jsonutils.dumps(status), http_verb='PUT')

        except requests.RequestException:
            return False

        if resp.status_code == httplib.OK:
            return True
