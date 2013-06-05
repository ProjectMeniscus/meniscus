import falcon

from meniscus.api.version.resources import VersionResource
from meniscus.api.pairing.resources import PairingConfigurationResource
from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.status.resources import WorkerStatusResource
from meniscus.api.datastore_init import db_handler
from meniscus import env

_LOG = env.get_logger(__name__)


def start_up():

    """
    This persona hosts resources from a few different APIs in order
    to facilitate the bootstrap buildout of a brand new meniscus grid. This
    persona effectively allows the new worker to pair with itself.
    """

    # Resources
    versions = VersionResource()
    configuration = PairingConfigurationResource()
    worker_registration = WorkerRegistrationResource(db_handler())
    worker_status = WorkerStatusResource(db_handler())

    # Routing
    application = api = falcon.API()

    # Pairing Routing
    api.add_route('/', versions)
    api.add_route('/v1/pairing/configure', configuration)

    # Worker Registration Routing
    api.add_route('/v1/pairing', worker_registration)
    api.add_route('/v1/worker/{worker_id}/status', worker_status)

    return application
