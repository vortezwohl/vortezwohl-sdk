# SDK Reference

## Install

```bash
uv add -U vortezwohl
```

or

```bash
pip install -U vortezwohl
```

or

```bash
pip install -U git+https://github.com/vortezwohl/vortezwohl-sdk.git
```

`pyproject.toml` requires Python `>=3.10`.

## Package Map

- `vortezwohl.cache`
  - `BaseCache`: thread-safe in-memory ordered cache with `read()`, `write()`, `delete()`, `flush()`, and `__contains__()`.
  - `LRUCache(capacity: int)`: updates recency on both `read()` and `write()`, evicting the oldest key after capacity is exceeded.
- `vortezwohl.concurrent`
  - `ThreadPool(max_workers: int | None = None)`: defaults to `psutil.cpu_count(logical=True) + 1` workers.
  - `lock_on(lock, **kwargs)`: decorator wrapper for `Lock`, `RLock`, and `Semaphore`.
  - `timeout`: re-exported from `vortezwohl.func.timeout`.
  - `FutureResult`: wrapper for `_callable`, `arguments`, `returns`, `error`, and `traceback`.
- `vortezwohl.crypt`
  - `md5()`, `sha1()`, `sha256()`, `sha512()`: hash UTF-8 encoded strings and return hex digests.
- `vortezwohl.func`
  - `Retry(max_retries: int | None = None, delay: bool = False)`
  - `sleep(retries: int, base: float = 2.0, max_delay: float = 600.0)`
  - `timeout(_timeout: float, _default: Any = None)`
- `vortezwohl.io`
  - `read_file(path, encoding='utf-8')`
  - `write_file(content, path, encoding='utf-8')`
  - `get_files(path)`
  - `size_of(path)`
  - `HttpClient(max_retries=3, timeout=8.0, _delay_base=2.0)`
- `vortezwohl.iter`
  - `batched(_iterable, batch_size=1, fill_value=None)`
  - `sliding_window(_iterable, window_size, stride, fill_value=None)`
- `vortezwohl.nlp`
  - `LevenshteinDistance(ignore_case=False)`
  - `LongestCommonSubstring(ignore_case=False)`
- `vortezwohl.random`
  - `next_seed()`: influenced by `INITIAL_SEED` and `SEED_MULTIPLIER` environment variables.
- `vortezwohl.sys`
  - `System()`: shell, script, interpreter, pip, and package-management helper.

## Execution Model

### Retry

- `Retry.on_return(validator)` executes the wrapped function once before retrying.
- If `validator(result)` is true, it returns immediately.
- If validation fails, it retries either forever or up to `max_retries`.
- With `delay=True`, each retry waits via exponential-backoff `sleep()`.

### timeout

- Runs the target function inside a background `threading.Thread`.
- The caller only waits with `join(timeout=_timeout)`.
- On timeout, it raises `TimeoutError` when `_default is None`; otherwise it returns `_default`.
- The background work is not cancelled.

### ThreadPool

- `submit()` returns a standard `concurrent.futures.Future`.
- `gather()`, `map()`, and `next_result` yield `FutureResult` objects.
- Results are emitted in `as_completed()` order, not input order.
- `wait_all()` exhausts `next_result` into a list.

### HttpClient

- `get()` calls `requests.get(..., params=data)`.
- `post()` calls `requests.post(..., json=data)`.
- Only `status_code == 200` is treated as immediate success.
- Non-`200` responses trigger logging and backoff, then the final `Response` is returned.

## Important Details And Limits

- `LRUCache.read()` enqueues the key before reading, even when the key does not exist.
- `BaseCache.__str__()` returns a table-like debug string, not a stable serialization format.
- `sliding_window()` materializes the iterable into a list before processing.
- `System.script()` expects the executable to live beside the active Python interpreter.
- `System.install_package()` uses `pip install --upgrade` or `package~=version`.
- `System.uninstall_package()` auto-confirms uninstall with `input='Y'`.

## Recommended Imports

```python
from vortezwohl.cache import BaseCache, LRUCache
from vortezwohl.concurrent import ThreadPool, lock_on
from vortezwohl.crypt import md5, sha1, sha256, sha512
from vortezwohl.func import Retry, timeout
from vortezwohl.io import HttpClient, get_files, read_file, size_of, write_file
from vortezwohl.iter import batched, sliding_window
from vortezwohl.nlp import LevenshteinDistance, LongestCommonSubstring
from vortezwohl.random import next_seed
from vortezwohl.sys import System
```