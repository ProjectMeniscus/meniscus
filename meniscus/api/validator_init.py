from oslo.config import cfg

from meniscus.validation import jsonv
import meniscus.config as config
from meniscus import env
from meniscus.validation.integration.falcon_hooks import validation_hook


_LOG = env.get_logger(__name__)

# Celery configuration options
_JSON_SCHEMA_GROUP = cfg.OptGroup(
    name='json_schema', title='Json Schema Options')
config.get_config().register_group(_JSON_SCHEMA_GROUP)

_JSON_SCHEMA = [
    cfg.StrOpt('schema_dir',
               default="../etc/meniscus/schemas/",
               help="""directory holding json schema files"""
               )
]

config.get_config().register_opts(_JSON_SCHEMA, group=_JSON_SCHEMA_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

conf = config.get_config()

_schema_loader = jsonv.DirectorySchemaLoader(conf.json_schema.schema_dir)
_validation_factory = jsonv.JsonSchemaValidatorFactory(_schema_loader)


def get_validator(schema_name):
    return validation_hook(_validation_factory.get_validator(schema_name))
