import falcon

from meniscus.api.correlation.resources import PublishMessageResource
from meniscus.api.callback.resources import CallbackResource
from meniscus.api.version.resources import VersionResource
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher


def start_up():

    versions = VersionResource()
    callback = CallbackResource()
    publish_message = PublishMessageResource()

    # Routing
    application = api = falcon.API()

    api.add_route('/', versions)
    api.add_route('/v1/tenant/{tenant_id}/publish', publish_message)
    api.add_route('/v1/callback', callback)

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    return application
