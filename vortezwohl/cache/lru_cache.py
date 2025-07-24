import threading

from typing_extensions import Any
from overrides import override

from vortezwohl.cache.base_cache import BaseCache


class LRUCache(BaseCache):
    def __init__(self, capacity: int):
        super().__init__()
        self._capacity = capacity
        self._recently_used = list()
        self._recently_used_lock = threading.RLock()

    def expand_to(self, capacity: int) -> None:
        self._capacity = capacity

    def __recently_used_enqueue(self, key: Any) -> Any:
        with self._recently_used_lock:
            if key in self._recently_used:
                self._recently_used.remove(key)
            self._recently_used.append(key)
            while len(self._recently_used) > self._capacity:
                self.delete(self.__recently_used_dequeue())
        return key

    def __recently_used_dequeue(self) -> None:
        key = None
        with self._recently_used_lock:
            if len(self._recently_used) > 0:
                key = self._recently_used.pop(0)
        return key

    @override
    def read(self, key: Any) -> Any | None:
        self.__recently_used_enqueue(key=key)
        return super().read(key=key)

    @override
    def write(self, key: Any, value: Any) -> Any | None:
        self.__recently_used_enqueue(key=key)
        return super().write(key=key, value=value)
