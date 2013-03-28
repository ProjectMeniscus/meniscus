import falcon
from meniscus.personas.worker.register_online import RegisterWorkerOnline
from meniscus.api.version.resources import VersionResource


def start_up(cfg=dict()):

    versions = VersionResource()
    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)

    register_worker_online = RegisterWorkerOnline()
    register_worker_online.run()

    return application
