import unittest

import requests
from mock import MagicMock
from mock import patch

from meniscus.openstack.common import jsonutils
from meniscus.personas.common.publish_stats import ConfigCache
from meniscus.personas.common.publish_stats import publish_worker_stats
from meniscus.personas.common.publish_stats import SystemInfo
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
        self.system_info = SystemInfo()
        self.info_format = MagicMock(return_value=self.system_info.format())
        self.request_uri = "{0}/worker/{1}/status".format(
            self.config.coordinator_uri, self.config.hostname)
        self.req_body = jsonutils.dumps({
            'worker_status': {
                'status': 'online',
                'system_info': self.system_info.format()
            }
        })
        self.get_config = MagicMock(return_value=self.config)
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_http_request_called(self):
        with patch.object(
                ConfigCache, 'get_config', self.get_config), patch(
                'meniscus.personas.common.publish_stats.http_request',
                self.http_request), patch(
                'meniscus.personas.common.publish_stats.get_config',
                self.get_config),\
            patch.object(
                SystemInfo, 'format',
                self.info_format):
            publish_worker_stats()
            self.http_request.assert_called_once_with(
                url=self.request_uri,
                json_payload=self.req_body,
                http_verb='PUT'
            )


if __name__ == '__main__':
    unittest.main()
