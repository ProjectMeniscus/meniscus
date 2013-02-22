import json
import falcon


class ApiResource(object):
    """
    Base class for API resources
    """
    pass


def abort(status=falcon.HTTP_500, message=None):
    """
    Helper function for aborting an API request process. Useful for error
    reporting and expcetion handling.
    """
    raise falcon.HTTPError(status, message)


def load_body(req, required=[]):
    """
    Helper function for loading an HTTP request body from JSON into a
    Python dictionary
    """
    try:
        raw_json = req.stream.read()

    except Exception:
        abort(falcon.HTTP_500, 'Read Error')

    try:
        parsed_body = json.loads(raw_json, 'utf-8')
    except ValueError as ve:
        abort(falcon.HTTP_400, 'Malformed JSON')
        
    return parsed_body
