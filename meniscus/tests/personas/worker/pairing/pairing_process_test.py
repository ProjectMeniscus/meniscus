import httplib
from mock import MagicMock
from mock import patch
import requests
import unittest

from meniscus.personas.worker.cache_params import CACHE_CONFIG
from meniscus.personas.worker.pairing.pairing_process import PairingProcess
import meniscus.personas.worker.pairing.pairing_process as pairing_process


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPairingProcess())
    return suite


class WhenTestingPairingProcess(unittest.TestCase):
    def setUp(self):
        self.api_secret = "3F2504E0-4F89-11D3-9A0C-0305E82C3301"
        self.coordinator_uri = "http://localhost:8080/v1"
        self.personality = 'worker.normalization'
        self.pairing_process = PairingProcess(
            self.api_secret, self.coordinator_uri, self.personality)
        self.native_proxy = MagicMock()
        self.cache_get = \
            u'{"coordinator_uri": "http://localhost:8080/v1", ' \
            u'"worker_token": "3F2504E0-4F89-11D3-9A0C-0305E82C3301", ' \
            u'"worker_id": "3F2504E0-4F89-11D3-9A0C-0305E82C3301"}'

        self.resp = requests.Response()
        self.http_request = MagicMock(return_value=self.resp)
        self.registration = dict()

    def test_process_start_on_run(self):
        with patch.object(pairing_process.Process, 'start') as start:
            self.pairing_process.run()
            start.assert_called_once()

    def test_server_restart_pair_with_coordinator(self):
        sys_assist = MagicMock()
        sys_assist.get_lan_ip.return_value = "192.168.1.1"
        sys_assist.get_cpu_core_count.return_value = "4"
        sys_assist.get_disk_size_GB.return_value = "20"
        sys_assist.get_sys_mem_total_MB.return_value = "4090"
        with patch('meniscus.personas.worker.pairing.pairing_process.'
                   'sys_assist', sys_assist), \
                patch.object(pairing_process.NativeProxy, 'restart') \
                as server_restart, \
                patch.object(pairing_process.PairingProcess,
                             '_register_with_coordinator') as register, \
                patch.object(pairing_process.PairingProcess,
                             '_get_worker_routes') as routes:

                self.pairing_process._pair_with_coordinator(
                    self.api_secret, self.coordinator_uri, self.personality)

                server_restart.assert_called_once()
                register.assert_called_once()
                routes.assert_called_once()

    def test_should_return_true_for_register_with_coordinator(self):
        self.resp.status_code = httplib.NON_AUTHORITATIVE_INFORMATION
        self.resp._content = '{"fake": "json"}'
        with patch('meniscus.personas.worker.pairing.pairing_process.'
                   'http_request', self.http_request):
            self.assertTrue(
                self.pairing_process._register_with_coordinator(
                    self.coordinator_uri, self.personality,
                    self.registration, self.api_secret))

    def test_should_return_true_for_get_worker_routes(self):
        self.resp.status_code = httplib.OK
        self.resp._content = '{"fake": "json"}'
        with patch.object(pairing_process.NativeProxy, 'cache_get',
                          return_value=self.cache_get) as cache_get:
            with patch('meniscus.personas.worker.pairing.pairing_process.'
                       'http_request', self.http_request):
                self.assertTrue(self.pairing_process._get_worker_routes())
                cache_get.assert_called_once_with('worker_configuration',
                                                  CACHE_CONFIG)

if __name__ == '__main__':
    unittest.main()
