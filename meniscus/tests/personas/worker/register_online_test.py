import httplib
import unittest

import requests
from mock import MagicMock
from mock import patch

from meniscus.data.model.worker import WorkerConfiguration
from meniscus.personas.worker.register_online import ConfigCache
import meniscus.personas.worker.register_online as register_online
from meniscus.personas.worker.register_online import RegisterWorkerOnline


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingRegisterWorkerOnline())
    return suite


class WhenTestingRegisterWorkerOnline(unittest.TestCase):
    def setUp(self):
        self.register_online = RegisterWorkerOnline()
        self.native_proxy = MagicMock()
        self.config = WorkerConfiguration(
            personality='correlation',
            personality_module='meniscus.personas.worker.correlation.app',
            worker_id='fgc7104e-8d93-47dc-a49a-8fb0d39e5192',
            worker_token='bbd6307f-8d93-47dc-a49a-8fb0d39e5192',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_process_start_on_run(self):
        with patch.object(register_online.Process, 'start') as start:
            self.register_online.run()
            start.assert_called_once()

    def test_register_worker_online_with_coordinator_return_true(self):
        self.resp.status_code = httplib.OK
        self.resp._content = '{"fake": "json"}'
        with patch.object(ConfigCache, 'get_config', self.get_config):
            with patch('meniscus.personas.worker.register_online.'
                       'http_request', self.http_request):
                self.assertTrue(self.register_online._register_worker_online())


if __name__ == '__main__':
    unittest.main()
