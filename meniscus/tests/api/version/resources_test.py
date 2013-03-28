import unittest
from mock import MagicMock

import falcon

from meniscus.api.version.resources import VersionResource
from meniscus.openstack.common import jsonutils


def suite():

    test_suite = unittest.TestSuite()
    test_suite.addTest(WhenTestingVersionResource())

    return test_suite


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

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('v1' in parsed_body)
        self.assertEqual('current', parsed_body['v1'])
