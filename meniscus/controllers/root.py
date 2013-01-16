from pecan import expose, redirect
from pecan.rest import RestController
from pecan.core import abort

from meniscus.model import session_maker

class TennantController(object):

    @expose()
    def index(self):
        abort(404)

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

