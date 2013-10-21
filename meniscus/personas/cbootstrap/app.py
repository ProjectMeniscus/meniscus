import falcon

from meniscus.api.version.resources import VersionResource
from meniscus.api.pairing.resources import PairingConfigurationResource
from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.status.resources import WorkerStatusResource
from meniscus.data.datastore import COORDINATOR_DB, datasource_handler
from meniscus import env

_LOG = env.get_logger(__name__)


def start_up():

    """
    This persona hosts resources from a few different APIs in order
    to facilitate the bootstrap buildout of a brand new meniscus grid. This
    persona effectively allows the new worker to pair with itself.
    """

    #Datastore adapter/session manager
    datastore = datasource_handler(COORDINATOR_DB)

    # Resources
    versions = VersionResource()
    configuration = PairingConfigurationResource()
    worker_registration = WorkerRegistrationResource()
    worker_status = WorkerStatusResource()

    # Routing
    application = api = falcon.API()

    # Pairing Routing
    api.add_route('/', versions)
    api.add_route('/v1/pairing/configure', configuration)

    # Worker Registration Routing
    api.add_route('/v1/pairing', worker_registration)
    api.add_route('/v1/worker/{worker_id}/status', worker_status)

    return application
