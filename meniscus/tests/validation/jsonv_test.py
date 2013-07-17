import unittest

from mock import MagicMock

from meniscus.validation.jsonv import (JsonSchemaValidatorFactory,
                                       DirectorySchemaLoader)


class WhenLoading(unittest.TestCase):

    def setUp(self):
        schema_loader = DirectorySchemaLoader('../etc/meniscus/schemas')
        validator_factory = JsonSchemaValidatorFactory(schema_loader)
        self.validator = validator_factory.get_validator('tenant')

    def tearDown(self):
        pass

    def test_should_validate_simple_tenant_object(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345'
            }
        }
        result = self.validator.validate(tenant_obj)
        self.assertTrue(result.valid)

    def test_should_reject_bad_tenant_id(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': 12345
            }
        }

        result = self.validator.validate(tenant_obj)
        self.assertFalse(result.valid)

    def test_should_reject_additional_properties(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345',
                'cool': 'should fail'
            }
        }

        result = self.validator.validate(tenant_obj)
        self.assertFalse(result.valid)

    def test_should_reject_mutex_objects(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345'
            },
            'host': {
                'id': 12345
            }
        }

        result = self.validator.validate(tenant_obj)
        self.assertFalse(result.valid)


if __name__ == '__main__':
    unittest.main()
