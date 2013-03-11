import falcon

from meniscus.api.coordinator.resources import WorkerConfigurationResource
from meniscus.api.coordinator.resources import WorkerRegistrationResource
from meniscus.api.coordinator.resources import VersionResource
from meniscus.api.datastore_init import db_handler


# Resources
versions = VersionResource()
worker_registration = WorkerRegistrationResource(db_handler())
worker_configuration = WorkerConfigurationResource(db_handler())
worker_status = WorkerRegistrationResource(db_handler())
# Routing
application = api = falcon.API()


api.add_route('/', versions)
api.add_route('/v1/worker/{worker_id}/configuration', worker_configuration)
api.add_route('/v1/worker/registration', worker_registration)
api.add_route('/v1/worker/{worker_id}/status', worker_status)
