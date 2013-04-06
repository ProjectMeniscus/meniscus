import unittest

import falcon
from mock import MagicMock

from meniscus.api.status.resources import WorkerUpdateResource
from meniscus.api.status.resources import WorkerStatusResource
from meniscus.api.status.resources import WorkersStatusResource
from meniscus.data.model.worker import Worker
from meniscus.data.model.worker import WorkerRegistration
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerUpdateOnPut())

    return suite


class WhenTestingWorkerUpdateOnPut(unittest.TestCase):
    def setUp(self):
        self.body = {'worker_status': 'online'}
        self.body_disk = {
            "disk_usage": {
                "/dev/sda1": {
                    "total": 313764528,
                    "used": 112512436
                }
            }
        }
        self.body_load = {
            "load_average": {
                "1": 0.24755859375,
                "5": 1.0751953125,
                "15": 0.9365234375
            }
        }

        self.body_bad = {'not_status': 'bad_status'}
        self.status = jsonutils.dumps(self.body)
        self.disk = jsonutils.dumps(self.body_disk)
        self.load = jsonutils.dumps(self.body_load)
        self.status = jsonutils.dumps(self.body)
        self.req = MagicMock()
        self.resp = MagicMock()
        self.registration = WorkerRegistration('worker.correlation').format()
        self.worker_dict = Worker(**self.registration).format()
        self.worker_not_found = None
        self.db_handler = MagicMock()
        self.resource = WorkerUpdateResource(self.db_handler)
        self.worker_id = '51375fc4eea50d53066292b6'

    def test_req_body_validation(self):
        #body fails for bad format
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_put(self.body_bad)

        #body passes without error
        self.resource._validate_req_body_on_put(self.body)

    def test_raises_worker_not_found(self):
        self.req.stream.read.return_value = self.status
        self.db_handler.find_one.return_value = self.worker_not_found
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_put(self.req, self.resp, self.worker_id)

    def test_returns_200_worker_status(self):
        self.req.stream.read.return_value = self.status
        self.db_handler.find_one.return_value = self.worker_dict
        self.resource.on_put(self.req, self.resp, self.worker_id)
        self.assertEquals(self.resp.status, falcon.HTTP_200)

    def test_returns_200_disk_usage(self):
        self.req.stream.read.return_value = self.disk
        self.db_handler.find_one.return_value = self.worker_dict
        self.resource.on_put(self.req, self.resp, self.worker_id)
        self.assertEquals(self.resp.status, falcon.HTTP_200)

    def test_returns_200_load_average(self):
        self.req.stream.read.return_value = self.load
        self.db_handler.find_one.return_value = self.worker_dict
        self.resource.on_put(self.req, self.resp, self.worker_id)
        self.assertEquals(self.resp.status, falcon.HTTP_200)


class WhenTestingWorkersStatus(unittest.TestCase):
    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.db_handler = MagicMock()
        self.resource = WorkersStatusResource(self.db_handler)
        self.registration = WorkerRegistration('worker.correlation').format()
        self.worker = Worker(**self.registration)
        self.worker_dict = Worker(**self.registration).format()

    def test_returns_200_on_get(self):
        self.db_handler.find.return_value = [self.worker_dict]
        self.resource.on_get(self.req, self.resp)
        self.assertEquals(self.resp.status, falcon.HTTP_200)
        resp = jsonutils.loads(self.resp.body)
        status = resp['status'][0]

        for key in resp.keys():
            self.assertTrue(key in self.worker.get_status().keys())


class WhenTestingWorkerStatus(unittest.TestCase):
    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.db_handler = MagicMock()
        self.resource = WorkerStatusResource(self.db_handler)
        self.registration = WorkerRegistration('worker.correlation').format()
        self.worker = Worker(**self.registration)
        self.worker_dict = Worker(**self.registration).format()
        self.worker_id = '51375fc4eea50d53066292b6'
        self.worker_not_found = None

    def test_raises_worker_not_found(self):
        self.db_handler.find_one.return_value = self.worker_not_found
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp, self.worker_id)

    def test_returns_200_on_get(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.resource.on_get(self.req, self.resp, self.worker_id)
        self.assertEquals(self.resp.status, falcon.HTTP_200)
        resp = jsonutils.loads(self.resp.body)
        status = resp['status']

        for key in resp.keys():
            self.assertTrue(key in self.worker.get_status().keys())


if __name__ == '__main__':
    unittest.main()
