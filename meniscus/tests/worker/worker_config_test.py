import unittest
from meniscus.config import init_config, get_config
from meniscus.api.worker.worker_config import worker_group, WORKER_OPTIONS


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenConfiguring())


class WhenConfiguring(unittest.TestCase):

    def test_loading(self):

        init_config(['--config-file', '../etc/meniscus/worker.cfg.example'])

        conf = get_config()
        conf.register_group(worker_group)
        conf.register_opts(WORKER_OPTIONS, group=worker_group)
        self.assertTrue(conf.worker_cfg.verbose)
        self.assertEqual(conf.worker_cfg.personality, 'cfg_worker_personality')
        self.assertEqual(conf.worker_cfg.name, 'cfg_worker_name')

if __name__ == '__main__':
    unittest.main()