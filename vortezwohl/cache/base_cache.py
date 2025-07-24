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

    def __contains__(self, key: Any) -> bool:
        contains = False
        with self._cache_lock:
            contains = (key in self._cache.keys())
        return contains

    def __getitem__(self, key: Any) -> Any:
        return self.read(key=key)

    def __setitem__(self, key: Any, value: Any) -> Any | None:
        return self.write(key=key, value=value)

    def __delitem__(self, key: Any) -> Any | None:
        return self.delete(key=key)

    def __str__(self) -> str:
        stringify = ''
        with self._cache_lock:
            _max_len = 8
            for key, value in self._cache.items():
                _max_len = max(_max_len, len(str(key)))
                _max_len = max(_max_len, len(str(value)))
            _padding = 2
            _max_len += _padding
            line_spliter = f'\n{"+" + "=" * (_max_len * 2 + 1) + "+"}\n'
            header = f'{self.__class__.__name__}(capacity={len(self._cache.keys())})'
            stringify = (f'{header:^{_max_len * 2 + 2}}{line_spliter}'
                         + f'|{"Key":^{_max_len}}|{"Value":^{_max_len}}|{line_spliter}'
                         + line_spliter.join([f'|{str(k):^{_max_len}}|{str(v):^{_max_len}}|' for k, v in self._cache.items()])
                         + (line_spliter if len(self) else ''))
        return stringify

    def __repr__(self) -> str:
        return self.__str__()

    def __len__(self) -> int:
        length = 0
        with self._cache_lock:
            length = len(self._cache.keys())
        return length

    def __eq__(self, other) -> bool:
        stringify = ''
        with self._cache_lock:
            stringify = str(self)
        return stringify == str(other)

    def __call__(self, key: Any) -> Any:
        return self.read(key=key)
