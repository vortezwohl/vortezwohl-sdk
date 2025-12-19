from typing_extensions import Callable, Any

from vortezwohl.io.http_client import HttpClient


def _sleep(retries: int, base: float = 2., max_delay: float = 600.):
    return HttpClient.sleep(retries=retries, base=base, max_delay=max_delay)


class MaxRetriesReachedError(RuntimeError):
    def __init__(self, retries: int):
        super().__init__(f'Max retries reached: {retries}.')


class Retry:
    def __init__(self, max_retries: int | None = None, delay: bool = False):
        self._max_retries = max_retries
        self._delay = delay

    def on_return(self, validator: Callable[Any, bool], ):
        def decorator(func: Callable):
            def wrapper(*_args, **_kwargs):
                result = func(*_args, **_kwargs)
                if validator(result):
                    return result
                else:
                    if self._max_retries is None:
                        retry_count = 0
                        while True:
                            if self._delay:
                                _sleep(retries=retry_count)
                            result = func(*_args, **_kwargs)
                            if validator(result):
                                return result
                    else:
                        for retry_count in range(self._max_retries):
                            if self._delay:
                                _sleep(retries=retry_count)
                            result = func(*_args, **_kwargs)
                            if validator(result):
                                return result
                        raise MaxRetriesReachedError(retries=self._max_retries)
            return wrapper
        return decorator

    def on_exceptions(self, exceptions: list[type] | type):
        if isinstance(exceptions, type):
            exceptions = [exceptions]

        def decorator(func: Callable):
            def wrapper(*_args, **_kwargs):
                def validator() -> tuple[bool, Any]:
                    result = None
                    need_retry = False
                    try:
                        result = func(*_args, **_kwargs)
                    except Exception as e:
                        for exception in exceptions:
                            if isinstance(e, exception):
                                need_retry = True
                                break
                    return need_retry, result
                _need_retry, _result = validator()
                if not _need_retry:
                    return _result
                else:
                    if self._max_retries is None:
                        retry_count = 0
                        while True:
                            if self._delay:
                                _sleep(retries=retry_count)
                            _need_retry, _result = validator()
                            if not _need_retry:
                                return _result
                    else:
                        for retry_count in range(self._max_retries):
                            if self._delay:
                                _sleep(retries=retry_count)
                            _need_retry, _result = validator()
                            if not _need_retry:
                                return _result
                        raise MaxRetriesReachedError(retries=self._max_retries)
            return wrapper
        return decorator
