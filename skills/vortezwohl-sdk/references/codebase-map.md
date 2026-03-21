# Codebase Map

## Package Shape

The project is a flat utility package with one main distribution package:

- `vortezwohl/__init__.py`
- `vortezwohl/cache/*`
- `vortezwohl/concurrent/*`
- `vortezwohl/crypt/*`
- `vortezwohl/func/*`
- `vortezwohl/io/*`
- `vortezwohl/iter/*`
- `vortezwohl/nlp/*`
- `vortezwohl/random/*`
- `vortezwohl/sys/*`

`pyproject.toml` declares a pure Python package requiring Python `>=3.10` and depending on `overrides`, `psutil`, `requests`, `typing-extensions`, and `urllib3>=2.5.0`.

## Root Module

### `vortezwohl/__init__.py`

Provides:

- constants: `NEW_LINE`, `BLANK`, `UTF_8`
- logger bootstrap for `vortezwohl`, `vortezwohl.io`, and `vortezwohl.retry`

Behavior notes:

- adds a console handler on import
- sets package logger to `INFO`
- acts as the source of shared string constants used by retry and IO logging

## Concurrency

### `vortezwohl/concurrent/thread_pool.py`

Primary class: `ThreadPool`

Public API:

- `ThreadPool(max_workers: int | None = None)`
- `submit(job, *args, **kwargs) -> Future`
- `gather(jobs, arguments=None) -> Iterable[FutureResult]`
- `map(job, arguments) -> Iterable[FutureResult]`
- `wait_all() -> list[FutureResult]`
- `next_result -> Iterable[FutureResult]`
- `shutdown(cancel_futures=True)`
- context manager support

Execution model:

- wraps `concurrent.futures.ThreadPoolExecutor`
- default worker count is `psutil.cpu_count(logical=True) + 1`
- stores submitted futures in an internal list guarded by `RLock`
- emits `FutureResult` objects that capture callable metadata, args, returns, error, and traceback
- `next_result`, `wait_all`, and `gather` all yield completion order

Non-obvious details:

- `submit` preserves either tuple args, dict kwargs, or no arguments, and stores the original argument payload in the result tuple.
- `gather` and `map` are the easiest fan-out helpers when the caller wants `FutureResult` instead of raw futures.
- Current implementation uses lambdas that close over loop variables in `gather`; for heterogeneous job lists, verify behavior carefully before relying on the reported callable identity.

### `vortezwohl/concurrent/future_result.py`

Data container: `FutureResult`

Fields exposed as properties:

- `callable`
- `arguments`
- `returns`
- `error`
- `traceback`

Use this wrapper when the caller wants uniform success/error handling without manually joining futures.

### `vortezwohl/concurrent/lock.py`

Decorator factory: `lock_on(lock, **kwargs)`

Purpose:

- wrap a function so it acquires a `Lock`, `RLock`, or `Semaphore` before execution

Behavior notes:

- if `blocking` is not supplied, or if `timeout` is supplied, it forces `blocking=True`
- releases semaphores via `release(n=1)`
- releases other locks via `release()`

Use this when the protected section is small and decorator-style synchronization is clearer than open-coded `with` or `acquire/release`.

## Retry And Timeout

### `vortezwohl/func/retry.py`

Exports:

- `sleep(retries, base=2.0, max_delay=600.0)`
- `Retry`
- `MaxRetriesReachedError`

`sleep`:

- computes exponential delay as `min(base ** retries, max_delay)`
- adds random jitter with `random.uniform(0.1, delay)`

`Retry(max_retries: int | None = None, delay: bool = False)`:

- `on_return(validator)`
- `on_exceptions(exceptions)`

`on_return` semantics:

- call once
- if `validator(result)` is true, return immediately
- otherwise retry forever when `max_retries is None`
- otherwise retry up to `max_retries` more times
- raise `MaxRetriesReachedError` on failure after all attempts

`on_exceptions` semantics:

- retry only when the raised exception is an instance of one of the declared types
- preserve unexpected exceptions by re-raising them immediately
- return successful result directly once any attempt succeeds

### `vortezwohl/func/timeout.py`

Decorator factory: `timeout(_timeout: float, _default: Any = None)`

Execution model:

- runs the wrapped function in a new `threading.Thread`
- waits with `thread.join(timeout=_timeout)`
- if still alive:
  - raise `TimeoutError` when `_default is None`
  - otherwise return `_default`
- if wrapped function raised, re-raise its first captured exception

Important limitation:

- the worker thread is not cancelled or killed after timeout; it may continue running in the background

## Cache

### `vortezwohl/cache/base_cache.py`

Base class: `BaseCache`

API:

- `read`
- `write`
- `flush`
- `delete`
- `__contains__`
- `__getitem__`
- `__setitem__`
- `__delitem__`
- `__len__`
- `__call__`
- pretty `__str__` table rendering

Implementation:

- stores data in an ordered mapping with `RLock`
- all basic operations are synchronized

### `vortezwohl/cache/lru_cache.py`

Subclass: `LRUCache(capacity: int)`

Adds:

- `expand_to(capacity)`

Execution model:

- tracks recency in a separate list guarded by another `RLock`
- every `read` and `write` enqueues the key to the tail
- when recency list exceeds capacity, oldest tracked key is deleted from cache

Important limitation:

- `read` enqueues keys before confirming they exist in the cache, so repeated misses also affect recency bookkeeping and can trigger eviction of real entries

## NLP

### `vortezwohl/nlp/base_string_similarity.py`

Abstract callable interface with:

- constructor flag `ignore_case`
- abstract `__call__`
- abstract `rank`

### `vortezwohl/nlp/levenshtein_distance.py`

Concrete class: `LevenshteinDistance(ignore_case=False)`

Behavior:

- computes edit distance with classic `O(m*n)` dynamic programming
- `rank(query, candidates)` sorts candidate strings by ascending distance

Best fit:

- fuzzy repair of model-generated ability names, field names, executable names, or other near-match strings

### `vortezwohl/nlp/longest_common_substring.py`

Concrete class: `LongestCommonSubstring(ignore_case=False)`

Behavior:

- computes the actual longest common contiguous substring
- `rank(query, candidates)` sorts candidates by descending substring length

Best fit:

- coarse similarity when overlap length matters more than edit distance

## IO

### `vortezwohl/io/file.py`

Exports:

- `read_file(path, encoding='utf-8')`
- `write_file(content, path, encoding='utf-8')`
- `get_files(path)`
- `size_of(path)`

Behavior notes:

- `read_file` falls back from UTF-8 to `gbk`, then to replacement decoding
- `write_file` creates parent directories automatically
- `size_of` works for file or directory recursively

### `vortezwohl/io/http_client.py`

Class: `HttpClient(max_retries=3, timeout=8.0, _delay_base=2.0)`

Methods:

- `get(url, data=None, headers=None, **kwargs)`
- `post(url, data, headers=None, **kwargs)`
- static `sleep(...)`

Execution model:

- retries on non-200 HTTP responses
- uses `requests.get(..., params=data, ...)`
- uses `requests.post(..., json=data, ...)`
- logs response body snippets between attempts
- uses the retry backoff helper from `vortezwohl.func.retry`

Important limitation:

- request exceptions such as connection errors are not caught here; callers that need exception retries should wrap usage with `Retry.on_exceptions(...)`

## Iteration Helpers

### `vortezwohl/iter/iter.py`

Exports:

- `batched(_iterable, batch_size=1, fill_value=None)`
- `sliding_window(_iterable, window_size, stride, fill_value=None)`

`batched`:

- yields fixed-size groups
- pads final batch with `fill_value`

`sliding_window`:

- materializes iterable to a list first
- emits fixed-size windows starting every `stride` items
- pads final partial windows with `fill_value`

Best fit:

- overlapped context extraction over line lists or token lists

## Crypt

### `vortezwohl/crypt/hash.py`

Exports:

- `md5`
- `sha1`
- `sha256`
- `sha512`

All helpers accept a text string and return the hex digest.

## Random

### `vortezwohl/random/seed_generator.py`

Export: `next_seed() -> int`

Execution model:

- lazy-loads env vars `INITIAL_SEED` and `SEED_MULTIPLIER`
- updates global counters under `SEED_LOCK`
- seeds Python's global `random` module with the computed value
- returns the new integer seed

Best fit:

- reproducible but evolving seeds across repeated model or sampling calls

## System

### `vortezwohl/sys/system.py`

Class: `System`

Responsibilities:

- discover current Python executable and venv scripts directory
- ensure `pip` exists with `python -m ensurepip --upgrade`
- fuzzy-match the actual pip executable name using `LevenshteinDistance`

Public API:

- `shell(cmd, workdir=None, timeout=None, force_check=False)`
- `script(script, argument)`
- `interpret(script, is_module=False)`
- `list_packages()`
- `show_package(package)`
- `package_size(package)`
- `package_version(package)`
- `install_package(package, version=None)`
- `uninstall_package(package)`

Behavior notes:

- `shell` returns `(stdout, returncode, stderr)`
- `install_package` installs `package~=version` when version is provided, otherwise upgrades latest
- `uninstall_package` auto-confirms via stdin `Y`

Use this module only when subprocess/package management is truly part of the task; for ordinary file editing, prefer direct shell commands from the agent runtime instead.
