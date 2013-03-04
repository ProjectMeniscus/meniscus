from meniscus.api.coordinator.resources import WorkerConfigurationResource
from meniscus.api.coordinator.resources import WorkerRegistrationResource
from mock import MagicMock

import falcon
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WorkerConfigurationResource())
    suite.addTest(WorkerRegistrationResource())
    return suite


class WhenTestingWorkerRegistration(unittest.TestCase):

    def setUp(self):
        self.stream = MagicMock()
        self.resp = MagicMock()
        self.resource = WorkerRegistrationResource()
        self.req = MagicMock()
        self.req.stream = self.stream

    def test_should_return_202_on_get(self):
        self.stream.read.return_value = \
            u'{"event" : { "type": "worker.registration",\
            "callback": "192.168.100.101:8080/v1/configuration/"},\
            "worker": { "hostname" : "worker-n01",\
            "ip_address_v4": "192.168.100.101",\
            "ip_address_v6": "::1",\
            "personality": "correlation|normalization|storage",\
            "system_info": [{"disk_gb" : "20",\
                            "os_type" : "Darwin-11.4.2-x86_64-i386-64bit",\
                            "memory_mb" : "1024",\
                            "architecture" : ""}]}}'
        self.resource.on_post(self.req, self.resp)
        self.assertEqual(falcon.HTTP_202, self.resp.status)

    def test_invalid_event_type_return_401_on_get(self):
        self.stream.read.return_value = \
            u'{"event" : { "type": "worker.monkey",\
            "callback": "192.168.100.101:8080/v1/configuration/"},\
            "worker": { "hostname" : "worker-n01",\
            "ip_address_v4": "192.168.100.101",\
            "ip_address_v6": "::1",\
            "personality": "correlation|normalization|storage",\
            "system_info": [{"disk_gb" : "20",\
                            "os_type" : "Darwin-11.4.2-x86_64-i386-64bit",\
                            "memory_mb" : "1024",\
                            "architecture" : ""}]}}'
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_post(self.req, self.resp)


class WhenTestingWorkerConfigurationResource(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.resource = WorkerConfigurationResource()

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

if __name__ == '__main__':
    unittest.main()
