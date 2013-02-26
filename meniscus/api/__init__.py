import falcon
import io
import json


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


def load_body(req):
    """
    Helper function for loading an HTTP request body from JSON into a
    Python dictionary
    """
    try:
        return json.load(io.TextIOWrapper(req.stream, 'utf-8'))
    except ValueError as ve:
        abort(falcon.HTTP_400, 'Malformed JSON')
    except Exception as ex:
        abort(falcon.HTTP_500, ex.message)