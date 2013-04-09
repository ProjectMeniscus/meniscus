import falcon

from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher


def start_up():

    versions = VersionResource()
    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    return application
