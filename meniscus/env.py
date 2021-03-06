from os import environ
from oslo.config import cfg
from meniscus.openstack.common import log
from meniscus.config import _DEFAULT_CONFIG_ARGS


CONF = cfg.CONF
CONF.import_opt('verbose', 'meniscus.openstack.common.log')
CONF.import_opt('debug', 'meniscus.openstack.common.log')
CONF.import_opt('log_file', 'meniscus.openstack.common.log')
CONF.import_opt('log_dir', 'meniscus.openstack.common.log')
CONF.import_opt('use_syslog', 'meniscus.openstack.common.log')
CONF.import_opt('syslog_log_facility', 'meniscus.openstack.common.log')
CONF.import_opt('log_config', 'meniscus.openstack.common.log')

try:
    cfg.CONF(args=_DEFAULT_CONFIG_ARGS)
except cfg.ConfigFilesNotFoundError as ex:
    pass


def get_logger(logger_name):
    return log.getLogger(logger_name)


def get(name, default=None):
    value = environ.get(name)
    return value if value else default
