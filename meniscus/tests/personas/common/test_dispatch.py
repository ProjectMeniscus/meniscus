import unittest

from mock import MagicMock, patch

from meniscus.personas.common.dispatch import (Dispatch, ObjectJsonWriter,
                                               DispatchException)


class WhenTestingDispatch(unittest.TestCase):
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
        self.sock = MagicMock()

    def test_dispatch_message_calls_writer(self):
        dispatch = Dispatch()
        write = MagicMock()
        with patch.object(ObjectJsonWriter, 'write', write):
            dispatch.dispatch_message(self.message, self.sock)
        write.assert_called_once_with(dict(), self.message, self.sock)

    def test_dispatch_raises_exception_on_write_error(self):
        dispatch = Dispatch()
        write = MagicMock(side_effect=Exception)
        with patch.object(ObjectJsonWriter, 'write', write):
            with self.assertRaises(DispatchException):
                dispatch.dispatch_message(self.message, self.sock)
