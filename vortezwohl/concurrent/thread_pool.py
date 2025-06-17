from concurrent.futures import ThreadPoolExecutor, as_completed
from types import NoneType

from typing_extensions import Iterable, Any

import psutil


class ThreadPool(object):
    def __init__(self, max_workers: int | None = None):
        if max_workers is None:
            max_workers = psutil.cpu_count(logical=True) + 1
        self._max_workers = max_workers
        self._thread_pool_executor = ThreadPoolExecutor(max_workers=self._max_workers)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.shutdown(cancel_futures=False)

    def gather(self, jobs: Iterable[callable], arguments: list[dict] | list[tuple] | list[NoneType] | None = None) -> Any:
        futures = []
        for i, job in enumerate(jobs):
            if arguments is None or arguments[i] is None:
                futures.append(self._thread_pool_executor.submit(job))
                continue
            if isinstance(arguments[i], dict):
                futures.append(self._thread_pool_executor.submit(lambda param: job(**param), arguments[i]))
            elif isinstance(arguments[i], Iterable):
                futures.append(self._thread_pool_executor.submit(lambda param: job(*param), arguments[i]))
            else:
                futures.append(self._thread_pool_executor.submit(job, arguments[i]))
        for future in as_completed(futures):
            try:
                yield future.result()
            except Exception as __e:
                yield __e

    def shutdown(self, cancel_futures: bool = True):
        self._thread_pool_executor.shutdown(wait=True, cancel_futures=cancel_futures)
        return self

    @property
    def thread_pool_executor(self):
        return self._thread_pool_executor

    @property
    def max_workers(self) -> int:
        return self._max_workers
