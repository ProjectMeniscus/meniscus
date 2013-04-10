
import falcon

from meniscus.api import abort


def _personality_not_valid():
    """
    sends an http 400 invalid personality request
    """
    abort(falcon.HTTP_400, 'invalid personality.')


def _status_not_valid():
    """
    sends an http 400 invalid status request
    """
    abort(falcon.HTTP_400, 'invalid status.')


def _registration_not_valid():
    """
    sends an http 400 invalid registration request
    """
    abort(falcon.HTTP_400, 'invalid registration request.')


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    abort(falcon.HTTP_404, 'unable to locate worker.')


