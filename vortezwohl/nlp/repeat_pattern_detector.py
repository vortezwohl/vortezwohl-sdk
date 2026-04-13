from overrides import override

from vortezwohl.nlp.base_pattern_detector import BasePatternDetector, PatternMatch


class RepeatPatternDetector(BasePatternDetector):
    def __init__(
        self,
        ignore_case: bool = False,
        min_pattern_len: int = 1,
        max_pattern_len: int | None = None,
    ):
        super().__init__(ignore_case=ignore_case)
        if min_pattern_len < 1:
            raise ValueError('min_pattern_len must be >= 1')
        self._min_pattern_len = min_pattern_len
        self._max_pattern_len = max_pattern_len

    @staticmethod
    def z_algorithm(text: str) -> list[int]:
        n = len(text)
        if n == 0:
            return []
        z = [0] * n
        left = 0
        right = 0
        for i in range(1, n):
            if i <= right:
                z[i] = min(right - i + 1, z[i - left])
            while i + z[i] < n and text[z[i]] == text[i + z[i]]:
                z[i] += 1
            if i + z[i] - 1 > right:
                left = i
                right = i + z[i] - 1
        z[0] = n
        return z

    @staticmethod
    def kmp_find_all(text: str, pattern: str) -> list[int]:
        if not pattern:
            raise ValueError('pattern must not be empty')
        lps = RepeatPatternDetector.__build_lps(pattern=pattern)
        positions: list[int] = []
        i = 0
        j = 0
        while i < len(text):
            if text[i] == pattern[j]:
                i += 1
                j += 1
                if j == len(pattern):
                    positions.append(i - j)
                    j = lps[j - 1]
            elif j > 0:
                j = lps[j - 1]
            else:
                i += 1
        return positions

    @staticmethod
    def __is_better_match(candidate: PatternMatch, best: PatternMatch | None) -> bool:
        if best is None:
            return True
        candidate_key = (
            candidate.repeat,
            len(candidate.pattern) * candidate.repeat,
            -len(candidate.pattern),
            -candidate.start
        )
        best_key = (
            best.repeat,
            len(best.pattern) * best.repeat,
            -len(best.pattern),
            -best.start
        )
        return candidate_key > best_key

    @staticmethod
    def __build_lps(pattern: str) -> list[int]:
        lps = [0] * len(pattern)
        length = 0
        i = 1
        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            elif length > 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
        return lps

    @override
    def detect(self, text: str) -> PatternMatch | None:
        return self.__most_repeated_substring(text=text)

    def __most_repeated_substring(self, text: str) -> PatternMatch | None:
        text = text or ''
        normalized_text = self._normalize(text=text)
        n = len(normalized_text)
        if n == 0:
            return None
        if self._max_pattern_len is None:
            max_pattern_len = n // 2
        else:
            max_pattern_len = min(self._max_pattern_len, n // 2)
        best: PatternMatch | None = None
        for start in range(n):
            suffix = normalized_text[start:]
            if len(suffix) < self._min_pattern_len * 2:
                break
            z = self.z_algorithm(text=suffix)
            upper = min(max_pattern_len, len(suffix) // 2)
            for pattern_len in range(self._min_pattern_len, upper + 1):
                repeat_count = 1 + z[pattern_len] // pattern_len
                if repeat_count < 2:
                    continue
                pattern = text[start:start + pattern_len]
                end = start + pattern_len * repeat_count
                candidate = PatternMatch(
                    pattern=pattern,
                    repeat=repeat_count,
                    start=start,
                    end=end
                )
                if self.__is_better_match(candidate=candidate, best=best):
                    best = candidate
        return best

    @override
    def locate(self, text: str, pattern: str) -> PatternMatch | None:
        return self.__longest_contiguous_repeat_substring(text=text, pattern=pattern)

    def __longest_contiguous_repeat_substring(
        self,
        text: str,
        pattern: str,
    ) -> PatternMatch | None:
        if not pattern:
            raise ValueError('pattern must not be empty')
        text = text or ''
        normalized_text = self._normalize(text=text)
        normalized_pattern = self._normalize(text=pattern)
        starts = set(self.kmp_find_all(text=normalized_text, pattern=normalized_pattern))
        if not starts:
            return None
        step = len(pattern)
        best: PatternMatch | None = None
        for start in sorted(starts):
            if start - step in starts:
                continue
            count = 1
            pos = start + step
            while pos in starts:
                count += 1
                pos += step
            matched_pattern = text[start:start + step]
            candidate = PatternMatch(
                pattern=matched_pattern,
                repeat=count,
                start=start,
                end=start + count * step
            )
            if best is None:
                best = candidate
                continue
            if count > best.repeat or (count == best.repeat and start < best.start):
                best = candidate
        return best
