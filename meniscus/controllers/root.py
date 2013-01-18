from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import db_session
from meniscus.model.util import find_tenant, find_host, find_host_profile
from meniscus.model.control import Tenant, Host, HostProfile


def _tenant_not_found(): abort(404, 'Unable to locate tenant.')
def _tenant_already_exists(): abort(500, 'Tenant already exists.')
def _host_not_found(): abort(404,'Unable to locate host.')


class TenantProfilesController(RestController):

    

    @expose()
    def get(self, tenant_name, hostname):
        abort(404)

    @expose()
    def set(self, tenant_name, hostname, profile_name):
        return profile_name


class HostController(object):

    def __init__(self, host_id):
        self.host_id = host_id

    @expose('json')
    def index(self):
        return find_host(id=self.host_id,
                         when_not_found=_host_not_found)

    @expose('json', generic=True)
    def profile(self):
        host = find_host(id=self.host_id,
                         when_not_found=_host_not_found)
        return host.profile

    @profile.when(method='POST')
    def set_profile(self, profile_id):
        pass


class HostsController(object):

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id

    @expose('json', generic=True)
    def index(self):
        tenant = find_tenant(tenant_id=self.tenant_id,
                             when_not_found=_tenant_not_found)

        return tenant.hosts

    @expose('json')
    @index.when(method='POST')
    def new_host(self, hostname, ip_address):
        tenant = find_tenant(tenant_id=self.tenant_id,
                             when_not_found=_tenant_not_found)

        # Check if the tenant already has a host with this hostname
        for host in tenant.hosts:
            if host.hostname == hostname:
                abort(400, 'Host already exists with'
                           ' id={0}'.format(host.id))

        # Create the new profile for the host
        new_host_profile = HostProfile(tenant.id,
                                       '{0}-profile'.format(hostname))

        # Create the new host definition
        new_host = Host(hostname, ip_address, new_host_profile)
        
        db_session().add(new_host)
        tenant.hosts.append(new_host)

        return new_host

    @expose()
    def _lookup(self, host_id, *remainder):
        return HostController(host_id), remainder


class TenantController(object):

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id

    @expose('json')
    def index(self):
        return find_tenant(tenant_id=self.tenant_id,
                           when_not_found=_tenant_not_found)

    @expose()
    def _lookup(self, tenant_resource, *remainder):
        if tenant_resource == 'hosts':
            return HostsController(self.tenant_id), remainder

        abort(404, 'Unable to locate tenant'
                   ' resource: {0}'.format(tenant_resource))


class RootController(object):

    def __init__(self, version):
        self.version = version

    @expose('json')
    @expose(generic=True)
    def index(self):
        return 'homedoc'

    @expose('json')
    @index.when(method='POST')
    def post(self, tenant_id):
        tenant = find_tenant(tenant_id=tenant_id)

        if tenant:
            abort(400, 'Tennant with tenant_id {0} '
                       'already exists'.format(tenant_id))

        new_tenant = Tenant(tenant_id)
        db_session().add(new_tenant)
        return new_tenant

    @expose()
    def _lookup(self, tenant_name, *remainder):
        return TenantController(tenant_name), remainder


class VersionController(object):

    @expose('json')
    def index(self):
        return {'v1': 'current'}

    @expose()
    def _lookup(self, version, *remainder):
        if version == 'v1':
            return RootController(version), remainder

        abort(404, 'No version matches {0}.'.format(version))
        

    @expose('json')
    def error(self, status):
        try:
            status = int(status)
        except ValueError:
            status = 0

        message = None

        if status == 404:
            message = 'not found'

        return dict(status=status, message=message)
