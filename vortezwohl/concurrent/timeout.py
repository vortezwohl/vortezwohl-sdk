import threading

from typing_extensions import Callable


def timeout(_timeout: float):
    def decorator(func: Callable):
        def wrapper(*_args, **_kwargs):
            result = []
            err = []

            def __wrapper():
                try:
                    result.append(func(*_args, **_kwargs))
                except Exception as e:
                    err.append(e)
                return
            thread = threading.Thread(target=__wrapper)
            thread.start()
            thread.join(timeout=_timeout)
            if thread.is_alive():
                raise TimeoutError(f'{func} timed out after {_timeout} seconds.')
            if len(err) > 0:
                raise err[0]
            return result[0] if len(result) > 0 else None
        return wrapper
    return decorator
