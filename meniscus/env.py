import logging

from os import environ as env


_DEFAULT_LOG_LEVEL = logging.WARN
_CONSOLE_STREAM = logging.StreamHandler()
_VALID_LOGGING_LEVELS = [
    'DEBUG',
    'INFO',
    'ERROR',
    'WARN'
]


def _init():
    if not '_INITIALIZED' in globals():
        globals()['_INITIALIZED'] = True

        log_level = get('LOG', None)
        if log_level:
            if log_level in _VALID_LOGGING_LEVELS:
                print('Overriding logging level to {}.'.format(log_level))
                globals()['_DEFAULT_LOG_LEVEL'] = getattr(logging, log_level)
            else:
                print('Logging level {} not understood.'.format(log_level))


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(_DEFAULT_LOG_LEVEL)
    logger.propagate = False
    logger.addHandler(_CONSOLE_STREAM)
    return logger


def get(name, default=None):
    value = env.get(name)
    return value if value else default


_init()
