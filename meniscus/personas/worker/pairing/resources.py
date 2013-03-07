import falcon
import json
import platform
import socket
import sys

if sys.platform == 'win32':
    import win32_sysinfo as sysinfo
elif sys.platform == 'darwin':
    import mac_sysinfo as sysinfo
elif 'linux' in sys.platform:
    import linux_sysinfo as sysinfo

from meniscus.api.utils.ip_assist import get_lan_ip
from meniscus.api.utils.request import http_request
from meniscus.api.utils.retry import retry
from meniscus.api import ApiResource, load_body
from meniscus.proxy import NativeProxy


class VersionResource(ApiResource):
    """ Return the current version of the Pairing API """

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


class PairingConfigurationResource(ApiResource):
    """
    Webhook callback for the system package coordinator to
    configure the worker for pairing with its coordinator
    """

    def on_post(self, req, resp):
        body = load_body(req)

        api_secret = body['api_secret']
        coordinator_uri = body['coordinator_uri']
        personality = body['personality']

        resp.status = falcon.HTTP_200


def pair_with_coordinator(api_secret, coordinator_uri, personality):

    ip_address_v4 = get_lan_ip()
    #get registration info and call the coordinator
    registration = {
        "hostname": socket.gethostname(),
        "callback": ip_address_v4 + ':8080/v1/configuration',
        "ip_address_v4": ip_address_v4,
        "ip_address_v6": "",
        "personality":  personality,
        "status": "waiting",
        "system_info": {
            "disk_gb": "20",
            "os_type": platform.platform(),
            "memory_mb": sysinfo.memory_available(),
            "architecture": platform.machine()
        }
    }

    auth_header = {'X-AUTH-TOKEN': api_secret}
    #register with coordinator
    if register_with_coordinator(coordinator_uri, personality, registration,
                                 auth_header):
        #if registered successfully, get worker routes
        if get_worker_routes():
            server = NativeProxy()
            server.restart()


@retry(tries=6, delay=60, backoff=2)
def register_with_coordinator(coordinator_uri, personality, registration, auth_header):
    """
    register with the coordinator and persist the configuration to the cache
    """
    resp = http_request(coordinator_uri + '/pairing', auth_header,
                        json.dumps(registration), http_verb='POST')

    if resp.status_code == falcon.HTTP_203:
        config = resp.json()
        config.update({"personality": personality,
                       "coordinator_uri": coordinator_uri})

        cache = NativeProxy()
        cache.cache_set('worker_configuration', json.dumps(config))
        return True

@retry(tries=6, delay=60, backoff=2)
def get_worker_routes():
    cache = NativeProxy()
    config = json.loads(cache.cache_get('worker_configuration'))
    coordinator_uri = config['coordinator_uri']

    token_header = {"worker_token": config['worker_token']}
    request_uri = "{0}/worker/{1}/configuration".format(coordinator_uri,
                                                        config['worker_token'])
    resp = http_request(request_uri, token_header, http_verb='GET')

    if resp.status_code == falcon.HTTP_200:
        routes = resp.json()

        cache = NativeProxy()
        cache.cache_set('worker_routes', json.dumps(routes))
        return True
