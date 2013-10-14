import unittest

import falcon
import falcon.testing as testing
from mock import MagicMock
from mock import patch
with patch('meniscus.api.tenant.resources.tenant_util', MagicMock()):
    from meniscus.api.tenant.resources import EventProducerResource
    from meniscus.api.tenant.resources import EventProducersResource
    from meniscus.api.tenant.resources import MESSAGE_TOKEN
    from meniscus.api.tenant.resources import TenantResource
    from meniscus.api.tenant.resources import TokenResource
    from meniscus.api.tenant.resources import UserResource
from meniscus.data.model.tenant import EventProducer
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.openstack.common import jsonutils


def suite():

    test_suite = unittest.TestSuite()

    test_suite.addTest(TestingTenantResourceOnPost())

    test_suite.addTest(TestingUserResourceOnGet())
    test_suite.addTest(TestingUserResourceOnDelete())

    test_suite.addTest(TestingEventProducersResourceOnGet())
    test_suite.addTest(TestingEventProducersResourceOnPost())

    test_suite.addTest(TestingEventProducerResourceOnGet())
    test_suite.addTest(TestingEventProducerResourceOnPut())
    test_suite.addTest(TestingEventProducerResourceOnDelete())

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
        self.producer_id = 432
        self.producer_name = 'producer1'
        self.producer_id_2 = 432
        self.producer_name_2 = 'producer2'
        self.not_valid_producer_id = 777
        self.producers = [
            EventProducer(self.producer_id, self.producer_name, 'syslog'),
            EventProducer(self.producer_id_2, self.producer_name_2, 'syslog')]
        self.token_original = 'ffe7104e-8d93-47dc-a49a-8fb0d39e5192'
        self.token_previous = 'bbd6302e-8d93-47dc-a49a-8fb0d39e5192'
        self.token_invalid = 'xxxyyy33-8d93-47dc-a49a-8fb0d39e5192'
        self.timestamp_original = "2013-03-19T18:16:48.411029Z"
        self.token = Token(self.token_original, self.token_previous,
                           self.timestamp_original)
        self.tenant_id = '1234'
        self.tenant_name = 'TenantName'
        self.tenant = Tenant(self.tenant_id, self.token,
                             event_producers=self.producers)
        self.tenant_not_found = MagicMock(return_value=None)
        self.tenant_found = MagicMock(return_value=self.tenant)

        self._set_resource()

    def _set_resource(self):
        pass


class TestingTenantResourceOnPost(TenantApiTestBase):
    def _set_resource(self):
        self.resource = TenantResource()
        self.test_route = '/v1/tenant'
        self.api.add_route(self.test_route, self.resource)

    def test_return_400_for_tenant_id_empty(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": ""}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_tenant_name_empty(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": "123",
                                                 "tenant_name": ""}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_tenant_not_provided(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"token": "1321316464646"}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_400_for_tenant_exist(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": "1234"}}))
            self.assertEqual(falcon.HTTP_400, self.srmock.status)

    def test_return_200_for_tenant_created(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found), patch(
                'meniscus.api.tenant.resources.tenant_util.create_tenant',
                MagicMock()):
            self.simulate_request(
                self.test_route,
                method='POST',
                headers={'content-type': 'application/json'},
                body=jsonutils.dumps({'tenant': {"tenant_id": "1234"}}))
            self.assertEqual(falcon.HTTP_201, self.srmock.status)


class TestingUserResourceOnGet(TenantApiTestBase):
    def _set_resource(self):
        self.resource = UserResource()
        self.test_route = '/v1/tenant/{tenant_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_201_if_tenant_not_found_create_it(self):
        self.ds_handler_no_tenant = MagicMock()
        self.ds_handler_no_tenant.put = MagicMock()
        self.ds_handler_no_tenant.find_one.side_effect = [None, self.tenant]
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant'):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_return_200_with_tenant_json(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_tenant_json(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('tenant' in parsed_body)
        parsed_tenant = parsed_body['tenant']
        tenant_dict = self.tenant.format()
        for key in tenant_dict:
            self.assertTrue(key in parsed_tenant)
            self.assertEqual(tenant_dict[key], parsed_tenant[key])


class TestingEventProducersResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducersResource()
        self.test_route = '/v1/tenant/{tenant_id}/producers'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_producer_json_on_get(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)

        self.assertTrue('event_producers'in parsed_body.keys())
        self.assertEqual(len(self.producers),
                         len(parsed_body['event_producers']))

        for producer in parsed_body['event_producers']:
            self.assertTrue(producer in [p.format() for p in self.producers])


class TestingEventProducersResourceOnPost(TenantApiTestBase):

    def _set_resource(self):
        self.resource = EventProducersResource()
        self.test_route = '/v1/tenant/{tenant_id}/producers'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        save_tenant = MagicMock()
        create_event_producer = MagicMock()
        with patch(
                'meniscus.api.tenant.resources.tenant_util.find_tenant',
                self.tenant_found), \
            patch(
                'meniscus.api.tenant.resources.tenant_util.save_tenant',
                save_tenant), \
            patch(
                'meniscus.api.tenant.resources.'
                'tenant_util.create_event_producer',
                create_event_producer):

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
        save_tenant = MagicMock()
        create_event_producer = MagicMock()
        with patch(
                'meniscus.api.tenant.resources.tenant_util.find_tenant',
                self.tenant_found), \
            patch(
                'meniscus.api.tenant.resources.tenant_util.save_tenant',
                save_tenant), \
            patch(
                'meniscus.api.tenant.resources.'
                'tenant_util.create_event_producer',
                create_event_producer):

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
        save_tenant = MagicMock()
        create_event_producer = MagicMock()
        with patch(
            'meniscus.api.tenant.resources.tenant_util.find_tenant',
            self.tenant_found), \
            patch(
                'meniscus.api.tenant.resources.tenant_util.save_tenant',
                save_tenant), \
            patch(
                'meniscus.api.tenant.resources.'
                'tenant_util.create_event_producer',
                create_event_producer):

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
        save_tenant = MagicMock()
        create_event_producer = MagicMock()
        with patch(
                'meniscus.api.tenant.resources.tenant_util.find_tenant',
                self.tenant_found), \
            patch(
                'meniscus.api.tenant.resources.tenant_util.save_tenant',
                save_tenant), \
            patch(
                'meniscus.api.tenant.resources.'
                'tenant_util.create_event_producer',
                create_event_producer):
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
        self.resource = EventProducerResource()
        self.test_route = '/v1/tenant/{tenant_id}' \
                          '/producers/{event_producer_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.not_valid_producer_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_producer_json(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        self.resource = EventProducerResource()
        self.test_route = '/v1/tenant/{tenant_id}' \
                          '/producers/{event_producer_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        save_tenant = MagicMock()
        with patch(
                'meniscus.api.tenant.resources.tenant_util.find_tenant',
                self.tenant_found), \
                patch(
                    'meniscus.api.tenant.resources.tenant_util.save_tenant',
                    save_tenant):
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
        self.resource = EventProducerResource()
        self.test_route = '/v1/tenant/{tenant_id}' \
                          '/producers/{event_producer_id}'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_producer_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.not_valid_producer_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        mock_tenant_util = MagicMock()
        mock_tenant_util.find_tenant.return_value = self.tenant_found

        with patch('meniscus.api.tenant.resources.tenant_util',
                   mock_tenant_util):
            self.simulate_request(
                '/v1/tenant/{tenant_id}/producers/{event_producer_id}'.format(
                    tenant_id=self.tenant_id,
                    event_producer_id=self.producer_id
                ),
                method='DELETE')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingTokenResourceOnHead(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource()
        self.test_route = '/v1/tenant/{tenant_id}/token'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_original})
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_404_for_invalid_token(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_invalid})
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_return_200_valid_token(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_original})
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_200_previous_token(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route,
                method='HEAD',
                headers={MESSAGE_TOKEN: self.token_previous})
            self.assertEqual(falcon.HTTP_200, self.srmock.status)


class TestingTokenResourceOnGet(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource()
        self.test_route = '/v1/tenant/{tenant_id}/token'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_not_found):
            self.simulate_request(
                self.test_route,
                method='GET',
                headers={MESSAGE_TOKEN: self.token_original})
            self.assertEqual(falcon.HTTP_404, self.srmock.status)

    def test_should_return_200_on_get(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.simulate_request(
                self.test_route.format(
                    tenant_id=self.tenant_id
                ),
                method='GET')
            self.assertEqual(falcon.HTTP_200, self.srmock.status)

    def test_should_return_token_json(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found):
            self.resource.on_get(self.req, self.resp, self.tenant_id)

        parsed_body = jsonutils.loads(self.resp.body)
        parsed_token = parsed_body['token']
        token_dict = self.token.format()
        for key in token_dict:
            self.assertEqual(parsed_token[key], token_dict[key])


class TestingTokenResourceOnPost(TenantApiTestBase):

    def _set_resource(self):
        self.resource = TokenResource()
        self.test_route = '/v1/tenant/{tenant_id}/token'
        self.api.add_route(self.test_route, self.resource)

    def test_return_404_for_tenant_not_found(self):
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found), patch(
                'meniscus.api.tenant.resources.tenant_util.save_tenant',
                MagicMock()):
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
        with patch('meniscus.api.tenant.resources.tenant_util.find_tenant',
                   self.tenant_found), patch(
                'meniscus.api.tenant.resources.tenant_util.save_tenant',
                MagicMock()):
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
        self.resource = TokenResource()

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
