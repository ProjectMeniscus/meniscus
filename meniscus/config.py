import os
from oslo.config import cfg

CONFIG_FILE_ENV_VAR = 'CONFIG_FILE'

if CONFIG_FILE_ENV_VAR in os.environ:
    _DEFAULT_CONFIG_ARGS = [ '--config-file', os.environ['CONFIG_FILE'] ]
else:
    _DEFAULT_CONFIG_ARGS = [ '--config-file', '/etc/meniscus/meniscus.cfg' ]

_config_opts = cfg.ConfigOpts()

def get_config():
    return _config_opts

def init_config(cfg_args=_DEFAULT_CONFIG_ARGS):
    _config_opts(args=cfg_args)
