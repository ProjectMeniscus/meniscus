import unittest
import uuid

from mock import MagicMock, patch
_db_handler = MagicMock()
with patch('meniscus.data.datastore.datasource_handler',
           MagicMock(return_value=_db_handler)):
    from meniscus.storage import transaction


class WhenTestingTransaction(unittest.TestCase):

    def setUp(self):
        self.transaction = transaction.Transaction()

    def test_lock_records(self):
        with self.assertRaises(NotImplementedError):
            self.transaction._lock_records()

    def test_retrieve_locked_records(self):
        with self.assertRaises(NotImplementedError):
            self.transaction._retrieve_locked_records()

    def test_process_locked_records(self):
        with self.assertRaises(NotImplementedError):
            self.transaction._process_locked_records()

    def test_release_lock(self):
        with self.assertRaises(NotImplementedError):
            self.transaction._release_lock()

    def test_process_transaction(self):
        with self.assertRaises(NotImplementedError):
            self.transaction.process_transaction()


class WhenTestingBatchMessageTransaction(unittest.TestCase):
    def setUp(self):
        self.transaction_id = str(uuid.uuid4())
        self.expire_seconds = 60
        self.sink_name = 'test_sink'
        self.time = 1372878456.223144
        with patch('meniscus.storage.transaction.time.time',
                   MagicMock(return_value=self.time)):
            self.transaction = transaction.BatchMessageTransaction(
                self.sink_name, self.transaction_id, self.expire_seconds)

    def test_constructor(self):
        self.assertEqual(self.transaction.transaction_id, self.transaction_id)
        self.assertEqual(
            self.transaction.transaction_field,
            "meniscus.correlation.destinations.{0}".format(self.sink_name))
        self.assertEqual(
            self.transaction.id_field,
            "{0}.transaction_id".format(self.transaction.transaction_field))
        self.assertEqual(
            self.transaction.time_field,
            "{0}.transaction_time".format(self.transaction.transaction_field))
        self.assertEqual(self.transaction.expire_seconds, self.expire_seconds)

    def test_lock_records(self):

        self.transaction._lock_records()
        _db_handler.set_field.assert_called_once_with(
            'logs',
            {
                self.transaction.time_field: self.time,
                self.transaction.id_field: self.transaction_id
            },
            {
                '$and': [
                    {
                        self.transaction.transaction_field: {'$exists': True}
                    },
                    {
                        '$or': [
                            {self.transaction.time_field:
                                {'$lt': self.transaction.threshold_time}
                             },
                            {
                                self.transaction.time_field: None
                            }
                        ]
                    }
                ]
            }
        )

    def test_retreive_locked_records(self):
        self.transaction._retrieve_locked_records()
        _db_handler.find.assert_called_once_with(
            'logs',
            {self.transaction.id_field: self.transaction.transaction_id},
            {"_id": False}
        )

    def test_release_lock(self):
        lock_task = MagicMock()
        lock_task.delay = MagicMock()
        with patch(
                'meniscus.storage.transaction._release_lock_task', lock_task):
            self.transaction._release_lock()
        lock_task.delay.assert_called_once_with(
            self.transaction.transaction_field,
            self.transaction.id_field,
            self.transaction.transaction_id)

    def test_process_locked_records(self):
        with self.assertRaises(NotImplementedError):
            self.transaction._process_locked_records()

    def test_process_transaction(self):
        _lock_records = MagicMock()
        _retrieve_locked_records = MagicMock()
        _process_locked_records = MagicMock()
        _release_lock = MagicMock()
        locked_records = MagicMock()
        locked_records.count.return_value = 1

        self.transaction._lock_records = _lock_records
        self.transaction._retrieve_locked_records = _retrieve_locked_records
        self.transaction._process_locked_records = _process_locked_records
        self.transaction._release_lock = _release_lock
        self.transaction.locked_records = locked_records

        self.transaction.process_transaction()
        _lock_records.assert_called_once()
        _retrieve_locked_records.assert_called_once()
        _process_locked_records.assert_called_once()
        _release_lock.assert_called_once()

    def test_handler_remove_field_called(self):
        remove_field = {self.transaction.transaction_field: ""}
        update_filter = {
            self.transaction.id_field: self.transaction.transaction_id
        }
        transaction._release_lock_task(
            self.transaction.transaction_field,
            self.transaction.id_field,
            self.transaction.transaction_id)

        _db_handler.remove_field.assert_called_once_with(
            "logs", remove_field, update_filter)

    def test_retry_called_on_exception(self):
        _db_handler.remove_field.side_effect = Exception
        transaction._release_lock_task.retry = MagicMock()

        transaction._release_lock_task(
            self.transaction.transaction_field,
            self.transaction.id_field,
            self.transaction.transaction_id)

        transaction._release_lock_task.retry.assert_called_once()
