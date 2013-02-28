import requests


def post_http(url, json_payload='{}'):
    headers = {'content-type': 'application/json'}

    try:
        resp = requests.post(url, data=json_payload, headers=headers)
        return resp.status_code

    except requests.ConnectionError as conn_err:
        # TODO: Log this when we have a logger ready
        raise conn_err
    except requests.HTTPError as http_err:
        # TODO: Log this when we have a logger ready
        raise http_err
    except requests.RequestException as req_err:
        # TODO: Log this when we have a logger ready
        raise req_err
