from meniscus.api.utils.retry import retry
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingRetry())
    return suite


class WhenTestingRetry(unittest.TestCase):

    def stuff(self):
        return True

    def test_retry_backoff_raised_value_error(self):
        with self.assertRaises(ValueError):
            @retry(tries=1, delay=1, backoff=0)
            def backoff_invalid():
                return True
            backoff_invalid()

    def test_retry_tries_raised_value_error(self):
        with self.assertRaises(ValueError):
            @retry(tries=-1, delay=1, backoff=2)
            def func_tries_invalid():
                return True
            func_tries_invalid()

    def test_retry_delays_raised_value_error(self):
        with self.assertRaises(ValueError):
            @retry(tries=1, delay=0, backoff=2)
            def delay_invalid():
                return True
            delay_invalid()

    def test_retry_func_returns_true_first_try(self):
        self.counter = 0
        self.tries = 2
        @retry(tries=self.tries, delay=1, backoff=2)
        def retry_valid():
            self.counter += 1
            return True
        result = retry_valid()
        self.assertTrue(result)
        self.assertTrue(self.counter == 1)

    def test_retry_func_returns_false(self):
        self.counter = 0
        self.tries = 2
        @retry(tries=self.tries, delay=0.1, backoff=2)
        def retry_once():
            self.counter += 1
            return False
        result = retry_once()
        self.assertFalse(result)
        self.assertTrue(self.counter == self.tries + 1)

    def test_retry_func_should_retry_twice(self):
        self.counter = 0
        self.tries = 2
        @retry(tries=self.tries, delay=0.1, backoff=2)
        def retry_once():
            self.counter += 1
            if self.counter < self.tries:
                return False
            return True
        result = retry_once()
        self.assertTrue(result)
        self.assertTrue(self.counter == self.tries)

if __name__ == '__main__':
    unittest.main()
