import meniscus.config as config
from meniscus.data import adapters
from meniscus.data.handler import datasource_handler

def db_handler():
    try:
        config.init_config()
    except config.cfg.ConfigFilesNotFoundError:
        #TODO(dmend) Log config error
        pass

    conf = config.get_config()
    _handler = datasource_handler(conf)
    _handler.connect()

    return _handler
