import falcon
import unittest

from meniscus.api.tenant.resources import \
    VersionResource, UserResource, TenantResource, \
    HostProfilesResource, HostProfileResource, \
    EventProducersResource, EventProducerResource, \
    HostResource, HostsResource
from meniscus.data.model.tenant import Tenant, Host, HostProfile, EventProducer
from meniscus.openstack.common import jsonutils

from mock import MagicMock
from mock import patch


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingVersionResource())
    suite.addTest(WhenTestingTenantResource())
    suite.addTest(WhenTestingUserResource())
    suite.addTest(WhenTestingHostProfilesResource())
    suite.addTest(WhenTestingHostProfileResource())
    suite.addTest(WhenTestingEventProducersResource())
    suite.addTest(WhenTestingEventProducerResource())
    suite.addTest(WhenTestingHostsResource())
    suite.addTest(WhenTestingHostResource())
    return suite


class TestingTenantApiBase(unittest.TestCase):

    def setUp(self):

        self.db_handler = MagicMock()

        self.stream = MagicMock()

        self.req = MagicMock()
        self.req.stream = self.stream

        self.resp = MagicMock()

        self.profile_id = 123
        self.not_valid_profile_id = 999
        self.profiles = [HostProfile(123, 'profile1',
                                     event_producer_ids=[432, 433]),
                         HostProfile(456, 'profile2',
                                     event_producer_ids=[432, 433])]

        self.producer_id = 432
        self.not_valid_producer_id = 777
        self.producers = [EventProducer(432, 'producer1', 'syslog'),
                          EventProducer(433, 'producer2', 'syslog')]

        self.host_id = 765
        self.not_valid_host_id = 888
        self.hosts = [Host(765, 'host1', ip_address_v4='192.168.1.1',
                           profile_id=123),
                      Host(766, 'host2', ip_address_v4='192.168.2.1',
                           profile_id=456)]

        self.tenant_id = '1234'
        self.tenant_not_found = MagicMock(return_value=None)
        self.tenant_found = MagicMock(
            return_value=Tenant(self.tenant_id, profiles=self.profiles,
                                event_producers=self.producers,
                                hosts=self.hosts))
        self.setResource()

    def setResource(self):
        pass


class WhenTestingVersionResource(unittest.TestCase):

    def setUp(self):
        self.req = MagicMock()
        self.resp = MagicMock()
        self.resource = VersionResource()

    def test_should_return_200_on_get(self):
        self.resource.on_get(self.req, self.resp)
        self.assertEqual(falcon.HTTP_200, self.resp.status)

    def test_should_return_version_json(self):
        self.resource.on_get(self.req, self.resp)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('v1' in parsed_body)
        self.assertEqual('current', parsed_body['v1'])


class WhenTestingTenantResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = TenantResource(self.db_handler)

    def test_should_throw_exception_for_tenant_id_not_provided_on_post(self):
        self.stream.read.return_value = u'{ "tenant_xxx" : "1237" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp)

    def test_should_throw_exception_for_tenant_id_empty_on_post(self):
        self.stream.read.return_value = u'{ "tenant_id" : "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp)

    def test_should_throw_exception_for_tenants_that_exist_on_post(self):
        self.stream.read.return_value = u'{ "tenant_id" : "1234" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp)

    def test_should_return_201_on_post(self):
        self.stream.read.return_value = u'{ "tenant_id" : "1234" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.resource.on_post(self.req, self.resp)

        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingUserResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = UserResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_tenant_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('tenant' in parsed_body)
        self.assertTrue('tenant_id' in parsed_body['tenant'])
        self.assertEqual(self.tenant_id, parsed_body['tenant']['tenant_id'])

    def test_should_throw_exception_for_tenants_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id)

    def test_should_return_200_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_delete(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingHostProfilesResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = HostProfilesResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_profiles_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('profiles' in parsed_body.keys())
        self.assertEqual(len(self.profiles), len(parsed_body['profiles']))

        for profile in parsed_body['profiles']:
            self.assertTrue('id' in profile.keys())
            self.assertTrue('name' in profile.keys())
            self.assertTrue('event_producers' in profile.keys())

    def test_should_throw_exception_for_tenants_not_found_on_post(self):
        self.stream.read.return_value = u'{ "name" : "profile1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_found_on_post(self):
        self.stream.read.return_value = u'{ "name" : "profile1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_name_not_provided_on_post(self):
        self.stream.read.return_value = u'{ "blah" : "profile99" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_name_empty_on_post(self):
        self.stream.read.return_value = u'{ "name" : "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_producer_not_found_on_post(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[1,2]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_return_201_on_post_no_event_producers(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)

    def test_should_return_201_on_post_with_event_producers(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingHostProfileResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = HostProfileResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_profile_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.not_valid_profile_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.profile_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_profile_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.profile_id)

        parsed_body = jsonutils.loads(self.resp.body)
        self.assertTrue('profile' in parsed_body.keys())
        self.assertTrue('id' in parsed_body['profile'].keys())
        self.assertTrue('name' in parsed_body['profile'].keys())
        self.assertTrue('event_producers' in parsed_body['profile'].keys())

    def test_should_throw_exception_for_profile_name_empty_on_put(self):
        self.stream.read.return_value = u'{ "name" : "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_tenants_not_found_on_put(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_profile_not_found_on_put(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_profile_id)

    def test_should_throw_exception_for_profile_duplicate_name_on_put(self):
        self.req.stream.read.return_value = u'{ "name" : "profile2" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_invalid_producers_on_put(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[1,2]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_return_200_on_put(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_put(self.req, self.resp, self.tenant_id,
                                 self.profile_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_throw_exception_for_tenants_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.profile_id)

    def test_should_throw_exception_for_profile_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.not_valid_profile_id)

    def test_should_return_200_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.profile_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingEventProducersResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = EventProducersResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_producer_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('event_producers'in parsed_body.keys())
        self.assertEqual(len(self.profiles),
                         len(parsed_body['event_producers']))

        for profile in parsed_body['event_producers']:
            self.assertTrue('id' in profile.keys())
            self.assertTrue('name' in profile.keys())
            self.assertTrue('pattern' in profile.keys())
            self.assertTrue('durable' in profile.keys())
            self.assertTrue('encrypted' in profile.keys())

    def test_should_throw_exception_for_tenants_not_found_on_post(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_name_not_provided_on_post(self):
        self.stream.read.return_value = u'{"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_name_empty_on_post(self):
        self.stream.read.return_value = u'{ "name" : "", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_pattern_not_provided_on_post(self):
        self.stream.read.return_value = u'{ "name" : "profile77" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_pattern_empty_on_post(self):
        self.stream.read.return_value = u'{ "name" : "profile77", ' \
                                        u'"pattern": "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_producer_found_on_post(self):
        self.stream.read.return_value = u'{ "name" : "producer1", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_return_201_on_post_no_optional_fields(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)

    def test_should_return_201_on_post(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingEventProducerResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = EventProducerResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.producer_id)

    def test_should_throw_exception_for_producer_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.producer_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_producer_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.producer_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('event_producer' in parsed_body.keys())
        self.assertTrue('id' in parsed_body['event_producer'].keys())
        self.assertTrue('name' in parsed_body['event_producer'].keys())
        self.assertTrue('pattern' in parsed_body['event_producer'].keys())
        self.assertTrue('durable' in parsed_body['event_producer'].keys())
        self.assertTrue('encrypted' in parsed_body['event_producer'].keys())

    def test_should_throw_exception_for_tenants_not_found_on_put(self):
        self.stream.read.return_value = u'{ "name" : "producer1", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.producer_id)

    def test_should_throw_exception_for_name_empty_on_put(self):
        self.stream.read.return_value = u'{ "name" : "", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_throw_exception_for_pattern_empty_on_put(self):
        self.stream.read.return_value = u'{ "name" : "producer1", ' \
                                        u'"pattern": "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_throw_exception_for_producer_not_found_on_put(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_throw_exception_for_producer_duplicate_name_on_put(self):
        self.stream.read.return_value = u'{ "name" : "producer2", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.producer_id)

    def test_should_return_200_on_put(self):
        self.stream.read.return_value = u'{ "name" : "producer32", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_put(self.req, self.resp, self.tenant_id,
                                 self.producer_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_throw_exception_for_tenants_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.producer_id)

    def test_should_throw_exception_for_producer_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.not_valid_producer_id)

    def test_should_return_200_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                    self.producer_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingHostsResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = HostsResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_host_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('hosts' in parsed_body.keys())
        self.assertEqual(len(self.profiles), len(parsed_body['hosts']))

        for profile in parsed_body['hosts']:
            self.assertTrue('id' in profile.keys())
            self.assertTrue('hostname' in profile.keys())
            self.assertTrue('ip_address_v4' in profile.keys())
            self.assertTrue('ip_address_v6' in profile.keys())
            self.assertTrue('profile' in profile.keys())

    def test_should_throw_exception_for_tenants_not_found_on_post(self):
        self.stream.read.return_value = u'{ "hostname" : "host1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_found_on_post(self):
        self.stream.read.return_value = u'{ "hostname" : "host1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_not_found_on_post(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", "profile_id": 999 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_return_201_on_post_no_profile(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)

    def test_should_return_201_on_post(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": 123 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingHostResource(TestingTenantApiBase):

    def setResource(self):
        self.resource = HostResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.host_id)

    def test_should_throw_exception_for_profile_not_found_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.not_valid_host_id)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.host_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_host_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.host_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('host'in parsed_body.keys())
        self.assertTrue('id' in parsed_body['host'].keys())
        self.assertTrue('hostname' in parsed_body['host'].keys())
        self.assertTrue('ip_address_v4' in parsed_body['host'].keys())
        self.assertTrue('ip_address_v6' in parsed_body['host'].keys())
        self.assertTrue('profile' in parsed_body['host'].keys())

    def test_should_throw_exception_for_tenants_not_found_on_put(self):
        self.stream.read.return_value = u'{ "hostname" : "host1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.host_id)

    def test_should_throw_exception_for_host_not_found_on_put(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": 123 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_host_id)

    def test_should_throw_exception_for_host_duplicate_name_on_put(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host2", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": 123 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.host_id)

    def test_should_throw_exception_for_invalid_profile_on_put(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host1", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": 999 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.host_id)

    def test_should_return_200_on_put(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": 123 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_put(self.req, self.resp, self.tenant_id,
                                 self.host_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_throw_exception_for_tenants_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.host_id)

    def test_should_throw_exception_for_host_not_found_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.not_valid_host_id)

    def test_should_return_200_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                    self.host_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


if __name__ == '__main__':
    unittest.main()
