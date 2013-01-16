from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import session_maker


class ProfileController(RestController):

    @expose()
    def get(self, tennant_id, hostname):
        abort(404)

    @expose()
    def set(self, tennant_id, hostname, profile_name):
        return profile_name


class HostController(RestController):

    @expose()
    def get(self, tennant_id, hostname):
        return hostname

    @expose()
    def post(self, tennant_id, **host_profile):
        if host_profile['hostname'] is None or host_profile['ip_address'] is None:
            abort(400)

        response.status_code = 202
        return response


class TennantController(RestController):

    host = HostController()
    
    @expose()
    def get(self, tennant_id):
        return tennant_id


class RootController(object):

    tennant = TennantController()

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

