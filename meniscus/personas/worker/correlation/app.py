import falcon

from meniscus.personas.worker.register_online import RegisterWorkerOnline
from meniscus.proxy import NativeProxy
from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.correlation.resources import VersionResource


def start_up(cfg=dict()):
    cache = NativeProxy()
    versions = VersionResource()
    publish_message = PublishMessageResource(cache)

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/v1/{tenant_id}/publish', publish_message)

    register_worker_online = RegisterWorkerOnline()
    register_worker_online.run()

    return application
