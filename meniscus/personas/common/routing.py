import httplib
import socket

import requests

from meniscus.api import personalities
from meniscus.api.utils.request import http_request
from meniscus.data.cache_handler import BlacklistCache
from meniscus.data.cache_handler import ConfigCache
from meniscus.personas.common.dispatch import Dispatch, DispatchException


def get_routes_from_coordinator():
    """
    get the associated routes for the worker and store them in cache
    """
    config_cache = ConfigCache()

    config = config_cache.get_config()

    token_header = {"WORKER-ID": config.worker_id,
                    "WORKER-TOKEN": config.worker_token}
    request_uri = "{0}/worker/{1}/routes".format(
        config.coordinator_uri, config.worker_id)

    try:
        resp = http_request(request_uri, token_header, http_verb='GET')

    except requests.RequestException:
        return False

    #if the coordinator issues a response, cache the worker routes
    #and return true
    if resp.status_code == httplib.OK:
        routes = resp.json()['routes']

        config_cache.set_routes(routes)

        return True


class RoutingException(Exception):
    """Raised when router is unable to forward message."""
    pass


class Router(object):
    def __init__(self):
        self._config_cache = ConfigCache()
        self._blacklist_cache = BlacklistCache()
        self._personality = self._config_cache.get_config().personality
        self._active_worker_socket = dict()
        self._dispatch = Dispatch()

    def _get_next_service_domain(self):
        if self._personality == personalities.CORRELATION:
            return personalities.STORAGE
        if self._personality == personalities.NORMALIZATION:
            return personalities.STORAGE
        return None

    def _get_route_targets(self, service_domain):
        routes = self._config_cache.get_routes()
        for domain in routes:
            if domain['service_domain'] == service_domain:
                return domain['targets']
        return None

    def _blacklist_worker(self, service_domain, worker_id):
        self._active_worker_socket[service_domain] = None
        self._blacklist_cache.add_blacklist_worker(worker_id)

        config = self._config_cache.get_config()
        if config:
            token_header = {
                "WORKER-ID": config.worker_id,
                "WORKER-TOKEN": config.worker_token
            }

            request_uri = "{0}/worker/{1}".format(
                config.coordinator_uri, worker_id)

            try:
                http_request(request_uri, token_header, http_verb='PUT')

            except requests.RequestException:
                #Todo log failure to contact coordinator
                pass

    def _get_worker_socket(self, service_domain):
        worker_socket = self._active_worker_socket.get(service_domain)
        if worker_socket:
            return worker_socket

        for worker in self._get_route_targets(service_domain):
            if not self._blacklist_cache.is_worker_blacklisted(
                    worker['worker_id']):

                if worker['ipv6_address']:
                    protocol = socket.AF_INET6
                    address = (worker['ipv6_address'], 9001, 0, 0)
                else:
                    protocol = socket.AF_INET
                    address = (worker['ipv4_address'], 9001)

                sock = socket.socket(protocol, socket.SOCK_STREAM)
                print sock
                try:
                    sock.connect(address)
                    worker_socket = (worker, sock)
                    self._active_worker_socket[service_domain] = worker_socket
                    return worker_socket
                except socket.error as ex:
                    self._blacklist_worker(
                        service_domain, worker['worker_id'])
        return None

    def route_message(self, message):
        next_service_domain = self._get_next_service_domain()
        worker_socket = self._get_worker_socket(next_service_domain)
        while worker_socket:
            worker, sock = worker_socket
            try:
                self._dispatch.dispatch_message(message, sock)
                return
            except DispatchException:
                #TODO(dmend) log this and report to coordinator
                self._blacklist_worker(next_service_domain,
                                       worker['worker_id'])
            worker_socket = self._get_worker_socket(next_service_domain)
        raise RoutingException()
