import falcon
import unittest

from meniscus.api.coordinator.registration_resources \
    import WorkerRegistrationResource
from meniscus.openstack.common import jsonutils
from mock import MagicMock
from mock import patch


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerRegistration())
    return suite


class WhenTestingWorkerRegistration(unittest.TestCase):

    def setUp(self):
        self.db_handler = MagicMock()
        self.stream = MagicMock()
        self.req = MagicMock()
        self.resp = MagicMock()
        self.req.stream = self.stream
        self.resource = WorkerRegistrationResource(self.db_handler)
        self.worker_id = '8cc3b103-9b23-4e1c-afb1-8c5973621b55'
        self.registered_worker = u'{"worker_status": "online"}'
        self._update_worker = MagicMock()
        self.mongo_worker = MagicMock()
        self.registration_request = u'{ "worker_registration": {\
                "hostname": "worker-04",\
                "callback": "172.22.15.25:8080/v1/configuration/",\
                "ip_address_v4": "172.23.1.100",\
                "ip_address_v6": "::1",\
                "personality": "worker.correlation",\
                "status": "new",\
                "system_info": [{"disk_gb": "20", \
                    "os_type": "Darwin-11.4.2-x86_64-i386-64bit",\
                    "memory_mb": "1024", "architecture": "" }]}}'
        self.failed_registration_request = u'{ "worker_monkey": {\
                "hostname": "worker-04",\
                "callback": "172.22.15.25:8080/v1/configuration/",\
                "ip_address_v4": "172.23.1.100",\
                "ip_address_v6": "::1",\
                "personality": "worker.correlation",\
                "status": "new",\
                "system_info": [{ "disk_gb": "20",\
                      "os_type": "Darwin-11.4.2-x86_64-i386-64bit",\
                      "memory_mb": "1024", "architecture": ""}]}}'
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

        self.setResource()

    def setResource(self):
        pass

    def test_should_return_202_on_post(self):
        self.stream.read.return_value = self.registration_request
        self.resource.on_post(self.req, self.resp)
        parsed_body = jsonutils.loads(self.resp.body)
        self.assertTrue('personality_module' in parsed_body.keys())
        self.assertTrue('worker_id' in parsed_body.keys())
        self.assertTrue('worker_token' in parsed_body.keys())
        self.assertEqual(falcon.HTTP_202, self.resp.status)

    def test_invalid_registration_return_401_on_get(self):
        self.stream.read.return_value = self.failed_registration_request

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

    def test_validate_worker_body_should_return_400(self):
        body = {
            "worker_regis": {
                "hostname": "worker-04",
                "callback": "172.22.15.25:8080/v1/configuration/",
                "ip_address_v4": "172.23.1.100",
                "ip_address_v6": "::1",
                "personality": "worker.correlation",
                "status": "new",
            }
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_worker_body(body)

    def test_update_worker_should_call_find_one(self):
        self.req.stream.read.return_value = self.registered_worker
        self.db_handler.find_one = MagicMock()
        self.resource._update_worker(self.req, self.worker_id)
        self.db_handler.find_one.assert_called_once_with(
            'worker', {'worker_id': self.worker_id})

    def test_update_worker_should_call_update_worker(self):
        self.req.stream.read.return_value = self.registered_worker
        self.db_handler.update = MagicMock()
        self.resource._update_worker(self.req, self.worker_id)
        self.db_handler.update.assert_called()

    def test_return_200_on_put(self):
        self.req.stream.read.return_value = self.registered_worker
        with patch.object(WorkerRegistrationResource, '_update_worker'):
            self.resource.on_put(self.req, self.resp, self.worker_id)
            self.assertEqual(falcon.HTTP_200, self.resp.status)

if __name__ == '__main__':
    unittest.main()
