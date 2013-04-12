import httplib
import unittest

from mock import MagicMock
from mock import patch
import requests

from meniscus.api import personalities
from meniscus.data.model.worker import WorkerConfiguration
import meniscus.personas.common.routing as routing


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingGetRoutesFromCoordinator())
    return suite


class WhenTestingGetRoutesFromCoordinator(unittest.TestCase):
    def setUp(self):
        super(WhenTestingGetRoutesFromCoordinator, )
        self.api_secret = "3F2504E0-4F89-11D3-9A0C-0305E82C3301"
        self.coordinator_uri = "http://localhost:8080/v1"
        self.personality = 'worker.normalization'
        self.native_proxy = MagicMock()
        self.get_config = WorkerConfiguration(
            personality='worker.pairing',
            personality_module='meniscus.personas.pairing.app',
            worker_token='token_id',
            worker_id='worker_id',
            coordinator_uri="192.168.1.1:8080/v1"
        )

        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)
        self.bad_request = MagicMock(side_effect=requests.RequestException)
        self.registration = dict()

    def test_should_return_true_for_get_worker_routes(self):
        self.resp.status_code = httplib.OK
        self.resp._content = """{
            "routes": [
                {
                    "service_domain": "correlation",
                    "targets": [
                        {
                            "worker_id":
                            "e773b64c-b28f-452a-bc3e-ba5a5d32f450",
                            "status": "ONLINE",
                            "ipv4_address": "127.0.0.1",
                            "ipv6_address": "::1"
                        },
                        {
                            "worker_id":
                            "2fcd200a-bb7f-4315-ae3e-6a6647d5e063",
                            "status": "ONLINE",
                            "ipv4_address": "127.0.0.1",
                            "ipv6_address": "::1"
                        },
                        {
                            "worker_id":
                            "9a21a842-3642-4ba5-8b3c-721b44d7931b",
                            "status": "ONLINE",
                            "ipv4_address": "127.0.0.1",
                            "ipv6_address": "::1"
                        },
                        {
                            "worker_id":
                            "27f96f4e-f6f1-4e98-8fc1-2c59fd6387bf",
                            "status": "OFFLINE",
                            "ipv4_address": "127.0.0.1",
                            "ipv6_address": "::1"
                        }
                    ]
                },
                {
                    "service_domain": "other",
                    "targets": []
                }
            ]
        }"""

        with patch.object(routing.ConfigCache, 'get_config',
                          return_value=self.get_config), patch(
                'meniscus.personas.common.routing.http_request',
                self.http_request), patch.object(
                routing.ConfigCache, 'set_config',) as set_config:

            self.assertTrue(routing.get_routes_from_coordinator())
            set_config.assert_called_once()

    def test_should_return_false_for_get_worker_routes(self):
        self.resp.status_code = httplib.OK
        self.resp._content = '{"fake": "json"}'

        with patch.object(routing.ConfigCache, 'get_config',
                          return_value=self.get_config), patch(
                'meniscus.personas.common.routing.'
                'http_request', self.bad_request), patch.object(
                routing.ConfigCache, 'set_config',) as set_config:

            self.assertFalse(routing.get_routes_from_coordinator())
            set_config.assert_called_once()


class WhenTestingRouter(unittest.TestCase):
    def setUp(self):
        self.config = WorkerConfiguration(
            personality='worker.pairing',
            personality_module='meniscus.personas.pairing.app',
            worker_token='token_id',
            worker_id='worker_id',
            coordinator_uri="192.168.1.1:8080/v1"
        )
        self.get_config = MagicMock(return_value=self.config)
        self.message = {
            "processid": "3071",
            "appname": "dhcpcd",
            "timestamp": "2013-04-05T15:51:18.607457-05:00",
            "hostname": "tohru",
            "priority": "30",
            "version": "1",
            "messageid": "-",
            "message": "wlan0: leased 10.6.173.172 for 3600 seconds\n",
            "sd": {
                "origin": {
                    "software": "rsyslogd",
                    "swVersion": "7.2.5",
                    "x-pid": "24592",
                    "x-info": "http://www.rsyslog.com"
                }
            }
        }
        self.targets = [
            {
                "worker_id": "e773b64c-b28f-452a-bc3e-ba5a5d32f450",
                "status": "ONLINE",
                "ipv4_address": "127.0.0.1",
                "ipv6_address": ""
            },
            {
                "worker_id": "2fcd200a-bb7f-4315-ae3e-6a6647d5e063",
                "status": "ONLINE",
                "ipv4_address": "127.0.0.1",
                "ipv6_address": ""
            },
            {
                "worker_id": "9a21a842-3642-4ba5-8b3c-721b44d7931b",
                "status": "ONLINE",
                "ipv4_address": "127.0.0.1",
                "ipv6_address": ""
            },
            {
                "worker_id": "27f96f4e-f6f1-4e98-8fc1-2c59fd6387bf",
                "status": "OFFLINE",
                "ipv4_address": "127.0.0.1",
                "ipv6_address": ""
            }]
        self.routes = [{"service_domain": "correlation",
                        "targets": self.targets}]
        self.get_routes = MagicMock(return_value=self.routes)
        self.blacklist_cache = MagicMock()
        self.dispatch = MagicMock()

    def test_get_service_domain(self):
        with patch.object(routing.ConfigCache, 'get_config', self.get_config):
            router = routing.Router()

        router._personality = personalities.CORRELATION
        next_service_domain = router._get_next_service_domain()
        self.assertEqual(next_service_domain, personalities.STORAGE)

        router._personality = personalities.NORMALIZATION
        next_service_domain = router._get_next_service_domain()
        self.assertEqual(next_service_domain, personalities.STORAGE)

        router._personality = personalities.STORAGE
        next_service_domain = router._get_next_service_domain()
        self.assertIsNone(next_service_domain)

    def test_get_route_targets(self):
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
                patch.object(routing.ConfigCache, 'get_routes',
                             self.get_routes):
            router = routing.Router()
            targets = router._get_route_targets('correlation')
            self.assertEqual(targets, self.targets)

            targets = router._get_route_targets('foo')
            self.assertIsNone(targets)

    def test_blacklist_worker(self):
        http_request = MagicMock()
        with patch.object(
                routing.ConfigCache, 'get_config', self.get_config), patch(
                'meniscus.personas.common.routing.http_request', http_request):
            router = routing.Router()
            router._blacklist_cache = self.blacklist_cache
            worker_id = '27f96f4e-f6f1-4e98-8fc1-2c59fd6387bf'
            service_domain = 'correlation'
            router._blacklist_worker(service_domain, worker_id)
        http_request.assert_called_once_with(
            "{0}/worker/{1}".format(self.config.coordinator_uri, worker_id),
            {
                "WORKER-ID": self.config.worker_id,
                "WORKER-TOKEN": self.config.worker_token
            },
            http_verb='PUT'
        )
        self.assertIsNone(router._active_worker_socket[service_domain])

    def test_blacklist_worker_except(self):
        http_request = MagicMock(side_effect=requests.RequestException)
        with patch.object(
                routing.ConfigCache, 'get_config', self.get_config), patch(
                'meniscus.personas.common.routing.http_request', http_request):
            router = routing.Router()
            router._blacklist_cache = self.blacklist_cache
            worker_id = '27f96f4e-f6f1-4e98-8fc1-2c59fd6387bf'
            service_domain = 'correlation'
            router._blacklist_worker(service_domain, worker_id)
        http_request.assert_called_once_with(
            "{0}/worker/{1}".format(self.config.coordinator_uri, worker_id),
            {
                "WORKER-ID": self.config.worker_id,
                "WORKER-TOKEN": self.config.worker_token
            },
            http_verb='PUT'
        )
        self.assertIsNone(router._active_worker_socket[service_domain])

    def test_get_worker_socket_returns_cached_socket(self):
        with patch.object(routing.ConfigCache, 'get_config', self.get_config):
            router = routing.Router()
            service_domain = 'correlation'
            cached_worker_socket = ('worker', 'socket')
            router._active_worker_socket[service_domain] = cached_worker_socket
            worker_socket = router._get_worker_socket(service_domain)
            self.assertEqual(cached_worker_socket, worker_socket)

    def test_get_worker_socket_returns_none(self):
        with patch.object(
                routing.ConfigCache, 'get_config',
                self.get_config), patch.object(
                routing.Router, '_get_route_targets',
                MagicMock(return_value=list())):
            router = routing.Router()
            service_domain = 'correlation'
            router._active_worker_socket[service_domain] = None
            self.assertIsNone(router._get_worker_socket(service_domain))

    def test_get_worker_socket_returns_ipv4_socket(self):
        sock = MagicMock()
        sock.connect = MagicMock()
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
                patch.object(routing.Router, '_get_route_targets',
                             MagicMock(return_value=self.targets)), \
                patch('meniscus.personas.common.routing.socket.socket',
                      MagicMock(return_value=sock)):
            router = routing.Router()
            service_domain = 'correlation'
            router._active_worker_socket[service_domain] = None
            self.assertTrue(router._get_worker_socket(service_domain))
            sock.connect.assert_called_once_with(('127.0.0.1', 9001))

    def test_get_worker_socket_returns_ipv6_socket(self):
        sock = MagicMock()
        sock.connect = MagicMock()
        self.targets[0]['ipv6_address'] = 'ff06::c3'
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
            patch.object(routing.Router, '_get_route_targets',
                         MagicMock(return_value=self.targets)), \
            patch('meniscus.personas.common.routing.socket.socket',
                  MagicMock(return_value=sock)):
            router = routing.Router()
            service_domain = 'correlation'
            router._active_worker_socket[service_domain] = None
            self.assertTrue(router._get_worker_socket(service_domain))
            sock.connect.assert_called_once_with(('ff06::c3', 9001, 0, 0))

    def test_get_worker_socket_throws_exception(self):
        sock = MagicMock()
        sock.connect = MagicMock(side_effect=routing.socket.error)
        blacklist = MagicMock()
        self.targets[0]['ipv6_address'] = 'ff06::c3'
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
            patch.object(routing.Router, '_get_route_targets',
                         MagicMock(return_value=self.targets)), \
            patch('meniscus.personas.common.routing.socket.socket',
                  MagicMock(return_value=sock)), \
                patch.object(routing.Router, '_blacklist_worker', blacklist):
            router = routing.Router()
            service_domain = 'correlation'
            router._active_worker_socket[service_domain] = None
            self.assertIsNone(router._get_worker_socket(service_domain))
            blacklist.assert_called()

    def test_route_message_calls_dispatch(self):
        dispatch_message = MagicMock()
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
                patch.object(routing.Router, '_get_next_service_domain',
                             MagicMock(return_value='storage')), \
                patch.object(routing.Router, '_get_worker_socket',
                             MagicMock(return_value=({'worker_id': 'some_id'},
                                                     'socket'))), \
                patch.object(routing.Dispatch, 'dispatch_message',
                             dispatch_message):
            router = routing.Router()
            router.route_message(self.message)
            dispatch_message.assert_called_with(self.message, 'socket')

    def test_route_message_throws_routing_exception(self):
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
            patch.object(routing.Router, '_get_next_service_domain',
                         MagicMock(return_value='storage')), \
            patch.object(routing.Router, '_get_worker_socket',
                         MagicMock(return_value=None)):
            with self.assertRaises(routing.RoutingException):
                router = routing.Router()
                router.route_message(self.message)

    def test_route_message_calls_blacklist_on_failure(self):
        dispatch_message = MagicMock(side_effect=routing.DispatchException)
        blacklist_worker = MagicMock()
        with patch.object(routing.ConfigCache, 'get_config',
                          self.get_config), \
            patch.object(routing.Router, '_get_next_service_domain',
                         MagicMock(return_value='storage')), \
            patch.object(routing.Router, '_get_worker_socket',
                         MagicMock(side_effect=[({'worker_id': 'some_id'},
                                                 'socket'), None])), \
            patch.object(routing.Router, '_blacklist_worker',
                         blacklist_worker), \
            patch.object(routing.Dispatch, 'dispatch_message',
                         dispatch_message):
            router = routing.Router()
            with self.assertRaises(routing.RoutingException):
                router.route_message(self.message)
                blacklist_worker.assert_called()


if __name__ == '__main__':
    unittest.main()
