from meniscus import config
from meniscus import env
from meniscus.queue import celery

from pylognorm import LogNormalizer
from oslo.config import cfg


_LOG = env.get_logger(__name__)

# Normalization configuration options
_NORMALIZATION_GROUP = cfg.OptGroup(
    name='liblognorm', title='Liblognorm options')
config.get_config().register_group(_NORMALIZATION_GROUP)

_NORMALIZATION = [
    cfg.StrOpt('rules_file',
               default=None,
               help="""file to load rules from"""
               )
]

config.get_config().register_opts(
    _NORMALIZATION, group=_NORMALIZATION_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)


def get_normalizer():
    normalization_conf = config.get_config().liblognorm
    normalizer = LogNormalizer()

    if normalization_conf.rules_file:
        _LOG.info('Loading normalization rules from: {}'.format(
            normalization_conf.rules_file))
        normalizer.load_rules(normalization_conf.rules_file)
    return normalizer
