import httplib
import threading
import unittest

import requests
from mock import MagicMock
from mock import patch

from meniscus.data.model.worker import WorkerConfiguration
from meniscus.personas.common.publish_stats import ConfigCache
import meniscus.personas.common.publish_stats as publish_stats
from meniscus.personas.common.publish_stats import WorkerStatsPublisher
from meniscus.personas.common.publish_stats import WorkerStatusPublisher


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerStatsPublisher())
    suite.addTest(WhenTestingWorkerStatusPublisher())
    return suite


class WhenTestingWorkerStatsPublisher(unittest.TestCase):
    def setUp(self):
        self.resource = WorkerStatsPublisher()
        self.conf = MagicMock()
        self.conf.status_update.load_ave_interval = 1
        self.conf.status_update.disk_usage_interval = 1
        self.get_config = MagicMock(return_value=self.conf)
        self.config = WorkerConfiguration(
            personality='worker.correlation',
            personality_module='meniscus.personas.worker.correlation.app',
            worker_id='fgc7104e-8d93-47dc-a49a-8fb0d39e5192',
            worker_token='bbd6307f-8d93-47dc-a49a-8fb0d39e5192',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_kill_terminates_sub_process(self):
        with patch.object(
                ConfigCache, 'get_config', self.get_config), patch(
                'meniscus.personas.common.publish_stats.http_request',
                self.http_request), patch(
                'meniscus.personas.common.publish_stats.get_config',
                self.get_config):
            self.resource.run()
            event = threading.Event()
            event.wait(1)
            self.assertTrue(self.resource.process.is_alive())
            self.resource.kill()
            event.wait(1)
            self.assertFalse(self.resource.process.is_alive())

    def test_http_request_called(self):
        with patch.object(
                ConfigCache, 'get_config', self.get_config), patch(
                'meniscus.personas.common.publish_stats.http_request',
                self.http_request), patch(
                'meniscus.personas.common.publish_stats.get_config',
                self.get_config):
            self.resource.run_once = True
            self.resource._send_stats(1, 1)
            self.http_request.assert_called_once()


class WhenTestingWorkerStatusPublisher(unittest.TestCase):
    def setUp(self):
        self.register_online = WorkerStatusPublisher('online')
        self.native_proxy = MagicMock()
        self.config = WorkerConfiguration(
            personality='worker.correlation',
            personality_module='meniscus.personas.worker.correlation.app',
            worker_id='fgc7104e-8d93-47dc-a49a-8fb0d39e5192',
            worker_token='bbd6307f-8d93-47dc-a49a-8fb0d39e5192',
            coordinator_uri='http://192.168.1.2/v1')
        self.get_config = MagicMock(return_value=self.config)
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_process_start_on_run(self):
        with patch.object(publish_stats.Process, 'start') as start:
            self.register_online.run()
            start.assert_called_once()

    def test_register_worker_online_with_coordinator_return_true(self):
        self.resp.status_code = httplib.OK
        self.resp._content = '{"fake": "json"}'
        with patch.object(ConfigCache, 'get_config', self.get_config):
            with patch('meniscus.personas.common.publish_stats.'
                       'http_request', self.http_request):
                self.assertTrue(
                    self.register_online._register_worker_online('online'))


if __name__ == '__main__':
    unittest.main()
