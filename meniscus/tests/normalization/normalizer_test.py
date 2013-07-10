import unittest

from mock import MagicMock, patch
from meniscus.normalization.normalizer import should_normalize


class WhenNormalizingMessages(unittest.TestCase):

    def setUp(self):
        self.bad_message = dict()
        self.good_message = {
            "processid": "3071",
            "appname": "dhcpcd",
            "timestamp": "2013-04-05T15:51:18.607457-05:00",
            "hostname": "tohru",
            "priority": "30",
            "pattern": "wpa_supplicant",
            "version": "1",
            "messageid": "-",
            "msg": "wlan0: leased 10.6.173.172 for 3600 seconds\n",
            "sd": {
                "origin": {
                    "software": "rsyslogd",
                    "swVersion": "7.2.5",
                    "x-pid": "24592",
                    "x-info": "http://www.rsyslog.com"
                }
            }
        }
        self.loaded_rules = ['wpa_supplicant']

    def test_normalize_message(self):
        target = 'meniscus.normalization.normalizer.loaded_normalizer_rules'
        with patch(target, self.loaded_rules):
            self.assertTrue(should_normalize(self.good_message))
