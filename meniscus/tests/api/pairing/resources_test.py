import unittest
import json

from mock import MagicMock
from mock import patch
import falcon

from meniscus.api.pairing.resources import PairingConfigurationResource


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPairingConfigurationResource())
    return suite


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
        with patch('meniscus.api.pairing.resources.PairingProcess',
                   MagicMock()):
            self.resource.on_post(self.req, self.resp)

if __name__ == '__main__':
    unittest.main()
