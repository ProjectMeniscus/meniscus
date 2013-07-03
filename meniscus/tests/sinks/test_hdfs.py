from datetime import date
import unittest
import uuid

from mock import MagicMock, patch
_db_handler = MagicMock()
with patch('meniscus.data.datastore.datasource_handler',
           MagicMock(return_value=_db_handler)):
    from meniscus.sinks import hdfs


class WhenTestingHdfsTransaction(unittest.TestCase):
    def setUp(self):
        self.transaction_id = str(uuid.uuid4())
        self.expire_seconds = 60
        self.sink_name = 'hdfs'
        self.hdfs_transaction = hdfs.HdfsTransaction(
            self.sink_name, self.transaction_id, self.expire_seconds)
        self.hdfs_transaction.locked_records = ['record']

    def test_process_locked_records_creates_file(self):
        write_dir = "{0}/{1}".format(
            hdfs.conf.hdfs_sink.base_directory,
            (date.fromtimestamp(
                self.hdfs_transaction.transaction_time)).isoformat())
        file_path = "{0}/{1}".format(write_dir, self.transaction_id)
        create_file = MagicMock()
        with patch.object(hdfs.webhdfs.PyWebHdfsClient,
                          'create_file', create_file):
            self.hdfs_transaction._process_locked_records()
        create_file.assert_called_once_with(file_path, '"record"')

    def test_process_locked_records_handles_exception(self):
        write_dir = "{0}/{1}".format(
            hdfs.conf.hdfs_sink.base_directory,
            (date.fromtimestamp(
                self.hdfs_transaction.transaction_time)).isoformat())
        file_path = "{0}/{1}".format(write_dir, self.transaction_id)
        make_dir = MagicMock()
        create_file = MagicMock(
            side_effect=[hdfs.webhdfs.errors.FileNotFound, True])
        with patch.object(hdfs.webhdfs.PyWebHdfsClient,
                          'create_file', create_file), patch.object(
                hdfs.webhdfs.PyWebHdfsClient, 'make_dir', make_dir):
            self.hdfs_transaction._process_locked_records()
        make_dir.assert_called_once_with(write_dir)
