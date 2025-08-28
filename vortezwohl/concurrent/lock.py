import threading
from typing_extensions import Callable, Union


def lock_on(lock: Union[threading.Lock, threading.RLock, threading.Semaphore], **kwargs):
    def decorator(func: Callable):
        def wrapper(*_args, **_kwargs):
            if 'blocking' not in kwargs or kwargs.get('timeout', None) is not None:
                kwargs['blocking'] = True
            lock.acquire(**kwargs)
            _ret = func(*_args, **_kwargs)
            if isinstance(lock, threading.Semaphore):
                lock.release(n=1)
            else:
                lock.release()
            return _ret
        return wrapper
    return decorator
