import json
import falcon

from meniscus import env


_LOG = env.get_logger(__name__)


def _load_json_body(stream):
    try:
        raw_json = stream.read()
    except Exception as ex:
        raise falcon.HTTPError(falcon.HTTP_500, 'Streaming body I/O error')

    try:
        return json.loads(raw_json)
    except ValueError as ve:
        raise falcon.HTTPError(falcon.HTTP_400, 'Malformed JSON body')


def validation_hook(validator):
    """
    This function creates a validator before hook for a falcon resource. Upon
    validation, the hook passes parameters to the request handler. Upon success
    the hook sets the 'validated' parameter to True and the 'doc' parameter
    equal to the parsed request body as a python array or dictionary.

    If the media type of the content is not JSON, this hook sets the
    'validated' parameter to False and the 'doc' parameter to None.

    If validation fails, this hook responds to the requester with a 400 and a
    detail message.
    """
    def validate(req, resp, params):
        params['validated_body'] = None

        # We only care about JSON content types
        if not (req.content_type
                and req.content_type.lower() == 'application/json'):

            _LOG.debug(
                'Failed validation: {0}'.format('Unsupported Media Type'))

            raise falcon.HTTPError(falcon.HTTP_415, 'Unsupported Media Type')

        json_body = _load_json_body(req.stream)
        result = validator.validate(json_body)

        if not result.valid:
            _LOG.debug(
                'Failed validation: {0}'.format(result.error.message))
            raise falcon.HTTPError(falcon.HTTP_400, result.error.message)

        # Set a custom parameters on the request
        params['validated_body'] = json_body
    return validate
