import httplib
import unittest

from mock import MagicMock
from mock import patch
import requests

from meniscus.data.model.worker import WorkerConfiguration
import meniscus.personas.common.routing as routing


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingGetRoutesFromCoordinator())
    return suite


class WhenTestingGetRoutesFromCoordinator(unittest.TestCase):
    def setUp(self):
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

if __name__ == '__main__':
    unittest.main()
