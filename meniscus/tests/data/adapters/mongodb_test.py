from config import config_opts
from datetime import datetime
from meniscus.api.tenant.resources import *

from mock import MagicMock

import falcon
import unittest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenFormattingResponses())

    return suite

