import unittest

from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import Token
from meniscus.data.model.tenant import Tenant


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingEventProducerObject())
    suite.addTest(WhenTestingHostProfileObject())
    suite.addTest(WhenTestingHostObject())
    suite.addTest(WhenTestingTokenObject())
    suite.addTest(WhenTestingTenantObject())


class WhenTestingEventProducerObject(unittest.TestCase):

    def setUp(self):
        self.event_producer = EventProducer('EVid',
                                            'mybillingsapp',
                                            'syslog',
                                            'true',
                                            'false')

    def test_event_producer_object_get_id(self):
        self.assertEqual(self.event_producer.get_id(), 'EVid')

    def test_event_producer_object_format(self):
        self.assertEqual(self.event_producer.format()['id'], 'EVid')
        self.assertEqual(self.event_producer.format()['name'], 'mybillingsapp')
        self.assertEqual(self.event_producer.format()['pattern'], 'syslog')
        self.assertEqual(self.event_producer.format()['durable'], 'true')
        self.assertEqual(self.event_producer.format()['encrypted'], 'false')


class WhenTestingHostProfileObject(unittest.TestCase):

    def setUp(self):
        self.host_profile = HostProfile('HPid',
                                        'appservers-1',
                                        [1, 2])
        self.host_prof_bare = HostProfile('HPid',
                                          'appservers-1')

    def test_host_profile_object_no_event_producers(self):
        self.assertEqual(self.host_prof_bare.format()['id'], 'HPid')
        self.assertEqual(self.host_prof_bare.format()['name'], 'appservers-1')
        self.assertEqual(self.host_prof_bare.format()['event_producers'], [])

    def test_host_profile_object_get_id(self):
        self.assertEqual(self.host_profile.get_id(), 'HPid')

    def test_host_profile_object_format(self):
        self.assertEqual(self.host_profile.format()['id'], 'HPid')
        self.assertEqual(self.host_profile.format()['name'], 'appservers-1')
        self.assertEqual(self.host_profile.format()['event_producers'], [1, 2])


class WhenTestingHostObject(unittest.TestCase):
    def setUp(self):
        self.host = Host('Hid', 'WebNode1', '192.168.1.1', '::1', '3')
        self.empty_host = Host('Hid', 'WebNode1')

    def test_host_object_get_id(self):
        self.assertEqual(self.host.get_id(), 'Hid')

    def test_host_object_format(self):
        self.assertEqual(self.host.format()['id'], 'Hid')
        self.assertEqual(self.host.format()['hostname'], 'WebNode1')
        self.assertEqual(self.host.format()['ip_address_v4'], '192.168.1.1')
        self.assertEqual(self.host.format()['ip_address_v6'], '::1')
        self.assertEqual(self.host.format()['profile'], '3')

    def test_host_object_minimal_parameters(self):
        self.assertEqual(self.empty_host.format()['id'], 'Hid')
        self.assertEqual(self.empty_host.format()['hostname'], 'WebNode1')
        self.assertEqual(self.empty_host.format()['ip_address_v4'], None)
        self.assertEqual(self.empty_host.format()['ip_address_v6'], None)
        self.assertEqual(self.empty_host.format()['profile'], None)


class WhenTestingTokenObject(unittest.TestCase):

    def setUp(self):
        self.empty_token = Token()
        self.test_token = Token('89c38542-0c78-41f1-bcd2-5226189ccab9',
                                '89c38542-0c78-41f1-bcd2-5226189ddab1',
                                '2013-04-01T21:58:16.995031Z')

    def test_token_new(self):
        self.assertIsNot(self.empty_token.format()['valid'],
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.empty_token.format()['previous'], None)
        self.assertIsNot(self.empty_token.format()['last_changed'],
                         '2013-04-01T21:58:16.995031Z')

    def test_token_reset(self):
        self.test_token.reset_token()
        self.assertIsNot(self.test_token.format()['valid'],
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.test_token.format()['previous'],
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertIsNot(self.test_token.format()['last_changed'],
                         '2013-04-01T21:58:16.995031Z')

    def test_token_reset_token_now(self):
        self.test_token.reset_token_now()
        self.assertIsNot(self.test_token.format()['valid'],
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.test_token.format()['previous'], None)
        self.assertIsNot(self.test_token.format()['last_changed'],
                         '2013-04-01T21:58:16.995031Z')

    def test_token_format(self):
        self.assertEqual(self.test_token.format()['valid'],
                         '89c38542-0c78-41f1-bcd2-5226189ccab9')
        self.assertEqual(self.test_token.format()['previous'],
                         '89c38542-0c78-41f1-bcd2-5226189ddab1')
        self.assertEqual(self.test_token.format()['last_changed'],
                         '2013-04-01T21:58:16.995031Z')

    def test_token_validate(self):
    #todo review token validate code
        pass


class WhenTestingTenantObject(unittest.TestCase):
    def setUp(self):
        self.test_token = Token('89c38542-0c78-41f1-bcd2-5226189ccab9',
                                '89c38542-0c78-41f1-bcd2-5226189ddab1',
                                '2013-04-01T21:58:16.995031Z')
        self.test_tenant_bare = Tenant('1022', self.test_token, [], [], [])
        self.test_tenant = Tenant('1022', self.test_token, [], [], [], 'MDBid')

    def test_tenant_get_id(self):
        self.assertEqual(self.test_tenant.get_id(), 'MDBid')

    def test_tenant_format(self):
        self.assertEqual(self.test_tenant_bare.format()['tenant_id'], '1022')
        self.assertEqual(self.test_tenant_bare.format()['hosts'], [])
        self.assertEqual(self.test_tenant_bare.format()['profiles'], [])
        self.assertEqual(
            self.test_tenant_bare .format()['event_producers'], [])
        self.assertTrue('token' in self.test_tenant.format())

    def test_tenant_format_for_save(self):
            self.assertEqual(
                self.test_tenant.format_for_save()['tenant_id'], '1022')
            self.assertEqual(self.test_tenant.format_for_save()['hosts'], [])
            self.assertEqual(
                self.test_tenant.format_for_save()['profiles'], [])
            self.assertEqual(
                self.test_tenant.format_for_save()['event_producers'], [])
            self.assertEqual(
                self.test_tenant.format_for_save()['_id'], 'MDBid')

if __name__ == '__main__':
    unittest.main()