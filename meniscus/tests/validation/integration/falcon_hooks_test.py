try:
    import testtools as unittest
except ImportError:
    import unittest

import io
import json
import falcon
import falcon.testing as testing

from meniscus.validation import SchemaLoader
from meniscus.validation.jsonv import JsonSchemaValidatorFactory
from meniscus.validation.integration.falcon_hooks import validation_hook


class SchemaMock(SchemaLoader):

    _SCHEMA = {
        'id': 'http://projectmeniscus.org/json/worker_configuration#',
        'type': 'object',
        'additionalProperties': False,

        'properties': {
            'animal':  {
                'enum': ['falcon', 'dog']
            }
        }
    }

    def load_schema(self, schema_ref):
        return self._SCHEMA

_validation_factory = JsonSchemaValidatorFactory(SchemaMock())


@falcon.before(validation_hook(_validation_factory.get_validator('mock')))
class ValidatedResource(object):

    def on_post(self, req, resp, validated, doc):
        self.req = req
        self.resp = resp
        self.validated = validated
        self.doc = doc


class TestValidationHook(testing.TestBase):

    def before(self):
        self.resource = ValidatedResource()
        self.api.add_route(self.test_route, self.resource)

    def test_unhandled_media_type(self):
        self.simulate_request(self.test_route,
                              method='POST',
                              headers={'content-type': 'application/xml'},
                              body=unicode('<animal type="falcon">'))

        self.assertFalse(self.resource.validated)

    def test_valid_payload(self):
        self.simulate_request(self.test_route,
                              method='POST',
                              headers={'content-type': 'application/json'},
                              body=json.dumps({'animal': 'falcon'}))

        self.assertTrue(self.resource.validated)
        self.assertEqual(self.resource.doc, {'animal': 'falcon'})

    def test_invalid_payload(self):
        self.simulate_request(self.test_route,
                              method='POST',
                              headers={'content-type': 'application/json'},
                              body=json.dumps({'animal': 'cat'}))

        self.assertEqual(falcon.HTTP_400, self.srmock.status)


if __name__ == '__main__':
    unittest.main()
