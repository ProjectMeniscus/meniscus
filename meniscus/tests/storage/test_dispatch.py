import unittest

from mock import MagicMock, patch
with patch('meniscus.data.datastore.datasource_handler', MagicMock()):
    from meniscus.sinks import (
        DEFAULT_SINK, VALID_SINKS, SECONDARY_SINKS)
    from meniscus.storage import dispatch


class WhenTestingStoragePersistence(unittest.TestCase):
    def setUp(self):
        self.message = {
            "profile": "http://projectmeniscus.org/cee/profiles/base",
            "ver": "1",
            "msgid": "-",
            "pri": "46",
            "pid": "-",
            "meniscus": {
                "tenant": "5164b8f4-16fb-4376-9d29-8a6cbaa02fa9",
                "correlation": {
                    "host_id": "1",
                    "durable": False,
                    "ep_id": None,
                    "pattern": None,
                    "encrypted": False,
                    "sinks": []
                }
            },
            "host": "tohru",
            "pname": "rsyslogd",
            "time": "2013-04-02T14:12:04.873490-05:00",
            "msg": "start",
            "native": {
                "origin": {
                    "x-info": "http://www.rsyslog.com",
                    "swVersion": "7.2.5",
                    "x-pid": "12662",
                    "software": "rsyslogd"
                }
            }
        }

        self.default_persist = MagicMock()
        self.secondary_persist = MagicMock()

    def test_message_sent_to_default_store_only(self):
        self.message['meniscus']['correlation']['sinks'] = [DEFAULT_SINK]
        with patch('meniscus.storage.dispatch.'
                   'default_store.persist_message.delay',
                   self.default_persist):
            dispatch.persist_message(self.message)
            self.default_persist.assert_called_once_with(self.message)

    def test_message_sent_to_secondary_sink_only(self):
        self.message['meniscus']['correlation']['sinks'] = SECONDARY_SINKS
        with patch('meniscus.storage.dispatch.'
                   'short_term_store.persist_message.delay',
                   self.secondary_persist):
            dispatch.persist_message(self.message)
            self.secondary_persist.assert_called_once_with(self.message)

    def test_message_sent_to_default_and_secondary_sinks(self):
        self.message['meniscus']['correlation']['sinks'] = VALID_SINKS
        with patch('meniscus.storage.dispatch.'
                   'default_store.persist_message.delay',
                   self.default_persist), \
            patch('meniscus.storage.dispatch.'
                  'short_term_store.persist_message.delay',
                  self.secondary_persist):
            dispatch.persist_message(self.message)
            self.default_persist.assert_called_once_with(self.message)
            self.secondary_persist.assert_called_once_with(self.message)
