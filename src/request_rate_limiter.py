import time
import logging

from functools import wraps

import requests


logger = logging.getLogger(__name__)


def rate_limiter(requests_per_second: float) -> callable:
    """Discard requests that exceed target request rate

    This decorator intercepts calls to requests.Session.request and drops
    requests that occur at an instantaneous rate greater than the rate
    specified by requests_per_second.

    Args:
        requests_per_second: maximum instantaneous requests per second rate
    """

    original_request = requests.Session.request

    min_delay = 1 / requests_per_second # delay between requests in seconds
    last_timestamp = 0

    def _rate_limited_request(*args, **kwargs) -> requests.Response or None:
        nonlocal last_timestamp

        time_diff = time.time() - last_timestamp
        if time_diff < min_delay:
            logging.warning("Rate limit exceeded: dropping request. "
                    "current rate %.3f requests per second", 1/time_diff)
            return None

        res = original_request(*args, **kwargs)
        last_timestamp = time.time()

        return res

    def wrapper(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            requests.Session.request = _rate_limited_request
            res = func(*args, **kwargs)
            requests.Session.request = original_request
            return res

        return _wrapper

    return wrapper
