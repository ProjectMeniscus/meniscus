from multiprocessing import Process
from meniscus.api.utils.retry import retry
from meniscus.personas.common.routing import get_routes_from_coordinator

#constants for retry methods
TRIES = 3
DELAY = 5
BACKOFF = 2


def get_updated_routes():
    @retry(tries=TRIES, delay=DELAY, backoff=BACKOFF)
    def _get_routes():
        """
        get the associated routes for the worker and store them in cache
        """
        return get_routes_from_coordinator()

    request_process = Process(target=_get_routes)
    request_process.run()
