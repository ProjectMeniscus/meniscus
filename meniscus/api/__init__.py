import json
import falcon

from meniscus.model import init_model

class ApiResource(object):
    pass


class VersionResource(ApiResource):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


def abort(resp, status=falcon.HTTP_500, message=None):
    raise falcon.HTTPError(status, message)


def load_body(req, required=[]):
    try:
        raw_json = req.body.read()
    except Exception:
        abort(falcon.HTTP_500, 'Read Error')

    try:
        parsed_body = json.loads(raw_json, 'utf-8')
    except ValueError:
        abort(falcon.HTTP_400, 'Malformed JSON')
        
    return parsed_body
