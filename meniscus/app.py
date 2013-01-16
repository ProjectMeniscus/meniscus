from pecan import make_app
from meniscus import model

def setup_app(config):
    
    model.init_model()
    
    return make_app(
        config.app.root,
        static_root     = config.app.static_root,
        template_path   = config.app.template_path,
        logging         = getattr(config, 'logging', {}),
        debug           = getattr(config.app, 'debug', False),
        force_canonical = getattr(config.app, 'force_canonical', True)
    )
