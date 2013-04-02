import unittest

import falcon
from mock import MagicMock
from mock import patch


from meniscus.app import bootstrap_api
from meniscus.data.model.worker import WorkerConfiguration


class TestingApIBootstrap(unittest.TestCase):

    def setUp(self):
        self.cache = MagicMock()
        self.cache.get_config.return_value = WorkerConfiguration(
            personality='worker.pairing',
            personality_module='meniscus.personas.worker.pairing.app',
            worker_token='token_id',
            worker_id='worker_id',
            coordinator_uri="192.168.1.1:8080/v1"
        )
        self.no_cache = MagicMock()
        self.no_cache.get_config.return_value = False

    def test_should_return_personality_from_cache(self):
        with patch('meniscus.app.config_cache', self.cache):
            application = bootstrap_api()
            self.assertIsInstance(application, falcon.API)

    def test_should_return_default_personality_module_when_no_cache(self):
        with patch('meniscus.app.config_cache', self.no_cache):
            application = bootstrap_api()
            self.assertIsInstance(application, falcon.API)


if __name__ == '__main__':
    unittest.main()
