import httplib

from multiprocessing import Process

import requests

from meniscus.api.utils.cache_params import CACHE_CONFIG
from meniscus.api.utils.cache_params import CONFIG_EXPIRES
from meniscus.api.utils.request import http_request
from meniscus.api.utils.retry import retry
from meniscus.data.model.worker import WorkerRegistration
from meniscus.openstack.common import jsonutils

from meniscus.proxy import NativeProxy


#constants for retry methods
TRIES = 6
DELAY = 60
BACKOFF = 2


class PairingProcess(object):
    def __init__(self, api_secret, coordinator_uri, personality):
        self._kwargs = {
            'api_secret': api_secret,
            'coordinator_uri': coordinator_uri,
            'personality': personality
        }
        self.process = Process(
            target=self._pair_with_coordinator, kwargs=self._kwargs)

    def run(self):
        self.process.start()

    def _pair_with_coordinator(self, api_secret, coordinator_uri, personality):

        #get registration info and call the coordinator
        worker_registration = WorkerRegistration(personality)
        registration = {'worker_registration': worker_registration.format()}

        auth_header = {'X-AUTH-TOKEN': api_secret}

        #register with coordinator
        if self._register_with_coordinator(
                coordinator_uri, personality, registration, auth_header):
            #if registered successfully, get worker routes and restart
            if self._get_worker_routes():
                server = NativeProxy()
                server.restart()

    @retry(tries=TRIES, delay=DELAY, backoff=BACKOFF)
    def _register_with_coordinator(
            self, coordinator_uri, personality, registration, auth_header):
        """
        register with the coordinator and persist the configuration to cache
        """
        try:
            resp = http_request(coordinator_uri + '/pairing', auth_header,
                                jsonutils.dumps(
                                    registration), http_verb='POST')
        except requests.ConnectionError:
            return False
        except requests.HTTPError:
            return False
        except requests.RequestException:
            return False

        if resp.status_code == httplib.ACCEPTED:
            config = resp.json()
            config.update({"personality": personality,
                           "coordinator_uri": coordinator_uri})

            cache = NativeProxy()
            cache.cache_set('worker_configuration',
                            jsonutils.dumps(config),
                            CONFIG_EXPIRES, CACHE_CONFIG)
            return True

    @retry(tries=TRIES, delay=DELAY, backoff=BACKOFF)
    def _get_worker_routes(self):
        """
        get the associated routes for the worker and store them in cache
        """
        cache = NativeProxy()
        config = jsonutils.loads(cache.cache_get('worker_configuration',
                                                 CACHE_CONFIG))
        coordinator_uri = config['coordinator_uri']

        token_header = {"WORKER-TOKEN": config['worker_token']}
        request_uri = "{0}/worker/{1}/configuration".format(
            coordinator_uri, config['worker_id'])

        try:
            resp = http_request(request_uri, token_header, http_verb='GET')

        except requests.RequestException:
            return False

        #if the coordinator issues a response, cache the worker routes
        #and return true
        if resp.status_code == httplib.OK:
            pipeline_workers = resp.json()

            cache = NativeProxy()
            cache.cache_set('pipeline_workers',
                            jsonutils.dumps(pipeline_workers),
                            CONFIG_EXPIRES, CACHE_CONFIG)
            return True
