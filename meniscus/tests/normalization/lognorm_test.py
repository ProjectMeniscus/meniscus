import unittest

from mock import MagicMock
from meniscus.normalization.lognorm import get_normalizer


class WhenTestingMessageNormalization(unittest.TestCase):

    def setUp(self):
        self.conf = MagicMock()
        self.conf.liblognorm = MagicMock()
        self.conf.liblognorm.rules_dir = '../etc/meniscus/normalizer_rules'

        self.normalizer, self.loaded_rules = get_normalizer(self.conf)

    def test_loading_rules(self):
        self.assertTrue('apache' in self.loaded_rules)
