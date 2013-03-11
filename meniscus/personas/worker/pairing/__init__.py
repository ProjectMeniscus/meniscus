import falcon

from meniscus.api.worker.resources import VersionResource
from resources import PairingConfigurationResource


def start_up(cfg=dict()):
    # Resources
    versions = VersionResource()
    configuration = PairingConfigurationResource()

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/v1/pairing/configure', configuration)

    return application
