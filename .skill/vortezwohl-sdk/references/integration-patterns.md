# Integration Patterns

## 1. Pick Control-Flow Helpers First

Decide first whether the task needs:

- retry behavior with `Retry`
- a synchronous wait bound with `timeout`
- parallel execution with `ThreadPool`
- hot-data caching with `LRUCache`
- small utility helpers such as `read_file`, `write_file`, `batched`, `sliding_window`, or `rank()`

This keeps `vortezwohl` in its intended role as a toolbox.

## 2. Retry At The I/O Boundary

Recommended:

```python
from requests.exceptions import RequestException

from vortezwohl.func import Retry
from vortezwohl.io import HttpClient

client = HttpClient(max_retries=2, timeout=5.0)


@Retry(max_retries=1, delay=True).on_exceptions(RequestException)
def fetch(url: str):
    response = client.get(url)
    if response.status_code != 200:
        raise RuntimeError(response.status_code)
    return response.json()
```

Avoid:

- stacking multiple aggressive retry layers around `HttpClient(max_retries=3)`
- assuming `client.get()` raises on failure instead of returning a `Response`

## 3. Accept Completion-Order Semantics In ThreadPool

Recommended:

```python
from vortezwohl.concurrent import ThreadPool
from vortezwohl.io import read_file

paths = ["a.txt", "b.txt", "c.txt"]
arguments = [(path,) for path in paths]

with ThreadPool() as pool:
    for result in pool.map(read_file, arguments=arguments):
        if result.error is None:
            print(result.returns)
```

Notes:

- `map()` and `gather()` do not preserve input order.
- If order matters, carry an index and re-sort results afterwards.

## 4. Use timeout() Defensively

Treat `timeout()` as a caller-side wait guard, not as cancellation. Default to raising `TimeoutError`; only provide `_default` when the caller has an explicit fallback policy and swallowing the timeout is intentional.

```python
from vortezwohl.func import timeout


@timeout(2.0)
def slow_call():
    ...
```

Notes:

- The background thread may keep running after timeout.
- Side-effecting functions need extra care around re-entry and duplicate execution.
- Add _default only for narrow cases such as best-effort enrichment, optional background metadata, or non-critical UI fallback values.

## 5. Instantiate System() Only Where Side Effects Are Acceptable

`System()` runs `python -m ensurepip --upgrade` in its constructor. That makes it better suited to scripts, automation, and controlled environments than to hot paths.

## 6. Switch Tools For Security And Advanced Networking

Do not force `vortezwohl` into:

- password storage, signing, encryption, or other security-sensitive flows
- session, cookie, OAuth, streaming, multipart, or pooled HTTP workflows
- distributed, TTL, or persistent caching requirements

## 7. Return Ordered Results From Concurrent Work

When tasks are independent but output order must match source order, submit work concurrently, capture an explicit index, then sort after collection.

```python
from vortezwohl.concurrent import ThreadPool


def process(index: int, chunk: str) -> tuple[int, str]:
    return index, convert(chunk)


ordered = []
with ThreadPool(16) as pool:
    for index, chunk in enumerate(chunks):
        pool.submit(process, index=index, chunk=chunk)
    for result in pool.next_result:
        if result.error:
            raise result.error
        ordered.append(result.returns)

ordered = [value for _, value in sorted(ordered, key=lambda item: item[0])]
```

Use this pattern instead of assuming `next_result` preserves submission order.

## 8. Use Levenshtein Distance To Denoise Closed-Set LLM Output

When an LLM is supposed to emit one item from a known set, recover minor spelling or casing errors by ranking against the canonical candidates.

```python
from vortezwohl.nlp import LevenshteinDistance

matcher = LevenshteinDistance(ignore_case=True)
ability_name = matcher.rank(raw_ability_name, allowed_ability_names)[0]
```

Good fits:

- ability names
- parameter names
- enum-like labels
- fixed action markers

Avoid using this for open-ended free text. Always validate the repaired value before triggering side effects.

## 9. Bound Caches And Validate LLM Output Before Caching

For repeated expensive LLM calls or post-processing, combine a bounded `LRUCache` with `Retry` and explicit output validation.

```python
from vortezwohl.cache import LRUCache
from vortezwohl.crypt import sha256
from vortezwohl.func import Retry

cache = LRUCache(capacity=8192)
retry = Retry(max_retries=8, delay=True)


@retry.on_exceptions([ValueError, TypeError])
def parse_entities(text: str) -> dict:
    key = sha256(text)
    if key in cache:
        return cache[key]
    result = call_model(text)
    if not isinstance(result, dict):
        raise TypeError("Result should be dict")
    if not result:
        raise ValueError("Empty result")
    cache[key] = result
    return result
```

Rules:

- pick an explicit capacity from config or workload estimates
- hash large composite inputs into stable keys
- cache only validated outputs
- do not let an ordinary dictionary grow forever for unbounded prompt or text keys

## 10. Use Overlapping Sliding Windows For Long-Text Extraction

For long text that exceeds practical model context, split into overlapping windows, process each window independently, then merge and clean the aggregate result.

```python
from vortezwohl.iter import sliding_window

lines = [line for line in text.splitlines() if line]
for window in sliding_window(lines, window_size=window_lines, stride=window_lines // 4, fill_value=None):
    window = [line for line in window if line is not None]
    chunk = "\n".join(window)
    submit(chunk)
```

Rules:

- use overlap so entities near window boundaries are seen more than once
- remove `None` fill values before joining text
- merge per-window results and deduplicate aliases afterwards
- remove self aliases such as `entity in aliases`
- when exact extraction matters, reject entities or aliases that do not exist in the source chunk or source text