import unittest
from oslo.config import cfg
from meniscus.config import init_config, get_config

# Node configuration options
node_group = cfg.OptGroup(name='node_cfg',
                          title='Node Configuration Test')
get_config().register_group(node_group)

NODE_OPTIONS = [
    cfg.BoolOpt('verbose', default=False, ),
    cfg.StrOpt('personality', default='default_personality',
               help="""Node personality"""),
    cfg.StrOpt('name', default='default_name', help="""Node name""" )
]

get_config().register_opts(NODE_OPTIONS, group=node_group)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenConfiguring())


class WhenConfiguring(unittest.TestCase):

    def test_loading(self):

        init_config(['--config-file', '../../node.cfg.example'])

        conf = get_config()
        conf.register_group(node_group)
        conf.register_opts(NODE_OPTIONS, group=node_group)

        self.assertTrue(conf.node_cfg.verbose)
        self.assertEqual(conf.node_cfg.personality, 'cfg_node_personality')
        self.assertEqual(conf.node_cfg.name, 'cfg_node_name')

# if __name__ == '__main__':
#     unittest.main()