from oslo.config import cfg
from meniscus.config import get_config

# Node configuration options
node_group = cfg.OptGroup(name='node_cfg',
                          title='Node Configuration Test')
get_config().register_group(node_group)

NODE_OPTIONS = [
    cfg.BoolOpt('verbose', default=False, ),
    cfg.StrOpt('personality', default='default_personality',
               help="""Node personality"""),
    cfg.StrOpt('name', default='default_name', help="""Node name""")
]

get_config().register_opts(NODE_OPTIONS, group=node_group)
