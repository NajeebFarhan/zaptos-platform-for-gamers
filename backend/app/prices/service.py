import asyncio
import re
import time
from typing import AsyncIterator

from app.config import EMPTY_PRICE_TTL, PRICE_TTL, STORE_TIMEOUT
from app.core.cache import cache
from app.core.http import http
from app.prices.catalog import DEAL_QUERIES
from app.prices.matcher import build_groups
from app.prices.models import Offer
from app.prices.stores import STORES, StoreBlocked

_inflight: dict[str, asyncio.Task] = {}


def query_key(query: str) -> str:
    return re.sub(r"\s+", " ", query.lower()).strip()


async def _scrape(store, query: str, key: str) -> list[dict]:
    offers = await asyncio.wait_for(store.search(http, query), STORE_TIMEOUT)
    data = [o.model_dump() for o in offers]
    cache.set(key, data, PRICE_TTL if data else EMPTY_PRICE_TTL)
    return data


def _task_done(task: asyncio.Task, key: str) -> None:
    _inflight.pop(key, None)
    if not task.cancelled():
        task.exception()  # mark as retrieved even if every waiter went away


async def fetch_store(store, query: str, refresh: bool = False) -> dict:
    """Offers from one store, served from cache when fresh, stale cache on failure."""
    key = f"offers:v1:{store.id}:{query_key(query)}"
    entry = cache.get_entry(key)
    if entry and entry[1] and not refresh:
        return {"store": store.id, "status": "ok", "cached": True, "stale": False, "ms": 0,
                "offers": entry[0], "count": len(entry[0]), "fetched_at": entry[2]}

    t0 = time.perf_counter()
    status, error = "ok", None
    task = _inflight.get(key)
    if task is None:
        task = asyncio.ensure_future(_scrape(store, query, key))
        _inflight[key] = task
        task.add_done_callback(lambda t, k=key: _task_done(t, k))
    try:
        offers = await asyncio.shield(task)
        fetched_at = time.time()
    except asyncio.TimeoutError:
        status, error = "timeout", f"no response in {STORE_TIMEOUT:.0f}s"
    except StoreBlocked as exc:
        status, error = "blocked", str(exc)
    except Exception as exc:  # parsing changes, network errors...
        status, error = "error", f"{type(exc).__name__}: {exc}"[:200]

    stale = False
    if status != "ok":
        if entry:
            offers, stale, fetched_at = entry[0], True, entry[2]
        else:
            offers, fetched_at = [], None
    return {"store": store.id, "status": status, "error": error, "cached": False, "stale": stale,
            "ms": int((time.perf_counter() - t0) * 1000), "offers": offers, "count": len(offers),
            "fetched_at": fetched_at}


def _summary(r: dict) -> dict:
    return {k: v for k, v in r.items() if k != "offers"}


def assemble(query: str, results: list[dict], took_ms: int) -> dict:
    offers = [Offer(**o) for r in results for o in r["offers"]]
    groups = build_groups(query, offers)
    return {
        "query": query,
        "groups": [g.model_dump() for g in groups],
        "stores": [_summary(r) for r in results],
        "total_offers": len(offers),
        "took_ms": took_ms,
        "generated_at": time.time(),
    }


async def search(query: str, refresh: bool = False) -> dict:
    t0 = time.perf_counter()
    results = await asyncio.gather(*(fetch_store(s, query, refresh) for s in STORES))
    return assemble(query, list(results), int((time.perf_counter() - t0) * 1000))


async def search_stream(query: str, refresh: bool = False) -> AsyncIterator[dict]:
    """Yields a progress event per store as each finishes, then the grouped result."""
    t0 = time.perf_counter()
    yield {"type": "start", "query": query, "stores": [s.id for s in STORES]}
    results: list[dict] = []
    for fut in asyncio.as_completed([fetch_store(s, query, refresh) for s in STORES]):
        r = await fut
        results.append(r)
        yield {"type": "store", **_summary(r)}
    order = {s.id: i for i, s in enumerate(STORES)}
    results.sort(key=lambda r: order[r["store"]])
    yield {"type": "result", **assemble(query, results, int((time.perf_counter() - t0) * 1000))}


async def _compute_deals() -> list[dict]:
    sem = asyncio.Semaphore(3)

    async def one(query: str, category: str) -> list[dict]:
        async with sem:
            res = await search(query)
        picks = []
        for g in res["groups"][:12]:
            if g["relevance"] < 75 or g["deal_score"] <= 0 or g["best"]["in_stock"] is False:
                continue
            picks.append({**g, "category": category, "source_query": query})
        return picks

    batches = await asyncio.gather(*(one(q, c) for q, c in DEAL_QUERIES), return_exceptions=True)
    seen, deals = set(), []
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for g in batch:
            if g["id"] not in seen:
                seen.add(g["id"])
                deals.append(g)
    deals.sort(key=lambda g: -g["deal_score"])
    return deals[:80]


async def deals(refresh: bool = False) -> dict:
    items = await cache.remember("deals:v4", PRICE_TTL, _compute_deals, refresh=refresh)
    entry = cache.get_entry("deals:v4")
    return {"deals": items, "generated_at": entry[2] if entry else time.time()}
