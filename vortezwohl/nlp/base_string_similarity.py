from abc import abstractmethod

from typing_extensions import Callable


class BaseStringSimilarity(Callable):
    def __init__(self, ignore_case: bool, *args, **kwargs):
        self._ignore_case = ignore_case

    @abstractmethod
    def __call__(self, *args, **kwargs): ...

    @abstractmethod
    def rank(self, s: str, S: list[str]) -> list[str]: ...
