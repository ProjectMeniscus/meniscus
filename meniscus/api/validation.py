import os

from oslo.config import cfg
from meniscus.config import get_config
from jsonschema import validate, ValidationError
from meniscus.openstack.common import jsonutils

_schema_group = cfg.OptGroup(name='schemas', title='API Schema Options')
get_config().register_group(_schema_group)

_SCHEMA_OPTIONS = [
    cfg.ListOpt('schema_directory',
                default='/etc/meniscus/schemas',
                help="""Directory to use when searching for JSON schemas."""
                )
]

get_config().register_opts(_SCHEMA_OPTIONS, group=_schema_group)


def load_body(req, required=[]):
    """
    Helper function for loading an HTTP request body from JSON into a
    Python dictionary
    """
    try:
        raw_json = req.stream.read()
    except Exception:
        abort(falcon.HTTP_500, 'Read Error')

    try:
        return jsonutils.loads(raw_json)
    except ValueError:
        abort(falcon.HTTP_400, 'Malformed JSON')


class SchemaError(Exception):

    def __init__(self, msg):
        self.msg = msg


class SchemaNotFoundError(SchemaError):

    def __init__(self, schema_file):
        super(SchemaNotFoundError, self).__init__(
            'Unable to locate schema file {}'.format(schema_file))


class MalformedSchemaError(SchemaError):

    def __init__(self, schema_file, ex):
        super(MalformedSchemaError, self).__init__(
            'Unable to read schema file {}. Reason: {}'.format(
                schema_file, ex.msg))


class ValidatorFactory(object):

    def __init__(self, conf):
        self.schema_directory = conf.schemas.schema_directory

    def get_validator(self, schema_name):
        schema_file = '{}/{}.json'.format(self.schema_directory, schema_name)

        if not os.path.isfile(schema_file):
            raise SchemaNotFoundError(schema_file)

        try:
            schema = jsonutils.loads(open(schema_file, 'r').read())
        except Exception as ex:
            raise MalformedSchemaError(schema_file, ex)

        return JsonSchemaValidator(schema)


class JsonSchemaValidator(object):

    def __init__(self, schema):
        self.schema = schema

    def validate(self, obj_graph):
        try:
            validate(obj_graph, self.schema)
            return (True, None)
        except ValidationError as ve:
            return (False, ve)


