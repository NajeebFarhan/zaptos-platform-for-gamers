import asyncio

import pytest

from app.core.cache import Cache


@pytest.fixture
def db(tmp_path):
    return Cache(tmp_path / "c.sqlite3")


class TestStorage:
    def test_round_trip_keeps_unicode(self, db):
        db.set("k", {"title": "₹ 59,999", "n": [1, 2]}, ttl=60)
        assert db.get("k") == {"title": "₹ 59,999", "n": [1, 2]}

    def test_missing_key(self, db):
        assert db.get("nope") is None
        assert db.get_entry("nope") is None

    def test_expired_entry_is_hidden_from_get_but_kept_for_stale_fallback(self, db):
        db.set("k", "old", ttl=-1)
        assert db.get("k") is None
        value, fresh, created = db.get_entry("k")
        assert (value, fresh) == ("old", False)
        assert created > 0

    def test_set_replaces(self, db):
        db.set("k", 1, 60)
        db.set("k", 2, 60)
        assert db.get("k") == 2

    def test_delete_prefix_only_removes_matching_keys(self, db):
        for k in ("web:a", "web:b", "offers:x"):
            db.set(k, 1, 60)
        db.delete_prefix("web:")
        assert (db.get("web:a"), db.get("web:b"), db.get("offers:x")) == (None, None, 1)

    def test_survives_a_restart(self, tmp_path):
        Cache(tmp_path / "c.sqlite3").set("k", "kept", 60)
        assert Cache(tmp_path / "c.sqlite3").get("k") == "kept"


class TestRemember:
    async def test_computes_once_then_serves_from_cache(self, db):
        calls = 0

        async def factory():
            nonlocal calls
            calls += 1
            return "v"

        assert await db.remember("k", 60, factory) == "v"
        assert await db.remember("k", 60, factory) == "v"
        assert calls == 1

    async def test_refresh_recomputes(self, db):
        values = iter(["first", "second"])

        async def factory():
            return next(values)

        assert await db.remember("k", 60, factory) == "first"
        assert await db.remember("k", 60, factory, refresh=True) == "second"
        assert db.get("k") == "second"

    async def test_concurrent_callers_share_one_computation(self, db):
        calls = 0

        async def factory():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.05)
            return "v"

        results = await asyncio.gather(*(db.remember("k", 60, factory) for _ in range(8)))
        assert results == ["v"] * 8
        assert calls == 1

    async def test_failure_falls_back_to_stale_value(self, db):
        db.set("k", "stale", ttl=-1)

        async def boom():
            raise RuntimeError("source down")

        assert await db.remember("k", 60, boom) == "stale"

    async def test_failure_without_stale_value_propagates_and_is_not_cached(self, db):
        attempts = 0

        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("down")
            return "ok"

        with pytest.raises(RuntimeError):
            await db.remember("k", 60, flaky)
        assert await db.remember("k", 60, flaky) == "ok"  # the failure didn't poison the key

    async def test_stale_fallback_can_be_disabled(self, db):
        db.set("k", "stale", ttl=-1)

        async def boom():
            raise RuntimeError("down")

        with pytest.raises(RuntimeError):
            await db.remember("k", 60, boom, stale_on_error=False)
