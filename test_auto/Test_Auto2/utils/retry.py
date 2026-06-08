import time


def retry(function, retries=3, delay=1, exceptions=(Exception,), on_retry=None):
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            return function()
        except exceptions as exc:
            last_exception = exc
            if on_retry:
                on_retry(exc, attempt)
            if attempt == retries:
                raise
            time.sleep(delay)


def retry_decorator(retries=3, delay=1, exceptions=(Exception,), on_retry=None):
    def decorator(function):
        def wrapper(*args, **kwargs):
            return retry(lambda: function(*args, **kwargs), retries, delay, exceptions, on_retry)
        return wrapper
    return decorator
