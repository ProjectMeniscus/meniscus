import unittest

from mock import MagicMock, patch

from meniscus.data.model.worker import Worker, SystemInfo

_db_handler = MagicMock()

from meniscus.data.model import worker_util


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerUtil())


class WhenTestingWorkerUtil(unittest.TestCase):

    def setUp(self):
        self.system_info = SystemInfo().format()
        self.worker = Worker(**{"hostname": "worker-01",
                                "ip_address_v4": "192.168.100.101",
                                "ip_address_v6": "::1",
                                "personality": "worker",
                                "status": "online",
                                "system_info": self.system_info})

    def test_create_worker_calls_db_put(self):
        put_method = MagicMock()
        with patch('meniscus.data.model.worker_util._db_handler.put',
                   put_method):
            worker_util.create_worker(self.worker)
            put_method.assert_called_once_with('worker', self.worker.format())

    def test_find_worker_returns_worker(self):
        find_one_method = MagicMock(return_value=self.worker.format())
        with patch('meniscus.data.model.worker_util._db_handler.find_one',
                   find_one_method):
            worker = worker_util.find_worker(self.worker.hostname)
            find_one_method.assert_called_once_with(
                'worker', {'hostname': self.worker.hostname})
            self.assertIsInstance(worker, Worker)

    def test_find_worker_returns_none(self):
        find_one_method = MagicMock(return_value=None)
        with patch('meniscus.data.model.worker_util._db_handler.find_one',
                   find_one_method):
            worker = worker_util.find_worker(self.worker.hostname)
            find_one_method.assert_called_once_with(
                'worker', {'hostname': self.worker.hostname})
            self.assertIsNone(worker)

    def test_save_worker(self):
        update_method = MagicMock(return_value=None)
        with patch('meniscus.data.model.worker_util._db_handler.update',
                   update_method):
            worker_util.save_worker(self.worker)
            update_method.assert_called_once_with(
                'worker', self.worker.format_for_save())

    def test_retrieve_all_workers(self):
        find_method = MagicMock(return_value=[self.worker.format_for_save()])
        with patch('meniscus.data.model.worker_util._db_handler.find',
                   find_method):
            workers = worker_util.retrieve_all_workers()
            find_method.assert_called_once_with('worker')
            for worker in workers:
                self.assertIsInstance(worker, Worker)
