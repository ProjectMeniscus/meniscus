from datetime import date
import uuid

from oslo.config import cfg
from pywebhdfs import webhdfs

from meniscus import config

from meniscus import env
from meniscus.openstack.common import jsonutils
from meniscus.queue import celery
from meniscus.storage import transaction


_LOG = env.get_logger(__name__)


# HDFS configuration options
_hdfs_group = cfg.OptGroup(name='hdfs_sink', title='HDFS Sink Options')
config.get_config().register_group(_hdfs_group)

_hdfs_options = [
    cfg.StrOpt('host',
               default='localhost',
               help="""WebHDFS hostname"""
               ),
    cfg.StrOpt('port',
               default='5700',
               help="""WebHDFS port number."""
               ),
    cfg.StrOpt('user_name',
               default='hdfs',
               help="""WebHDFS user_name."""
               ),
    cfg.StrOpt('base_directory',
               default='user/hdfs/laas',
               help="""base HDFS directory to use"""
               ),
    cfg.IntOpt('transaction_expire',
               default=300,
               help="""length of time for a write to hdfs before expiring"""
               ),
    cfg.IntOpt('transfer_frequency',
               default=60,
               help="""frequency to write records to hdfs"""
               )
]

config.get_config().register_opts(_hdfs_options, group=_hdfs_group)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

conf = config.get_config()

TRANSACTION_EXPIRE = conf.hdfs_sink.transaction_expire
FREQUENCY = conf.hdfs_sink.transfer_frequency
SINK = 'hdfs'


class HdfsTransaction(transaction.BatchMessageTransaction):

    def _process_locked_records(self):

        write_dir = "{0}/{1}".format(
            conf.hdfs_sink.base_directory,
            (date.fromtimestamp(self.transaction_time)).isoformat())
        file_path = "{0}/{1}".format(write_dir, self.transaction_id)

        transaction_data = "\n".join(
            [jsonutils.dumps(record) for record in self.locked_records])

        hdfs_client = webhdfs.PyWebHdfsClient(
            host=conf.hdfs_sink.host,
            port=conf.hdfs_sink.port,
            user_name=conf.hdfs_sink.user_name)

        try:
            hdfs_client.create_file(file_path, transaction_data)
        except webhdfs.errors.FileNotFound:
            hdfs_client.make_dir(write_dir)
            hdfs_client.create_file(file_path, transaction_data)


@celery.task(name="hdfs.send")
def send_to_hdfs():
    """sends a batch of messages to hdfs"""
    transaction_id = str(uuid.uuid4())
    hdfs_transaction = HdfsTransaction(
        SINK, transaction_id, TRANSACTION_EXPIRE)
    hdfs_transaction.process_transaction()
