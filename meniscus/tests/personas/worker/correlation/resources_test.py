import falcon
import httplib
from meniscus.personas.worker.correlation import PublishResource
import requests
import unittest

from meniscus.personas.worker.pairing.pairing_process import PairingProcess
from mock import MagicMock
from mock import patch


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingPublishResource())
    return suite


class WhenTestingPublishResource(unittest.TestCase):

    def setUp(self):
        self.cache = MagicMock()
        self.resource = PublishResource()
        self.CACHE_TENANT = "CACHE_TENANT"
        self.tenant_id = "1234"
        self.message_token = "5B838B98-49FC-4CAA-807A-9E7B4F7EBEB4"

    def test_validate_req_body_on_post_hostname_not_provided(self):
        body = {
            'nothostname': 'blah',
            'procname': 'myproducer'
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)

    def test_validate_req_body_on_post_hostname_empty(self):
        body = {
            'hostname': '',
            'procname': 'myproducer'
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)

    def test_validate_req_body_on_post_procname_not_provided(self):
        body = {
            'hostname': 'blah',
            'notprocname': 'myproducer'
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)

    def test_validate_req_body_on_post_procname_empty(self):
        body = {
            'nothostname': 'blah',
            'procname': ''
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)

    def test_get_validate_tenant_from_cache_does_not_exist(self):
        self.cache.cache_exists.return_value = None
        result = self.resource._get_validated_tenant_from_cache(
            self.cache, self.tenant_id, self.message_token)
        self.assertEquals(result, None)



if __name__ == '__main__':
    unittest.main()
