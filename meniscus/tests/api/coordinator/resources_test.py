import unittest

import falcon
import falcon.testing as testing
from mock import MagicMock

from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.data.model.worker import WorkerRegistration
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerRegistrationOnPost())
    return suite


class WhenTestingWorkerRegistrationOnPost(testing.TestBase):

    def before(self):

        self.db_handler = MagicMock()
        self.resource = WorkerRegistrationResource(self.db_handler)
        self.body = {'worker_registration':
                     WorkerRegistration('worker').format()}
        self.body_bad_personality = {'worker_registration':
                                     WorkerRegistration(
                                         'bad_personality').format()}
        self.body_bad = {'worker_registration': 'bad_registration'}
        self.registration = jsonutils.dumps(
            {'worker_registration':
             WorkerRegistration('worker').format()})
        self.req = MagicMock()
        self.req.content_type = 'application/json'
        self.req.stream.read.return_value = self.registration
        self.resp = MagicMock()
        self.test_route = '/v1/pairing'
        self.api.add_route(self.test_route, self.resource)

    def test_returns_400_for_bad_personality(self):
        self.simulate_request(
            self.test_route,
            method='POST',
            headers={
                'content-type': 'application/json',
            },
            body=jsonutils.dumps(self.body_bad_personality))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_returns_415_for_unsupported_content_type(self):
        self.simulate_request(
            self.test_route,
            method='POST',
            headers={
                'content-type': 'application/xml',
            },
            body=jsonutils.dumps(self.body))
        self.assertEqual(falcon.HTTP_415, self.srmock.status)

    def test_returns_202_for_registered_worker(self):
        self.simulate_request(
            self.test_route,
            method='POST',
            headers={
                'content-type': 'application/json',
            },
            body=jsonutils.dumps(self.body))
        self.assertEqual(falcon.HTTP_202, self.srmock.status)

    def test_returns_202_on_post(self):
        self.resource.on_post(self.req, self.resp)
        self.assertEquals(self.resp.status, falcon.HTTP_202)

        resp_body = jsonutils.loads(self.resp.body)
        worker_identity = resp_body['worker_identity']
        self.assertTrue('personality_module' in worker_identity)
        self.assertTrue('worker_id' in worker_identity)
        self.assertTrue('worker_token' in worker_identity)


if __name__ == '__main__':
    unittest.main()
