from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import Session
from meniscus.model.control import Tennant, Host

def find_tennant(tennant_id):
    return Session.query(Tennant).filter_by(name=tennant_id).first()

def find_host_by_id(host_id):
    return Session.query(Host).filter_by(id=host_id).first()

def find_host_by_hostname(hostname):
    return Session.query(Host).filter_by(hostname=hostname).first()


class ProfileController(RestController):

    @expose()
    def get(self, tennant_id, hostname):
        abort(404)

    @expose()
    def set(self, tennant_id, hostname, profile_name):
        return profile_name


class HostController(object):

    def __init__(self, host_id):
        self.host_id = host_id

    @expose('json', generic=True)
    def index(self):        
        found_host = find_host_by_id(self.host_id)

        if not found_host:
            abort(404, 'Unable to find a host with id={0}'.format(self.host_id))
        
        return found_host


class HostsController(object):

    def __init__(self, tennant_id):
        self.tennant_id = tennant_id

    @expose('json', generic=True)
    def index(self):        
        found_tennant = find_tennant(self.tennant_id)

        if not found_tennant:
            abort(404, "Unable to locate tennant: {0}".format(tennant_id))
        
        return found_tennant.hosts

    @index.when(method='POST')
    def new_host(self, hostname, ip_address):
        found_host = find_host_by_hostname(hostname)

        if found_host:
            abort(400, 'Host already exists with id={0}'.format(found_host.id))
        
        new_host_profile = Host(hostname, ip_address, None)
        Session.add(new_host_profile)
        self.tennant.hosts.append(new_host_profile)
        return new_host_profile

    @expose()
    def _lookup(self, host_id, *remainder):
        return HostController(host_id), remainder


class TennantController(object):

    def __init__(self, tennant_id):
        self.tennant_id = tennant_id

    @expose('json', generic=True)
    def index(self):
        found_tennant = find_tennant(self.tennant_id)

        if not found_tennant:
            abort(404, "Unable to locate tennant: {0}".format(tennant_id))

        return found_tennant

    @index.when(method='POST')
    def post(self):
        found_tennant = find_tennant(tennant_id)

        if found_tennant:
            abort(400)

        new_tennant = Tennant(tennant_id, [])
        Session.add(new_tennant)
        return new_tennant

    @expose()
    def _lookup(self, tennant_resource, *remainder):
        if tennant_resource == 'hosts':
            return HostsController(self.tennant_id), remainder

        abort(404, 'Unable to locate tennant resource: {0}'.format(tennant_resource))


class RootController(object):

    @expose()
    def index(self):
        return 'homedoc'

    @expose()
    def _lookup(self, version, tennant_id, *remainder):
        if version == 'v1':
            return TennantController(tennant_id), remainder

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

