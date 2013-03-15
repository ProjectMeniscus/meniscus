import httplib
import requests

from meniscus.openstack.common import jsonutils
from meniscus.api.utils.request import http_request
from meniscus.api.utils.retry import retry
from meniscus.proxy import NativeProxy
from multiprocessing import Process


#constants for retry methods
TRIES = 6
DELAY = 60
BACKOFF = 2


class RegisterWorkerOnline(object):
    def __init__(self,):

        self.process = Process(
            target=self._register_worker_online)

    def run(self):
        self.process.start()

    @retry(tries=TRIES, delay=DELAY, backoff=BACKOFF)
    def _register_worker_online(self):
        """
        register the worker with the coordinator with an online status
        """
        cache = NativeProxy()
        config = jsonutils.loads(cache.cache_get('worker_configuration'))
        coordinator_uri = config['coordinator_uri']

        token_header = {"WORKER-TOKEN": config['worker_token']}

        request_uri = "{0}/worker/{1}/status".format(
            coordinator_uri, config['worker_id'])

        status = {"worker_status": "online"}

        try:
            resp = http_request(request_uri, token_header,
                                jsonutils.dumps(status), http_verb='PUT')
        except requests.ConnectionError:
            return False

        if resp.status_code == httplib.OK:
            return True
