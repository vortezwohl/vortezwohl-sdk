import threading

from typing_extensions import Any, OrderedDict


class BaseCache:
    def __init__(self):
        self._cache = OrderedDict()
        self._cache_lock = threading.RLock()

    def read(self, key: Any) -> Any | None:
        value = None
        with self._cache_lock:
            value = self._cache.get(key, None)
        return value

    def write(self, key: Any, value: Any) -> Any | None:
        with self._cache_lock:
            self._cache[key] = value
        return value

    def flush(self) -> None:
        with self._cache_lock:
            self._cache.clear()
        return

    def delete(self, key: Any) -> Any | None:
        with self._cache_lock:
            if key in self._cache.keys():
                value = self._cache[key]
                del self._cache[key]
                return value
        return
