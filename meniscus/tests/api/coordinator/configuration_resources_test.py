import unittest
from mock import MagicMock
from meniscus.api.coordinator.configuration_resources import *


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerConfiguration())
    return suite


class WhenTestingWorkerConfiguration(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.db_handler = MagicMock()
        self.resource = WorkerConfigurationResource(self.db_handler)
        self.stream = MagicMock()
        self.req.stream = self.stream
        self.worker_id = MagicMock()

    def test_should_return_error_401_personality_not_valid_on_get(self):
        self.req.get_header.return_value = ['ACCEPT',
                                            'CONTENT-TYPE',
                                            'WORKER-TOKEN']
        with self.assertRaises(falcon.HTTPError):
            self.resource.on_get(self.req, self.resp, self.worker_id)


if __name__ == '__main__':
    unittest.main()
