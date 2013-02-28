from oslo.config import cfg
from meniscus.config import get_config

# Node configuration options
worker_group = cfg.OptGroup(name='worker_cfg',
                            title='Worker Configuration Test')
get_config().register_group(worker_group)

WORKER_OPTIONS = [
    cfg.BoolOpt('verbose', default=False, ),
    cfg.StrOpt('personality', default='default_personality',
               help="""Worker personality"""),
    cfg.StrOpt('name', default='default_name', help="""Worker name""")
]

get_config().register_opts(WORKER_OPTIONS, group=worker_group)
