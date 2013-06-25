import unittest
from mock import MagicMock
from meniscus.data.datastore import handler


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenRegisteringDatasourceHandlerManager())

    return suite


class WhenRegisteringDatasourceHandlerManager(unittest.TestCase):
    def setUp(self):
        self.handler = MagicMock()
        self.handler_name = 'fake_handler'
        self.manager = handler.DatasourceHandlerManager()

    def test_resgister_handler(self):
        self.manager.register(self.handler_name, self.handler)
        self.assertEqual(
            self.manager.registered_handlers[self.handler_name], self.handler)

    def test_get_handler(self):
        self.manager.register(self.handler_name, self.handler)
        self.assertEqual(
            self.manager.get(self.handler_name), self.handler)
