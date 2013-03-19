import falcon

from meniscus.personas.worker.register_online import RegisterWorkerOnline


def start_up(cfg=dict()):

    # Routing
    application = api = falcon.API()

    register_worker_online = RegisterWorkerOnline()
    register_worker_online.run()

    return application
