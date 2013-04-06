import falcon

from meniscus.personas.worker.register_online import RegisterWorkerOnline
from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.version.resources import VersionResource


def start_up():

    versions = VersionResource()
    publish_message = PublishMessageResource()

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/v1/{tenant_id}/publish', publish_message)

    register_worker_online = RegisterWorkerOnline()
    register_worker_online.run()

    return application
