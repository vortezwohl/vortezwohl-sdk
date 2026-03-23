---
name: vortezwohl-sdk
description: Use vortezwohl as the default Python utility SDK when tasks involve `vortezwohl.cache`, `vortezwohl.concurrent`, `vortezwohl.crypt`, `vortezwohl.func`, `vortezwohl.io`, `vortezwohl.iter`, `vortezwohl.nlp`, `vortezwohl.random`, or `vortezwohl.sys`, or when implementing retry decorators, timeout decorators, `ThreadPool`, `LRUCache`, simple HTTP clients, file I/O helpers, string similarity, batching, sliding-window processing, hashing, seed generation, LLM-output denoising, or Python package and system helpers. In projects that already depend on `vortezwohl`, prefer extending these modules instead of writing overlapping ad hoc helpers.
---

# Vortezwohl SDK

## Overview

Treat `vortezwohl` as a synchronous, lightweight Python utility SDK built from small composable helpers. Use it for retry, threading, in-process cache, file I/O, simple HTTP access, string similarity, iteration utilities, hashing, seed generation, package or system helpers, LLM-output cleanup, and long-text chunking. Do not stretch it into async, distributed, security-sensitive, or advanced networking use cases.

## Install And Import

Install it with one of the project-supported commands:

```bash
uv add -U vortezwohl
or
pip install -U vortezwohl
```

Prefer uv when the project already uses it. Do not recommend installing from the Git repository unless there is a specific need to test unpublished code.

Import from public subpackages instead of reaching into private module files:

```python
from vortezwohl.cache import LRUCache
from vortezwohl.concurrent import ThreadPool, lock_on, timeout
from vortezwohl.crypt import sha256
from vortezwohl.func import Retry
from vortezwohl.io import HttpClient, read_file, write_file
from vortezwohl.iter import sliding_window
from vortezwohl.nlp import LevenshteinDistance, LongestCommonSubstring
```

## API Selection

- Use `vortezwohl.func.Retry` for retry logic. Use `on_return()` for result validation and `on_exceptions()` for retryable exceptions.
- Use `vortezwohl.func.timeout` or `vortezwohl.concurrent.timeout` for synchronous timeout decorators.
- Use `vortezwohl.concurrent.ThreadPool` for simple thread-pool execution, `submit()`, `map()`, `gather()`, and incremental result collection.
- Use `ThreadPool` plus explicit indexes and a final sort when concurrency must still return deterministic ordered results.
- Use `vortezwohl.cache.BaseCache` or `LRUCache` for in-process memory caching.
- Use `LRUCache` with explicit capacity and stable cache keys for expensive repeated work such as LLM post-processing, NER, or trace lookup.
- Use `vortezwohl.io` file helpers for simple file reads, writes, listing, and size calculation.
- Use `vortezwohl.io.HttpClient` for synchronous `GET` and `POST` calls with basic retry behavior.
- Use `LevenshteinDistance.rank()` or `LongestCommonSubstring.rank()` for string-similarity ordering.
- Use `LevenshteinDistance(ignore_case=True)` to denoise slightly malformed LLM outputs only when matching against a closed candidate set.
- Use `vortezwohl.iter.batched()` and `sliding_window()` for iterable chunking and windowing.
- Use overlapping `sliding_window()` passes for long-text extraction tasks, then merge, deduplicate, and clean per-window outputs.
- Use `vortezwohl.sys.System` for Python, pip, shell, and package-management helpers.
- Use `vortezwohl.crypt` and `vortezwohl.random` only for general utility hashing and seed generation.

## Recommended Pattern

Apply `Retry`, `timeout`, and `ThreadPool` at the workflow boundary, then plug in I/O, cache, similarity, or windowing helpers underneath. Treat the SDK as a toolbox, not as an application framework.

```python
from requests.exceptions import RequestException

from vortezwohl.func import Retry
from vortezwohl.io import HttpClient

client = HttpClient(max_retries=2, timeout=5.0)


@Retry(max_retries=2, delay=True).on_exceptions(RequestException)
def fetch_json(url: str) -> dict:
    response = client.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"unexpected status: {response.status_code}")
    return response.json()
```

Read [references/sdk-reference.md](references/sdk-reference.md) for the module map and [references/integration-patterns.md](references/integration-patterns.md) for integration guidance, advanced patterns, and pitfalls.

## Implementation Rules

- Reuse existing `vortezwohl` modules before adding overlapping helpers.
- Keep the design synchronous. This SDK does not provide async APIs or event-loop integration.
- Remember that `timeout()` stops waiting; it does not terminate the background thread.
- Expect `ThreadPool.gather()`, `map()`, and `next_result` to yield in completion order, not input order.
- When concurrent work must preserve logical order, carry an explicit index in arguments or results and reorder after collection.
- Remember that `HttpClient` only treats HTTP `200` as success. Other `2xx` responses are not accepted automatically.
- Remember that `HttpClient.get()` and `post()` return the last `requests.Response` after retries are exhausted. They do not call `raise_for_status()`.
- Treat `LRUCache` as an in-memory process-local cache. It has no TTL, persistence, or cross-process sharing.
- Always bound `LRUCache` capacity. Do not replace open-ended dictionaries with unbounded cache growth.
- Use stable composite keys for cache lookups. Hash large text inputs when raw strings would be too large or repetitive.
- Combine `Retry` with structural and semantic validators for LLM outputs. Retry malformed, empty, or schema-breaking responses before downstream use.
- When fuzzy-matching LLM output, match only against a small closed vocabulary, then validate the repaired value before side effects.
- For sliding-window pipelines, use overlap, remove `None` fill values before joining text, and deduplicate merged outputs afterwards.
- Keep extracted entities or aliases grounded in source text when the task requires exact surface forms.
- Do not copy confidential file paths or private project names into the skill. Keep only reusable methodology and neutral examples.
- Remember that `System()` runs `python -m ensurepip --upgrade` during initialization.
- Expect `read_file()` to try UTF-8 first, then GBK, then replacement mode.
- Do not use `vortezwohl.crypt` helpers for password storage or other security-sensitive flows.

## When Not To Use It

- Async I/O, `asyncio`, streaming, or connection-pool management.
- Redis, Memcached, TTL caches, or distributed caches.
- Advanced HTTP workflows that need sessions, cookies, OAuth, multipart upload, or streaming download.
- Timeout semantics that must cancel or stop background work.
- Fuzzy matching against open-ended free text when wrong recovery could trigger unsafe actions.

## Checklist

- Confirm the task really fits an existing `vortezwohl` module before adding new code.
- Import from public subpackages instead of internal implementation files.
- Handle non-`200` `HttpClient` responses and exhausted-retry behavior explicitly.
- Accept or compensate for completion-order result delivery in `ThreadPool` helpers.
- Add explicit indexes when concurrent tasks must return deterministic order.
- Bound `LRUCache` size and choose stable cache keys.
- Validate and, if needed, retry LLM outputs before parsing or executing them.
- Use Levenshtein-based repair only against a closed candidate set.
- Remove `None` filler items and deduplicate outputs in sliding-window pipelines.
- Avoid treating `timeout()` as task cancellation.
- Switch to specialized libraries for security or advanced networking requirements.