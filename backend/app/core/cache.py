"""Tiny SQLite-backed TTL cache.

- Survives restarts, so we don't re-scrape stores every time the server boots.
- `remember()` de-duplicates concurrent requests for the same key.
- Expired entries are kept so callers can fall back to stale data when a
  source is temporarily down (better a 40-minute-old price than nothing).
"""

import asyncio
import json
import sqlite3
import threading
import time
from typing import Any, Awaitable, Callable

from app.config import CACHE_DB


class Cache:
    def __init__(self, path):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires REAL NOT NULL, created REAL NOT NULL)"
        )
        self._conn.commit()
        self._lock = threading.Lock()
        self._inflight: dict[str, asyncio.Future] = {}

    def get_entry(self, key: str) -> tuple[Any, bool, float] | None:
        """Return (value, is_fresh, created_ts) or None."""
        with self._lock:
            row = self._conn.execute(
                "SELECT value, expires, created FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if not row:
            return None
        value, expires, created = row
        return json.loads(value), expires > time.time(), created

    def get(self, key: str) -> Any:
        entry = self.get_entry(key)
        if entry and entry[1]:
            return entry[0]
        return None

    def set(self, key: str, value: Any, ttl: float) -> None:
        now = time.time()
        payload = json.dumps(value, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires, created) VALUES (?, ?, ?, ?)",
                (key, payload, now + ttl, now),
            )
            self._conn.commit()

    def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM cache WHERE key LIKE ?", (prefix + "%",))
            self._conn.commit()

    async def remember(
        self,
        key: str,
        ttl: float,
        factory: Callable[[], Awaitable[Any]],
        *,
        refresh: bool = False,
        stale_on_error: bool = True,
    ) -> Any:
        if not refresh:
            hit = self.get(key)
            if hit is not None:
                return hit
        if key in self._inflight:
            return await asyncio.shield(self._inflight[key])

        fut = asyncio.get_running_loop().create_future()
        fut.add_done_callback(lambda f: f.cancelled() or f.exception())  # mark exception retrieved
        self._inflight[key] = fut
        try:
            value = await factory()
            self.set(key, value, ttl)
            fut.set_result(value)
            return value
        except Exception as exc:
            entry = self.get_entry(key) if stale_on_error else None
            if entry is not None:
                fut.set_result(entry[0])
                return entry[0]
            fut.set_exception(exc)
            raise
        finally:
            self._inflight.pop(key, None)


cache = Cache(CACHE_DB)
