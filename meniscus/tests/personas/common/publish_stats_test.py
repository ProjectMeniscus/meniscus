import unittest

import requests
from mock import MagicMock
from mock import patch

from meniscus.openstack.common import jsonutils
from meniscus.personas.common.publish_stats import ConfigCache
from meniscus.personas.common.publish_stats import publish_worker_stats
from meniscus.data.model.worker import SystemInfo
from meniscus.data.model.worker import Worker
from meniscus.data.model.worker import WorkerConfiguration


def suite():

    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPublishStats())
    return suite


class WhenTestingPublishStats(unittest.TestCase):
    def setUp(self):
        self.conf = MagicMock()
        self.conf.status_update.worker_status_interval = 60
        self.get_config = MagicMock(return_value=self.conf)
        self.config = WorkerConfiguration(
            personality='worker',
            hostname='worker01',
            coordinator_uri='http://192.168.1.2/v1')
        self.system_info = SystemInfo().format()
        self.request_uri = "{0}/worker/{1}/status".format(
            self.config.coordinator_uri, self.config.hostname)

        self.worker_status = {
            'worker_status': Worker(personality='worker').format()
        }
        self.worker_status['worker_status']['system_info'] = self.system_info
        self.req_body = jsonutils.dumps(self.worker_status)

        self.get_config = MagicMock(return_value=self.config)
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_http_request_called(self):
        with patch.object(
                ConfigCache, 'get_config', self.get_config), patch(
                'meniscus.personas.common.publish_stats.http_request',
                self.http_request), patch(
                'meniscus.personas.common.publish_stats.get_config',
                self.get_config), patch.object(
                SystemInfo, 'format',
                MagicMock(return_value=self.system_info)):

            publish_worker_stats()

            self.http_request.assert_called_once_with(
                url=self.request_uri,
                json_payload=self.req_body,
                http_verb='PUT'
            )


if __name__ == '__main__':
    unittest.main()
