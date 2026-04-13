from abc import ABC, abstractmethod


PatternMatch = tuple[str, int, int, int]


class BasePatternDetector(ABC):
    def __init__(self, ignore_case: bool = False):
        self._ignore_case = ignore_case

    def _normalize(self, text: str) -> str:
        return text.lower() if self._ignore_case else text

    def __call__(self, text: str) -> PatternMatch | None:
        return self.detect(text=text)

    @abstractmethod
    def detect(self, text: str) -> PatternMatch | None: ...

    @abstractmethod
    def locate(self, text: str, pattern: str) -> PatternMatch | None: ...
