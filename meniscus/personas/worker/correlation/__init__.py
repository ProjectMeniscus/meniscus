import falcon
from meniscus.personas.worker.register_online import RegisterWorkerOnline
from meniscus.personas.worker.correlation.resources import PublishResource


def start_up(cfg=dict()):

    # Routing
    application = api = falcon.API()

    register_worker_online = RegisterWorkerOnline()
    register_worker_online.run()
    publish = PublishResource()

    api.add_route('/v1/{tenant_id}/publish', publish)

    return application
