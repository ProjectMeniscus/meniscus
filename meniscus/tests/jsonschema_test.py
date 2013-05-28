import os
import json
import unittest
from jsonschema import validate, ValidationError


class WhenLoading(unittest.TestCase):

    def setUp(self):
        schema_json = open('../etc/meniscus/schemas/tenant.json', 'r').read()
        self.schema = json.loads(schema_json)

    def tearDown(self):
        pass

    def test_should_validate_host_object(self):
        host_obj = {
            'host': {
                'id': 12345
            }
        }
        validate(host_obj, self.schema)

    def test_should_validate_simple_tenant_object(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345'
            }
        }
        validate(tenant_obj, self.schema)

    def test_should_reject_bad_tenant_id(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': 12345
            }
        }

        with self.assertRaises(ValidationError):
            validate(tenant_obj, self.schema)

    def test_should_reject_additional_properties(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345',
                'cool': 'should fail'
            }
        }

        with self.assertRaises(ValidationError):
            validate(tenant_obj, self.schema)

    def test_should_reject_mutex_objects(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345'
            },
            'host': {
                'id': 12345
            }
        }

        with self.assertRaises(ValidationError):
            validate(tenant_obj, self.schema)


if __name__ == '__main__':
    unittest.main()
