import traceback
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from threading import Lock
from types import NoneType
from typing_extensions import Iterable, Callable, Dict, Tuple

import psutil

from vortezwohl.concurrent.future_result import FutureResult


class ThreadPool:
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

    def gather(self, jobs: Iterable[Callable], arguments: list[Dict] | list[Tuple] | list[NoneType] | None = None) -> Iterable[FutureResult]:
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
                res = future.result()
                yield FutureResult(_callable=res[0], arguments=res[1], returns=res[2],
                                   error=None, traceback=None)
            except Exception as __e:
                yield FutureResult(_callable=None, arguments=None, returns=None,
                                   error=__e, traceback=traceback.format_exc())

    def map(self, job: Callable, arguments: list[Dict] | list[Tuple] | list[NoneType] | None = None) -> Iterable[FutureResult]:
        return self.gather(jobs=[job] * len(arguments), arguments=arguments)

    def shutdown(self, cancel_futures: bool = True):
        self._thread_pool_executor.shutdown(wait=True, cancel_futures=cancel_futures)
        return self

    def wait_all(self) -> list[FutureResult]:
        _res = []
        for _ in self.next_result:
            _res.append(_)
        return _res

    @property
    def next_result(self) -> Iterable[FutureResult]:
        for f in as_completed(self._futures):
            try:
                res = f.result()
                yield FutureResult(_callable=res[0], arguments=res[1], returns=res[2],
                                   error=None, traceback=None)
            except Exception as __e:
                yield FutureResult(_callable=None, arguments=None, returns=None,
                                   error=__e, traceback=traceback.format_exc())
            finally:
                with self._futures_lock:
                    self._futures.remove(f)

    @property
    def thread_pool_executor(self) -> ThreadPoolExecutor:
        return self._thread_pool_executor

    @property
    def max_workers(self) -> int:
        return self._max_workers
