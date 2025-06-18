import traceback
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from threading import Lock
from types import NoneType

from typing_extensions import Iterable, Any, Callable, Dict, Tuple

import psutil


class ThreadPool(object):
    def __init__(self, max_workers: int | None = None):
        if max_workers is None:
            max_workers = psutil.cpu_count(logical=True) + 1
        self._max_workers = max_workers
        self._thread_pool_executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._futures = list()
        self._futures_lock = Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.shutdown(cancel_futures=False)

    def submit(self, job: Callable, *args, **kwargs) -> Future:
        _future = None
        if len(args) > 0:
            _future = self._thread_pool_executor.submit(lambda param: (job, param, job(*param)), args)
        elif len(kwargs) > 0:
            _future = self._thread_pool_executor.submit(lambda param: (job, param, job(**param)), kwargs)
        else:
            _future = self._thread_pool_executor.submit(lambda: (job, None, job()))
        with self._futures_lock:
            self._futures.append(_future)
        return _future

    def gather(self, jobs: Iterable[Callable], arguments: list[Dict] | list[Tuple] | list[NoneType] | None = None) \
            -> tuple[Callable, Any, Any] | Exception:
        futures = []
        for i, job in enumerate(jobs):
            if arguments is None or arguments[i] is None:
                futures.append(self._thread_pool_executor.submit(lambda: (job, None, job())))
                continue
            if isinstance(arguments[i], dict):
                futures.append(self._thread_pool_executor.submit(lambda param: (job, param, job(**param)), arguments[i]))
            elif isinstance(arguments[i], Iterable):
                futures.append(self._thread_pool_executor.submit(lambda param: (job, param, job(*param)), arguments[i]))
            else:
                futures.append(self._thread_pool_executor.submit(lambda param: (job, param, job(param)), arguments[i]))
        for future in as_completed(futures):
            try:
                yield future.result()
            except Exception as __e:
                yield __e, traceback.format_exc()

    def map(self, jobs: Iterable[Callable], arguments: list[Dict] | list[Tuple] | list[NoneType] | None = None) \
            -> tuple[Callable, Any, Any] | Exception:
        return self.gather(jobs=jobs, arguments=arguments)

    def shutdown(self, cancel_futures: bool = True):
        self._thread_pool_executor.shutdown(wait=True, cancel_futures=cancel_futures)
        return self

    @property
    def next_result(self) -> Any:
        for f in as_completed(self._futures):
            try:
                yield f.result()
            finally:
                with self._futures_lock:
                    self._futures.remove(f)

    @property
    def thread_pool_executor(self) -> ThreadPoolExecutor:
        return self._thread_pool_executor

    @property
    def max_workers(self) -> int:
        return self._max_workers
