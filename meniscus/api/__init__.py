import falcon

from meniscus import env
from meniscus.openstack.common import jsonutils

_LOG = env.get_logger(__name__)


class ApiResource(object):
    """
    Base class for API resources
    """
    pass


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
        _LOG.debug(ex)
        abort(falcon.HTTP_500, 'Read Error')

    try:
        obj = jsonutils.loads(raw_json)
    except ValueError, ex:
        _LOG.debug('Malformed JSON: {0}'.format(raw_json))
        abort(falcon.HTTP_400, 'Malformed JSON')

    if validator:
        validation_result = validator.validate(obj)
        if not validation_result[0]:
            _LOG.debug('JSON schema validation failed: {0}'.format(obj))
            abort(falcon.HTTP_400, validation_result[1].message)

    return obj


def handle_api_exception(operation_name=None):
    """
    Handle general exceptions by logging exception
    and returning 500 back to client
    """
    def exceptions_decorator(fn):
        def handler(*args, **kwargs):
            try:
                fn(*args, **kwargs)

            except falcon.HTTPError as ex:
                _LOG.debug('{0} : {1}'.format(ex.status, ex.title))
                raise ex
            except Exception as e:
                message = ('{0} failure - please contact site '
                           'administrator').format(operation_name or "System")
                _LOG.exception(operation_name)
                abort(message=message)
        return handler
    return exceptions_decorator
