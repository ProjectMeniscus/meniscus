import unittest

from mock import MagicMock
from mock import patch
import falcon

from meniscus.api.callback.resources import CallbackResource
from meniscus.api.callback.resources import ROUTES
def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingCallbackResource())
    return suite


class WhenTestingCallbackResource(unittest.TestCase):
    def setUp(self):
        self.resource = CallbackResource()
        self.req = MagicMock()
        self.resp = MagicMock()

        self.req.get_header.return_value = ROUTES

    def test_type_routes_returns_200(self):
        get_routes = MagicMock()
        with patch('meniscus.api.callback.resources.callback_methods.'
                   'get_routes_from_coordinator', get_routes):
            self.resource.on_head(self.req, self.resp)
            self.assertEquals(self.resp.status, falcon.HTTP_200)
            get_routes.assert_called_once_with()

if __name__ == '__main__':
    unittest.main()

