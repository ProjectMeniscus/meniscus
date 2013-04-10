
import unittest
from mock import MagicMock

import falcon

from meniscus.api.coordinator import coordinator_flow
from meniscus.api.coordinator import coordinator_exceptions as exception
from meniscus.data.model.worker import SystemInfo
from meniscus.data.model.worker import WorkerRegistration
from meniscus.data.model.worker import Worker


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingCoordinatorFlow())
    return suite


class WhenTestingCoordinatorFlow(unittest.TestCase):
    def setUp(self):
        self.db_handler = MagicMock()
        self.db_handler.return_value = MagicMock
        self.resource = coordinator_flow
        self.worker_id = "0123456789"
        self.req = MagicMock()
        self.resp = MagicMock()
        self.body_bad_header = {'worker':
                                WorkerRegistration('correlation').format()}
        self.body_bad_personality = {'worker_registration':
                                     WorkerRegistration(
                                         'bad_personality').format()}
        self.new_status = 'offline'
        self.new_bad_status = 'bad_status'
        self.system_info = SystemInfo()
        self.worker_dict = {'hostname': "worker-01",
                            "callback": "192.168.100.101:8080/v1/callback/",
                            "ip_address_v4": "192.168.100.101",
                            "ip_address_v6": "::1",
                            "personality": "worker.storage",
                            "status": "draining",
                            "system_info": {
                                "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                                "memory_mb": "1024",
                                "architecture": "",
                                "cpu_cores": "4",
                                "load_average": "0.234353456",
                                "disk_usage": {
                                    "/dev/sda1": {
                                        "total": 313764528,
                                        "used": 112512436
                                    }
                                }
                            }
                            }
        self.worker = Worker(_id='010101',
                             worker_id=self.worker_id,
                             worker_token='9876543210',
                             hostname='worker01',
                             callback='172.22.15.25:8080/v1/config/',
                             ip_address_v4='172.23.1.100',
                             ip_address_v6='::1',
                             personality='correlation',
                             status='new',
                             system_info=self.system_info.format())
        self.worker_list = [
            {"hostname": "worker-01",
             "callback": "192.168.100.101:8080/v1/callback/",
             "ip_address_v4": "192.168.100.101",
             "ip_address_v6": "::1",
             "personality": "storage",
             "status": "draining",
             "system_info": {
                 "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                 "memory_mb": "1024",
                 "architecture": "",
                 "cpu_cores": "4",
                 "load_average": "0.234353456",
                 "disk_usage": {
                     "/dev/sda1": {
                         "total": 313764528,
                         "used": 112512436
                     }}}},
            {"hostname": "worker-01",
             "callback": "192.168.100.101:8080/v1/callback/",
             "ip_address_v4": "192.168.100.101",
             "ip_address_v6": "::1",
             "personality": "storage",
             "status": "online",
             "system_info": {
                 "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                 "memory_mb": "1024",
                 "architecture": "",
                 "cpu_cores": "4",
                 "load_average": "0.234353456",
                 "disk_usage": {
                     "/dev/sda1": {
                         "total": 313764528,
                         "used": 112512436
                     }}}},
            {'hostname': "worker-01",
             "callback": "192.168.100.101:8080/v1/callback/",
             "ip_address_v4": "192.168.100.101",
             "ip_address_v6": "::1",
             "personality": "normalization",
             "status": "draining",
             "system_info": {
                 "os_type": "Darwin-11.4.2-x86_64-i386-64bit",
                 "memory_mb": "1024",
                 "architecture": "",
                 "cpu_cores": "4",
                 "load_average": "0.234353456",
                 "disk_usage": {
                     "/dev/sda1": {
                         "total": 313764528,
                         "used": 112512436
                     }}}}]

        self.resource.find_worker = MagicMock(return_value=self.worker)

    def test_req_body_validation(self):
        #body fails for bad format
        with self.assertRaises(falcon.HTTPError):
            self.resource.validate_worker_registration_req_body(
                self.body_bad_personality)

        #body success
        with self.assertRaises(falcon.HTTPError):
            self.resource.validate_worker_registration_req_body(
                self.body_bad_header)

    def test_add_worker(self):
        pass

    def test_find_worker(self):
        self.db_handler.find_one = MagicMock(return_value=self.worker.format())
        self.assertEqual(self.resource.find_worker(self.db_handler,
                                                   self.worker_id),
                         self.worker)

    # def test_find_worker_empty(self):
    #     self.db_handler.find_one = MagicMock(return_value=[])
    #     with self.assertRaises(falcon.HTTPError):
    #             self.resource.find_worker(self.db_handler, self.worker_id)

    def test_update_worker_status_fail(self):
        with self.assertRaises(falcon.HTTPError):
            self.resource.update_worker_status(self.db_handler,
                                               self.worker,
                                               self.new_bad_status)

    def test_update_worker_status_success(self):
        self.resource.update_worker_status(self.db_handler,
                                           self.worker,
                                           self.new_status)
        self.assertEquals(self.worker.status, self.new_status)

    def test_get_routes(self):
        self.db_handler.find = MagicMock(return_value=self.worker_list)
        routes = self.resource.get_routes(self.db_handler, self.worker_id)
        for route in routes['routes']:
            self.assertTrue('targets' in route)
            self.assertTrue('service_domain' in route)
            for worker in route['targets']:
                self.assertTrue('hostname' in worker)
                self.assertTrue('status' in worker)
                self.assertTrue('ip_address_v4' in worker)
                self.assertTrue('ip_address_v6' in worker)





