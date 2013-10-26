import os
from oslo.config import cfg


def _get(name, default=None):
    value = os.environ.get(name)
    return value if value else default


_DEFAULT_CONFIG_ARGS = [
    '--config-file',
    _get('CONFIG_FILE', '/etc/meniscus/meniscus.cfg')
]

_config_opts = cfg.ConfigOpts()


def get_config():
    return _config_opts


def init_config(cfg_args=_DEFAULT_CONFIG_ARGS):
    _config_opts(args=cfg_args)
