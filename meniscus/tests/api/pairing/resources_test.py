import unittest

import falcon
import falcon.testing as testing
from mock import MagicMock
from mock import patch

from meniscus.openstack.common import jsonutils
from meniscus.api.pairing.resources import PairingConfigurationResource


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPairingConfigurationResource())
    return suite


class WhenTestingPairingConfigurationResource(testing.TestBase):
    def before(self):
        self.configuration = {
            'pairing_configuration': {
                "api_secret": "ce20a1f3-151b-4302-ad42-52d91349fe8b",
                "coordinator_uri": "http://localhost:8080/v1",
                "personality": "worker"
            }
        }
        self.configuration_bad_secret = {
            'pairing_configuration': {
                "api_secret": "this is not a uuid",
                "coordinator_uri": "http://localhost:8080/v1",
                "personality": "worker"
            }
        }
        self.configuration_bad_personality = {
            'pairing_configuration': {
                "api_secret": "ce20a1f3-151b-4302-ad42-52d91349fe8b",
                "coordinator_uri": "http://localhost:8080/v1",
                "personality": "invalid_personality"
            }
        }
        self.resource = PairingConfigurationResource()
        self.test_route = '/v1/pairing/configure'
        self.api.add_route(self.test_route, self.resource)

    def test_should_return_400_on_bad_secret(self):
        with patch('meniscus.api.pairing.resources.PairingProcess',
                   MagicMock()):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                },
                body=jsonutils.dumps(self.configuration_bad_secret))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_should_return_400_on_bad_personality(self):
        with patch('meniscus.api.pairing.resources.PairingProcess',
                   MagicMock()):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                },
                body=jsonutils.dumps(self.configuration_bad_personality))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_should_return_200_on_post(self):
        with patch('meniscus.api.pairing.resources.PairingProcess',
                   MagicMock()):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={
                    'content-type': 'application/json',
                },
                body=jsonutils.dumps(self.configuration))
        self.assertEqual(falcon.HTTP_200, self.srmock.status)

if __name__ == '__main__':
    unittest.main()
