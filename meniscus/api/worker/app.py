import falcon

from meniscus.api.worker.resources import VersionResource
from meniscus.api.worker.resources import ConfigurationResource


# Resources
versions = VersionResource()
configuration = ConfigurationResource()

# Routing
application = api = falcon.API()

api.add_route('/', versions)
api.add_route('/v1/callback/configuration', configuration)