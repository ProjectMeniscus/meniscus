import unittest
import meniscus.env as env


class WhenGettingLoggers(unittest.TestCase):

    def test_should_get_logger(self):
        logger = env.get_logger('meniscus.env_test')
        self.assertIsNotNone(logger)


if __name__ == '__main__':
    unittest.main()
