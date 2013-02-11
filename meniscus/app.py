import falcon

from meniscus.api import VersionResource
from meniscus.model import init_model, db_session

from meniscus.api.user_service import TenantResource, UserResource, HostProfilesResource, HostProfileResource, HostsResource, HostResource

# Initialize the data model
init_model()

# Resources
versions = VersionResource()
tenant = TenantResource(db_session())
user = UserResource(db_session())
profiles = HostProfilesResource(db_session())
profile = HostProfileResource(db_session())
hosts = HostsResource(db_session())
host = HostResource(db_session())

# Routing
application = api = falcon.API()

api.add_route('/', versions)
api.add_route('/v1/tenant', tenant)
api.add_route('/v1/tenant/{tenant_id}', user)
api.add_route('/v1/tenant/{tenant_id}/profiles', profiles)
api.add_route('/v1/tenant/{tenant_id}/profiles/{profile_id}', profile)
api.add_route('/v1/tenant/{tenant_id}/hosts', hosts)
api.add_route('/v1/tenant/{tenant_id}/hosts/{host_id}', host)
