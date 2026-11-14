"""HTTP layer: routing, validation, the SSE stream and CORS. Stores are fakes, nothing touches the network."""

import json

import pytest

from tests.conftest import FakeStore, make_offer

GPU = "MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card"
FRONTEND = "https://zaptos-platform-for-gamers.najeebmazumdar.workers.dev"


@pytest.fixture
def store(stores):
    (s,) = stores(FakeStore("alpha", [make_offer("alpha", GPU, 59999)]))
    return s


def sse_events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in filter(None, text.split("\n\n")):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def test_health(client):
    assert client.get("/api/health").json() == {"ok": True}


class TestMeta:
    def test_lists_stores_categories_and_currency(self, client, store):
        body = client.get("/api/prices/meta").json()
        assert [s["id"] for s in body["stores"]] == ["alpha"]
        assert body["currency"] == "INR"
        assert {"gpu", "consoles"} <= {c["id"] for c in body["categories"]}
        assert body["trending"]


class TestSearch:
    def test_returns_grouped_products(self, client, store):
        res = client.get("/api/prices/search", params={"q": "rtx 5060"})
        assert res.status_code == 200
        body = res.json()
        assert body["query"] == "rtx 5060"
        assert body["groups"][0]["best"]["price"] == 59999
        assert body["stores"][0]["status"] == "ok"

    def test_query_whitespace_is_normalised(self, client, store):
        client.get("/api/prices/search", params={"q": "  rtx    5060 "})
        assert store.queries == ["rtx 5060"]

    @pytest.mark.parametrize("q, status", [("a", 400), ("  ", 400), ("x" * 121, 400)])
    def test_rejects_bad_queries_before_scraping(self, client, store, q, status):
        assert client.get("/api/prices/search", params={"q": q}).status_code == status
        assert store.calls == 0

    def test_missing_query_is_a_validation_error(self, client, store):
        assert client.get("/api/prices/search").status_code == 422

    def test_refresh_flag_reaches_the_service(self, client, store):
        client.get("/api/prices/search", params={"q": "rtx 5060"})
        client.get("/api/prices/search", params={"q": "rtx 5060", "refresh": "true"})
        assert store.calls == 2


class TestStream:
    def test_is_server_sent_events_ending_with_the_result(self, client, store):
        res = client.get("/api/prices/search/stream", params={"q": "rtx 5060"})
        assert res.headers["content-type"].startswith("text/event-stream")
        assert res.headers["cache-control"] == "no-cache"
        events = sse_events(res.text)
        assert [name for name, _ in events] == ["start", "store", "result"]
        assert events[-1][1]["groups"][0]["best"]["price"] == 59999

    def test_validates_the_query_too(self, client, store):
        assert client.get("/api/prices/search/stream", params={"q": "a"}).status_code == 400


class TestTrack:
    def body(self, **item):
        return {"items": [{"key": "k", "title": GPU, "query": "rtx 5060", **item}]}

    def test_returns_latest_prices_for_saved_items(self, client, store):
        res = client.post("/api/prices/track", json=self.body())
        assert res.status_code == 200
        assert res.json()["results"]["k"]["status"] == "ok"

    def test_query_falls_back_to_the_title_and_long_ones_are_cut_at_a_word(self, client, store):
        long_title = " ".join(["Graphics"] * 40)  # 359 chars
        client.post("/api/prices/track", json={"items": [{"key": "k", "title": long_title}]})
        (query,) = store.queries
        assert len(query) <= 120 and query.startswith("Graphics") and not query.endswith(" ")

    @pytest.mark.parametrize("bad", [
        {"items": [{"key": "k", "title": "x"}]},  # title too short
        {"items": [{"key": "k" * 65, "title": GPU}]},  # key too long
        {"items": [{"key": "k", "title": GPU, "urls": ["u"] * 21}]},  # too many urls
        {"items": [{"key": "k", "title": GPU}] * 61},  # too many items
        {"nope": []},
    ])
    def test_rejects_invalid_bodies(self, client, store, bad):
        assert client.post("/api/prices/track", json=bad).status_code == 422
        assert store.calls == 0


def test_deals(client, store):
    body = client.get("/api/prices/deals").json()
    assert set(body) == {"deals", "generated_at"}


class TestGuides:
    def test_lists_the_four_supported_games(self, client):
        games = client.get("/api/guides/games").json()["games"]
        assert {g["id"] for g in games} == {"valorant", "genshin-impact", "mobile-legends", "csgo"}

    def test_unknown_game_is_404(self, client):
        assert client.get("/api/guides/not-a-game").status_code == 404
        assert client.get("/api/guides/not-a-game/latest").status_code == 404

    @pytest.mark.parametrize("url", [
        "http://127.0.0.1/admin",
        "http://localhost:8000/api/health",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/x",
        "http://example.com:8080/",
    ])
    def test_article_reader_refuses_internal_and_non_http_urls(self, client, url):
        res = client.get("/api/guides/article", params={"url": url})
        assert res.status_code == 400, res.text


class TestCors:
    def preflight(self, client, origin):
        return client.options("/api/prices/search", headers={
            "Origin": origin, "Access-Control-Request-Method": "GET"})

    @pytest.mark.parametrize("origin", [
        FRONTEND,
        "https://3f9a1c2b-zaptos-platform-for-gamers.najeebmazumdar.workers.dev",  # Cloudflare preview deploy
        "http://localhost:5173",
    ])
    def test_allows_the_frontend(self, client, origin):
        assert self.preflight(client, origin).headers.get("access-control-allow-origin") == origin

    @pytest.mark.parametrize("origin", [
        "https://evil.example.com",
        FRONTEND + ".evil.com",
        "https://zaptos-platform-for-gamers.najeebmazumdar.workers.dev.evil.com",
        "http://zaptos-platform-for-gamers.najeebmazumdar.workers.dev",  # wrong scheme
        "https://other-project.najeebmazumdar.workers.dev",
    ])
    def test_blocks_everyone_else(self, client, origin):
        assert "access-control-allow-origin" not in self.preflight(client, origin).headers

    def test_simple_requests_get_the_header_too(self, client):
        res = client.get("/api/health", headers={"Origin": FRONTEND})
        assert res.headers["access-control-allow-origin"] == FRONTEND
