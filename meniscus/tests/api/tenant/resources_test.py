import unittest

import falcon
from mock import MagicMock
from mock import patch

from meniscus.api.tenant.resources import EventProducerResource
from meniscus.api.tenant.resources import EventProducersResource
from meniscus.api.tenant.resources import HostResource
from meniscus.api.tenant.resources import HostProfileResource
from meniscus.api.tenant.resources import HostsResource
from meniscus.api.tenant.resources import HostProfilesResource
from meniscus.api.tenant.resources import TenantResource
from meniscus.api.tenant.resources import TokenResource
from meniscus.api.tenant.resources import UserResource
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Host
from meniscus.data.model.tenant import HostProfile
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.openstack.common import jsonutils


def suite():

    test_suite = unittest.TestSuite()

    test_suite.addTest(WhenTestingTenantResourceOnPost())

    test_suite.addTest(WhenTestingUserResourceOnGet())
    test_suite.addTest(WhenTestingUserResourceOnDelete())

    test_suite.addTest(WhenTestingHostProfilesResourceOnGet())
    test_suite.addTest(WhenTestingHostProfilesResourceOnPost())

    test_suite.addTest(WhenTestingHostProfileResourceOnGet())
    test_suite.addTest(WhenTestingHostProfileResourceOnPut())
    test_suite.addTest(WhenTestingHostProfileResourceOnDelete())

    test_suite.addTest(WhenTestingEventProducersResourceOnGet())
    test_suite.addTest(WhenTestingEventProducersResourceOnPost())

    test_suite.addTest(WhenTestingEventProducerResourceOnGet())
    test_suite.addTest(WhenTestingEventProducerResourceOnPut())
    test_suite.addTest(WhenTestingEventProducerResourceOnDelete())

    test_suite.addTest(WhenTestingHostsResourceValidation())
    test_suite.addTest(WhenTestingHostsResourceOnGet())
    test_suite.addTest(WhenTestingHostsResourceOnPost())

    test_suite.addTest(WhenTestingHostResourceValidation())
    test_suite.addTest(WhenTestingHostResourceOnGet())
    test_suite.addTest(WhenTestingHostResourceOnPut())
    test_suite.addTest(WhenTestingHostResourceOnDelete())

    test_suite.addTest(WhenTestingTokenResourceOnHead())
    test_suite.addTest(WhenTestingTokenResourceOnGet())
    test_suite.addTest(WhenTestingTokenResourceOnPost())

    return test_suite


class TestingTenantApiBase(unittest.TestCase):

    def setUp(self):
        self.validator = MagicMock()
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
        self.token_original = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.token_previous = 'bbd6302e-8d93-47dc-a49a-8fb0d39e5192'
        self.timestamp_original = "2013-03-19T18:16:48.411029Z"
        self.token = Token(self.token_original, self.token_previous,
                           self.timestamp_original)
        self.tenant_id = '1234'
        self.tenant = Tenant(self.tenant_id, self.token,
                             profiles=self.profiles,
                             event_producers=self.producers,
                             hosts=self.hosts)
        self.tenant_not_found = MagicMock(return_value=None)
        self.tenant_found = MagicMock(return_value=self.tenant)

        self._set_resource()

    def _set_resource(self):
        pass


class WhenTestingTenantResourceOnPost(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = TenantResource(self.db_handler)

    def test_should_throw_exception_for_tenant_id_not_provided(self):
        self.stream.read.return_value = u'{ "tenant_xxx" : "1237" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp)

    def test_should_throw_exception_for_tenant_id_empty(self):
        self.stream.read.return_value = u'{ "tenant_id" : "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp)

    def test_should_throw_exception_for_tenants_that_exist(self):
        self.stream.read.return_value = u'{ "tenant_id" : "1234" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp)

    def test_should_return_201(self):
        self.stream.read.return_value = u'{ "tenant_id" : "1234" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.resource.on_post(self.req, self.resp)

        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingUserResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = UserResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_tenant_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('tenant' in parsed_body)
        self.assertTrue('tenant_id' in parsed_body['tenant'])
        self.assertEqual(self.tenant_id, parsed_body['tenant']['tenant_id'])


class WhenTestingUserResourceOnDelete(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = UserResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_delete(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingHostProfilesResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
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


class WhenTestingHostProfilesResourceOnPost(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostProfilesResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        self.stream.read.return_value = u'{ "name" : "profile1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_found(self):
        self.stream.read.return_value = u'{ "name" : "profile1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_name_empty(self):
        self.stream.read.return_value = u'{ "blah" : "profile99" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.stream.read.return_value = u'{ "name" : "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_producer_not_found(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[1,2]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_return_201_no_event_producers(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)

    def test_should_return_201_with_event_producers(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingHostProfileResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
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


class WhenTestingHostProfileResourceOnPut(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostProfileResource(self.db_handler)

    def test_should_throw_exception_for_profile_name_empty(self):
        self.stream.read.return_value = u'{ "name" : "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_tenant_not_found(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_profile_not_found(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_profile_id)

    def test_should_throw_exception_for_profile_duplicate_name(self):
        self.req.stream.read.return_value = u'{ "name" : "profile2" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_producers_not_found(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[1,2]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.profile_id)

    def test_should_throw_exception_for_invalid_producers(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":"55"}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_profile_id)
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":["bad_data"]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_profile_id)

    def test_should_return_200(self):
        self.stream.read.return_value = \
            u'{ "name" : "profile99", "event_producer_ids":[432]}'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_put(self.req, self.resp, self.tenant_id,
                                 self.profile_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingHostProfileResourceOnDelete(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostProfileResource(self.db_handler)

    def test_should_throw_exception_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.profile_id)

    def test_should_throw_exception_for_profile_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.not_valid_profile_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.profile_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingEventProducersResourceValidate(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = EventProducersResource(self.db_handler)

    def test_should_throw_exception_for_bad_durable_val(self):
        body = {
            'name': 'ep_name',
            'pattern': 'syslog',
            'durable': "bad_data"
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)

    def test_should_throw_exception_for_bad_encrypted_val(self):
        body = {
            'name': 'ep_name',
            'pattern': 'syslog',
            'encrypted': "bad_data"
        }
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)


class WhenTestingEventProducersResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
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


class WhenTestingEventProducersResourceOnPost(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = EventProducersResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_name_empty(self):
        self.stream.read.return_value = u'{"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.stream.read.return_value = u'{ "name" : "", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_pattern_empty(self):
        self.stream.read.return_value = u'{ "name" : "profile77" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.stream.read.return_value = u'{ "name" : "profile77", ' \
                                        u'"pattern": "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_producer_found(self):
        self.stream.read.return_value = u'{ "name" : "producer1", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_return_201_no_optional_fields(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)

    def test_should_return_201(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingEventProducerResourceValidate(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)

    def test_should_throw_exception_for_bad_durable_val(self):
        body = {'durable': "bad_data"}
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_put(body)

    def test_should_throw_exception_for_bad_encrypted_val(self):
        body = {'encrypted': "bad_data"}
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_put(body)


class WhenTestingEventProducerResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.producer_id)

    def test_should_throw_exception_for_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.producer_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_producer_json(self):
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


class WhenTestingEventProducerResourceOnPut(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        self.stream.read.return_value = u'{ "name" : "producer1", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.producer_id)

    def test_should_throw_exception_for_name_empty(self):
        self.stream.read.return_value = u'{ "name" : "", ' \
                                        u'"pattern": "syslog" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_throw_exception_for_pattern_empty(self):
        self.stream.read.return_value = u'{ "name" : "producer1", ' \
                                        u'"pattern": "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_throw_exception_for_producer_not_found(self):
        self.stream.read.return_value = u'{ "name" : "producer55", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_producer_id)

    def test_should_throw_exception_for_producer_duplicate_name(self):
        self.stream.read.return_value = u'{ "name" : "producer2", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.producer_id)

    def test_should_return_200(self):
        self.stream.read.return_value = u'{ "name" : "producer32", ' \
                                        u'"pattern": "syslog", ' \
                                        u'"durable": true, ' \
                                        u'"encrypted": false }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_put(self.req, self.resp, self.tenant_id,
                                 self.producer_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingEventProducerResourceOnDelete(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.producer_id)

    def test_should_throw_exception_for_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.not_valid_producer_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                    self.producer_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingHostsResourceValidation(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostsResource(self.db_handler)

    def test_should_throw_value_error_bad_profile_id(self):
        body = {'hostname': 'host', 'profile_id': "bad_data"}
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)

        body = {'hostname': 'host', 'profile_id': [1, 2]}
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_post(body)


class WhenTestingHostsResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostsResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_host_json(self):
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


class WhenTestingHostsResourceOnPost(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostsResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        self.stream.read.return_value = u'{ "hostname" : "host1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_hostname_not_provided(self):
        self.stream.read.return_value = u'{ "ip_address_v4": "192.168.1.1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_hostname_empty(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "", ' \
            u'"ip_address_v4": "192.168.1.1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_host_found(self):
        self.stream.read.return_value = u'{ "hostname" : "host1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_throw_exception_for_profile_not_found(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", "profile_id": 999 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_return_201_no_profile(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)

    def test_should_return_201(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": 123 }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertEquals(falcon.HTTP_201, self.resp.status)


class WhenTestingHostResourceValidation(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)

    def test_should_throw_value_error_bad_profile_id(self):
        body = {'profile_id': "bad_data"}
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_put(body)

        body = {'profile_id': [1, 2]}
        with self.assertRaises(falcon.HTTPError):
            self.resource._validate_req_body_on_put(body)


class WhenTestingHostResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)

    def test_should_throw_exception_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.host_id)

    def test_should_throw_exception_for_profile_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id,
                                     self.not_valid_host_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.host_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)

    def test_should_return_host_json(self):
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


class WhenTestingHostResourceOnPut(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)

    def test_should_throw_exception_for_tenant_not_found(self):
        self.stream.read.return_value = u'{ "hostname" : "host1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.host_id)

    def test_should_throw_exception_for_hostname_empty(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "", ' \
            u'"ip_address_v4": "192.168.1.1" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_put(self.req, self.resp, self.tenant_id,
                                     self.not_valid_host_id)

    def test_should_throw_exception_for_host_not_found(self):
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

    def test_should_throw_exception_for_host_duplicate_name(self):
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

    def test_should_throw_exception_for_invalid_profile(self):
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

    def test_should_return_200(self):
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

    def test_should_return_200_with_empty_profile(self):
        self.stream.read.return_value = \
            u'{ "hostname" : "host77", ' \
            u'"ip_address_v4": "192.168.1.1", ' \
            u'"ip_address_v6": "2001:0db8:85a3:0042:1000:8a2e:0370:7334", ' \
            u'"profile_id": "" }'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_put(self.req, self.resp, self.tenant_id,
                                 self.host_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingHostResourceOnDelete(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)

    def test_should_throw_exception_for_tenants_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.host_id)

    def test_should_throw_exception_for_host_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                        self.not_valid_host_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_delete(self.req, self.resp, self.tenant_id,
                                    self.host_id)
        self.assertEquals(falcon.HTTP_200, self.resp.status)


class WhenTestingTokenResourceOnHead(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)

    def test_should_throw_exception_for_tenant_not_found(self):
        self.req.get_header.return_value = \
            'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_head(self.req, self.resp, self.tenant_id)

    def test_should_call_tenant_not_found(self):
        tenant_not_found_method = MagicMock(
            side_effect=falcon.HTTPError(falcon.HTTP_404, "tenant_not_found"))
        self.req.get_header.return_value = \
            'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found), \
                patch('meniscus.api.tenant.resources._tenant_not_found',
                      tenant_not_found_method):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_head(self.req, self.resp, self.tenant_id)
            tenant_not_found_method.assert_called_once_with()

    def test_should_throw_exception_for_tenant_not_found(self):
        self.req.get_header.return_value = \
            'zzz7104e-8d93-47dc-a49a-8fb0d39e5192'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_head(self.req, self.resp, self.tenant_id)

    def test_should_call_message_token_is_invalid(self):
        message_token_is_invalid_method = MagicMock(
            side_effect=falcon.HTTPError(falcon.HTTP_400, "invalid token"))
        self.req.get_header.return_value = \
            'zzz7104e-8d93-47dc-a49a-8fb0d39e5192'
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found), \
                patch('meniscus.api.tenant.resources._tenant_not_found',
                      message_token_is_invalid_method):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_head(self.req, self.resp, self.tenant_id)
            message_token_is_invalid_method.assert_called_once_with()

    def test_should_return_200_valid_token(self):
        self.req.get_header.return_value = self.token_original
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_head(self.req, self.resp, self.tenant_id)
            self.assertEquals(self.resp.status, falcon.HTTP_200)

    def test_should_return_200_previous_token(self):
        self.req.get_header.return_value = self.token_previous
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_head(self.req, self.resp, self.tenant_id)
            self.assertEquals(self.resp.status, falcon.HTTP_200)


class WhenTestingTokenResourceOnGet(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)

    def test_should_throw_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_get(self.req, self.resp, self.tenant_id)

    def test_should_return_200(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)
        token_dict = parsed_body['token']
        self.assertEquals(falcon.HTTP_200, self.resp.status)
        self.assertTrue('valid'in token_dict.keys())
        self.assertTrue('previous' in token_dict.keys())
        self.assertTrue('last_changed' in token_dict.keys())


class WhenTestingTokenResourceValidation(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)

    def test_should_throw_exception_for_non_bool_value(self):
        body = {'token': {'invalidate_now': 'True'}}
        with(self.assertRaises(falcon.HTTPError)):
            self.resource._validate_req_body_on_post(body)

    def test_should_not_throw_exception_for_bool_value(self):
        body = {'token': {'invalidate_now': True}}
        self.resource._validate_req_body_on_post(body)

    def test_iso_timestamp_format_should_throw_exception_for_time_limit(self):
        bad_time_format = "2013-03-19"
        new_token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                          None, bad_time_format)
        with(self.assertRaises(ValueError)):
            self.resource._validate_token_min_time_limit_reached(new_token)

    def test_should_throw_exception_for_time_limit(self):
        new_token = Token()
        with(self.assertRaises(falcon.HTTPError)):
            self.resource._validate_token_min_time_limit_reached(new_token)

    def test_should_not_throw_exception_for_time_limit(self):
        self.resource._validate_token_min_time_limit_reached(self.token)


class WhenTestingTokenResourceOnPost(TestingTenantApiBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)

    def test_should_throw_exception_for_tenant_not_found_on_post(self):
        self.req.stream = None

        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            with self.assertRaises(falcon.HTTPError):
                self.resource.on_post(self.req, self.resp, self.tenant_id)

    def test_should_invalidate_now(self):
        self.req.stream = MagicMock(return_value=True)
        self.req.stream.read.return_value = \
            u'{"token": {"invalidate_now": true}}'

        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
                self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertNotEqual(self.tenant.token.valid, self.token_original)
        self.assertEqual(self.tenant.token.previous, None)
        self.assertGreater(self.tenant.token.last_changed,
                           self.timestamp_original)
        self.assertEqual(falcon.HTTP_203, self.resp.status)

    def test_should_invalidate_with_optional_body(self):
        self.req.stream = None
        self.req.stream = MagicMock(return_value=True)
        self.req.stream.read.return_value = \
            u'{"token": {"invalidate_now": false}}'

        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertNotEqual(self.tenant.token.valid, self.token_original)
        self.assertEqual(self.tenant.token.previous, self.token_original)
        self.assertGreater(self.tenant.token.last_changed,
                           self.timestamp_original)
        self.assertEqual(falcon.HTTP_203, self.resp.status)

    def test_should_invalidate(self):
        self.req.stream = None

        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_post(self.req, self.resp, self.tenant_id)
        self.assertNotEqual(self.tenant.token.valid, self.token_original)
        self.assertEqual(self.tenant.token.previous, self.token_original)
        self.assertGreater(self.tenant.token.last_changed,
                           self.timestamp_original)
        self.assertEqual(falcon.HTTP_203, self.resp.status)


if __name__ == '__main__':
    unittest.main()
