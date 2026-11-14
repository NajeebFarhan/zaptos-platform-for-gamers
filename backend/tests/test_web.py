"""Guide discovery helpers and the article reader's SSRF protection (no real DNS or network)."""

from types import SimpleNamespace

import pytest

from app.guides import web

HOSTS = {
    "public.example": ["93.184.216.34"],
    "internal.example": ["10.0.0.5"],
    "metadata.example": ["169.254.169.254"],
    "loopback.example": ["127.0.0.1"],
    "v6loopback.example": ["::1"],
    "mixed.example": ["93.184.216.34", "192.168.1.10"],  # DNS-rebinding style: one public, one private record
}


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch):
    def getaddrinfo(host, port, *a, **kw):
        if host not in HOSTS:
            import socket
            raise socket.gaierror("unknown host")
        return [(0, 0, 0, "", (ip, 0)) for ip in HOSTS[host]]
    monkeypatch.setattr(web.socket, "getaddrinfo", getaddrinfo)


class TestAssertPublic:
    @pytest.mark.parametrize("url", ["http://public.example/a", "https://public.example:443/a", "http://public.example:80/"])
    async def test_allows_public_hosts(self, url):
        await web._assert_public(url)

    @pytest.mark.parametrize("url, why", [
        ("http://internal.example/", "private"),
        ("http://metadata.example/latest/meta-data/", "private"),
        ("http://loopback.example/", "private"),
        ("http://v6loopback.example/", "private"),
        ("http://mixed.example/", "private"),
        ("http://unknown.example/", "resolve"),
        ("http://public.example:8080/", "port"),
        ("http://public.example:22/", "port"),
        ("file:///etc/passwd", "http"),
        ("ftp://public.example/", "http"),
        ("javascript:alert(1)", "http"),
        ("http:///nohost", "http"),
    ])
    async def test_blocks_everything_else(self, url, why):
        with pytest.raises(web.UnsafeURL, match=why):
            await web._assert_public(url)


class FakeHttp:
    def __init__(self, routes):
        self.routes, self.seen = routes, []

    async def get(self, url, **kw):
        assert kw.get("allow_redirects") is False, "redirects must be followed manually so every hop is checked"
        self.seen.append(url)
        status, headers, text = self.routes[url]
        return SimpleNamespace(status_code=status, headers=headers, text=text)


class TestFetchPublic:
    async def test_returns_the_final_url_and_response(self, monkeypatch):
        monkeypatch.setattr(web, "http", FakeHttp({"http://public.example/a": (200, {}, "hi")}))
        url, resp = await web._fetch_public("http://public.example/a")
        assert (url, resp.text) == ("http://public.example/a", "hi")

    async def test_follows_redirects_to_public_hosts(self, monkeypatch):
        monkeypatch.setattr(web, "http", FakeHttp({
            "http://public.example/a": (301, {"location": "/b"}, ""),
            "http://public.example/b": (200, {}, "done"),
        }))
        url, resp = await web._fetch_public("http://public.example/a")
        assert url == "http://public.example/b" and resp.text == "done"

    async def test_redirect_to_an_internal_host_is_blocked_before_it_is_requested(self, monkeypatch):
        fake = FakeHttp({"http://public.example/a": (302, {"location": "http://metadata.example/latest"}, "")})
        monkeypatch.setattr(web, "http", fake)
        with pytest.raises(web.UnsafeURL):
            await web._fetch_public("http://public.example/a")
        assert fake.seen == ["http://public.example/a"]

    async def test_redirect_loops_are_cut_off(self, monkeypatch):
        monkeypatch.setattr(web, "http", FakeHttp({"http://public.example/a": (302, {"location": "/a"}, "")}))
        with pytest.raises(web.UnsafeURL, match="redirects"):
            await web._fetch_public("http://public.example/a")


ARTICLE = ("<html><head><title>Jett Guide</title></head><body><article><h1>Jett Guide</h1>"
           + "".join(f"<p>Paragraph {i}: use Tailwind to reposition quickly, then dash out of trouble when the "
                     f"round opens up, and keep your Updraft for the high ground angles that matter.</p>" for i in range(8))
           + "<script>steal()</script></article></body></html>")


class TestReadArticle:
    def serve(self, monkeypatch, status=200, ctype="text/html; charset=utf-8", body=ARTICLE):
        monkeypatch.setattr(web, "http", FakeHttp({"http://public.example/a": (status, {"content-type": ctype}, body)}))

    async def test_extracts_a_clean_reader_view(self, monkeypatch):
        self.serve(monkeypatch)
        art = await web.read_article("http://public.example/a")
        assert art["domain"] == "public.example"
        assert "Tailwind" in art["html"] and "steal" not in art["html"]
        assert art["words"] > 50 and art["minutes"] >= 1

    @pytest.mark.parametrize("status, ctype, body, msg", [
        (404, "text/html", "x", "HTTP 404"),
        (200, "application/pdf", "x", "not an HTML"),
        (200, "text/html", "<html><body><script>renderApp()</script></body></html>", "readable content"),  # JS-only page
    ])
    async def test_unreadable_sources_fail_with_a_reason(self, monkeypatch, status, ctype, body, msg):
        self.serve(monkeypatch, status, ctype, body)
        with pytest.raises(RuntimeError, match=msg):
            await web.read_article("http://public.example/a")


class TestHelpers:
    @pytest.mark.parametrize("href, expected", [
        ("//duckduckgo.com/l/?uddg=https%3A%2F%2Fgame8.co%2Fguide&rut=abc", "https://game8.co/guide"),
        ("https://duckduckgo.com/y.js?ad=1", None),  # ads / internal
        ("https://example.com/page", "https://example.com/page"),
        ("javascript:alert(1)", None),
        ("", None),
        (None, None),
    ])
    def test_unwrap_ddg(self, href, expected):
        assert web._unwrap_ddg(href) == expected

    @pytest.mark.parametrize("url, kind", [
        ("https://www.youtube.com/watch?v=1", "video"),
        ("https://youtu.be/1", "video"),
        ("https://www.reddit.com/r/valheim", "forum"),
        ("https://valorant.fandom.com/wiki/Jett", "wiki"),
        ("https://game8.co/games/genshin", "article"),
    ])
    def test_kind(self, url, kind):
        assert web._kind(url) == kind

    def test_popular_sites_match_on_the_domain_not_a_substring(self):
        assert web._is_popular("game8.co") and web._is_popular("valorant.fandom.com")
        assert not web._is_popular("evilgame8.co") and not web._is_popular("game8.co.evil.com")

    def test_domain_of_strips_www(self):
        assert web.domain_of("https://WWW.Example.com/x") == "example.com"
