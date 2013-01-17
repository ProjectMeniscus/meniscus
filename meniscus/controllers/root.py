from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import db_session
from meniscus.model.util import find_tenant, find_host_by_id
from meniscus.model.control import Tenant, Host


def _tenant_not_found(): abort(404, "Unable to locate tenant.")
def _tenant_already_exists(): abort(500, "Tenant already exists.")


class ProfileController(RestController):

    @expose()
    def get(self, tenant_id, hostname):
        abort(404)

    @expose()
    def set(self, tenant_id, hostname, profile_name):
        return profile_name


class HostController(object):

    def __init__(self, host_id):
        self.host_id = host_id

    def _locate_host(self, host_id):
        found_host = find_host_by_id(host_id)

        if not found_host:
            abort(404,
                  'Unable to find a host'
                  ' with id={0}'.format(self.host_id))

        return found_host

    @expose('json')
    def index(self):
        return self._locate_host(self.host_id)

    @expose('json', generic=True)
    def profile(self):
        found_host = self._locate_host(self.host_id)
        return found_host.profile

    @profile.when(method='POST')
    def set_profile(self, profile_id):
        pass


class HostsController(object):

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id

    @expose('json', generic=True)
    def index(self):
        found_tenant = find_tenant(self.tenant_id)

        if not found_tenant:
            abort(404, "Unable to locate tenant: {0}".format(tenant_id))

        return found_tenant.hosts

    @expose('json')
    @index.when(method='POST')
    def new_host(self, hostname, ip_address):
        found_tenant = find_tenant(tenant_id=self.tenant_id,
                                     when_not_found=_tenant_not_found)

        for host in found_tenant.hosts:
            if host.hostname == hostname:
                abort(400, 'Host already exists with'
                           ' id={0}'.format(found_host.id))

        new_host_profile = Host(hostname, ip_address, None)
        db_session().add(new_host_profile)
        found_tenant.hosts.append(new_host_profile)
        return new_host_profile

    @expose()
    def _lookup(self, host_id, *remainder):
        return HostController(host_id), remainder


class TenantController(object):

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id

    @expose('json', generic=True)
    def index(self):
        return find_tenant(tenant_id=self.tenant_id,
                            when_not_found=_tenant_not_found)

    @expose('json')
    @index.when(method='POST')
    def post(self):
        found_tenant = find_tenant(self.tenant_id)

        if found_tenant:
            abort(400)

        new_tenant = Tenant(self.tenant_id, [])
        db_session().add(new_tenant)
        return new_tenant

    @expose()
    def _lookup(self, tenant_resource, *remainder):
        if tenant_resource == 'hosts':
            return HostsController(self.tenant_id), remainder

        abort(404, 'Unable to locate tenant'
                   ' resource: {0}'.format(tenant_resource))


class VersionController(object):

    def __init__(self, version):
        self.version = version

    @expose()
    def index(self):
        return 'homedoc'

    @expose()
    def _lookup(self, tenant_id, *remainder):
        return TenantController(tenant_id), remainder


class RootController(object):

    @expose('json')
    def index(self):
        return {'v1': 'current'}

    @expose()
    def _lookup(self, version, *remainder):
        return VersionController(version), remainder

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
