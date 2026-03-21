# Patterns And Recipes

## 1. Thread Pool Plus Retry

Reference project:

- `D:\project\novel_reimagine\novel_reimagine\agent\commentary_script\script_convertor.py`

Observed pattern:

- define a retry-wrapped single-item worker
- split source content into independent units
- submit units into `ThreadPool`
- consume `threads.next_result`
- re-sort by original index after concurrent completion

Why it fits `vortezwohl`:

- `Retry` keeps the worker function simple
- `ThreadPool` yields `FutureResult` objects that retain original kwargs, so the caller can recover the source index from `res.arguments`

Recommended template:

```python
retry = Retry(max_retries=5, delay=True)

@retry.on_exceptions(ValueError)
def process_item(index: int, item: str) -> str:
    ...

threads = ThreadPool(16)
for i, item in enumerate(items):
    threads.submit(process_item, index=i, item=item)

results = []
for res in threads.next_result:
    if res.error:
        raise res.error
    results.append((res.arguments["index"], res.returns))

ordered = [value for _, value in sorted(results, key=lambda x: x[0])]
```

Use this when work items are independent and final ordering can be reconstructed after completion.

## 2. Levenshtein Repair For Noisy Model Output

Reference project:

- `D:\project\Autono\autono\prompt\next_move_prompt.py`

Observed pattern:

- model outputs an ability name or parameter key that may be slightly wrong
- code ranks valid candidates with `LevenshteinDistance.rank(...)`
- top-ranked valid symbol is used as the repaired value

Why it fits `vortezwohl`:

- the implementation is tiny, deterministic, and easy to apply post-generation
- it is especially useful when the allowed value set is closed and fairly small

Recommended template:

```python
distance = LevenshteinDistance(ignore_case=True)
fixed_name = distance.rank(model_name, valid_names)[0]
fixed_key = distance.rank(model_key, list(valid_params.keys()))[0]
```

Use this for:

- ability names
- tool names
- enum-like strings
- JSON field names
- executable names discovered from a directory

Do not use this blindly when candidate sets are huge or semantically ambiguous.

## 3. Timeout Around Long Pipelines

Reference project:

- `D:\project\neo-translator\neo_translator\__main__.py`

Observed pattern:

- decorate the long-running pipeline with `@timeout(...)`
- wrap that same pipeline with `Retry` for recoverable validation failures

Why it fits `vortezwohl`:

- the timeout decorator is simple to add and does not require async refactors
- it works well for pipelines that should degrade or fail fast at the orchestration level

Recommended template:

```python
retry = Retry(max_retries=3, delay=True)

@retry.on_exceptions([ValueError, TimeoutError])
@timeout(300)
def pipeline(...):
    ...
```

Critical warning:

- timed-out work may still continue in the background thread
- avoid non-idempotent side effects unless the caller can tolerate duplicates

## 4. LRU Cache For Trace IDs Or Expensive Text Work

Reference project:

- `D:\project\any-llm-sdk\any_llm\llm.py`

Companion pattern from another project:

- `D:\project\novel_localizer\novel_localizer\util\ner.py`
- combine `LRUCache` with `sha256` to cache expensive LLM NER output

Recommended template:

```python
cache = LRUCache(capacity=8192)

def cached_work(text: str) -> dict:
    key = sha256(text)
    if key in cache:
        return cache[key]
    result = expensive_call(text)
    cache[key] = result
    return result
```

Use this when:

- function outputs are deterministic enough
- memory must stay bounded
- keys can be normalized into stable strings

## 5. Sliding Window Over Text With Parallel Fan-Out

Reference project:

- `D:\project\novel_localizer\novel_localizer\util\ner.py`

Observed pattern:

- split text into lines
- generate overlapping windows with `sliding_window`
- fan windows out through `ThreadPool`
- merge entity dictionaries afterward

Why it fits `vortezwohl`:

- `sliding_window` expresses overlap directly
- `ThreadPool` makes each window independent
- `LRUCache` can suppress repeated work for duplicate windows or repeated requests

Recommended template:

```python
windows = sliding_window(lines, window_size=64, stride=16, fill_value=None)
threads = ThreadPool(64)
for chunk in windows:
    text = "\n".join(x for x in chunk if x is not None)
    threads.submit(process_chunk, text=text)
```

Use this when:

- downstream logic needs local context overlap
- full-text processing is too large or too noisy in one shot
- post-processing can merge partial results

## 6. HTTP Calls With Explicit Exception Retry

The SDK's `HttpClient` only retries based on status code. For production-facing network work, pair it with `Retry.on_exceptions(...)`.

Recommended template:

```python
from requests.exceptions import HTTPError, ConnectionError, Timeout

retry = Retry(max_retries=2, delay=True)
client = HttpClient(max_retries=3, timeout=30)

@retry.on_exceptions([HTTPError, ConnectionError, Timeout])
def fetch_json(url: str) -> dict:
    response = client.get(url)
    if response.status_code != 200:
        raise HTTPError(response.text)
    return response.json()
```

This separates:

- status-code retries handled inside `HttpClient`
- transport-exception retries handled outside via `Retry`

## 7. Package And Tool Discovery With Fuzzy Matching

Reference project inside this package:

- `vortezwohl/sys/system.py`

Observed pattern:

- read filesystem entries
- rank them against a desired tool name using `LevenshteinDistance`
- pick the closest match

Use this only when executable naming may vary across platforms or environments, and log or inspect the resolved value before relying on it in critical automation.

## Pattern Selection Guide

Choose the smallest viable combination:

- need bounded parallel fan-out: `ThreadPool`
- need retry on bad return value: `Retry.on_return`
- need retry on exceptions: `Retry.on_exceptions`
- need wall-clock guardrail: `timeout`
- need deterministic fuzzy correction: `LevenshteinDistance`
- need bounded memoization: `LRUCache`
- need chunking without overlap: `batched`
- need chunking with overlap: `sliding_window`

Prefer adding one primitive at a time. This package is most maintainable when each helper's responsibility stays obvious from the call site.
