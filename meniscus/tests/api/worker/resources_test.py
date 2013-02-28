from meniscus.api.worker.resources import VersionResource
from meniscus.api.worker.resources import ConfigurationResource

from mock import MagicMock

import falcon
import json
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingVersionResource())
    suite.addTest(WhenTestingConfigurationResource())
    return suite


class TestingWorkerApiBase(unittest.TestCase):

    def setUp(self):
        pass

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


class WhenTestingConfigurationResource(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.stream = MagicMock()
        self.req.stream = self.stream
        self.resource = ConfigurationResource()

    def test_should_return_202_on_post(self):
        self.stream.read.return_value = u'{}'
        self.resource.on_post(self.req, self.resp)
        self.assertEqual(falcon.HTTP_202, self.resp.status)


if __name__ == '__main__':
    unittest.main()
