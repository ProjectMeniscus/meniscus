import falcon
import unittest
import json

from meniscus.api.coordinator.resources import *
from mock import MagicMock
from mock import patch


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerConfiguration())
    suite.addTest(WhenTestingWorkerRegistration())
    return suite


class TestingCoordinatorApiBase(unittest.TestCase):

    def setUp(self):
        self.db_handler = MagicMock()
        self.stream = MagicMock()
        self.req = MagicMock()
        self.resp = MagicMock()
        self.req.stream = self.stream

        self.db_handler.find_one.return_value = \
            {"worker_id": "51375fc4eea50d53066292b6",
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
        self.setResource()

    def setResource(self):
        pass


class WhenTestingVersionResource(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.resource = VersionResource()

    def test_should_return_200_on_get(self):
        self.resource.on_get(self.req, self.resp)
        self.assertEqual(falcon.HTTP_200, self.resp.status)

    def test_should_return_version_json(self):
        self.resource.on_get(self.req, self.resp)

        parsed_body = json.loads(self.resp.body)

        self.assertTrue('v1' in parsed_body)
        self.assertEqual('current', parsed_body['v1'])


class WhenTestingWorkerRegistration(TestingCoordinatorApiBase):

    def setResource(self):
        self.resource = WorkerRegistrationResource(self.db_handler)

    def test_should_return_203_on_post(self):
        self.stream.read.return_value = \
            u'{ "worker_registration": {\
                "hostname": "worker-04",\
                "callback": "172.22.15.25:8080/v1/configuration/",\
                "ip_address_v4": "172.23.1.100",\
                "ip_address_v6": "::1",\
                "personality": "worker.correlation",\
                "status": "new",\
                "system_info": [\
                    {\
                        "disk_gb": "20",\
                        "os_type": "Darwin-11.4.2-x86_64-i386-64bit",\
                        "memory_mb": "1024",\
                        "architecture": ""\
            }]}}'
        self.resource.on_post(self.req, self.resp)
        parsed_body = json.loads(self.resp.body)
        self.assertTrue('personality_module' in parsed_body.keys())
        self.assertTrue('worker_id' in parsed_body.keys())
        self.assertTrue('worker_token' in parsed_body.keys())
        self.assertEqual(falcon.HTTP_203, self.resp.status)

    def test_invalid_registration_return_401_on_get(self):
        self.stream.read.return_value = \
            u'{ "worker_monkey": {\
                "hostname": "worker-04",\
                "callback": "172.22.15.25:8080/v1/configuration/",\
                "ip_address_v4": "172.23.1.100",\
                "ip_address_v6": "::1",\
                "personality": "worker.correlation",\
                "status": "new",\
                "system_info": [\
                    {\
                        "disk_gb": "20",\
                        "os_type": "Darwin-11.4.2-x86_64-i386-64bit",\
                        "memory_mb": "1024",\
                        "architecture": ""\
            }]}}'
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_post(self.req, self.resp)

    def test_should_return_401_on_get(self):
        self.req.get_header.return_value = ''
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp)

    def test_should_return_403_on_get(self):
        self.req.get_header.return_value = ['role1', 'role2', 'role3']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp)

    def test_should_return_another_403_on_get(self):
        self.req.get_header.return_value = ['role1', 'role2', 'role3']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp)

    def test_should_return_200_on_get(self):
        self.req.get_header.return_value = ['role1', 'role2', 'meniscus_role',
                                            'role3']
        self.resource.on_get(self.req, self.resp)
        self.assertEqual(falcon.HTTP_200, self.resp.status)


class WhenTestingWorkerConfiguration(TestingCoordinatorApiBase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.db_handler = MagicMock()
        self.resource = WorkerConfigurationResource(self.db_handler)
        self.stream = MagicMock()
        self.req.stream = self.stream
        self.worker_id = MagicMock()
    # GET /v1/worker/8cc3b103-9b23-4e1c-afb1-8c5973621b55/configuration HTTP/1.1
    # ACCEPT: application/json
    # CONTENT-TYPE: application/json
    # WORKER-TOKEN: 94d6176b-9188-4409-8648-7374d0326e6b

    def test_should_return_error_401_personality_not_valid_on_get(self):
        self.req.get_header.return_value = ['ACCEPT',
                                            'CONTENT-TYPE',
                                            'WORKER-TOKEN']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp, self.worker_id)

    # def test_should_return_200_on_get(self):
    #     self.stream.read.return_value = u'"hostname": "worker-01", \
    #                 "ip_address_v4": "192.168.100.101",\
    #                 "ip_address_v6": "::1",\
    #                 "personality": "correlation|normalization|storage"'
    #     self.resource.on_get(self.req, self.resp, self.worker_id)
    #     self.assertEqual(falcon.HTTP_200, self.resp.status)

if __name__ == '__main__':
    unittest.main()
