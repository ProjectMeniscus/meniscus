import unittest

from mock import MagicMock, patch
with patch('meniscus.data.datastore.datasource_handler', MagicMock()):
    from meniscus.storage.default_store import persist_message


class WhenTestingStoragePersistence(unittest.TestCase):
    def setUp(self):
        self.message = {
            "processid": "3071",
            "appname": "dhcpcd",
            "timestamp": "2013-04-05T15:51:18.607457-05:00",
            "hostname": "tohru",
            "priority": "30",
            "version": "1",
            "messageid": "-",
            "message": "wlan0: leased 10.6.173.172 for 3600 seconds\n",
            "sd": {
                "origin": {
                    "software": "rsyslogd",
                    "swVersion": "7.2.5",
                    "x-pid": "24592",
                    "x-info": "http://www.rsyslog.com"
                }
            }
        }

        self.db_handler = MagicMock()

    def test_persist_message_calls_db_put(self):
        with patch('meniscus.storage.default_store._db_handler',
                   self.db_handler):
            persist_message(self.message)
            self.db_handler.put.assert_called_once_with('logs', self.message)
