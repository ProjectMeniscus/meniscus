import meniscus.config as config
from meniscus.data import adapters
from meniscus import env
from meniscus.data.handler import datasource_handler


_LOG = env.get_logger(__name__)


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
