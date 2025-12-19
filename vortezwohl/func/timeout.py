import threading
from typing_extensions import Callable, Any


def timeout(_timeout: float, _default: Any = None):
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
                if _default is None:
                    raise TimeoutError(f'{func} timed out after {_timeout} seconds.')
                else:
                    return _default
            if len(err) > 0:
                raise err[0]
            return result[0] if len(result) > 0 else None
        return wrapper
    return decorator
