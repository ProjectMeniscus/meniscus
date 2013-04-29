import falcon

from meniscus.api.version.resources import VersionResource
from meniscus.api.pairing.resources import PairingConfigurationResource
from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.coordinator.resources import WorkerWatchlistResource
from meniscus.api.coordinator.resources import WorkerRoutesResource
from meniscus.api.status.resources import WorkerUpdateResource
from meniscus.api.datastore_init import db_handler


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
    worker_watchlist = WorkerWatchlistResource(db_handler())
    worker_routes = WorkerRoutesResource(db_handler())
    worker_update = WorkerUpdateResource(db_handler())

    # Routing
    application = api = falcon.API()

    # Pairing Routing
    api.add_route('/', versions)
    api.add_route('/v1/pairing/configure', configuration)

    # Worker Registration Routing
    api.add_route('/v1/pairing', worker_registration)
    api.add_route('/v1/worker/{worker_id}', worker_watchlist)
    api.add_route('/v1/worker/{worker_id}/routes', worker_routes)
    api.add_route('/v1/worker/{worker_id}/status', worker_update)

    return application
