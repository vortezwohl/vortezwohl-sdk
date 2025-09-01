import threading

from typing_extensions import Callable


def timeout(_timeout: float):
    def decorator(func: Callable):
        def wrapper(*_args, **_kwargs):
            result = []

            def __wrapper():
                result.append(func(*_args, **_kwargs))
                return
            thread = threading.Thread(target=__wrapper)
            thread.start()
            thread.join(timeout=_timeout)
            if thread.is_alive():
                raise TimeoutError(f'{func} timed out after {_timeout} seconds.')
            return result[0]
        return wrapper
    return decorator
