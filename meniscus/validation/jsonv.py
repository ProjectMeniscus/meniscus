import os
import json

from meniscus.validation import *
from jsonschema import validate, ValidationError


class DirectorySchemaLoader(SchemaLoader):

    def __init__(self, *directories):
        self.directories = [
            d[0:len(d)-1] if d.endswith(os.sep) else d for d in directories]

    def load_schema(self, schema_ref):
        for directory in self.directories:
            formatted_path = '{}{}{}'.format(directory, os.sep, schema_ref)
            if os.path.isfile(formatted_path):
                return self._read_json(formatted_path)
        raise SchemaNotFoundError(schema_ref)

    def _read_json(self, schema_file):
        try:
            return json.loads(open(schema_file, 'r').read())
        except Exception as ex:
            raise MalformedSchemaError(schema_file, ex)


class JsonSchemaValidatorFactory(ValidatorFactory):

    def __init__(self, schema_loader):
        self.schema_loader = schema_loader

    def get_validator(self, schema_name):
        if not schema_name.endswith('.json'):
            schema_ref = '{}.json'.format(schema_name)
        else:
            schema_ref = schema_name
        return JsonSchemaValidator(self.schema_loader.load_schema(schema_ref))


class JsonSchemaValidator(ObjectValidator):

    def __init__(self, schema):
        self.schema = schema

    def validate(self, obj_graph):
        try:
            validate(obj_graph, self.schema)
            return ValidationResult(True)
        except ValidationError as ve:
            return ValidationResult(False, ve)
