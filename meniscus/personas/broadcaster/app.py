import falcon

from meniscus.api.broadcaster.resources import BroadcastResource
from meniscus.api.callback.resources import CallbackResource
from meniscus.api.version.resources import VersionResource
from meniscus.personas.broadcaster.broadcaster import Broadcaster
from meniscus.personas.common.publish_stats import WorkerStatusPublisher
from meniscus.personas.common.publish_stats import WorkerStatsPublisher


def start_up():

    versions = VersionResource()
    callback = CallbackResource()
    broadcast = BroadcastResource()

    # Routing
    application = api = falcon.API()
    api.add_route('/', versions)
    api.add_route('/v1/callback', callback)
    api.add_route('/v1/broadcast', broadcast)

    register_worker_online = WorkerStatusPublisher('online')
    register_worker_online.run()

    publish_stats_service = WorkerStatsPublisher()
    publish_stats_service.run()

    # Broadcaster process
    broadcaster = Broadcaster()
    broadcaster.run()

    return application
