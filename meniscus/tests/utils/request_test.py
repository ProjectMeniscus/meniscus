from meniscus.api.utils.request import post_http

from mock import MagicMock
from mock import patch

import falcon
import requests
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingUtilsRequest())
    return suite


class WhenTestingUtilsRequest(unittest.TestCase):

    def setUp(self):
        self.requests = MagicMock()
        self.url = 'http://localhost:8080/somewhere'
        self.json_payload = u'{}'

    def test_should_cause_a_connection_exception(self):
        with patch.object(requests, 'post') as mock_method:
            with self.assertRaises(requests.ConnectionError):
                mock_method.side_effect = requests.ConnectionError
                post_http(self.url, self.json_payload)

    def test_should_cause_a_http_exception(self):
        with patch.object(requests, 'post') as mock_method:
            with self.assertRaises(requests.HTTPError):
                mock_method.side_effect = requests.HTTPError
                post_http(self.url, self.json_payload)

    def test_should_cause_a_request_exception(self):
        with patch.object(requests, 'post') as mock_method:
            with self.assertRaises(requests.RequestException):
                mock_method.side_effect = requests.RequestException
                post_http(self.url, self.json_payload)

    def test_should_return_http_200(self):
        with patch.object(requests, 'post') as mock_method:
            mock_method.return_value.status_code = falcon.HTTP_200
            self.assertEqual(post_http(self.url, self.json_payload), falcon.HTTP_200)


if __name__ == '__main__':
    unittest.main()
