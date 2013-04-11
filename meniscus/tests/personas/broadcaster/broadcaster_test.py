from time import sleep
import unittest

import requests

from mock import MagicMock
from mock import patch

from meniscus.personas.broadcaster.broadcaster_process import BroadcastCache
from meniscus.personas.broadcaster.broadcaster_process \
    import BroadcasterProcess


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingBroadcasterProcess())
    return suite


class WhenTestingBroadcasterProcess(unittest.TestCase):
    def setUp(self):
        self.resource = BroadcasterProcess()
        self.conf = MagicMock()
        self.conf.broadcast_settings.broadcast_message_interval = 1
        self.target_list = [
            'http://hostname1.domain:8080/callback',
            'http://hostname2.domain:8080/callback',
            'http://hostname3.domain:8080/callback',
            'http://hostname4.domain:8080/callback'
        ]
        self.get_targets = MagicMock(return_value=self.target_list)
        self.delete_message = MagicMock()
        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)

    def test_kill_terminates_sub_process(self):
        with patch.object(
                BroadcastCache, 'get_targets', self.get_targets), patch(
                    'meniscus.personas.broadcaster.broadcaster_process.'
                    'http_request',
                    self.http_request):
            self.resource.run()
            sleep(1)
            self.assertTrue(self.resource.process.is_alive())
            self.resource.kill()
            sleep(1)
            self.assertFalse(self.resource.process.is_alive())

    def test_http_request_called(self):
        with patch.object(
                BroadcastCache, 'get_targets', self.get_targets), patch(
                'meniscus.personas.broadcaster.broadcaster_process.'
                'http_request',
                self.http_request), patch.object(
                    BroadcastCache, 'delete_message', self.delete_message):
            self.resource.run_once = True
            self.resource._broadcast_route_messages(1)
            self.http_request.assert_called_once()
            self.delete_message.assert_called_once_with('ROUTES')


if __name__ == '__main__':
    unittest.main()
