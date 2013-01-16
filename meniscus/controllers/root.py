from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort, response

from meniscus.model import Session
from meniscus.model.control import Tennant


class ProfileController(RestController):

    @expose()
    def get(self, tennant_id, hostname):
        abort(404)

    @expose()
    def set(self, tennant_id, hostname, profile_name):
        return profile_name


class HostController(RestController):

    @expose('json')
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
    
    @expose('json')
    def get(self, tennant_id):
        found_tennant = Session.query(Tennant).filter_by(name=tennant_id).first()

        if not found_tennant:
            abort(404, "unable to locate {0}".format(tennant_id))

        return found_tennant

    @expose()
    def post(self, tennant_id):
        found_tennant = Session.query(Tennant).filter_by(name=tennant_id).first()

        if found_tennant:
            abort(400)

        Session.add(Tennant(tennant_id, []))

        response.status_code = 202
        return response


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

