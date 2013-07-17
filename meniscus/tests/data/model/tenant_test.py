import unittest

from mock import MagicMock, patch

from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Token
from meniscus.data.model.tenant import Tenant


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingEventProducerObject())
    suite.addTest(WhenTestingTokenObject())
    suite.addTest(WhenTestingTenantObject())


class WhenTestingEventProducerObject(unittest.TestCase):

    def setUp(self):
        with patch('meniscus.data.model.tenant.DEFAULT_SINK',
                   'elasticsearch'):
            self.event_producer = EventProducer('EVid',
                                                'mybillingsapp',
                                                'syslog',
                                                'true',
                                                'false')

    def test_event_producer_object_get_id(self):
        self.assertEqual(self.event_producer.get_id(), 'EVid')

    def test_event_producer_object_format(self):
        ep_dict = self.event_producer.format()
        self.assertEqual(ep_dict['id'], 'EVid')
        self.assertEqual(ep_dict['name'], 'mybillingsapp')
        self.assertEqual(ep_dict['pattern'], 'syslog')
        self.assertEqual(ep_dict['durable'], 'true')
        self.assertEqual(ep_dict['encrypted'], 'false')
        self.assertListEqual(ep_dict['sinks'], ['elasticsearch'])


class WhenTestingTokenObject(unittest.TestCase):

    def setUp(self):
        self.empty_token = Token()
        self.test_token = Token('89c38542-0c78-41f1-bcd2-5226189ccab9',
                                '89c38542-0c78-41f1-bcd2-5226189ddab1',
                                '2013-04-01T21:58:16.995031Z')
        self.true_token_string = '89c38542-0c78-41f1-bcd2-5226189ccab9'
        self.previous_token_string = '89c38542-0c78-41f1-bcd2-5226189ddab1'
        self.false_token_string = '89c38542-0c78-41f1-bcd2-5226189d453sh'
        self.empty_token_string = ''

    def test_token_new(self):
        self.assertIsNot(self.empty_token.valid,
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.empty_token.previous, None)
        self.assertIsNot(self.empty_token.last_changed,
                         '2013-04-01T21:58:16.995031Z')

    def test_token_reset(self):
        self.test_token.reset_token()

        self.assertIsNot(self.test_token.valid,
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.test_token.previous,
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertIsNot(self.test_token.last_changed,
                         '2013-04-01T21:58:16.995031Z')

    def test_token_reset_token_now(self):
        self.test_token.reset_token_now()
        self.assertIsNot(self.test_token.valid,
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.test_token.previous, None)
        self.assertIsNot(self.test_token.last_changed,
                         '2013-04-01T21:58:16.995031Z')

    def test_token_format(self):
        token_dict = self.test_token.format()
        self.assertEqual(token_dict['valid'],
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(token_dict['previous'],
                         '89c38542-0c78-41f1-bcd2-5226189ddab1')
        self.assertEqual(token_dict['last_changed'],
                         '2013-04-01T21:58:16.995031Z')

    def test_token_validate(self):
        self.assertFalse(
            self.test_token.validate_token(self.empty_token_string))
        self.assertTrue(self.test_token.validate_token(self.true_token_string))
        self.assertTrue(
            self.test_token.validate_token(self.previous_token_string))
        self.assertFalse(
            self.test_token.validate_token(self.false_token_string))


class WhenTestingTenantObject(unittest.TestCase):
    def setUp(self):
        self.test_token = Token('89c38542-0c78-41f1-bcd2-5226189ccab9',
                                '89c38542-0c78-41f1-bcd2-5226189ddab1',
                                '2013-04-01T21:58:16.995031Z')
        self.test_tenant_bare = Tenant('1022', self.test_token)
        self.test_tenant = Tenant('1022', self.test_token, [], 'MDBid',
                                  'TenantName')

    def test_tenant_get_id(self):
        self.assertEqual(self.test_tenant.get_id(), 'MDBid')

    def test_tenant_format(self):
        tenant_dict = self.test_tenant_bare.format()
        self.assertEqual(tenant_dict['tenant_id'], '1022')
        self.assertEqual(tenant_dict['event_producers'], [])
        self.assertTrue('token' in tenant_dict)

    def test_tenant_format_for_save(self):
        tenant_dict = self.test_tenant.format_for_save()
        self.assertEqual(tenant_dict['tenant_id'], '1022')
        self.assertEqual(tenant_dict['tenant_name'], 'TenantName')
        self.assertEqual(tenant_dict['event_producers'], [])
        self.assertEqual(tenant_dict['_id'], 'MDBid')

if __name__ == '__main__':
    unittest.main()
