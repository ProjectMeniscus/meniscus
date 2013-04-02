import unittest

import falcon
from mock import MagicMock
from mock import patch

from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.coordinator.resources import WorkerConfigurationResource
from meniscus.data.model.worker import Worker
from meniscus.data.model.worker import WorkerRegistration
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerRegistrationOnPost())
    suite.addTest(WhenTestingWorkerRegistrationOnPut())
    suite.addTest(WhenTestingWorkerConfigurationOnGet())
    return suite


class WhenTestingWorkerRegistrationOnPost(unittest.TestCase):
    def setUp(self):

        self.db_handler = MagicMock()
        self.resource = WorkerRegistrationResource(self.db_handler)
        self.body = {'worker_registration':
                     WorkerRegistration('worker.correlation').format()}
        self.body_bad_personality = {'worker_registration':
                                     WorkerRegistration(
                                         'worker.bad_personality').format()}
        self.body_bad = {'worker_registration': 'bad_registration'}
        self.registration = jsonutils.dumps(
            {'worker_registration':
             WorkerRegistration('worker.correlation').format()})
        self.req = MagicMock()
        self.req.stream.read.return_value = self.registration
        self.resp = MagicMock()

    def test_req_body_validation(self):
        #body fails for bad format
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(self.body_bad)

        #body fails for bad personality
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(self.body_bad_personality)

        #body passes without error
        self.resource._validate_req_body_on_post(self.body)

    def test_returns_202_on_post(self):
        self.resource.on_post(self.req, self.resp)
        self.assertEquals(self.resp.status, falcon.HTTP_202)

        resp_body = jsonutils.loads(self.resp.body)
        self.assertTrue('personality_module' in resp_body)
        self.assertTrue('worker_id' in resp_body)
        self.assertTrue('worker_token' in resp_body)


class WhenTestingWorkerRegistrationOnPut(unittest.TestCase):
    def setUp(self):
        self.body = {'worker_status': 'online'}
        self.body_bad = {'not_status': 'bad_status'}
        self.status = jsonutils.dumps(self.body)
        self.req = MagicMock()
        self.req.stream.read.return_value = self.status
        self.resp = MagicMock()
        self.registration = WorkerRegistration('worker.correlation').format()
        self.worker_dict = Worker(**self.registration).format()
        self.worker_not_found = None
        self.db_handler = MagicMock()
        self.resource = WorkerRegistrationResource(self.db_handler)
        self.worker_id = '51375fc4eea50d53066292b6'

    def test_req_body_validation(self):
        #body fails for bad format
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_put(self.body_bad)

        #body passes without error
        self.resource._validate_req_body_on_put(self.body)

    def test_raises_worker_not_found(self):
        self.db_handler.find_one.return_value = self.worker_not_found
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_put(self.req, self.resp, self.worker_id)

    def test_returns_200_on_post(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.resource.on_put(self.req, self.resp, self.worker_id)
        self.assertEquals(self.resp.status, falcon.HTTP_200)


class WhenTestingWorkerConfigurationOnGet(unittest.TestCase):
    def setUp(self):

        self.req = MagicMock()
        self.resp = MagicMock()
        self.registration = WorkerRegistration('worker.correlation').format()
        self.worker_dict = Worker(**self.registration).format()
        self.worker_not_found = None
        self.db_handler = MagicMock()
        self.resource = WorkerConfigurationResource(self.db_handler)
        self.worker_id = '51375fc4eea50d53066292b6'
        downstream_setup = WorkerRegistration('worker.storage').format()
        self.downstream = [Worker(**downstream_setup).format(),
                           Worker(**downstream_setup).format(),
                           Worker(**downstream_setup).format()]

    def test_raises_worker_not_found(self):
        self.db_handler.find_one.return_value = self.worker_not_found
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp, self.worker_id)

    def test_should_return_200(self):
        self.db_handler.find_one.return_value = self.worker_dict
        self.db_handler.find.return_value = self.downstream
        self.resource.on_get(self.req, self.resp, self.worker_id)
        self.assertEquals(self.resp.status, falcon.HTTP_200)
        resp_body = jsonutils.loads(self.resp.body)
        pipeline = resp_body['pipeline_workers']
        for worker in pipeline:
            self.assertTrue('hostname' in worker)
            self.assertTrue('ip_address_v4' in worker)
            self.assertTrue('ip_address_v6' in worker)
            self.assertTrue('personality' in worker)

if __name__ == '__main__':
    unittest.main()