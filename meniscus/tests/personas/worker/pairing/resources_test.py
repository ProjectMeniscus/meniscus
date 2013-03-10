from meniscus.personas.worker.pairing.resources \
    import VersionResource, PairingConfigurationResource

from mock import MagicMock
from mock import patch

import falcon
import unittest
import json


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPairingVersionResource())
    suite.addTest(WhenTestingPairingConfigurationResource())
    return suite


class WhenTestingPairingVersionResource(unittest.TestCase):

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


class WhenTestingPairingConfigurationResource(unittest.TestCase):
    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.resource = PairingConfigurationResource()

    def test_should_return_200_on_post(self):
        self.req.stream.read.return_value = \
            u'{ "api_secret" : "1234", ' \
            u'"coordinator_uri" : "http://localhost:8080/v1" , ' \
            u'"personality" : "1234"  }'
        with patch('meniscus.personas.worker.pairing.resources.PairingProcess',
                   MagicMock()):
            self.resource.on_post(self.req, self.resp)

if __name__ == '__main__':
    unittest.main()