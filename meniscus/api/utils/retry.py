import time
import math

from meniscus import env

_LOG = env.get_logger(__name__)


# Retry decorator with exponential backoff
def retry(tries, delay=3, backoff=2):
    """
    Retries a function or method until it returns True.

    delay sets the initial delay in seconds, and backoff sets the factor by
    which the delay should lengthen after each failure. backoff must be
    greater than 1, or else it isn't really a backoff. tries must be at least
    0, and delay greater than 0."""

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 0:
        raise ValueError("tries must be 0 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay  # make mutable

            rv = f(*args, **kwargs)  # first attempt
            while mtries > 0:
                if rv is True:  # Done on success
                    return True

                _LOG.debug(
                    'function {0} failed, will retry in {1} seconds'
                    .format(f.__name__, mdelay))
                mtries -= 1      # consume an attempt
                time.sleep(mdelay)  # wait...
                mdelay *= backoff  # make future wait longer

                rv = f(*args, **kwargs)  # Try again

            _LOG.debug(
                'function {0} failed, max retries exceeded'
                .format(f.__name__))
            return False  # Ran out of tries :-(

        return f_retry  # true decorator -> decorated function
    return deco_retry  # @retry(arg[, ...]) -> true decorator
