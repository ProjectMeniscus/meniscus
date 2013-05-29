import unittest

from mock import MagicMock
from meniscus.api.validation import ValidatorFactory


class WhenLoading(unittest.TestCase):

    def setUp(self):
        conf = MagicMock()
        conf.schemas.schema_directory = '../etc/meniscus/schemas'
        validator_factory = ValidatorFactory(conf)
        self.validator = validator_factory.get_validator('tenant')

    def tearDown(self):
        pass

    def test_should_validate_host_object(self):
        host_obj = {
            'host': {
                'id': 12345,
                'hostname': 'test'
            }
        }
        result = self.validator.validate(host_obj)
        self.assertTrue(result[0])

    def test_should_validate_simple_tenant_object(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345'
            }
        }
        result = self.validator.validate(tenant_obj)
        self.assertTrue(result[0])

    def test_should_reject_bad_tenant_id(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': 12345
            }
        }

        result = self.validator.validate(tenant_obj)
        self.assertFalse(result[0])

    def test_should_reject_additional_properties(self):
        tenant_obj = {
            'tenant': {
                'tenant_id': '12345',
                'cool': 'should fail'
            }
        }

        result = self.validator.validate(tenant_obj)
        self.assertFalse(result[0])

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
        self.assertFalse(result[0])


if __name__ == '__main__':
    unittest.main()
