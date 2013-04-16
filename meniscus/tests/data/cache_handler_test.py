import unittest

from mock import MagicMock
from mock import patch

from meniscus.data.cache_handler import BLACKLIST_EXPIRES
from meniscus.data.cache_handler import BlacklistCache
from meniscus.data.cache_handler import BroadcastCache
from meniscus.data.cache_handler import Cache
from meniscus.data.cache_handler import CACHE_BROADCAST
from meniscus.data.cache_handler import CACHE_BLACKLIST
from meniscus.data.cache_handler import CACHE_CONFIG
from meniscus.data.cache_handler import CACHE_TENANT
from meniscus.data.cache_handler import CACHE_TOKEN
from meniscus.data.cache_handler import ConfigCache
from meniscus.data.cache_handler import CONFIG_EXPIRES
from meniscus.data.cache_handler import DEFAULT_EXPIRES
from meniscus.data.cache_handler import TenantCache
from meniscus.data.cache_handler import TokenCache
from meniscus.data.cache_handler import NativeProxy
from meniscus.data.model.tenant import Tenant
from meniscus.data.model.tenant import Token
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.openstack.common import jsonutils


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingBaseCache())
    suite.addTest(WhenTestingConfigCache())
    suite.addTest(WhenTestingTenantCache())
    return suite


class WhenTestingBaseCache(unittest.TestCase):
    def test_cache_raises_not_implemented(self):
        cache = Cache()
        with self.assertRaises(NotImplementedError):
            cache.clear()


class WhenTestingConfigCache(unittest.TestCase):
    def setUp(self):
        self.cache_clear = MagicMock()
        self.cache_true = MagicMock(return_value=True)
        self.cache_false = MagicMock(return_value=False)
        self.cache_update = MagicMock()
        self.cache_set = MagicMock()
        self.cache_del = MagicMock()
        self.config = WorkerConfiguration(
            personality='correlation',
            personality_module='meniscus.personas.worker.correlation.app',
            worker_id='fgc7104e-8d93-47dc-a49a-8fb0d39e5192',
            worker_token='bbd6307f-8d93-47dc-a49a-8fb0d39e5192',
            coordinator_uri='http://192.168.1.2/v1')
        self.config_json = jsonutils.dumps(self.config.format())
        self.cache_get_config = MagicMock(return_value=self.config_json)
        self.routes = [
            {
                "service_domain": "correlation|normalization|storage",
                "targets": [
                    {
                        "worker_id": "488eb3fc-34dd-48ad-a1bb-99ee2a43bf1d",
                        "ip_address_v4": "192.168.100.101",
                        "ip_address_v6": "::1",
                        "status": "online|draining"
                    },
                    {
                        "worker_id": "e0ac0dc3-694e-4522-94f0-fb25a4dbb8a1",
                        "ip_address_v4": "192.168.100.102",
                        "ip_address_v6": "::1",
                        "status": "online|draining"
                    },
                    {
                        "worker_id": "64d7a5ab-55b6-4ff7-b362-0d67544bb6f8",
                        "ip_address_v4": "192.168.100.103",
                        "ip_address_v6": "::1",
                        "status": "online|draining"
                    }
                ]
            }
        ]
        self.routes_json = jsonutils.dumps(self.routes)
        self.cache_get_routes = MagicMock(return_value=self.routes_json)

    def test_clear_calls_cache_clear(self):
        with patch.object(NativeProxy, 'cache_clear', self.cache_clear):
            config_cache = ConfigCache()
            config_cache.clear()
        self.cache_clear.assert_called_once_with(CACHE_CONFIG)

    def test_set_config_calls_cache_update(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_update', self.cache_update):
            config_cache = ConfigCache()
            config_cache.set_config(self.config)

        self.cache_update.assert_called_once_with(
            'worker_configuration', jsonutils.dumps(self.config.format()),
            CONFIG_EXPIRES, CACHE_CONFIG)

    def test_set_config_calls_cache_set(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_set', self.cache_set):
            config_cache = ConfigCache()
            config_cache.set_config(self.config)

        self.cache_set.assert_called_once_with(
            'worker_configuration', jsonutils.dumps(self.config.format()),
            CONFIG_EXPIRES, CACHE_CONFIG)

    def test_get_config_calls_returns_config(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_get',  self.cache_get_config):
            config_cache = ConfigCache()
            config = config_cache.get_config()

        self.cache_get_config.assert_called_once_with(
            'worker_configuration', CACHE_CONFIG)
        self.assertIsInstance(config, WorkerConfiguration)

    def test_get_config_calls_returns_none(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false):
            config_cache = ConfigCache()
            config = config_cache.get_config()

        self.assertIs(config, None)

    def test_delete_config_calls_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            config_cache = ConfigCache()
            config_cache.delete_config()

        self.cache_del.assert_called_once_with(
            'worker_configuration', CACHE_CONFIG)

    def test_delete_config_does_not_call_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            config_cache = ConfigCache()
            config_cache.delete_config()

        with self.assertRaises(AssertionError):
            self.cache_del.assert_called_once_with(
                'worker_configuration', CACHE_CONFIG)

    def test_set_routes_calls_cache_update(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_update', self.cache_update):
            config_cache = ConfigCache()
            config_cache.set_routes(self.routes)

        self.cache_update.assert_called_once_with(
            'routes', jsonutils.dumps(self.routes),
            CONFIG_EXPIRES, CACHE_CONFIG)

    def test_set_routes_calls_cache_set(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_set', self.cache_set):
            config_cache = ConfigCache()
            config_cache.set_routes(self.routes)

        self.cache_set.assert_called_once_with(
            'routes', jsonutils.dumps(self.routes),
            CONFIG_EXPIRES, CACHE_CONFIG)

    def test_get_routes_calls_returns_config(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_get',  self.cache_get_routes):
            config_cache = ConfigCache()
            routes = config_cache.get_routes()

        self.cache_get_routes.assert_called_once_with(
            'routes', CACHE_CONFIG)
        self.assertEqual(routes, self.routes)

    def test_get_routes_calls_returns_none(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false):
            config_cache = ConfigCache()
            routes = config_cache.get_routes()

        self.assertIs(routes, None)

    def test_delete_routes_calls_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            config_cache = ConfigCache()
            config_cache.delete_routes()

        self.cache_del.assert_called_once_with(
            'routes', CACHE_CONFIG)

    def test_delete_routes_does_not_call_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            config_cache = ConfigCache()
            config_cache.delete_routes()

        with self.assertRaises(AssertionError):
            self.cache_del.assert_called_once_with(
                'routes', CACHE_CONFIG)


class WhenTestingTenantCache(unittest.TestCase):
    def setUp(self):
        self.cache_clear = MagicMock()
        self.cache_true = MagicMock(return_value=True)
        self.cache_false = MagicMock(return_value=False)
        self.cache_update = MagicMock()
        self.cache_set = MagicMock()
        self.cache_del = MagicMock()
        self.tenant_id = '101'
        self.tenant = Tenant(
            tenant_id=self.tenant_id,
            token=Token()
        )
        self.tenant_json = jsonutils.dumps(self.tenant.format())
        self.cache_get_tenant = MagicMock(return_value=self.tenant_json)

    def test_clear_calls_cache_clear(self):
        with patch.object(NativeProxy, 'cache_clear', self.cache_clear):
            tenant_cache = TenantCache()
            tenant_cache.clear()
        self.cache_clear.assert_called_once_with(CACHE_TENANT)

    def test_set_tenant_calls_cache_update(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_update', self.cache_update):
            tenant_cache = TenantCache()
            tenant_cache.set_tenant(self.tenant)

        self.cache_update.assert_called_once_with(
            self.tenant_id, jsonutils.dumps(self.tenant.format()),
            DEFAULT_EXPIRES, CACHE_TENANT)

    def test_set_tenant_calls_cache_set(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_set', self.cache_set):
            tenant_cache = TenantCache()
            tenant_cache.set_tenant(self.tenant)

        self.cache_set.assert_called_once_with(
            self.tenant_id, jsonutils.dumps(self.tenant.format()),
            DEFAULT_EXPIRES, CACHE_TENANT)

    def test_get_tenant_calls_returns_tenant(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_get',  self.cache_get_tenant):
            tenant_cache = TenantCache()
            tenant = tenant_cache.get_tenant(self.tenant_id)

        self.cache_get_tenant.assert_called_once_with(
            self.tenant_id, CACHE_TENANT)
        self.assertIsInstance(tenant, Tenant)

    def test_get_tenant_calls_returns_none(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false):
            tenant_cache = TenantCache()
            tenant = tenant_cache.get_tenant(self.tenant_id)

        self.assertIs(tenant, None)

    def test_delete_tenant_calls_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            tenant_cache = TenantCache()
            tenant_cache.delete_tenant(self.tenant_id)

        self.cache_del.assert_called_once_with(
            self.tenant_id, CACHE_TENANT)

    def test_delete_tenant_does_not_call_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            tenant_cache = TenantCache()
            tenant_cache.delete_tenant(self.tenant_id)

        with self.assertRaises(AssertionError):
            self.cache_del.assert_called_once_with(
                self.tenant_id, CACHE_TENANT)


class WhenTestingTokenCache(unittest.TestCase):
    def setUp(self):
        self.cache_clear = MagicMock()
        self.cache_true = MagicMock(return_value=True)
        self.cache_false = MagicMock(return_value=False)
        self.cache_update = MagicMock()
        self.cache_set = MagicMock()
        self.cache_del = MagicMock()
        self.tenant_id = '101'
        self.token = Token()
        self.token_json = jsonutils.dumps(self.token.format())
        self.cache_get_token = MagicMock(return_value=self.token_json)

    def test_clear_calls_cache_clear(self):
        with patch.object(NativeProxy, 'cache_clear', self.cache_clear):
            token_cache = TokenCache()
            token_cache.clear()
        self.cache_clear.assert_called_once_with(CACHE_TOKEN)

    def test_set_token_calls_cache_update(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_update', self.cache_update):
            token_cache = TokenCache()
            token_cache.set_token(self.tenant_id, self.token)

        self.cache_update.assert_called_once_with(
            self.tenant_id, jsonutils.dumps(self.token.format()),
            DEFAULT_EXPIRES, CACHE_TOKEN)

    def test_set_token_calls_cache_set(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_set', self.cache_set):
            token_cache = TokenCache()
            token_cache.set_token(self.tenant_id, self.token)

        self.cache_set.assert_called_once_with(
            self.tenant_id, jsonutils.dumps(self.token.format()),
            DEFAULT_EXPIRES, CACHE_TOKEN)

    def test_get_token_calls_returns_tenant(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_get',  self.cache_get_token):
            token_cache = TokenCache()
            token = token_cache.get_token(self.tenant_id)

        self.cache_get_token.assert_called_once_with(
            self.tenant_id, CACHE_TOKEN)
        self.assertIsInstance(token, Token)

    def test_get_token_calls_returns_none(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false):
            token_cache = TokenCache()
            token = token_cache.get_token(self.tenant_id)

        self.assertIs(token, None)

    def test_delete_token_calls_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            token_cache = TokenCache()
            token_cache.delete_token(self.tenant_id)

        self.cache_del.assert_called_once_with(
            self.tenant_id, CACHE_TOKEN)

    def test_delete_token_does_not_call_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            token_cache = TokenCache()
            token_cache.delete_token(self.tenant_id)

        with self.assertRaises(AssertionError):
            self.cache_del.assert_called_once_with(
                self.tenant_id, CACHE_TOKEN)


class WhenTestingBroadcastCache(unittest.TestCase):
    def setUp(self):
        self.cache_clear = MagicMock()
        self.cache_true = MagicMock(return_value=True)
        self.cache_false = MagicMock(return_value=False)
        self.cache_update = MagicMock()
        self.cache_set = MagicMock()
        self.cache_del = MagicMock()
        self.message_type = 'ROUTES'
        self.target_list = [
            'http://hostname1.domain:8080/callback',
            'http://hostname2.domain:8080/callback',
            'http://hostname3.domain:8080/callback',
            'http://hostname4.domain:8080/callback'
        ]
        #self.token = Token()
        #self.token_json = jsonutils.dumps(self.token.format())
        self.cache_get_targets = MagicMock(return_value=self.target_list)

    def test_clear_calls_cache_clear(self):
        with patch.object(NativeProxy, 'cache_clear', self.cache_clear):
            broadcast_cache = BroadcastCache()
            broadcast_cache.clear()
        self.cache_clear.assert_called_once_with(CACHE_BROADCAST)

    def test_set_message_and_targets_calls_cache_update(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_update', self.cache_update):
            broadcast_cache = BroadcastCache()
            broadcast_cache.set_message_and_targets(self.message_type,
                                                    self.target_list)

        self.cache_update.assert_called_once_with(
            self.message_type, str(self.target_list),
            DEFAULT_EXPIRES, CACHE_BROADCAST)

    def test_set_message_and_targets_calls_cache_set(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_set', self.cache_set):
            broadcast_cache = BroadcastCache()
            broadcast_cache.set_message_and_targets(self.message_type,
                                                    self.target_list)

        self.cache_set.assert_called_once_with(
            self.message_type, str(self.target_list),
            DEFAULT_EXPIRES, CACHE_BROADCAST)

    def test_get_targets_calls_returns_target_list(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_get',  self.cache_get_targets):
            broadcast_cache = BroadcastCache()
            targets = broadcast_cache.get_targets(self.message_type)

        self.cache_get_targets.assert_called_once_with(
            self.message_type, CACHE_BROADCAST)
        self.assertEquals(targets, self.target_list)

    def test_get_targets_calls_returns_none(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false):
            broadcast_cache = BroadcastCache()
            targets = broadcast_cache.get_targets(self.target_list)

        self.assertIs(targets, None)

    def test_delete_message_calls_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            broadcast_cache = BroadcastCache()
            broadcast_cache.delete_message(self.message_type)

        self.cache_del.assert_called_once_with(
            self.message_type, CACHE_BROADCAST)

    def test_delete_message_does_not_call_cache_del(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false
        ), patch.object(NativeProxy, 'cache_del', self.cache_del):
            broadcast_cache = BroadcastCache()
            broadcast_cache.delete_message(self.message_type)

        with self.assertRaises(AssertionError):
            self.cache_del.assert_called_once_with(
                self.message_type, CACHE_BROADCAST)


class WhenTestingBlacklistCache(unittest.TestCase):
    def setUp(self):
        self.cache_clear = MagicMock()
        self.cache_true = MagicMock(return_value=True)
        self.cache_false = MagicMock(return_value=False)
        self.cache_update = MagicMock()
        self.cache_set = MagicMock()
        self.cache_del = MagicMock()
        self.worker_id = 'd45aecac-a959-42f0-95da-36e3d8eeb3ec'

    def test_clear_calls_cache_clear(self):
        with patch.object(NativeProxy, 'cache_clear', self.cache_clear):
            blacklist_cache = BlacklistCache()
            blacklist_cache.clear()
        self.cache_clear.assert_called_once_with(CACHE_BLACKLIST)

    def test_add_blacklist_worker_calls_cache_update(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true
        ), patch.object(NativeProxy, 'cache_update', self.cache_update):
            blacklist_cache = BlacklistCache()
            blacklist_cache.add_blacklist_worker(self.worker_id)
        self.cache_update.assert_called_once()

    def test_is_worker_blacklisted_returns_false(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_false):
            blacklist_cache = BlacklistCache()
            return_val = blacklist_cache.is_worker_blacklisted(self.worker_id)

        self.assertFalse(return_val)
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true):
            blacklist_cache = BlacklistCache()
            return_val = blacklist_cache.is_worker_blacklisted(None)

        self.assertFalse(return_val)

    def test_is_worker_blacklisted_returns_true(self):
        with patch.object(
                NativeProxy, 'cache_exists', self.cache_true):
            blacklist_cache = BlacklistCache()
            return_val = blacklist_cache.is_worker_blacklisted(self.worker_id)

        self.assertTrue(return_val)


if __name__ == '__main__':
    unittest.main()
