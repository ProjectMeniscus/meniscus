from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import db_session
from meniscus.model.util import find_tenant, find_host, find_host_profile
from meniscus.model.control import Tenant, Host, HostProfile


def _tenant_not_found(): abort(404, 'Unable to locate tenant.')
def _tenant_already_exists(): abort(400, 'Tenant already exists.')
def _host_not_found(): abort(404,'Unable to locate host.')
def _profile_not_found(): abort(404,'Unable to locate host profile.')


class EventProducerController(object):

    def __init__(self, event_producer):
        self.event_producer = event_producer

    @expose('json')
    def index(self):
        return event_producer

    @expose()
    def set(self, tenant_name, hostname, profile_name):
        return profile_name


class HostController(object):

    def __init__(self, host):
        self.host = host

    @expose('json')
    def index(self):
        return self.host

    @expose('json', generic=True)
    def profile(self):
        return self.host.profile

    @expose('json')
    @profile.when(method='PUT')
    def set_profile(self, profile_id):
        profile = find_host_profile(id=profile_id,
                                    when_not_found=_profile_not_found)

        self.host.profile = profile
        self.host.profile_id = profile_id

        db_session().add(self.host)
        db_session().flush()
        
        return self.host
        


class TenantHostsController(object):

    def __init__(self, tenant):
        self.tenant = tenant

    @expose('json', generic=True)
    def index(self):
        return self.tenant.hosts

    @expose('json')
    @index.when(method='POST')
    def new_host(self, hostname=None, ip_address=None):        
        # Check if the tenant already has a host with this hostname
        for host in self.tenant.hosts:
            if host.hostname == hostname:
                abort(400, 'Host with hostname {0} already exists with'
                           ' id={1}'.format(hostname, host.id))

        # Create the new profile for the host
        new_host_profile = HostProfile(self.tenant.id,
                                       '{0}-profile'.format(hostname))

        # Create the new host definition
        new_host = Host(hostname, ip_address, new_host_profile)
        
        db_session().add(new_host)
        self.tenant.hosts.append(new_host)
        db_session().flush()

        return new_host

    @expose()
    def _lookup(self, host_id, *remainder):
        host = find_host(host_id, when_not_found=_host_not_found)
        return HostController(host), remainder


class TenantHostProfilesController(object):

    def __init__(self, tenant):
        self.tenant = tenant

    @expose('json', generic=True)
    def index(self):
        return self.tenant.profiles

    @expose('json')
    @index.when(method='POST')
    def new_profile(self, name=None):        
        # Check if the tenant already has a profile with this name
        for profile in self.tenant.profiles:
            if profile.name == name:
                abort(400, 'Profile with name {0} already exists.'
                                .format(hostname, host.id))

        # Create the new profile for the host
        new_host_profile = HostProfile(self.tenant.id, name)

        self.tenant.profiles.append(new_host_profile)
        db_session().add(new_host_profile)
        db_session().flush()

        return new_host_profile

    @expose()
    def _lookup(self, host_id, *remainder):
        pass


class TenantController(object):

    def __init__(self, tenant):
        self.tenant = tenant
        self.hosts = TenantHostsController(tenant)
        self.profiles = TenantHostProfilesController(tenant)

    @expose('json')
    def index(self):
        return self.tenant


class RootController(object):

    def __init__(self, version):
        self.version = version

    @expose('json')
    def index(self):
        return 'homedoc'

    @expose('json')
    def tenant(self, tenant_id):
        tenant = find_tenant(tenant_id=tenant_id)

        if tenant:
            abort(400, 'Tenant with tenant_id {0} '
                       'already exists'.format(tenant_id))

        new_tenant = Tenant(tenant_id)
        db_session().add(new_tenant)
        db_session().flush()
        
        return new_tenant

    @expose()
    def _lookup(self, tenant_id, *remainder):
        tenant = find_tenant(tenant_id=tenant_id,
                             when_not_found=_tenant_not_found)
        return TenantController(tenant), remainder


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
