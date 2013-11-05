import unittest

import falcon
import falcon.testing as testing
from mock import MagicMock, patch


from meniscus.api.status.resources import WorkerStatusResource
from meniscus.api.status.resources import WorkersStatusResource
from meniscus.data.model.worker import Worker
from meniscus.data.model.worker import SystemInfo
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerUpdateOnPut())

    return suite


class WhenTestingWorkerUpdateOnPut(testing.TestBase):
    def before(self):
        self.status = 'online'
        self.hostname = 'worker01'
        self.personality = 'worker'
        self.ip4 = "192.168.100.101",
        self.ip6 = "::1",
        self.system_info = SystemInfo().format()
        self.worker_status = {
            'worker_status': {
                'hostname': self.hostname,
                'system_info': self.system_info,
                'status': self.status
            }
        }

        self.bad_status = 'bad_status'
        self.bad_system_info = SystemInfo()
        self.bad_worker_status = {
            'worker_status': {
                'hostname': self.hostname,
                'system_info': self.system_info,
                'status': self.bad_status
            }
        }

        self.worker = Worker(**{"hostname": "worker01",
                                "ip_address_v4": "192.168.100.101",
                                "ip_address_v6": "::1",
                                "personality": "worker",
                                "status": "online",
                                "system_info": self.system_info})

        self.req = MagicMock()
        self.resp = MagicMock()
        self.resource = WorkerStatusResource()
        self.test_route = '/v1/worker/{hostname}/status'
        self.api.add_route(self.test_route, self.resource)

    def test_returns_400_body_validation(self):
        with patch('meniscus.data.model.worker_util.save_worker', MagicMock()):
            self.simulate_request(
                self.test_route,
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(self.bad_worker_status))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_202_for_new_worker_when_worker_not_found(self):
        create_worker = MagicMock()
        body_json = jsonutils.dumps({
            'worker_status': {
                self.worker.format()
            }})
        with patch('meniscus.data.model.worker_util.find_worker',
                   MagicMock(return_value=None),
                   'meniscus.data.model.worker_util.create_worker',
                   create_worker):

            self.simulate_request(
                self.test_route,
                method='PUT',
                headers={
                    'content-type': 'application/json'
                },
                body=body_json)
            self.assertEqual(falcon.HTTP_202, self.srmock.status)

    def test_returns_400_bad_worker_status(self):
        with patch('meniscus.data.model.worker_util.find_worker',
                   MagicMock(return_value=self.worker)):
            self.simulate_request(
                self.test_route,
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(self.bad_worker_status))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_when_load_average_is_negative_then_should_return_http_400(self):
        with patch('meniscus.data.model.worker_util.find_worker',
                   MagicMock(return_value=self.worker)):
            system_info = SystemInfo()
            system_info.load_average = {"1": -2, "15": -2, "5": -2}
            self.simulate_request(
                self.test_route,
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({
                    'worker_status': {
                        'hostname': self.hostname,
                        'system_info': system_info.format(),
                        'status': self.status
                    }
                }))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    # # TODO: fix this
    # def test_returns_200_worker_status(self):
    #     with patch('meniscus.data.model.worker_util.find_worker',
    #                MagicMock(return_value=self.worker)):
    #         self.simulate_request(
    #             self.test_route,
    #             method='PUT',
    #             headers={'content-type': 'application/json'},
    #             body=jsonutils.dumps(self.worker.get_status()))
    #         self.assertEqual(falcon.HTTP_200, self.srmock.status)


class WhenTestingWorkersStatus(unittest.TestCase):
    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.hostname = 'worker01'
        self.resource = WorkersStatusResource()
        self.worker = Worker(_id='010101',
                             hostname=self.hostname,
                             ip_address_v4='172.23.1.100',
                             ip_address_v6='::1',
                             personality='worker01',
                             status='online',
                             system_info={})

    def test_returns_200_on_get(self):
        with patch('meniscus.data.model.worker_util.retrieve_all_workers',
                   MagicMock(return_value=[self.worker])):
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
        self.hostname = 'worker01'
        self.resource = WorkerStatusResource()
        self.worker = Worker(_id='010101',
                             hostname=self.hostname,
                             ip_address_v4='172.23.1.100',
                             ip_address_v6='::1',
                             personality='worker01',
                             status='online',
                             system_info={})
        self.hostname = 'worker01'
        self.worker_not_found = None

    def test_raises_worker_not_found(self):
        with patch('meniscus.data.model.worker_util.find_worker',
                   MagicMock(return_value=None)):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.hostname)

    def test_returns_200_on_get(self):
        with patch('meniscus.data.model.worker_util.find_worker',
                   MagicMock(return_value=self.worker)):
            self.resource.on_get(self.req, self.resp, self.hostname)
            self.assertEquals(self.resp.status, falcon.HTTP_200)
            resp = jsonutils.loads(self.resp.body)
            status = resp['status']

            for key in resp.keys():
                self.assertTrue(key in self.worker.get_status().keys())


if __name__ == '__main__':
    unittest.main()
