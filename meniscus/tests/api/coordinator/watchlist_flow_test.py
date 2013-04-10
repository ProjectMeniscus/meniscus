
import unittest

from mock import MagicMock

from meniscus.api.coordinator import coordinator_flow
from meniscus.api.coordinator import watchlist_flow
from meniscus.data.model.worker import SystemInfo
from meniscus.data.model.worker import WorkerRegistration
from meniscus.data.model.worker import Worker


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWatchlistFlow())
    return suite


class WhenTestingWatchlistFlow(unittest.TestCase):
    def setUp(self):
        self.db_handler = MagicMock()
        self.worker_id = "0123456789"
        self.req = MagicMock()
        self.resp = MagicMock()
        self.body_bad_header = {'worker':
                                WorkerRegistration('correlation').format()}
        self.body_bad_personality = {'worker_registration':
                                     WorkerRegistration(
                                     'bad_personality').format()}
        self.new_status = 'offline'
        self.new_bad_status = 'bad_status'
        self.system_info = SystemInfo()
        self.watchlist_dict = {"_id": "010101",
                               "watch_count": 5,
                               "worker_id": "0123456789",
                               "last_changed": "2013-04-09T15:11:19.818Z"
                               }
        self.watchlist_dict_over = {"_id": "010101",
                                    "watch_count": 7,
                                    "worker_id": "123456789",
                                    "last_changed": "2013-04-09T15:11:19.818Z"
                                    }
        self.worker = Worker(_id='010101',
                             worker_id=self.worker_id,
                             worker_token='9876543210',
                             hostname='worker01',
                             callback='172.22.15.25:8080/v1/config/',
                             ip_address_v4='172.23.1.100',
                             ip_address_v6='::1',
                             personality='correlation',
                             status='offline',
                             system_info=self.system_info.format())
        self.worker_online = Worker(_id='010101',
                                    worker_id=self.worker_id,
                                    worker_token='9876543210',
                                    hostname='worker01',
                                    callback='172.22.15.25:8080/v1/config/',
                                    ip_address_v4='172.23.1.100',
                                    ip_address_v6='::1',
                                    personality='correlation',
                                    status='online',
                                    system_info=self.system_info.format())

    def test_add_watchlist_item(self):
        watchlist_flow._add_watchlist_item(self.db_handler, self.worker_id)

    def test_update_watchlist_item(self):
        watchlist_flow._update_watchlist_item(self.db_handler,
                                              self.watchlist_dict)

    def test_delete_expired_watchlist_item(self):
        watchlist_flow._delete_expired_watchlist_items(self.db_handler)

    def test_broadcast_config_change(self):
        watchlist_flow.broadcast_config_change(self.db_handler, self.worker)

    def test_process_watchlist_item(self):
        watchlist_flow.process_watchlist_item(self.db_handler, self.worker_id)

    def test_process_watchlist_item_new_item(self):
        self.db_handler.find_one.return_value = None
        self.assertIs(watchlist_flow.process_watchlist_item(
            self.db_handler, self.worker_id), None)

    def test_process_watchlist_item_count_at_threshold(self):
        coordinator_flow.find_worker = MagicMock(return_value=self.worker)
        self.db_handler.find_one.return_value = self.watchlist_dict
        watchlist_flow.process_watchlist_item(self.db_handler, self.worker_id)

    def test_process_watchlist_item_count_at_threshold(self):
        coordinator_flow.find_worker = MagicMock(
            return_value=self.worker_online)
        self.db_handler.find_one.return_value = self.watchlist_dict
        watchlist_flow.process_watchlist_item(self.db_handler, self.worker_id)

if __name__ == '__main__':
    unittest.main()

