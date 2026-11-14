"""Shared async HTTP client.

Uses curl_cffi so requests carry a real browser TLS fingerprint (many Indian
retailers sit behind bot filters that reject plain Python clients). Requests
are throttled per host so we stay polite: limited concurrency plus a minimum
gap between consecutive requests to the same site.
"""

import asyncio
import time
from collections import defaultdict
from urllib.parse import urlparse

from curl_cffi.requests import AsyncSession


class HttpClient:
    def __init__(self, per_host_concurrency: int = 2, min_interval: float = 0.4):
        self._session: AsyncSession | None = None
        self._per_host_concurrency = per_host_concurrency
        self._sems: dict[str, asyncio.Semaphore] = {}
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._last: dict[str, float] = defaultdict(float)
        self.min_interval = min_interval

    async def start(self) -> None:
        if self._session is None:
            self._session = AsyncSession(
                impersonate="chrome",
                timeout=20,
                headers={"Accept-Language": "en-IN,en;q=0.9"},
            )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _sem(self, host: str) -> asyncio.Semaphore:
        if host not in self._sems:
            self._sems[host] = asyncio.Semaphore(self._per_host_concurrency)
        return self._sems[host]

    async def _throttle(self, host: str) -> None:
        async with self._locks[host]:
            wait = self._last[host] + self.min_interval - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self._last[host] = time.monotonic()

    async def get(self, url: str, *, params=None, headers=None, timeout: float = 20, retries: int = 1,
                  allow_redirects: bool = True):
        if self._session is None:
            await self.start()
        host = urlparse(url).netloc
        async with self._sem(host):
            last_exc: Exception | None = None
            for attempt in range(retries + 1):
                await self._throttle(host)
                try:
                    resp = await self._session.get(
                        url, params=params, headers=headers, timeout=timeout, allow_redirects=allow_redirects
                    )
                except Exception as exc:  # network error, TLS error, timeout...
                    last_exc = exc
                    if attempt < retries:
                        await asyncio.sleep(0.8 * (attempt + 1))
                        continue
                    raise
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                return resp
            raise last_exc or RuntimeError("request failed")


http = HttpClient()
