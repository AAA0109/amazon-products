import functools
import logging
import time

from apps.ads_api.exceptions.auth.token import AuthFailed

_logger = logging.getLogger(__name__)


def retry_auth_failed(max_retries):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(adapter_instance, *args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    result = func(adapter_instance, *args, **kwargs)
                except AuthFailed as e:
                    retries += 1
                    _logger.warning(f"Authentication failed. Retrying in 5 seconds [{retries}/{max_retries}], {e}")
                    time.sleep(5)
                else:
                    return result
            raise AuthFailed("Authentication failed after maximum retries")

        return wrapper

    return decorator
