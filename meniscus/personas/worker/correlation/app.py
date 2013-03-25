import falcon

from meniscus.personas.worker.register_online import RegisterWorkerOnline
from meniscus.proxy import NativeProxy
from resources import PublishMessageResource
from resources import VersionResource


def start_up(cfg=dict()):
    cache = NativeProxy()
    versions = VersionResource()
    publish_message = PublishMessageResource(cache)

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/{tenant_id}/publish', publish_message)

    register_worker_online = RegisterWorkerOnline()
    register_worker_online.run()

    return application

