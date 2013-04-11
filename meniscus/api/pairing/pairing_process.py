import httplib

from multiprocessing import Process

import requests

from meniscus.api.utils.request import http_request
from meniscus.api.utils.retry import retry
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.data.model.worker import WorkerRegistration
from meniscus.data.cache_handler import ConfigCache
from meniscus.openstack.common import jsonutils
from meniscus.personas.common import routing
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
            resp = http_request(coordinator_uri + '/registration', auth_header,
                                jsonutils.dumps(
                                    registration), http_verb='POST')

        except requests.RequestException:
            return False

        if resp.status_code == httplib.ACCEPTED:
            body = resp.json()
            config = WorkerConfiguration(
                personality, body['personality_module'], body['worker_token'],
                body['worker_id'], coordinator_uri)

            config_cache = ConfigCache()
            config_cache.set_config(config)

            return True

    @retry(tries=TRIES, delay=DELAY, backoff=BACKOFF)
    def _get_worker_routes(self):
        """
        get the associated routes for the worker and store them in cache
        """
        return routing.get_routes_from_coordinator()
