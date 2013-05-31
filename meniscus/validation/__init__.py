class SchemaError(Exception):

    def __init__(self, msg):
        self.msg = msg


class SchemaNotFoundError(SchemaError):

    def __init__(self, schema_file):
        super(SchemaNotFoundError, self).__init__(
            'Unable to locate schema file {}'.format(schema_file))


class MalformedSchemaError(SchemaError):

    def __init__(self, schema_file, message):
        super(MalformedSchemaError, self).__init__(
            'Unable to read schema file {}. Reason: {}'.format(
                schema_file, message))


class SchemaLoader(object):

    def load_schema(self, schema_ref):
        raise NotImplementedError


class ValidatorFactory(object):

    def get_validator(self, schema_name):
        raise NotImplementedError


class ValidationResult(object):

    def __init__(self, valid, error=None):
        self.valid = valid
        self.error = error


class ObjectValidator(object):

    def validate(self, obj_graph):
        raise NotImplementedError
