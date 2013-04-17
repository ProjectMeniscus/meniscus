
import httplib
import unittest

from mock import MagicMock
from mock import patch
import requests


from meniscus.api.coordinator import watchlist_flow
from meniscus.data.model.worker import SystemInfo
from meniscus.data.model.worker import WorkerRegistration
from meniscus.data.model.worker import Worker, WatchlistItem


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWatchlistFlow())
    return suite


class WhenTestingWatchlistFlow(unittest.TestCase):
    def setUp(self):
        self.broadcaster_list = [
            Worker(**WorkerRegistration(personality='broadcaster',
                                        status='online').format()).format(),
            Worker(**WorkerRegistration(personality='broadcaster',
                                        status='online').format()).format(),
            Worker(**WorkerRegistration(personality='broadcaster',
                                        status='online').format()).format(),
        ]
        self.broadcaster_uri_list = [worker['ip_address_v4']
                                     for worker in self.broadcaster_list]
        self.target_list = [
            Worker(**WorkerRegistration(personality='coordinator',
                                        status='online').format()).format(),
            Worker(**WorkerRegistration(personality='normalization',
                                        status='online').format()).format(),
            Worker(**WorkerRegistration(personality='coordinator',
                                        status='online').format()).format(),
        ]
        self.target_uri_list = {"broadcast": {"type": "ROUTES", "targets":
                                [worker['callback']
                                for worker in self.target_list]}}

        self.damaged_worker = Worker(**WorkerRegistration(
            personality='storage').format())
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
                               "watch_count":
                               watchlist_flow.WATCHLIST_COUNT_THRESHOLD - 1,
                               "worker_id": "0123456789",
                               "last_changed": "2013-04-09T15:11:19.818Z"
                               }
        self.watchlist_dict_over = {"_id": "010101",
                                    "watch_count":
                                    watchlist_flow.WATCHLIST_COUNT_THRESHOLD
                                    + 1,
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
        self.db_handler.put = MagicMock()
        watch_item = WatchlistItem(self.watchlist_dict['worker_id'])
        watchlist_flow._add_watchlist_item(self.db_handler, watch_item)
        self.db_handler.put.assert_called_once_with(
            'watchlist', watch_item.format())

    def test_update_watchlist_item(self):
        self.db_handler.update = MagicMock()
        watch_item = WatchlistItem(self.watchlist_dict['worker_id'],
                                   self.watchlist_dict['last_changed'],
                                   self.watchlist_dict['watch_count'],
                                   self.watchlist_dict['_id'])
        watchlist_flow._update_watchlist_item(self.db_handler,
                                              watch_item)
        self.db_handler.update.assert_called_once_with(
            'watchlist', watch_item.format_for_save())

    def test_delete_expired_watchlist_item(self):
        self.db_handler.delete = MagicMock()
        watchlist_flow._delete_expired_watchlist_items(self.db_handler)
        self.db_handler.delete.assert_called_once()

    def test_get_broadcaster_list_true(self):
        db_handler = MagicMock()
        db_handler.find.return_value = self.broadcaster_list
        self.assertEqual(watchlist_flow._get_broadcaster_list(db_handler),
                         self.broadcaster_uri_list)

    def test_get_broadcaster_list_empty(self):
        db_handler = MagicMock()
        db_handler.find = MagicMock(return_value=[])
        self.assertFalse(
            watchlist_flow._get_broadcaster_list(db_handler))

    def test_get_broadcaster_list_empty_find(self):
        db_handler = MagicMock()
        db_handler.find = MagicMock(return_value=[])
        self.assertFalse(
            watchlist_flow._get_broadcast_targets(db_handler,
                                                  self.damaged_worker))

    def test_get_broadcaster_list_no_upstream_personality(self):
        damaged_worker = Worker(**WorkerRegistration(
            personality='correlation').format())
        db_handler = MagicMock()
        self.assertFalse(
            watchlist_flow._get_broadcast_targets(db_handler, damaged_worker))

    def test_get_broadcast_targets_list_empty(self):
        db_handler = MagicMock()
        db_handler.find - MagicMock(return_value=[])
        self.assertFalse(
            watchlist_flow._get_broadcast_targets(db_handler,
                                                  self.damaged_worker))

    def test_get_broadcast_targets_list_true(self):
        db_handler = MagicMock()
        db_handler.find.return_value = self.target_list
        self.assertEqual(
            watchlist_flow._get_broadcast_targets(db_handler,
                                                  self.damaged_worker),
            self.target_uri_list)

    def test_send_target_list_to_broadcaster_false_empty_target_list(self):
        db_handler = MagicMock()
        watchlist_flow._get_broadcast_targets = MagicMock(
            return_value=[])
        watchlist_flow._get_broadcaster_list = MagicMock(
            return_value=self.broadcaster_uri_list)
        result = watchlist_flow._send_target_list_to_broadcaster(
            db_handler, self.damaged_worker)
        self.assertFalse(result)

    def test_send_target_list_to_broadcaster_bad_response_code(self):
        db_handler = MagicMock()
        resp = MagicMock()
        resp.status_code = httplib.BAD_REQUEST
        http_request = MagicMock(return_value=resp)
        watchlist_flow._get_broadcast_targets = MagicMock(
            return_value=self.target_uri_list)
        watchlist_flow._get_broadcaster_list = MagicMock(
            return_value=self.broadcaster_uri_list)
        with patch('meniscus.api.coordinator.'
                   'watchlist_flow.http_request', http_request):
            result = watchlist_flow._send_target_list_to_broadcaster(
                db_handler, self.damaged_worker)
            self.assertFalse(result)

    def test_send_target_list_to_broadcaster_no_connection_made(self):
        db_handler = MagicMock()
        http_request = MagicMock(
            side_effect=requests.RequestException)
        watchlist_flow._get_broadcast_targets = MagicMock(
            return_value=self.target_uri_list)
        watchlist_flow._get_broadcaster_list = MagicMock(
            return_value=self.broadcaster_uri_list)
        with patch('meniscus.api.coordinator.'
                   'watchlist_flow.http_request', http_request):
            self.assertFalse(watchlist_flow._send_target_list_to_broadcaster(
                             db_handler, self.damaged_worker))

    def test_send_target_list_to_broadcaster_connection_made(self):
        db_handler = MagicMock()
        resp = MagicMock()
        resp.status_code = httplib.OK
        http_request = MagicMock(return_value=resp)
        watchlist_flow._get_broadcast_targets = MagicMock(
            return_value=self.target_uri_list)
        watchlist_flow._get_broadcaster_list = MagicMock(
            return_value=self.broadcaster_uri_list)
        with patch('meniscus.api.coordinator.'
                   'watchlist_flow.http_request', http_request):
            result = watchlist_flow._send_target_list_to_broadcaster(
                db_handler, self.damaged_worker)
            self.assertTrue(result)

    def test_broadcast_config_change(self):
        watchlist_flow._send_target_list_to_broadcaster(self.db_handler,
                                                        self.worker)

    def test_process_watchlist_item(self):
        watchlist_flow.process_watchlist_item(self.db_handler, self.worker_id)

    def test_process_watchlist_item_new_item(self):
        self.db_handler.find_one.return_value = None
        self.assertIs(watchlist_flow.process_watchlist_item(
            self.db_handler, self.worker_id), None)

    def test_process_watchlist_item_count_at_threshold(self):
        find_worker = MagicMock(return_value=self.worker)
        with patch('meniscus.api.coordinator.coordinator_flow.find_worker',
                   find_worker):
            self.db_handler.find_one.return_value = self.watchlist_dict
            watchlist_flow.process_watchlist_item(self.db_handler,
                                                  self.worker_id)
            find_worker.assert_called_once_with(self.db_handler,
                                                self.worker_id)

    def test_process_watchlist_item_count_at_threshold(self):
        find_worker = MagicMock(return_value=self.worker_online)
        with patch('meniscus.api.coordinator.coordinator_flow.find_worker',
                   find_worker):
            self.db_handler.find_one.return_value = self.watchlist_dict
            watchlist_flow.process_watchlist_item(self.db_handler,
                                                  self.worker_id)
            find_worker.assert_called_once_with(self.db_handler,
                                                self.worker_id)

if __name__ == '__main__':
    unittest.main()
