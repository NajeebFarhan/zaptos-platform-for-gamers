"""Contract checks against the REAL stores. Skipped by default; run with:  pytest -m live

The fixtures in test_store_parsers.py prove the parsers work on a page we saved. These prove
the stores still *look* like that page. When one fails, the store changed its markup or API:
save a fresh response over the matching fixture, then fix the parser until both pass.

A bot wall (HTTP 403/429, captcha) skips instead of failing: it says nothing about the parser.
"""

import pytest

from app.core.http import HttpClient
from app.prices.stores import STORES, StoreBlocked

pytestmark = pytest.mark.live


@pytest.fixture
async def http():
    client = HttpClient()
    await client.start()
    yield client
    await client.close()


@pytest.mark.parametrize("store", STORES, ids=lambda s: s.id)
async def test_store_still_returns_well_formed_offers(store, http):
    try:
        offers = await store.search(http, "rtx 5060")
    except StoreBlocked as exc:
        pytest.skip(f"{store.id} is blocking us right now: {exc}")

    assert offers, f"{store.id} returned nothing for a very common query: its markup probably changed"
    for o in offers:
        assert o.store == store.id
        assert o.title.strip(), o
        assert o.price > 0, o
        assert o.url.startswith("http"), o
        assert o.mrp is None or o.mrp > o.price, o
        assert o.rating is None or 0 < o.rating <= 5, o
    priced = sum(1 for o in offers if o.price)
    assert priced == len(offers)
    # a healthy parse fills in most optional fields too; a sudden drop means a selector broke
    with_image = sum(1 for o in offers if o.image)
    assert with_image >= len(offers) // 2, f"{store.id}: only {with_image}/{len(offers)} offers have an image"
