import unittest

from mock import MagicMock
from mock import patch

from meniscus.api.callback import callback_methods


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingUpdateRoutes())
    return suite


class WhenTestingUpdateRoutes(unittest.TestCase):

    def test_get_routes_from_coord_called_once(self):
        coord_call = MagicMock(return_value=True)
        with patch('meniscus.api.callback.callback_methods.'
                   'get_routes_from_coordinator', coord_call):
            callback_methods.get_updated_routes()
            coord_call.assert_called_once_with()

if __name__ == '__main__':
    unittest.main()
