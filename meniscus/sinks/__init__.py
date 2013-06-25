
from oslo.config import cfg

import meniscus.config as config
from meniscus import env
from meniscus.sinks import elasticsearch


_LOG = env.get_logger(__name__)

_DATA_SINKS_GROUP = cfg.OptGroup(name='data_sinks', title='Data Sink List')
config.get_config().register_group(_DATA_SINKS_GROUP)

_SINK = [
    cfg.ListOpt('valid_sinks',
                default=['elasticsearch', 'hdfs'],
                help="""valid data sinks list"""
    ),
    cfg.ListOpt('default_sinks',
                default=['elasticsearch'],
                help="""default data sinks list"""
    )
]

config.get_config().register_opts(_SINK, group=_DATA_SINKS_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

conf = config.get_config()

VALID_SINKS = conf.data_sinks.valid_sinks
DEFAULT_SINKS = conf.data_sinks.default_sinks

def persist_message(message):

    sinks = message['meniscus']['correlation']['sinks']
    if 'elasticsearch' in sinks:
        elasticsearch.persist_message.delay(message)