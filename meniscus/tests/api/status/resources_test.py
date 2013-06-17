import unittest

import falcon
import falcon.testing as testing
from mock import MagicMock, patch

from meniscus.api.status.resources import WorkerStatusResource
from meniscus.api.status.resources import WorkersStatusResource
from meniscus.data.model.worker import Worker
from meniscus.data.model.worker import WorkerRegistration
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerUpdateOnPut())

    return suite


class WhenTestingWorkerUpdateOnPut(testing.TestBase):
    def before(self):
        self.body_status = {'status': 'online'}
        self.bad_status = {'status': 'not_a_real_status'}
        self.body_disk = {
            "disk_usage": [
                {
                    "device": "/dev/sda1",
                    "total": 313764528,
                    "used": 112512436
                }
            ]
        }
        self.disk_bad_val = {
            "disk_usage": [
                {
                    "device": "/dev/sda1",
                    "total": "313764528",
                    "used": 112512436
                }
            ]
        }
        self.disk_bad_keys = {
            "disk_usage": [
                {
                    "bad_key": "/dev/sda1",
                    "total": 313764528,
                    "used": 112512436
                }
            ]
        }
        self.body_load_ave = {
            "load_average": {
                "1": 0.24755859375,
                "5": 1.0751953125,
                "15": 0.9365234375
            }
        }
        self.bad_load_ave_val = {
            "load_average": {
                "1": "0.1234",
                "5": 1.0751953125,
                "15": 0.9365234375
            }
        }
        self.bad_load_ave_keys = {
            "load_average": {
                "bad_key": "0.1234",
                "5": 1.0751953125,
                "15": 0.9365234375
            }
        }

        self.body_bad = {'not_good': 'bad_status'}
        self.status = jsonutils.dumps(self.body_status)
        self.disk = jsonutils.dumps(self.body_disk)
        self.load = jsonutils.dumps(self.body_load_ave)
        self.req = MagicMock()
        self.resp = MagicMock()
        self.registration = WorkerRegistration('worker').format()
        self.worker_dict = Worker(**self.registration).format()
        self.worker_not_found = None
        self.db_handler = MagicMock()
        self.resource = WorkerStatusResource(self.db_handler)
        self.worker_id = '51375fc4eea50d53066292b6'
        self.test_route = '/v1/worker/{worker_id}/status'
        self.api.add_route(self.test_route, self.resource)

    def test_returns_400_body_validation(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.body_bad))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_raises_worker_not_found(self):
        self.db_handler.find_one.return_value = self.worker_not_found
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.body_status))
        self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_returns_400_bad_worker_status(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.bad_status))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_returns_200_worker_status(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.body_status))
        self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_returns_400_disk_usage_bad_keys(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.disk_bad_keys))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_returns_400_disk_usage_bad_value(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.disk_bad_val))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_returns_200_disk_usage(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.body_disk))
        self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_returns_400_load_average_bad_value(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.bad_load_ave_val))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_returns_400_load_average_bad_keys(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.bad_load_ave_keys))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_returns_200_load_average(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.simulate_request(
            self.test_route,
            method='PUT',
            headers={'content-type': 'application/json'},
            body=jsonutils.dumps(self.body_load_ave))
        self.assertEqual(falcon.HTTP_200, self.srmock.status)


class WhenTestingWorkersStatus(unittest.TestCase):
    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.db_handler = MagicMock()
        self.resource = WorkersStatusResource(self.db_handler)
        self.registration = WorkerRegistration('worker').format()
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
        self.registration = WorkerRegistration('worker').format()
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
