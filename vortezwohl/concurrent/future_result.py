from typing_extensions import Callable, Dict, Tuple, Any


class FutureResult:
    def __init__(self, _callable: Callable | None, arguments: Dict | Tuple | None,
                 returns: Any, error: Exception | None, traceback: str | None):
        self._callable = _callable
        self._arguments = arguments
        self._returns = returns
        self._error = error
        self._traceback = traceback

    @property
    def callable(self):
        return self._callable

    @property
    def arguments(self):
        return self._arguments

    @property
    def returns(self):
        return self._returns

    @property
    def error(self):
        return self._error

    @property
    def traceback(self):
        return self._traceback
