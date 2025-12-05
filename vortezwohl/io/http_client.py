import logging
import random
import time
import requests

logger = logging.getLogger('vortezwohl.io')


class HttpClient:
    def __init__(self, max_retries: int = 3, timeout: float = 8., _delay_base: float = 2.):
        self._max_retries = max_retries
        self._timeout = timeout
        self._delay_base = _delay_base

    @staticmethod
    def sleep(retries: int, base: float = 2.):
        retries = max(retries, 1)
        delay = base ** retries
        time.sleep(delay + random.uniform(.1, delay))
        return

    def get(self, url: str, data: dict | None = None, headers: dict | None = None):
        r = None
        retry_count = 0
        for _ in range(self._max_retries + 1):
            if r is not None:
                retry_count += 1
                logger.warning(f'Failed to request {url} ({r.status_code}), retrying {retry_count}/{self._max_retries}')
                self.sleep(_, base=self._delay_base)
            r = requests.get(url=url, params=data, headers=headers, timeout=self._timeout)
            if r.status_code == 200:
                return r
        return r

    def post(self, url: str, data: dict, headers: dict | None = None):
        r = None
        retry_count = 0
        for _ in range(self._max_retries + 1):
            if r is not None:
                retry_count += 1
                logger.warning(f'Failed to request {url} ({r.status_code}), retrying {retry_count}/{self._max_retries}')
                self.sleep(_, base=self._delay_base)
            r = requests.post(url=url, json=data, headers=headers, timeout=self._timeout)
            if r.status_code == 200:
                return r
        return r
