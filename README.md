# *vortezwohl-sdk*

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/vortezwohl/vortezwohl-sdk)

Practical Python utility SDKs by Vortez Wohl.

`vortezwohl` is a small synchronous toolbox for common application tasks:
in-memory caching, thread-pool execution, retry and timeout decorators, simple
file and HTTP helpers, iterable chunking, string similarity, repeated-pattern
detection, hashing, seed generation, and Python environment helpers.

## Requirements

- Python `>=3.10`
- Runtime dependencies: `overrides`, `psutil`, `requests`,
  `typing-extensions`, `urllib3>=2.5.0`

## Installation

With `pip`:

```bash
pip install -U vortezwohl
```

With `uv`:

```bash
uv add -U vortezwohl
```

From GitHub:

```bash
pip install -U git+https://github.com/vortezwohl/vortezwohl-sdk.git
```

## Quick Start

```python
from vortezwohl.cache import LRUCache
from vortezwohl.concurrent import ThreadPool
from vortezwohl.func import Retry
from vortezwohl.io import HttpClient
from vortezwohl.nlp import LevenshteinDistance

cache = LRUCache(capacity=128)
cache["answer"] = 42

client = HttpClient(max_retries=2, timeout=5.0)


@Retry(max_retries=2, delay=True).on_return(lambda value: value is not None)
def fetch_text(url: str) -> str | None:
    response = client.get(url)
    if response.status_code != 200:
        return None
    return response.text


distance = LevenshteinDistance(ignore_case=True)
best_match = distance.rank("pyhton", ["python", "java", "go"])[0]

with ThreadPool(max_workers=4) as pool:
    for result in pool.map(str.upper, [("a",), ("b",), ("c",)]):
        if result.error:
            raise result.error
        print(result.returns)
```

## Package Map

| Module | Public API | Purpose |
| --- | --- | --- |
| `vortezwohl.cache` | `BaseCache`, `LRUCache` | Thread-safe in-memory caches |
| `vortezwohl.concurrent` | `ThreadPool`, `lock_on`, `timeout` | Thread-pool helpers, locking decorator, timeout decorator |
| `vortezwohl.crypt` | `md5`, `sha1`, `sha256`, `sha512` | Text hash helpers |
| `vortezwohl.func` | `Retry`, `sleep`, `timeout` | Retry and timeout decorators |
| `vortezwohl.io` | `read_file`, `write_file`, `get_files`, `size_of`, `HttpClient` | File helpers and simple HTTP client |
| `vortezwohl.iter` | `batched`, `sliding_window` | Iterable batching and windowing |
| `vortezwohl.nlp` | `LevenshteinDistance`, `LongestCommonSubstring`, `PatternMatch`, `RepeatPatternDetector` | String similarity and repeated-pattern detection |
| `vortezwohl.random` | `next_seed` | Process-local seed generation |
| `vortezwohl.sys` | `System` | Python, pip, shell, and package helpers |

## Caching

### `BaseCache`

`BaseCache` is a thread-safe dictionary-like cache backed by an ordered mapping.

```python
from vortezwohl.cache import BaseCache

cache = BaseCache()
cache.write("name", "vortezwohl")
cache["count"] = 1

assert cache.read("name") == "vortezwohl"
assert cache("count") == 1
assert "name" in cache

deleted = cache.delete("name")
cache.flush()
```

Main methods and operations:

- `read(key) -> Any | None`
- `write(key, value) -> Any | None`
- `delete(key) -> Any | None`
- `flush() -> None`
- `key in cache`
- `cache[key]`, `cache[key] = value`, `del cache[key]`
- `cache(key)` as a shorthand for `cache.read(key)`
- `len(cache)`, `str(cache)`, `repr(cache)`

### `LRUCache`

`LRUCache` extends `BaseCache` with a fixed capacity and least-recently-used
eviction.

```python
from vortezwohl.cache import LRUCache

cache = LRUCache(capacity=2)
cache.write("a", 1)
cache.write("b", 2)
cache.read("a")
cache.write("c", 3)

assert "b" not in cache
assert cache.read("a") == 1

cache.expand_to(10)
```

Notes:

- `capacity` limits the number of cached keys.
- `expand_to(capacity)` changes the capacity for future operations.
- `read()` and `write()` both update recency.
- The cache is in-process memory only. It has no TTL, persistence, or
  cross-process sharing.

## Concurrency

### `ThreadPool`

`ThreadPool` wraps `concurrent.futures.ThreadPoolExecutor` and returns
`FutureResult` objects for completed work.

```python
from vortezwohl.concurrent import ThreadPool


def square(value: int) -> int:
    return value * value


with ThreadPool(max_workers=4) as pool:
    pool.submit(square, 2)
    pool.submit(square, 3)

    for result in pool.next_result:
        if result.error:
            print(result.traceback)
        else:
            print(result.arguments, result.returns)
```

Constructor:

- `ThreadPool(max_workers: int | None = None)`
- When `max_workers` is `None`, the default is logical CPU count plus one.

Methods and properties:

- `submit(job, *args, **kwargs) -> Future`
- `gather(jobs, arguments=None) -> Iterable[FutureResult]`
- `map(job, arguments) -> Iterable[FutureResult]`
- `wait_all() -> list[FutureResult]`
- `shutdown(cancel_futures=True)`
- `next_result -> Iterable[FutureResult]`
- `thread_pool_executor -> ThreadPoolExecutor`
- `max_workers -> int`

`arguments` in `gather()` and `map()` may contain dictionaries for keyword
arguments, tuples/lists for positional arguments, scalar values for one
positional argument, or `None` for no arguments.

```python
from vortezwohl.concurrent import ThreadPool


def add(a: int, b: int) -> int:
    return a + b


with ThreadPool(max_workers=2) as pool:
    for result in pool.map(add, [(1, 2), (3, 4)]):
        print(result.returns)
```

Important behavior:

- Results are yielded in completion order, not input order.
- If deterministic ordering matters, include an index in the arguments or
  return value and sort after collection.
- Worker exceptions are captured into `FutureResult.error` and
  `FutureResult.traceback`.

### `FutureResult`

`FutureResult` exposes:

- `callable`: the original callable when available
- `arguments`: the submitted arguments when available
- `returns`: the return value
- `error`: the captured exception, or `None`
- `traceback`: the formatted traceback string, or `None`

### `lock_on`

`lock_on(lock, **kwargs)` decorates a function and runs it while holding a
`threading.Lock`, `threading.RLock`, or `threading.Semaphore`.

```python
import threading

from vortezwohl.concurrent import lock_on

lock = threading.RLock()
counter = 0


@lock_on(lock)
def increment() -> int:
    global counter
    counter += 1
    return counter
```

Keyword arguments are passed to `lock.acquire()`. For semaphores, the decorator
releases one permit after the wrapped function returns or raises.

### `timeout`

`timeout` is available from both `vortezwohl.func` and
`vortezwohl.concurrent`.

```python
import time

from vortezwohl.func import timeout


@timeout(_timeout=0.1, _default="fallback")
def slow_call() -> str:
    time.sleep(1)
    return "done"


assert slow_call() == "fallback"
```

Behavior:

- `@timeout(_timeout)` raises `TimeoutError` when the wrapped function takes too
  long.
- `@timeout(_timeout, _default=value)` returns `value` instead of raising.
- Exceptions raised by the wrapped function are re-raised.
- The implementation waits in a background thread. A timeout stops waiting; it
  does not kill the running thread.

## Retry Helpers

### `Retry`

`Retry(max_retries=None, delay=False)` creates decorators for retrying either
invalid return values or selected exception types.

`max_retries` is the number of retries after the first attempt. The total number
of attempts is therefore `max_retries + 1`. When `max_retries` is `None`, retry
continues indefinitely.

Retry on return validation:

```python
from vortezwohl.func import Retry


@Retry(max_retries=3, delay=True).on_return(lambda value: value is not None)
def read_optional() -> str | None:
    return "ok"
```

Retry on exceptions:

```python
import requests

from vortezwohl.func import Retry


@Retry(max_retries=2, delay=True).on_exceptions(requests.RequestException)
def call_remote() -> str:
    response = requests.get("https://example.com", timeout=3)
    response.raise_for_status()
    return response.text
```

Notes:

- `on_return(validator)` succeeds when `validator(result)` is truthy.
- `on_exceptions(*exceptions)` retries only the exception types supplied.
- Non-retryable exceptions are raised immediately.
- Exhausted retries raise `MaxRetriesReachedError` from
  `vortezwohl.func.retry`.
- `delay=True` uses exponential backoff with jitter through `sleep()`.

### `sleep`

```python
from vortezwohl.func import sleep

sleep(retries=1, base=2.0, max_delay=600.0)
```

`sleep()` sleeps for an exponential delay plus random jitter. It is used by
`Retry` and `HttpClient`.

## File And HTTP I/O

### File Helpers

```python
from vortezwohl.io import get_files, read_file, size_of, write_file

content = read_file("README.md")
output_path = write_file("hello", "tmp/example.txt")
files = get_files("tmp")
bytes_used = size_of("tmp")
```

Functions:

- `read_file(path, encoding="utf-8") -> str`
- `write_file(content, path, encoding="utf-8") -> str`
- `get_files(path) -> list`
- `size_of(path) -> int`

Behavior:

- `read_file()` tries the requested encoding first, then `gbk`, then the
  requested encoding with replacement for invalid characters.
- `write_file()` creates parent directories automatically. Text is written with
  the requested encoding; bytes are written in binary mode.
- `get_files()` returns immediate files under an existing directory as absolute
  paths. It does not recurse into subdirectories.
- `size_of()` returns bytes for a file or recursively totals a directory. Missing
  paths return `0`.

### `HttpClient`

`HttpClient` is a small synchronous wrapper around `requests.get()` and
`requests.post()`.

```python
from vortezwohl.io import HttpClient

client = HttpClient(max_retries=3, timeout=8.0)

response = client.get(
    "https://httpbin.org/get",
    data={"q": "vortezwohl"},
    headers={"Accept": "application/json"},
)

payload = client.post(
    "https://httpbin.org/post",
    data={"name": "vortezwohl"},
)
```

Constructor:

- `HttpClient(max_retries=3, timeout=8.0, _delay_base=2.0)`

Methods:

- `get(url, data=None, headers=None, **kwargs)`
- `post(url, data, headers=None, **kwargs)`
- `sleep(retries, base=2.0, max_delay=600.0)`

Important behavior:

- `get()` sends `data` as query parameters.
- `post()` sends `data` as JSON.
- The client returns a `requests.Response`.
- Only HTTP status code `200` is treated as success.
- Non-`200` responses are retried until retries are exhausted; the final
  response is then returned.
- The client does not call `raise_for_status()`.
- Extra keyword arguments are passed to the retry sleep helper, not to
  `requests`.

## Iterable Helpers

### `batched`

```python
from vortezwohl.iter import batched

list(batched([1, 2, 3, 4, 5], batch_size=2, fill_value=None))
# [[1, 2], [3, 4], [5, None]]
```

`batched(_iterable, batch_size=1, fill_value=None)` yields fixed-size lists. The
last batch is padded with `fill_value` when needed.

### `sliding_window`

```python
from vortezwohl.iter import sliding_window

list(sliding_window([1, 2, 3, 4, 5], window_size=3, stride=2, fill_value=None))
# [[1, 2, 3], [3, 4, 5], [5, None, None]]
```

`sliding_window(_iterable, window_size, stride, fill_value=None)` yields
fixed-size windows. The final window is padded with `fill_value` when needed.

## NLP Helpers

### `LevenshteinDistance`

```python
from vortezwohl.nlp import LevenshteinDistance

distance = LevenshteinDistance(ignore_case=True)

assert distance("kitten", "sitting") == 3
assert distance.rank("pyhton", ["java", "python", "rust"])[0] == "python"
```

API:

- `LevenshteinDistance(ignore_case=False)`
- `distance(s_1, s_2) -> int`
- `distance.rank(s, S) -> list[str]`

`rank()` returns candidates sorted by smaller edit distance first.

### `LongestCommonSubstring`

```python
from vortezwohl.nlp import LongestCommonSubstring

lcs = LongestCommonSubstring(ignore_case=True)

assert lcs("abcdef", "zabxy") == "ab"
assert lcs.rank("abcdef", ["xxcde", "abzzz"])[0] == "xxcde"
```

API:

- `LongestCommonSubstring(ignore_case=False)`
- `lcs(s_1, s_2) -> str`
- `lcs.rank(s, S) -> list[str]`

`rank()` returns candidates sorted by longer common substring first.

### `RepeatPatternDetector`

`RepeatPatternDetector` finds contiguous repeated substrings.

```python
from vortezwohl.nlp import RepeatPatternDetector

detector = RepeatPatternDetector(ignore_case=True, min_pattern_len=1)

match = detector.detect("abcabcabcxyz")
assert match.pattern == "abc"
assert match.repeat == 3
assert match.start == 0
assert match.end == 9

located = detector.locate("hahaha!", "ha")
assert located.repeat == 3
```

API:

- `RepeatPatternDetector(ignore_case=False, min_pattern_len=1, max_pattern_len=None)`
- `detector.detect(text) -> PatternMatch | None`
- `detector.locate(text, pattern) -> PatternMatch | None`
- `detector(text)` as a shorthand for `detector.detect(text)`
- `RepeatPatternDetector.z_algorithm(text) -> list[int]`
- `RepeatPatternDetector.kmp_find_all(text, pattern) -> list[int]`

`PatternMatch` is a frozen dataclass with:

- `pattern: str`
- `repeat: int`
- `start: int`
- `end: int`

Notes:

- `min_pattern_len` must be at least `1`.
- `max_pattern_len` limits the maximum pattern length considered by `detect()`.
- `locate()` raises `ValueError` when `pattern` is empty.
- With `ignore_case=True`, matching is case-insensitive, but the returned
  pattern is sliced from the original text.

## Hash Helpers

```python
from vortezwohl.crypt import md5, sha1, sha256, sha512

md5_digest = md5("hello")
sha1_digest = sha1("hello")
sha256_digest = sha256("hello")
sha512_digest = sha512("hello")
```

All hash helpers accept a `str`, encode it with UTF-8, and return a hexadecimal
digest.

These helpers are general-purpose convenience wrappers. Do not use them as a
complete password-storage or security-sensitive cryptography solution.

## Random Seed Helper

```python
from vortezwohl.random import next_seed

seed = next_seed()
```

`next_seed()` returns an integer seed, calls `random.seed(seed)`, and updates
process-local seed state protected by a lock.

Environment variables read during first use:

- `INITIAL_SEED`, default `0`
- `SEED_MULTIPLIER`, default `1`

The seed value is bounded by `1e64`.

## System Helpers

`System` wraps common Python environment and package-management operations.

```python
from vortezwohl.sys import System

system = System()

stdout, code, stderr = system.shell("python --version")
packages = system.list_packages()
version = system.package_version("requests")
size = system.package_size("requests")
```

Constructor behavior:

- Stores the current Python executable and working directory.
- Runs `python -m ensurepip --upgrade`.
- Locates the best-matching `pip` executable in the Python executable directory.

Methods:

- `shell(cmd, workdir=None, timeout=None, force_check=False) -> tuple[str, int, str]`
- `script(script, argument)`
- `interpret(script, is_module=False)`
- `list_packages() -> list[str]`
- `show_package(package) -> list[str]`
- `package_size(package) -> int`
- `package_version(package) -> str`
- `install_package(package, version=None) -> str | bool`
- `uninstall_package(package) -> str | bool`

Notes:

- `shell()` uses `subprocess.run(..., shell=True, capture_output=True, text=True)`.
- `force_check=True` raises `subprocess.CalledProcessError` on non-zero exit.
- `interpret(script, is_module=True)` runs `python -m <script>`.
- `install_package(package)` upgrades the package.
- `install_package(package, version)` uses `pip install package~=version`.
- `uninstall_package(package)` runs pip uninstall and confirms with `Y`.
- Package install and uninstall methods return `False` on pip failure.

## Logging

Importing `vortezwohl` configures package loggers:

- `vortezwohl`
- `vortezwohl.io`
- `vortezwohl.retry`

The root `vortezwohl` logger has a console handler and a formatter. The package
sets logger levels to `INFO` by default.

## Practical Guidance

- Use `Retry` at I/O or model-call boundaries where transient failures are
  expected.
- Use `ThreadPool` for straightforward synchronous parallel work; sort results
  yourself if input order matters.
- Use `LRUCache` for bounded in-process memoization.
- Use `HttpClient` only for simple JSON POST and query-parameter GET workflows.
  Use `requests` directly for sessions, streaming, multipart upload, cookies, or
  advanced authentication.
- Use `timeout()` to stop waiting for a result, not to cancel the underlying
  operation.
- Use `LevenshteinDistance.rank()` only when fuzzy matching against a known,
  closed candidate set.
- Use `sliding_window()` with overlap for long-text processing, then remove
  padding values and deduplicate merged outputs.
