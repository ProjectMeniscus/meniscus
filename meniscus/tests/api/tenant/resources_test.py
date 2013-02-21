from datetime import datetime
from meniscus.api.tenant.resources import *
from meniscus.model.tenant import Tenant, Host, HostProfile

from mock import MagicMock

import falcon
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenFormattingResponses())
    suite.addTest(WhenTestingVersionResource())

    return suite


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


if __name__ == '__main__':
    unittest.main()
