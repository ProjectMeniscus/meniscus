import falcon

from meniscus.personas.worker.publish_stats import WorkerStatusPublisher
from meniscus.personas.worker.publish_stats import WorkerStatsPublisher
from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.version.resources import VersionResource


def start_up():

    versions = VersionResource()
    publish_message = PublishMessageResource()

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/v1/{tenant_id}/publish', publish_message)

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    return application
