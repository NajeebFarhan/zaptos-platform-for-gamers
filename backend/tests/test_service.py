"""The price service with scripted fake stores: caching, failures, scoping, streaming, wishlist tracking."""

import asyncio

import pytest

from app.core.cache import cache
from app.prices import service
from app.prices.stores.base import StoreBlocked
from tests.conftest import FakeStore, make_offer

GPU_A = "MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card"
GPU_B = "MSI GeForce RTX 5060 8G Ventus 2X OC Graphic Card"
PHONE = "Samsung Galaxy S25 5G AI Smartphone (Titanium Silverblue, 12GB RAM, 256GB Storage), 200MP Camera"


def two_stores():
    return (FakeStore("alpha", [make_offer("alpha", GPU_A, 60000, in_stock=True)]),
            FakeStore("beta", [make_offer("beta", GPU_B, 59000, in_stock=True)]))


def by_id(res):
    return {s["store"]: s for s in res["stores"]}


class TestSearch:
    async def test_groups_the_same_product_across_stores_and_picks_the_cheapest(self, stores):
        stores(*two_stores())
        res = await service.search("rtx 5060")
        assert res["total_offers"] == 2
        (group,) = res["groups"]
        assert group["store_count"] == 2
        assert group["best"]["store"] == "beta"
        assert group["savings"] == 1000

    async def test_second_search_is_served_from_cache(self, stores):
        alpha, beta = stores(*two_stores())
        await service.search("rtx 5060")
        res = await service.search("  RTX   5060 ")  # same query once normalised
        assert (alpha.calls, beta.calls) == (1, 1)
        assert by_id(res)["alpha"]["cached"] is True

    async def test_refresh_bypasses_the_cache(self, stores):
        (alpha, _) = stores(*two_stores())
        await service.search("rtx 5060")
        await service.search("rtx 5060", refresh=True)
        assert alpha.calls == 2

    async def test_concurrent_identical_searches_scrape_each_store_once(self, stores):
        alpha = FakeStore("alpha", [make_offer("alpha", GPU_A, 60000)], delay=0.05)
        stores(alpha)
        await asyncio.gather(*(service.fetch_store(alpha, "rtx 5060") for _ in range(5)))
        assert alpha.calls == 1


class TestFailures:
    @pytest.mark.parametrize("error, status", [
        (StoreBlocked("HTTP 403"), "blocked"),
        (RuntimeError("markup changed"), "error"),
    ])
    async def test_one_failing_store_never_breaks_the_search(self, stores, error, status):
        stores(FakeStore("good", [make_offer("good", GPU_A, 60000)]), FakeStore("bad", error=error))
        res = await service.search("rtx 5060")
        assert by_id(res)["bad"]["status"] == status
        assert by_id(res)["bad"]["count"] == 0
        assert by_id(res)["good"]["status"] == "ok"
        assert len(res["groups"]) == 1

    async def test_error_details_are_reported(self, stores):
        stores(FakeStore("bad", error=RuntimeError("markup changed")))
        assert "RuntimeError: markup changed" in by_id(await service.search("rtx 5060"))["bad"]["error"]

    async def test_slow_store_times_out(self, stores, monkeypatch):
        monkeypatch.setattr(service, "STORE_TIMEOUT", 0.05)
        stores(FakeStore("slow", [make_offer("slow", GPU_A, 1000)], delay=1))
        res = await service.search("rtx 5060")
        assert by_id(res)["slow"]["status"] == "timeout"

    async def test_failure_serves_stale_prices_instead_of_nothing(self, stores):
        (alpha,) = stores(FakeStore("alpha", [make_offer("alpha", GPU_A, 60000)]))
        await service.search("rtx 5060")
        alpha.error = RuntimeError("store is down")
        res = await service.search("rtx 5060", refresh=True)
        summary = by_id(res)["alpha"]
        assert (summary["status"], summary["stale"], summary["count"]) == ("error", True, 1)
        assert res["groups"][0]["best"]["price"] == 60000

    async def test_failures_are_not_cached_as_results(self, stores):
        (alpha,) = stores(FakeStore("alpha", error=RuntimeError("down")))
        await service.search("rtx 5060")
        alpha.error, alpha.offers = None, [make_offer("alpha", GPU_A, 60000)]
        res = await service.search("rtx 5060")
        assert by_id(res)["alpha"]["status"] == "ok" and res["total_offers"] == 1


class TestScope:
    """Marketplaces sell everything; PC-specialist stores don't need filtering."""

    async def test_only_marketplaces_are_filtered_and_only_by_scope(self, stores):
        offers = lambda sid: [make_offer(sid, GPU_A, 60000), make_offer(sid, PHONE, 80000)]  # noqa: E731
        stores(FakeStore("market", offers("market"), kind="Marketplace"),
               FakeStore("specialist", offers("specialist")))
        res = await service.search("samsung")
        assert by_id(res)["market"]["count"] == 1
        assert by_id(res)["specialist"]["count"] == 2

    async def test_scope_also_applies_to_results_cached_earlier(self, stores):
        stores(FakeStore("market", [make_offer("market", PHONE, 80000)], kind="Marketplace"))
        key = f"offers:v1:market:{service.query_key('samsung')}"
        cache.set(key, [make_offer("market", PHONE, 80000).model_dump()], ttl=600)  # cached before the filter existed
        res = await service.search("samsung")
        assert (by_id(res)["market"]["cached"], by_id(res)["market"]["count"]) == (True, 0)


class TestStream:
    async def test_emits_start_then_one_event_per_store_then_the_result(self, stores):
        stores(*two_stores())
        events = [e async for e in service.search_stream("rtx 5060")]
        assert [e["type"] for e in events] == ["start", "store", "store", "result"]
        assert events[0]["stores"] == ["alpha", "beta"]
        assert {e["store"] for e in events[1:3]} == {"alpha", "beta"}
        assert "offers" not in events[1]  # progress events stay small
        assert events[-1]["total_offers"] == 2
        assert [s["store"] for s in events[-1]["stores"]] == ["alpha", "beta"]  # result keeps store order

    async def test_fast_stores_are_reported_before_slow_ones(self, stores):
        stores(FakeStore("slow", [make_offer("slow", GPU_A, 1)], delay=0.1), FakeStore("fast", [make_offer("fast", GPU_A, 1)]))
        events = [e async for e in service.search_stream("rtx 5060")]
        assert [e["store"] for e in events if e["type"] == "store"] == ["fast", "slow"]


class TestTrack:
    def item(self, key="k1", title=GPU_A, query="rtx 5060", urls=()):
        return {"key": key, "query": query, "title": title, "urls": list(urls)}

    async def test_finds_the_saved_product_again(self, stores):
        stores(*two_stores())
        res = await service.track([self.item()])
        assert res["results"]["k1"]["status"] == "ok"
        assert res["results"]["k1"]["group"]["best"]["price"] == 59000

    async def test_reports_missing_when_the_product_is_gone_or_a_different_model(self, stores):
        stores(*two_stores())
        res = await service.track([self.item(title="MSI RTX 5070 Ventus 2X OC 12GB")])
        assert res["results"]["k1"] == {"status": "missing", "group": None}

    async def test_items_sharing_a_query_share_one_search(self, stores):
        (alpha, _) = stores(*two_stores())
        await service.track([self.item("a"), self.item("b", title=GPU_B)])
        assert alpha.calls == 1

    async def test_matches_by_listing_url_even_if_the_title_changed(self, stores):
        alpha, _ = stores(*two_stores())
        url = alpha.offers[0].url
        res = await service.track([self.item(title="completely renamed", urls=[url])])
        assert res["results"]["k1"]["status"] == "ok"


class TestDeals:
    async def test_scans_every_deal_query_once_and_caches(self, stores):
        (alpha,) = stores(FakeStore("alpha", [make_offer("alpha", GPU_A, 60000, mrp=80000)]))
        first = await service.deals()
        calls = alpha.calls
        assert calls == len(service.DEAL_QUERIES)
        await service.deals()
        assert alpha.calls == calls
        assert set(first) == {"deals", "generated_at"}

    async def test_a_dead_store_gives_an_empty_page_not_an_exception(self, stores):
        stores(FakeStore("alpha", error=RuntimeError("down")))
        assert (await service.deals())["deals"] == []
