"""Shared test setup.

The app builds its cache and HTTP client at import time, so the environment has to be
configured *before* anything from `app` is imported: the cache goes to a throwaway file
(tests never touch backend/data) and the startup warm-up scrape is switched off.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="zaptos-tests-")
os.environ["CACHE_DB"] = str(Path(_TMP) / "cache.sqlite3")
os.environ["WARM_DEALS_ON_STARTUP"] = "0"
os.environ.setdefault("STORE_TIMEOUT", "1")  # keep timeout tests fast
for _var in ("CORS_ORIGINS", "CORS_ORIGIN_REGEX"):  # the CORS tests assert the defaults, not your shell
    os.environ.pop(_var, None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.cache import cache  # noqa: E402
from app.prices import service  # noqa: E402
from app.prices.models import Offer  # noqa: E402
from app.prices.stores.base import Store, StoreBlocked  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_offer(store: str = "fake", title: str = "MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card",
               price: float = 59999, **kw) -> Offer:
    return Offer(store=store, title=title, url=kw.pop("url", f"https://{store}.example/{abs(hash(title))}"),
                 price=price, **kw)


class FakeStore(Store):
    """A store whose behaviour the test scripts: offers, an exception to raise, or a delay."""

    def __init__(self, id: str = "fake", offers: list[Offer] | None = None, *, kind: str = "PC Specialist",
                 error: Exception | None = None, delay: float = 0):
        self.id, self.name, self.kind = id, id.title(), kind
        self.home, self.color = f"https://{id}.example", "#000000"
        self.offers, self.error, self.delay = offers or [], error, delay
        self.queries: list[str] = []

    @property
    def calls(self) -> int:
        return len(self.queries)

    async def search(self, http, query, limit=24):
        self.queries.append(query)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return list(self.offers)


@pytest.fixture(autouse=True)
def _clean_state():
    """Every test starts with an empty cache and no in-flight scrapes."""
    cache._conn.execute("DELETE FROM cache")
    cache._conn.commit()
    cache._inflight.clear()
    service._inflight.clear()
    yield


@pytest.fixture
def stores(monkeypatch):
    """Replace the real stores with fakes: `stores(FakeStore(...), FakeStore(...))`."""
    def install(*fakes: Store) -> list[Store]:
        monkeypatch.setattr(service, "STORES", list(fakes))
        monkeypatch.setattr("app.api.prices.STORES", list(fakes))
        return list(fakes)
    return install


@pytest.fixture
def client(monkeypatch):
    """The real app over an in-process client, with no real HTTP session: an accidental
    outbound request fails the test instead of reaching a live site."""
    from app.core.http import http
    from app.main import app

    async def noop():
        return None

    monkeypatch.setattr(http, "start", noop)
    monkeypatch.setattr(http, "close", noop)
    with TestClient(app) as c:
        yield c


__all__ = ["FakeStore", "StoreBlocked", "fixture_text", "make_offer"]
