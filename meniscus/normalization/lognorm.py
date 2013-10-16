import os

from meniscus import config
from meniscus import env

from pylognorm import LogNormalizer
from oslo.config import cfg


_LOG = env.get_logger(__name__)

# Normalization configuration options
_NORMALIZATION_GROUP = cfg.OptGroup(
    name='liblognorm', title='Liblognorm options')
config.get_config().register_group(_NORMALIZATION_GROUP)

_NORMALIZATION = [
    cfg.StrOpt('rules_dir',
               default=None,
               help="""directory to load rules from"""
               )
]

config.get_config().register_opts(
    _NORMALIZATION, group=_NORMALIZATION_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)


def get_normalizer(conf=config.get_config()):
    """This returns both a normalizer as well as a list of loaded rules"""
    normalization_conf = conf.liblognorm
    normalizer = LogNormalizer()
    loaded_rules = list()
    if normalization_conf.rules_dir:
        loaded_rules = load_rules(normalizer, normalization_conf.rules_dir)
    return normalizer, loaded_rules


def load_rules(normalizer, path):
    loaded = list()
    if not os.path.isdir(path):
        raise IOError(
            'Unable to load rules. {} is not a directory'.format(path))
    for possible_rule in os.listdir(path):
        if possible_rule.endswith('.db'):
            normalizer.load_rules(os.path.join(path, possible_rule))
            loaded.append(possible_rule.rstrip('.db'))
    return loaded
