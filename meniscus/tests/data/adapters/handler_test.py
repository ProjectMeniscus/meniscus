
from mock import MagicMock

import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenConfiguringHandlers())

    return suite


class WhenConfiguringHandlers(unittest.TestCase):
    pass
