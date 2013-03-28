import httplib
import unittest

import requests
from mock import MagicMock
from mock import patch

import meniscus.personas.worker.register_online as register_online
from meniscus.api.utils.cache_params import CACHE_CONFIG
from meniscus.personas.worker.register_online import RegisterWorkerOnline


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingRegisterWorkerOnline())
    return suite


class WhenTestingRegisterWorkerOnline(unittest.TestCase):
    def setUp(self):
        self.register_online = RegisterWorkerOnline()
        self.native_proxy = MagicMock()
        self.cache_get = \
            u'{"coordinator_uri": "http://localhost:8080/v1", ' \
            u'"worker_token": "3F2504E0-4F89-11D3-9A0C-0305E82C3301", ' \
            u'"worker_id": "3F2504E0-4F89-11D3-9A0C-0305E82C3301"}'
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_process_start_on_run(self):
        with patch.object(register_online.Process, 'start') as start:
            self.register_online.run()
            start.assert_called_once()

    def test_register_worker_online_with_coordinator_return_true(self):
        self.resp.status_code = httplib.OK
        self.resp._content = '{"fake": "json"}'
        with patch.object(register_online.NativeProxy, 'cache_get',
                          return_value=self.cache_get) as cache_get:
            with patch('meniscus.personas.worker.register_online.'
                       'http_request', self.http_request):
                self.assertTrue(self.register_online._register_worker_online())
                cache_get.assert_called_once_with('worker_configuration',
                                                  CACHE_CONFIG)


if __name__ == '__main__':
    unittest.main()
