import unittest

import falcon
import falcon.testing as testing
from mock import MagicMock
from mock import patch

from meniscus.api.tenant.resources import EventProducerResource
from meniscus.api.tenant.resources import EventProducersResource
from meniscus.api.tenant.resources import HostResource
from meniscus.api.tenant.resources import HostProfileResource
from meniscus.api.tenant.resources import HostsResource
from meniscus.api.tenant.resources import HostProfilesResource
from meniscus.api.tenant.resources import MESSAGE_TOKEN
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

    test_suite.addTest(TestingTenantResourceOnPost())

    test_suite.addTest(TestingUserResourceOnGet())
    test_suite.addTest(TestingUserResourceOnDelete())

    test_suite.addTest(TestingHostProfilesResourceOnGet())
    test_suite.addTest(TestingHostProfilesResourceOnPost())

    test_suite.addTest(TestingHostProfileResourceOnGet())
    test_suite.addTest(TestingHostProfileResourceOnPut())
    test_suite.addTest(TestingHostProfileResourceOnDelete())

    test_suite.addTest(TestingEventProducersResourceOnGet())
    test_suite.addTest(TestingEventProducersResourceOnPost())

    test_suite.addTest(TestingEventProducerResourceOnGet())
    test_suite.addTest(TestingEventProducerResourceOnPut())
    test_suite.addTest(TestingEventProducerResourceOnDelete())

    test_suite.addTest(TestingHostsResourceOnGet())
    test_suite.addTest(TestingHostsResourceOnPost())

    test_suite.addTest(TestingHostResourceOnGet())
    test_suite.addTest(TestingHostResourceOnPut())
    test_suite.addTest(TestingHostResourceOnDelete())

    test_suite.addTest(TestingTokenResourceOnHead())
    test_suite.addTest(TestingTokenResourceOnGet())
    test_suite.addTest(TestingTokenResourceOnPost())

    return test_suite


class TenantApiTestBase(testing.TestBase):
    def before(self):
        self.db_handler = MagicMock()
        self.req = MagicMock()
        self.req.content_type = 'application/json'

        self.resp = MagicMock()
        self.profile_id = 123
        self.profile_name = 'profile1'
        self.profile_id_2 = 456
        self.profile_name_2 = 'profile2'
        self.not_valid_profile_id = 999
        self.profiles = [HostProfile(self.profile_id, self.profile_name,
                                     event_producer_ids=[432, 433]),
                         HostProfile(self.profile_id_2, self.profile_name_2,
                                     event_producer_ids=[432, 433])]
        self.producer_id = 432
        self.producer_name = 'producer1'
        self.producer_id_2 = 432
        self.producer_name_2 = 'producer2'
        self.not_valid_producer_id = 777
        self.producers = [
            EventProducer(self.producer_id, self.producer_name, 'syslog'),
            EventProducer(self.producer_id_2, self.producer_name_2, 'syslog')]
        self.host_id = 765
        self.host_name = 'host1'
        self.host_id_2 = 766
        self.host_name_2 = 'host2'
        self.not_valid_host_id = 888
        self.host_1 = Host(self.host_id, self.host_name,
                           ip_address_v4='192.168.1.1',
                           profile_id=self.profile_id)
        self.host_2 = Host(self.host_id_2, self.host_name_2,
                           ip_address_v4='192.168.2.1',
                           profile_id=self.profile_id_2)
        self.hosts = [self.host_1, self.host_2]
        self.token_original = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.token_previous = 'bbd6302e-8d93-47dc-a49a-8fb0d39e5192'
        self.token_invalid = 'xxxyyy33-8d93-47dc-a49a-8fb0d39e5192'
        self.timestamp_original = "2013-03-19T18:16:48.411029Z"
        self.token = Token(self.token_original, self.token_previous,
                           self.timestamp_original)
        self.tenant_id = '1234'
        self.tenant_name = 'TenantName'
        self.tenant = Tenant(self.tenant_id, self.token,
                             profiles=self.profiles,
                             event_producers=self.producers,
                             hosts=self.hosts)
        self.tenant_not_found = MagicMock(return_value=None)
        self.tenant_found = MagicMock(return_value=self.tenant)

        self._set_resource()

    def _set_resource(self):
        pass


class TestingTenantResourceOnPost(TenantApiTestBase):
    def _set_resource(self):
        self.resource = TenantResource(self.db_handler)
        self.test_route = '/v1/tenant'
        self.api.add_route(self.test_route, self.resource)

    def test_return_400_for_tenant_id_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": ""}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_tenant_name_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": "123",
                                                 "tenant_name": ""}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_tenant_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"token": "1321316464646"}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_tenant_exist(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": "1234"}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_200_for_tenant_created(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": "1234"}}))
            self.assertEqual(falcon.HTTP_201, self.srmock.status)


class TestingUserResourceOnGet(TenantApiTestBase):
    def _set_resource(self):
        self.resource = UserResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_200_with_tenant_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_tenant_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('tenant' in parsed_body)
        parsed_tenant = parsed_body['tenant']
        tenant_dict = self.tenant.format()
        for key in tenant_dict:
            self.assertTrue(key in parsed_tenant)
            self.assertEqual(tenant_dict[key], parsed_tenant[key])


class TestingUserResourceOnDelete(TenantApiTestBase):

    def _set_resource(self):
        self.resource = UserResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_200_for_tenant_deleted(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='DELETE')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingHostProfilesResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostProfilesResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/profiles'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_200_for_tenant_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_profiles_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('profiles' in parsed_body.keys())
        self.assertEqual(len(self.profiles), len(parsed_body['profiles']))
        parsed_profiles = parsed_body['profiles']
        profiles_dict = [p.format() for p in self.profiles]
        for profile in profiles_dict:
            self.assertTrue(profile in parsed_profiles)


class TestingHostProfilesResourceOnPost(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostProfilesResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/profiles'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'profile': {'name': 'profile777'}}))
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_profile_already_exists(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'profile': {"name": "profile1"}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_profile_name_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'profile': {"name": ""}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_profile_name_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {'profile': {"event_producer_ids": [432]}}
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_producer_not_exist(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            "name": "profile99",
                            "event_producer_ids": [1, 2]
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_201_with_empty_producers(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            "name": "profile99",
                            "event_producer_ids": []
                        }
                    }
                )
            )

    def test_return_201_with_producers(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            "name": "profile99",
                            "event_producer_ids": [432]
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)


class TestingHostProfileResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostProfileResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/profiles/{profile_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_profile_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.not_valid_profile_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_profile_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.profile_id)

        parsed_body = jsonutils.loads(self.resp.body)
        parsed_profile = parsed_body['profile']
        profile_dict = [p.format() for p in self.profiles
                        if p._id == self.profile_id][0]
        for key in profile_dict:
            self.assertEqual(parsed_profile[key], profile_dict[key])


class TestingHostProfileResourceOnPut(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostProfileResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/profiles/{profile_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'profile': {'name': self.profile_name}}))
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_400_for_profile_name_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'profile': {'name': ""}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_404_for_profile_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.not_valid_profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'profile': {'name': self.profile_name}}))
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_change_name_when_new_name_in_use(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {'profile': {'name': self.profile_name_2}})
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_invalid_producer(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            'name': self.profile_name,
                            "event_producer_ids": [self.not_valid_producer_id]
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_invalid_producer_string(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            'name': self.profile_name,
                            "event_producer_ids": "string"
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_invalid_producer_string_in_array(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            'name': self.profile_name,
                            "event_producer_ids": ["3", 23]
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_200_on_profile_update(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'profile': {
                            'name': self.profile_name,
                            "event_producer_ids": [self.producer_id]
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingHostProfileResourceOnDelete(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostProfileResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/profiles/{profile_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_profile_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.not_valid_profile_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_delete(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/profiles/{profile_id}'.format(
                    tenant_id=self.tenant_id,
                    profile_id=self.profile_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingEventProducersResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducersResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/producers'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_producer_json_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('event_producers'in parsed_body.keys())
        self.assertEqual(len(self.profiles),
                         len(parsed_body['event_producers']))

        for producer in parsed_body['event_producers']:
            self.assertTrue(producer in [p.format() for p in self.producers])


class TestingEventProducersResourceOnPost(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducersResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/producers'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog'
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_name_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': '',
                            'pattern': 'syslog'
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_name_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'pattern': 'syslog'
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_pattern_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': ''
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_pattern_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55'
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_pattern_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_bad_durable(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'pattern': 'syslog',
                            'durable': "false"
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_bad_encrypted(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'pattern': 'syslog',
                            'encrypted': "true"
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_bad_type_sink(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog',
                            'sinks': 'true'
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_unsupported_and_supported_sink(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog',
                            'sinks': ['mysql', 'elasticsearch']
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_duplicate_supported_sink(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog',
                            'sinks': ['hdfs', 'hdfs']
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_201_for_one_supported_sink(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog',
                            'sinks': ['elasticsearch']
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)

    def test_return_201_for_multiple_supported_sink(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog',
                            'sinks': ["elasticsearch", "hdfs"]
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)

    def test_return_201_without_optional_fields(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog'
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)

    def test_return_201_with_optional_fields(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': 'producer55',
                            'pattern': 'syslog',
                            'durable': True,
                            'encrypted': False,
                            'sinks': ['elasticsearch']
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)


class TestingEventProducerResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}' \
                          '/producers/{event_producer_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.not_valid_producer_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_producer_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.producer_id)

        parsed_body = jsonutils.loads(self.resp.body)
        parsed_producer = parsed_body['event_producer']
        producer_dict = [p.format() for p in self.producers
                         if p._id == self.producer_id][0]

        for key in producer_dict:
            self.assertEqual(producer_dict[key], parsed_producer[key])


class TestingEventProducerResourceOnPut(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}' \
                          '/producers/{event_producer_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'pattern': 'syslog',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_name_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'pattern': 'syslog',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_name_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': '',
                            'pattern': 'syslog',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_pattern_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_pattern_name_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'pattern': '',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_404_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.not_valid_producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'pattern': 'syslog',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_producer_name_change_name_already_taken(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name_2,
                            'pattern': 'syslog',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_200_producer_updated(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'event_producer': {
                            'name': self.producer_name,
                            'pattern': 'syslog',
                            'encrypted': False,
                            'durable': False
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingEventProducerResourceOnDelete(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducerResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}' \
                          '/producers/{event_producer_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.not_valid_producer_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingHostsResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostsResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/hosts'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_host_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        parsed_hosts = parsed_body['hosts']
        for host in [h.format() for h in self.hosts]:
            host in parsed_hosts


class WhenTestingHostsResourceValidation(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostsResource(self.db_handler)

    def test_should_throw_value_error_bad_profile_id(self):
        body = {'hostname': 'host', 'profile_id': "bad_data"}
        self.assertRaises(
            falcon.HTTPError,
            self.resource._validate_req_body_on_post, body)

        body = {'hostname': 'host', 'profile_id': [1, 2]}
        self.assertRaises(
            falcon.HTTPError,
            self.resource._validate_req_body_on_post,
            body)


class TestingHostsResourceOnPost(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostsResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/hosts'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': 'newhost',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_hostname_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': '',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_name_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_host_already_exists(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': self.host_name,
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_invalid_profile(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': 'newhost',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.not_valid_profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_201_create_with_no_profile(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': 'newhost',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': ''
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)

    def test_return_201_for_created(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': 'newhost',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_201, self.srmock.status)


class TestingHostResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/hosts/{host_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_host_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.not_valid_host_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_host_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id,
                                 self.host_id)

        parsed_body = jsonutils.loads(self.resp.body)

        parsed_host = parsed_body['host']
        host_dict = self.host_1.format()
        for key in host_dict:
            self.assertEquals(parsed_host[key], host_dict[key])


class TestingHostResourceOnPut(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/hosts/{host_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': 'newhost',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_host_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.not_valid_host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': self.host_name,
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_hostname_empty(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': '',
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_hostname_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_change_hostname_name_already_exists(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': self.host_name_2,
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_invalid_profile(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': self.host_name,
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.not_valid_profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_200_on_update_no_profile(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': self.host_name,
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.not_valid_profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_200_on_update(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='PUT',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'host': {
                            'hostname': self.host_name,
                            'ip_address_v4': '127.0.0.1',
                            'ip_address_v6': '',
                            'profile_id': self.not_valid_profile_id
                        }
                    }
                )
            )
            self.assertEqual(falcon.HTTP_400, self.srmock.status)


class TestingHostResourceOnDelete(TenantApiTestBase):

    def _set_resource(self):
        self.resource = HostResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/hosts/{host_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_host_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.not_valid_host_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id,
                    host_id=self.host_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingTokenResourceOnHead(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/token'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_original})
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_invalid_token(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_invalid})
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_200_valid_token(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_original})
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_200_previous_token(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_previous})
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingTokenResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/token'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET',
                headers={MESSAGE_TOKEN: self.token_original})
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_token_json(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)
        parsed_token = parsed_body['token']
        token_dict = self.token.format()
        for key in token_dict:
            self.assertEqual(parsed_token[key], token_dict[key])


class TestingTokenResourceOnPost(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)
        self.test_route = '/v1/tenant/{tenant_id}/token'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'token': {
                            'invalidate_now': False
                        }
                    }
                ))
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_400_for_invalidate_now_not_provided(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'token': {
                        }
                    }
                ))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_invalidate_now_not_boolean(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'token': {
                            'invalidate_now': "true"
                        }
                    }
                ))
        self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_203_for_invalidate_now(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'token': {
                            'invalidate_now': True
                        }
                    }
                ))
        self.assertEqual(falcon.HTTP_203, self.srmock.status)
        self.assertNotEqual(self.tenant.token.valid, self.token_original)
        self.assertEqual(self.tenant.token.previous, None)
        self.assertGreater(self.tenant.token.last_changed,
                           self.timestamp_original)

    def test_return_203_for_invalidate_now_false(self):
        with patch('meniscus.api.tenant.resources.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps(
                    {
                        'token': {
                            'invalidate_now': False
                        }
                    }
                ))
        self.assertEqual(falcon.HTTP_203, self.srmock.status)
        self.assertNotEqual(self.tenant.token.valid, self.token_original)
        self.assertEqual(self.tenant.token.previous, self.token_original)
        self.assertGreater(self.tenant.token.last_changed,
                           self.timestamp_original)


class TestingTokenResourceValidation(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource(self.db_handler)

    def test_iso_timestamp_format_should_throw_exception_for_time_limit(self):
        bad_time_format = "2013-03-19"
        new_token = Token('ffe7104e-8d93-47dc-a49a-8fb0d39e5192',
                          None, bad_time_format)
        self.assertRaises(
            ValueError,
            self.resource._validate_token_min_time_limit_reached,
            new_token)

    def test_should_throw_exception_for_time_limit_not_reached(self):
        new_token = Token()
        self.assertRaises(
            falcon.HTTPError,
            self.resource._validate_token_min_time_limit_reached,
            new_token)

    def test_should_not_throw_exception_for_time_limit(self):
        self.assertTrue(
            self.resource._validate_token_min_time_limit_reached(self.token))


if __name__ == '__main__':
    unittest.main()
