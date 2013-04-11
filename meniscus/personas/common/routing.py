import httplib

import requests

from meniscus.api.utils.request import http_request
from meniscus.data.cache_handler import ConfigCache


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
