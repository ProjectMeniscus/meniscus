import unittest

from meniscus.normalization.normalizer import *


class WhenTestingMessageNormalization(unittest.TestCase):
    def setUp(self):
        self.message = {
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

    def test_normalize_message(self):
        self.assertTrue(should_normalize(self.message))
        normalize_message(self.message)
