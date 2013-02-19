import json
import falcon


"""
Base class for API resources
"""


class ApiResource(object):
    pass


"""
Helper function for aborting an API request process. Useful for error
reporting and expcetion handling.
"""


def abort( status=falcon.HTTP_500, message=None):
    raise falcon.HTTPError(status, message)

"""
Helper function for loading an HTTP request body from JSON into a
Python dictionary
"""


def load_body(req, required=[]):
    try:
        raw_json = req.stream.read()

    except Exception:
        abort(falcon.HTTP_500, 'Read Error')

    try:
        parsed_body = json.loads(raw_json, 'utf-8')
    except ValueError as ve:
        print ve
        abort(falcon.HTTP_400, 'Malformed JSON')
        
    return parsed_body
