from os import environ as env
from oslo.config import cfg
from meniscus.openstack.common import log as logging


def get_logger(logger_name):
    return logging.getLogger(logger_name)


def get(name, default=None):
    value = env.get(name)
    return value if value else default
