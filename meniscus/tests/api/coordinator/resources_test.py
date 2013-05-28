import unittest

import falcon
from mock import MagicMock

from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.data.model.worker import WorkerRegistration
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerRegistrationOnPost())
    return suite


class WhenTestingWorkerRegistrationOnPost(unittest.TestCase):
    def setUp(self):

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
        self.req.stream.read.return_value = self.registration
        self.resp = MagicMock()

    def test_returns_202_on_post(self):
        self.resource.on_post(self.req, self.resp)
        self.assertEquals(self.resp.status, falcon.HTTP_202)

        resp_body = jsonutils.loads(self.resp.body)
        self.assertTrue('personality_module' in resp_body)
        self.assertTrue('worker_id' in resp_body)
        self.assertTrue('worker_token' in resp_body)


if __name__ == '__main__':
    unittest.main()
