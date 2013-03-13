import unittest
from mock import MagicMock
from meniscus.api.coordinator.configuration_resources import *


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerConfiguration())
    return suite


class WhenTestingWorkerConfiguration(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.db_handler = MagicMock()
        self.db_handler.find.return_value = [
            {
                "hostname": "worker-01",
                "ip_address_v4": "192.168.100.101",
                "ip_address_v6": "::1",
                "personality": "worker.normalization"},
            {
                "hostname": "worker-02",
                "ip_address_v4": "192.168.100.102",
                "ip_address_v6": "::1",
                "personality": "worker.normalization"
            },
            {
                "hostname": "worker-03",
                "ip_address_v4": "192.168.100.103",
                "ip_address_v6": "::1",
                "personality": "worker.normalization"
            }]

        self.resource = WorkerConfigurationResource(self.db_handler)
        self.stream = MagicMock()
        self.req.stream = self.stream
        self.worker_id = MagicMock()

    def test_should_return_error_401_personality_not_valid_on_get(self):
        self.req.get_header.return_value = ['ACCEPT',
                                            'CONTENT-TYPE',
                                            'WORKER-TOKEN']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp, self.worker_id)

    def test_should_return_200_on_get_correlation(self):
        self.db_handler.find_one.return_value = \
            {"_id": "ObjectId('513e43b6eea50d3e3eb82ccb')",
             "worker_id": "51375fc4eea50d53066292b6",
             "worker_token": "o234ks3453oi34",
             "hostname": "worker-04",
             "callback": "172.22.15.25:8080/v1/configuration/",
             "ip_address_v4": "172.23.1.100",
             "ip_address_v6": "::1",
             "personality": "worker.correlation",
             "status": "new",
             "system_info": [
                 {"disk_gb": "20",
                  "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                  "memory_mb": "1024",
                  "architecture": ""}]}
        self.resource.on_get(self.req, self.resp, self.worker_id)
        self.assertEqual(falcon.HTTP_200, self.resp.status)

    def test_should_return_200_on_get_normalization(self):
        self.db_handler.find_one.return_value = \
            {"_id": "ObjectId('513e43b6eea50d3e3eb82ccb')",
             "worker_id": "51375fc4eea50d53066292b6",
             "worker_token": "o234ks3453oi34",
             "hostname": "worker-04",
             "callback": "172.22.15.25:8080/v1/configuration/",
             "ip_address_v4": "172.23.1.100",
             "ip_address_v6": "::1",
             "personality": "worker.normalization",
             "status": "new",
             "system_info": [
                 {"disk_gb": "20",
                  "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                  "memory_mb": "1024",
                  "architecture": ""}]}
        self.resource.on_get(self.req, self.resp, self.worker_id)
        self.assertEqual(falcon.HTTP_200, self.resp.status)

    def test_should_return_200_on_get_storage(self):
        self.db_handler.find_one.return_value = \
            {"_id": "ObjectId('513e43b6eea50d3e3eb82ccb')",
             "worker_id": "51375fc4eea50d53066292b6",
             "worker_token": "o234ks3453oi34",
             "hostname": "worker-04",
             "callback": "172.22.15.25:8080/v1/configuration/",
             "ip_address_v4": "172.23.1.100",
             "ip_address_v6": "::1",
             "personality": "worker.storage",
             "status": "new",
             "system_info": [
                 {"disk_gb": "20",
                  "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                  "memory_mb": "1024",
                  "architecture": ""}]}
        self.resource.on_get(self.req, self.resp, self.worker_id)
        self.assertEqual(falcon.HTTP_200, self.resp.status)

    def test_should_abort_worker_not_found(self):
        self.db_handler.find_one.return_value = None
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp, self.worker_id)

if __name__ == '__main__':
    unittest.main()
