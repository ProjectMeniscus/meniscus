from meniscus.data import adapters
from meniscus.data.handler import datasource_handler
from meniscus.config import init_config, get_config


init_config()
conf = get_config()
_handler = datasource_handler(conf)
_handler.connect()


def db_handler():
    return _handler
