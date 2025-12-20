import logging
import random
import time

from typing_extensions import Callable, Any

from vortezwohl import NEW_LINE, BLANK

logger = logging.getLogger('vortezwohl.retry')


def sleep(retries: int, base: float = 2., max_delay: float = 600.):
    retries = max(retries, 1)
    delay = min(base ** retries, max_delay)
    time.sleep(delay + random.uniform(.1, delay))
    return


class MaxRetriesReachedError(RuntimeError):
    def __init__(self, retries: int, message: str):
        super().__init__(f'Max attempts reached: {retries + 1}\n{message}')


class Retry:
    def __init__(self, max_retries: int | None = None, delay: bool = False):
        self._max_retries = max_retries
        self._delay = delay

    def on_return(self, validator: Callable[Any, bool]):
        def decorator(func: Callable):
            def wrapper(*_args, **_kwargs):
                result = func(*_args, **_kwargs)
                if validator(result):
                    return result
                else:
                    logger.debug('Validation failed.\n'
                                 '- Retrying...')
                    if self._max_retries is None:
                        retry_count = 0
                        while True:
                            if self._delay:
                                sleep(retries=retry_count)
                            result = func(*_args, **_kwargs)
                            if validator(result):
                                return result
                            else:
                                logger.debug('Validation failed.\n'
                                             f'- Retry {retry_count + 1}/inf'
                                             f' : {str(result).replace(NEW_LINE, BLANK)}')
                    else:
                        for retry_count in range(self._max_retries):
                            if self._delay:
                                sleep(retries=retry_count)
                            result = func(*_args, **_kwargs)
                            if validator(result):
                                return result
                            else:
                                logger.debug(f'Validation failed.\n'
                                             f'- Retry {retry_count + 1}/{self._max_retries}'
                                             f' : {str(result).replace(NEW_LINE, BLANK)}')
                        raise MaxRetriesReachedError(retries=self._max_retries,
                                                     message='Validation failed.\n'
                                                             f'Returns: {result}')
            return wrapper
        return decorator

    def on_exceptions(self, exceptions: list[type] | type):
        if isinstance(exceptions, type):
            exceptions = [exceptions]

        def decorator(func: Callable):
            def wrapper(*_args, **_kwargs):
                def validator() -> tuple[tuple, bool, Any]:
                    result = None
                    need_retry = False
                    error_type = None
                    error_super_type = None
                    error = None
                    try:
                        result = func(*_args, **_kwargs)
                    except Exception as e:
                        for exception in exceptions:
                            if isinstance(e, exception):
                                need_retry = True
                                error = e
                                error_type = e.__class__.__name__
                                error_super_type = exception.__name__
                                break
                    return (error, error_type, error_super_type), need_retry, result
                (_error, _error_type, _error_super_type), _need_retry, _result = validator()
                if not _need_retry:
                    return _result
                else:
                    logger.debug(f'Validation failed, {_error_type}({_error_super_type}) occurred: {str(_error)}.\n'
                                 '- Retrying...')
                    if self._max_retries is None:
                        retry_count = 0
                        while True:
                            if self._delay:
                                sleep(retries=retry_count)
                            (_error, _error_type, _error_super_type), _need_retry, _result = validator()
                            if not _need_retry:
                                return _result
                            else:
                                logger.debug(f'Validation failed, {_error_type}({_error_super_type}) occurred: {str(_error)}.\n'
                                             f'- Retry {retry_count + 1}/inf '
                                             f': {str(_result).replace(NEW_LINE, BLANK)}')
                    else:
                        for retry_count in range(self._max_retries):
                            if self._delay:
                                sleep(retries=retry_count)
                            (_error, _error_type, _error_super_type), _need_retry, _result = validator()
                            if not _need_retry:
                                return _result
                            else:
                                logger.debug(f'Validation failed, {_error_type}({_error_super_type}) occurred: {str(_error)}.\n' 
                                             f'- Retry {retry_count + 1}/{self._max_retries} '
                                             f': {str(_result).replace(NEW_LINE, BLANK)}')
                        raise MaxRetriesReachedError(retries=self._max_retries,
                                                     message=f'{_error_type}({_error_super_type}) '
                                                             f'occurred: {str(_error)}\n'
                                                             f'Returns: {_result}')
            return wrapper
        return decorator
