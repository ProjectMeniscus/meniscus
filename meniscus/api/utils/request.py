import requests

from meniscus import env


_LOG = env.get_logger(__name__)


HTTP_VERBS = (
    'GET',
    'POST',
    'DELETE',
    'PUT',
    'HEAD'
)


def http_request(url, add_headers=None, json_payload='{}', http_verb='GET',
                 request_timeout=1.0):
    headers = {'content-type': 'application/json'}

    if add_headers:
        headers.update(add_headers)
    http_verb = str(http_verb).upper()

    if not http_verb in HTTP_VERBS:
        raise ValueError(
            'Invalid HTTP verb supplied: {0}'.format(http_verb))

    try:
        if http_verb == 'GET':
            return requests.get(url, headers=headers, timeout=request_timeout)
        elif http_verb == 'POST':
            return requests.post(url, data=json_payload, headers=headers,
                                 timeout=request_timeout)
        elif http_verb == 'DELETE':
            return requests.delete(url, data=json_payload, headers=headers,
                                   timeout=request_timeout)
        elif http_verb == 'PUT':
            return requests.put(url, data=json_payload, headers=headers,
                                timeout=request_timeout)
        elif http_verb == 'HEAD':
            return requests.head(url, headers=headers, timeout=request_timeout)

    except requests.ConnectionError as conn_err:
        _LOG.exception(conn_err.message)
        raise conn_err
    except requests.HTTPError as http_err:
        _LOG.exception(http_err.message)
        raise http_err
    except requests.RequestException as req_err:
        _LOG.exception(req_err.message)
        raise req_err
