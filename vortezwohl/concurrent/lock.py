import threading
from typing_extensions import Callable, Union


def lock_on(lock: Union[threading.Lock, threading.RLock, threading.Semaphore]):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            lock.acquire(blocking=True)
            _ret = func(*args, **kwargs)
            lock.release()
            return _ret
        return wrapper
    return decorator
