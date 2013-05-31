import falcon

from meniscus import env
from meniscus.openstack.common import jsonutils

LOG = env.get_logger(__name__)

class ApiResource(object):
    """
    Base class for API resources
    """

    def __init__(self, validator=None):
        self.validator = validator

    def load_body(self, req):
        return load_body(req, self.validator)


def abort(status=falcon.HTTP_500, message=None):
    """
    Helper function for aborting an API request process. Useful for error
    reporting and exception handling.
    """
    raise falcon.HTTPError(status, message)


def format_response_body(body):
    """
    Helper function for formatting the response body as JSON into a
    Python dictionary
    """
    return jsonutils.dumps(body)


def load_body(req, validator=None):
    """
    Helper function for loading an HTTP request body from JSON into a
    Python dictionary
    """
    try:
        raw_json = req.stream.read()
    except Exception, ex:
        LOG.debug(ex.message)
        abort(falcon.HTTP_500, 'Read Error')

    try:
        obj = jsonutils.loads(raw_json)
    except ValueError, ex:
        LOG.debug(ex.message)
        abort(falcon.HTTP_400, 'Malformed JSON')

    if validator:
        validation_result = validator.validate(obj)
        if not validation_result[0]:
            LOG.debug('json validation failed')
            abort(falcon.HTTP_400, validation_result[1].message)

    return obj
