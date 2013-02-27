from meniscus.api.coordinator.resources import NodeConfigurationResource
from mock import MagicMock

import falcon
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(NodeConfigurationResource())

    return suite


class WhenTestingNodeConfigurationResource(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.resource = NodeConfigurationResource()

    def test_should_return_401_on_get(self):
        self.req.get_header.return_value = ''
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp)

    def test_should_return_403_on_get(self):
        self.req.get_header.return_value = ['role1', 'role2', 'role3']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp)

    def test_should_return_another_403_on_get(self):
        self.req.get_header.return_value = ['role1', 'role2', 'role3']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp)

    def test_should_return_200_on_get(self):
        self.req.get_header.return_value = ['role1', 'role2', 'meniscus_role',
                                            'role3']
        self.resource.on_get(self.req, self.resp)
        self.assertEqual(falcon.HTTP_200, self.resp.status)

if __name__ == '__main__':
    unittest.main()
