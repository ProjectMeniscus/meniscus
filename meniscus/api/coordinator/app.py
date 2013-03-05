import falcon

from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.coordinator.resources import VersionResource

# Resources
versions = VersionResource()
worker_registration = WorkerRegistrationResource()
# Routing
application = api = falcon.API()

api.add_route('/', versions)
api.add_route('/v1/worker/registration', worker_registration)
