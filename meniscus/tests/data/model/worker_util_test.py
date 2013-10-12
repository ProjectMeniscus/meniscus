import unittest

from mock import MagicMock, patch

from meniscus.data.model.worker import Worker, WorkerRegistration
from meniscus.openstack.common import jsonutils
_db_handler = MagicMock()

from meniscus.data.model import worker_util


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerUtil())


class WhenTestingWorkerUtil(unittest.TestCase):
    def setUp(self):
        self.worker = Worker(
            **WorkerRegistration(personality="worker").format())

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
            worker = worker_util.find_worker(self.worker.worker_id)
            find_one_method.assert_called_once_with(
                'worker', {'worker_id': self.worker.worker_id})
            self.assertIsInstance(worker, Worker)

    def test_find_worker_returns_none(self):
        find_one_method = MagicMock(return_value=None)
        with patch('meniscus.data.model.worker_util._db_handler.find_one',
                   find_one_method):
            worker = worker_util.find_worker(self.worker.worker_id)
            find_one_method.assert_called_once_with(
                'worker', {'worker_id': self.worker.worker_id})
            self.assertIsNone(worker)
