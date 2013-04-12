import unittest

from mock import MagicMock
from mock import patch

import falcon

from meniscus.api.broadcaster.resources import BroadcastResource


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingBroadcastResource())
    return suite


class WhenTestingBroadcastResource(unittest.TestCase):
    def setUp(self):
        self.resource = BroadcastResource()
        self.cache = MagicMock()
        self.req = MagicMock()
        self.resp = MagicMock()

    def test_should_return_202_on_put(self):
        self.req.stream.read.return_value = \
            u'{"broadcast": { "type": "ROUTES",' \
            u'"targets": [' \
            u'"http://hostname1.domain:8080/callback",' \
            u'"http://hostname2.domain:8080/callback",' \
            u'"http://hostname3.domain:8080/callback",' \
            u'"http://hostname4.domain:8080/callback" ]}}'
        with patch('meniscus.api.broadcaster.resources.BroadcastResource',
                   MagicMock()):
            self.resource.on_put(self.req, self.resp)
        self.assertEquals(self.resp.status, falcon.HTTP_202)


if __name__ == '__main__':
    unittest.main()
