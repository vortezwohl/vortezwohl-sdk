# Config And Execution

## Package-Wide Defaults

### Python And Dependencies

- package name: `vortezwohl`
- Python requirement: `>=3.10`
- runtime dependencies:
  - `overrides`
  - `psutil`
  - `requests`
  - `typing-extensions`
  - `urllib3>=2.5.0`

### Logging

Importing `vortezwohl` configures package loggers:

- `vortezwohl`
- `vortezwohl.io`
- `vortezwohl.retry`

Default level is `INFO`. Debug traces exist in retry and IO paths, but they are only visible when the application's logging config enables them.

## Parameters By Module

### `ThreadPool`

Constructor:

- `max_workers: int | None = None`

Semantics:

- `None` means `psutil.cpu_count(logical=True) + 1`
- `submit(job, *args, **kwargs)` returns raw `Future`
- `gather(jobs, arguments=None)` expects `arguments` aligned with `jobs`
- `map(job, arguments)` is `gather` with the same job repeated

Operational guidance:

- use `submit` + `next_result` when feeding work incrementally
- use `gather` or `map` when all jobs are known upfront
- use `wait_all` when you need a materialized list of all results

### `Retry`

Constructor:

- `max_retries: int | None = None`
- `delay: bool = False`

Semantics:

- `max_retries=None` means unbounded retries
- `delay=True` enables exponential backoff plus jitter
- `max_retries=n` generally means up to `n + 1` attempts total

Backoff helper:

- `sleep(retries, base=2.0, max_delay=600.0)`

Practical reading of delay:

- retry 0 sleeps roughly `1.1s` to `2s`
- retry 1 sleeps roughly `2.1s` to `4s`
- retry 2 sleeps roughly `4.1s` to `8s`
- delay saturates at `max_delay`

### `timeout`

Decorator args:

- `_timeout: float`
- `_default: Any = None`

Semantics:

- `_default=None` means raise `TimeoutError`
- otherwise return `_default`
- the work thread may outlive the caller after timeout

Use this when the caller can tolerate abandoned background work or when downstream systems already isolate side effects. Do not assume hard cancellation.

### `HttpClient`

Constructor:

- `max_retries: int = 3`
- `timeout: float = 8.0`
- `_delay_base: float = 2.0`

Request behavior:

- total attempts: up to `max_retries + 1`
- retries only when a response object exists and `status_code != 200`
- each retry sleeps with `sleep(current_retry_index, base=_delay_base, **kwargs)`

Caller responsibility:

- wrap with `Retry.on_exceptions` if DNS, SSL, connection reset, or timeout exceptions should retry too
- inspect non-200 response bodies before discarding them; the client returns the last response after retry exhaustion

### `LRUCache`

Constructor:

- `capacity: int`

State:

- `_cache`: ordered mapping
- `_recently_used`: list

Operational guidance:

- good for bounded memoization of expensive pure-ish functions
- avoid depending on strict LRU semantics under heavy miss traffic unless the implementation is adjusted
- prefer stable deterministic keys such as hashes, tuples, or normalized strings

### `LevenshteinDistance` And `LongestCommonSubstring`

Constructor flag:

- `ignore_case: bool = False`

Operational guidance:

- `LevenshteinDistance` is better for typo correction and label repair
- `LongestCommonSubstring` is better for overlap-driven ranking
- both are dynamic-programming implementations and can become expensive on very long strings or large candidate sets

### `read_file` / `write_file`

Parameters:

- `read_file(path, encoding='utf-8')`
- `write_file(content, path, encoding='utf-8')`

Encoding behavior:

- `read_file` tries UTF-8, then GBK, then replacement mode
- `write_file` writes bytes in binary mode or strings in text mode

### `batched` / `sliding_window`

Parameters:

- `batched(_iterable, batch_size=1, fill_value=None)`
- `sliding_window(_iterable, window_size, stride, fill_value=None)`

Operational guidance:

- `sliding_window` copies the iterable into memory first
- choose `stride < window_size` for overlap
- choose `fill_value=None` when downstream code knows to filter padding

### `next_seed`

Environment variables:

- `INITIAL_SEED`
- `SEED_MULTIPLIER`

Semantics:

- both env vars are lazily read only on first use
- internal globals are mutated on every call
- function also reseeds the module-level `random` generator

### `System`

Key parameters:

- `shell(..., timeout=None, force_check=False)`
- `install_package(package, version=None)`
- `interpret(script, is_module=False)`

Operational guidance:

- `force_check=True` raises `subprocess.CalledProcessError` on non-zero exit
- `install_package(version=x)` uses compatible-release syntax `~=`
- constructor side effect: runs `ensurepip --upgrade`

## Composition Order

Decorator order matters.

Example:

```python
retry = Retry(max_retries=3, delay=True)

@retry.on_exceptions(ValueError)
@timeout(30)
def work(...):
    ...
```

This means:

1. `timeout` wraps the function first.
2. `Retry` sees `TimeoutError` or `ValueError` only if they escape the timeout wrapper.
3. Since `Retry.on_exceptions(ValueError)` does not include `TimeoutError`, timeouts will not retry in this example.

Use this mental model when combining retry and timeout. If timeout-driven retries are required, include `TimeoutError` in the retry exception list or restructure the wrappers.

## Important Caveats

### `ThreadPool`

- completion order is not stable submission order
- `gather` uses closure-captured `job` variables; treat callable metadata as suspect when jobs differ

### `timeout`

- does not stop side effects already running in the worker thread

### `HttpClient`

- non-200 responses retry
- network exceptions bubble

### `LRUCache`

- misses still touch recency tracking

### `System`

- constructor performs environment-sensitive subprocess work
- avoid creating `System()` just to inspect a constant or path unless package management behavior is actually needed

## Recommended Verification After Changes

- unit-test one success path and one failure path for every modified decorator or helper
- if touching concurrency, run a small multi-job smoke test and inspect both success and error `FutureResult`
- if touching cache behavior, test hit, miss, update, delete, and eviction
- if touching retry behavior, test exact attempt counts and final exception text
- if touching timeout behavior, test both `_default=None` and `_default=<sentinel>`
