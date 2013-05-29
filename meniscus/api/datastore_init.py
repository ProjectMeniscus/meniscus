import meniscus.config as config

from meniscus.env import get_logger
from meniscus.data import adapters
from meniscus.data.handler import datasource_handler


_LOG = get_logger('meniscus.api.datastore_init')


def db_handler():
    try:
        config.init_config()
    except config.cfg.ConfigFilesNotFoundError as ex:
        _LOG.exception(ex)
        pass

    conf = config.get_config()
    _handler = datasource_handler(conf)
    _handler.connect()

    return _handler
