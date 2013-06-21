
from oslo.config import cfg
from pywebhdfs.webhdfs import errors, PyWebHdfsClient
import meniscus.config as config
from meniscus import env
from meniscus.openstack.common import jsonutils, timeutils
from meniscus.queue import celery

_LOG = env.get_logger(__name__)

# Celery configuration options
_HDFS_GROUP = cfg.OptGroup(name='hdfs', title='HDFS Options')
config.get_config().register_group(_HDFS_GROUP)

_HDFS = [
    cfg.StrOpt('hostname',
               default="localhost",
               help="""hostname of hdfs"""
    ),
    cfg.StrOpt('port',
               default=50070,
               help="""Port number for WebHDFS on namenode"""
    ),
    cfg.StrOpt('user_name',
               default='hdfs',
               help="""disable celery rate limit"""
    ),
    cfg.StrOpt('base_directory',
               default="usr/hdfs/laas",
               help="""default serialization method to use"""
    )
]

config.get_config().register_opts(_HDFS, group=_HDFS_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

conf = config.get_config()


hdfs = PyWebHdfsClient(conf.hdfs.hostname, conf.hdfs.port, conf.hdfs.user_name)
base_directory = conf.hdfs.basedirectory


@celery.task(acks_late=True, max_retries=None,
             ignore_result=True, serializer="json")
def persist_message(message):
    """Takes a message and persists it to the default datastore."""

    tenant_id =  message['meniscus']['tenant']
    tenant_dir = '{base_directory}/{tenant_id}'.format(
        base_directory=base_directory, tenant_id=tenant_id)

    message_time = timeutils.parse_isotime(message['time'])
    message_date = message_time.date()
    file_name = message_date.isoformat()


    message_json = '{message}\n'.format(message=jsonutils.dumps(message))

    try:
        write_to_hdfs(tenant_dir, file_name, message_json)

    except Exception as ex:
        _LOG.exception(ex)
        persist_message.retry()

def write_to_hdfs(hdfs_dir, file_name, file_data):

    full_path = '{hdfs_dir}/{file_name}'.format(
        hdfs_dir=hdfs_dir, file_name=file_name)
    try:
        hdfs.append_file(full_path, file_data)

    except errors.FileNotFound:
        _LOG.debug('webhdfs: {hdfs_path} not found, creating file')
        hdfs.make_dir(hdfs_dir)
        hdfs.create_file(full_path, file_data)



