import unittest

from meniscus.data.handler import register_handler


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenRegisteringDatasourceHandler())

    return suite


class FakeHandler():
    pass


class WhenRegisteringDatasourceHandler(unittest.TestCase):

    def test_something(self):
        register_handler('fake_handler', FakeHandler)
