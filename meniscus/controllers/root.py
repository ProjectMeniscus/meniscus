from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import db_session
from meniscus.model.util import find_tenant, find_host_by_id
from meniscus.model.control import Tenant, Host


def _tenant_not_found(): abort(404, 'Unable to locate tenant.')
def _tenant_already_exists(): abort(500, 'Tenant already exists.')
def _host_not_found(): abort(404,'Unable to locate host.')


class ProfileController(RestController):

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
        return find_host_by_id(host_id=self.host_id,
                               when_not_found=_host_not_found)

    @expose('json', generic=True)
    def profile(self):
        host = find_host_by_id(host_id=self.host_id,
                                     when_not_found=_host_not_found)
        return host.profile

    @profile.when(method='POST')
    def set_profile(self, profile_id):
        pass


class HostsController(object):

    def __init__(self, tenant_name):
        self.tenant_name = tenant_name

    @expose('json', generic=True)
    def index(self):
        tenant = find_tenant(name=self.tenant_name,
                             when_not_found=_tenant_not_found)

        return tenant.hosts

    @expose('json')
    @index.when(method='POST')
    def new_host(self, hostname, ip_address):
        tenant = find_tenant(name=self.tenant_name,
                                   when_not_found=_tenant_not_found)

        for host in tenant.hosts:
            if host.hostname == hostname:
                abort(400, 'Host already exists with'
                           ' id={0}'.format(host.id))

        new_host_profile = Host(hostname, ip_address, None)
        db_session().add(new_host_profile)
        tenant.hosts.append(new_host_profile)
        return new_host_profile

    @expose()
    def _lookup(self, host_id, *remainder):
        return HostController(host_id), remainder


class TenantController(object):

    def __init__(self, tenant_name):
        self.tenant_name = tenant_name

    @expose('json')
    def index(self):
        return find_tenant(name=self.tenant_name,
                           when_not_found=_tenant_not_found)

    @expose()
    def _lookup(self, tenant_resource, *remainder):
        if tenant_resource == 'hosts':
            return HostsController(self.tenant_name), remainder

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
    def post(self, name):
        tenant = find_tenant(name)

        if tenant:
            abort(400, 'Tennant with name {0} '
                       'already exists'.format(name))

        new_tenant = Tenant(name)
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
