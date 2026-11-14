"""Find guides on the open web and turn articles into a clean reader view.

- Discovery: DuckDuckGo's HTML endpoint (lite endpoint as fallback).
- Fresh guides: WordPress REST APIs of large esports/guide publishers.
- Reading: trafilatura extracts the main article body; we sanitise it.
"""

import asyncio
import ipaddress
import re
import socket
from datetime import datetime
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import trafilatura
from selectolax.lexbor import LexborHTMLParser

from app.config import ARTICLE_TTL, GUIDE_SEARCH_TTL
from app.core.cache import cache
from app.core.http import http
from app.core.text import clean
from app.guides.sanitize import sanitize_html

POPULAR = {
    "mobalytics.gg", "dotesports.com", "thespike.gg", "game8.co", "gamewith.net", "oneesports.gg", "sportskeeda.com",
    "dexerto.com", "pcgamesn.com", "gamerant.com", "ign.com", "keqingmains.com", "genshin.gg", "liquipedia.net",
    "esports.gg", "win.gg", "pcgamer.com", "rockpapershotgun.com", "eurogamer.net", "polygon.com", "thegamer.com",
    "tracker.gg", "blitz.gg", "prosettings.net", "afkgaming.com", "hltv.org", "totalcsgo.com", "csgoskins.gg",
    "mlbbhub.com", "ggrecon.com", "gamesradar.com", "fandom.com", "playvalorant.com", "hoyolab.com",
    "mobilelegends.com", "counter-strike.net", "theloadout.com", "insider-gaming.com", "esportstales.com",
}

WP_SOURCES = [
    {"name": "Dot Esports", "api": "https://dotesports.com/wp-json/wp/v2/posts"},
    {"name": "Mobalytics", "api": "https://mobalytics.gg/wp-json/wp/v2/posts"},
    {"name": "PCGamesN", "api": "https://www.pcgamesn.com/wp-json/wp/v2/posts"},
]
GUIDE_HINT = re.compile(r"\b(guide|how to|best|tier list|tips|build|builds|team|teams|settings|crosshair|"
                        r"lineups?|beginner|explained|every|all|ranked|meta|counter|combo)\b", re.I)


def domain_of(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _kind(url: str) -> str:
    d = domain_of(url)
    if "youtube.com" in d or "youtu.be" in d:
        return "video"
    if "reddit.com" in d or "steamcommunity.com" in d or "forum" in d:
        return "forum"
    if "fandom.com" in d or "liquipedia" in d or "wiki" in d:
        return "wiki"
    return "article"


def _is_popular(d: str) -> bool:
    return any(d == p or d.endswith("." + p) for p in POPULAR)


def _result(title: str, url: str, snippet: str) -> dict:
    d = domain_of(url)
    return {"title": clean(title), "url": url, "snippet": clean(snippet), "domain": d,
            "favicon": f"https://icons.duckduckgo.com/ip3/{d}.ico", "kind": _kind(url), "popular": _is_popular(d)}


def _unwrap_ddg(href: str) -> str | None:
    if not href:
        return None
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        return unquote(target) if target else None
    if "duckduckgo.com" in parsed.netloc:
        return None  # ads / internal links
    return href if parsed.scheme in ("http", "https") else None


async def _ddg_html(query: str) -> list[dict]:
    resp = await http.get("https://html.duckduckgo.com/html/", params={"q": query, "kl": "in-en"})
    if resp.status_code != 200:
        raise RuntimeError(f"ddg html {resp.status_code}")
    tree = LexborHTMLParser(resp.text)
    out = []
    for r in tree.css(".result"):
        if "result--ad" in (r.attributes.get("class") or ""):
            continue
        a = r.css_first("a.result__a")
        if a is None:
            continue
        url = _unwrap_ddg(a.attributes.get("href"))
        if not url:
            continue
        sn = r.css_first(".result__snippet")
        out.append(_result(a.text(), url, sn.text() if sn else ""))
    return out


async def _ddg_lite(query: str) -> list[dict]:
    resp = await http.get("https://lite.duckduckgo.com/lite/", params={"q": query, "kl": "in-en"})
    if resp.status_code != 200:
        raise RuntimeError(f"ddg lite {resp.status_code}")
    tree = LexborHTMLParser(resp.text)
    links = tree.css("a.result-link")
    snippets = tree.css("td.result-snippet")
    out = []
    for i, a in enumerate(links):
        url = _unwrap_ddg(a.attributes.get("href"))
        if url:
            out.append(_result(a.text(), url, snippets[i].text() if i < len(snippets) else ""))
    return out


async def web_search(query: str, limit: int = 12) -> list[dict]:
    async def load():
        results: list[dict] = []
        for engine in (_ddg_html, _ddg_lite):
            try:
                results = await engine(query)
            except Exception:
                results = []
            if results:
                break
        if not results:
            raise RuntimeError("search engines unavailable")
        seen, uniq = set(), []
        for r in results:
            key = r["url"].split("#")[0].rstrip("/")
            if key not in seen:
                seen.add(key)
                uniq.append(r)
        # popular guide sites first, keep engine order otherwise
        uniq.sort(key=lambda r: (not r["popular"], r["kind"] == "forum"))
        return uniq[:limit]

    return await cache.remember(f"web:search:{query.lower()}", GUIDE_SEARCH_TTL, load)


async def latest_guides(game: dict, limit: int = 12) -> list[dict]:
    async def from_source(src: dict) -> list[dict]:
        resp = await http.get(src["api"], params={
            "search": game["wp_search"], "per_page": 20,
            "_fields": "id,date,link,title,excerpt,yoast_head_json.og_image,jetpack_featured_media_url",
        }, headers={"Accept": "application/json"})
        if resp.status_code != 200:
            return []
        try:
            posts = resp.json()
        except ValueError:
            return []
        out = []
        needle = game["wp_search"].lower()
        for p in posts if isinstance(posts, list) else []:
            title = clean(re.sub(r"<[^>]+>", "", (p.get("title") or {}).get("rendered", "")))
            link = p.get("link") or ""
            if needle not in title.lower() and game["id"] not in link.lower():
                continue
            if "/news/" in link or not ("/guide" in link or GUIDE_HINT.search(title)):
                continue
            og = (p.get("yoast_head_json") or {}).get("og_image") or []
            image = (og[0].get("url") if og else None) or p.get("jetpack_featured_media_url")
            excerpt = clean(re.sub(r"<[^>]+>", "", (p.get("excerpt") or {}).get("rendered", "")))
            out.append({"title": title, "url": link, "image": image, "excerpt": excerpt[:220],
                        "date": p.get("date"), "source": src["name"], "domain": domain_of(link)})
        return out

    async def load():
        batches = await asyncio.gather(*(from_source(s) for s in WP_SOURCES), return_exceptions=True)
        items = [x for b in batches if isinstance(b, list) for x in b]
        items.sort(key=lambda x: x.get("date") or "", reverse=True)
        if len(items) < 4:
            # thin publisher coverage (e.g. MLBB): top up from a web search for guides
            try:
                found = await web_search(f"{game['search_name']} guide {datetime.now().year}")
            except Exception:
                found = []
            have = {i["url"] for i in items}
            for r in found:
                if r["kind"] == "article" and r["url"] not in have:
                    items.append({"title": r["title"], "url": r["url"], "image": None, "excerpt": r["snippet"][:220],
                                  "date": None, "source": r["domain"], "domain": r["domain"]})
        return items[:limit]

    return await cache.remember(f"web:latest:v2:{game['id']}", GUIDE_SEARCH_TTL, load)


# ------------------------------------------------------------------ reader

class UnsafeURL(ValueError):
    pass


async def _assert_public(url: str) -> None:
    """Block SSRF: only public http(s) hosts, never localhost/private ranges."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UnsafeURL("only http(s) URLs are allowed")
    if parsed.port not in (None, 80, 443):
        raise UnsafeURL("non-standard ports are not allowed")
    try:
        infos = await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeURL("host does not resolve") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise UnsafeURL("host resolves to a private address")


async def _fetch_public(url: str):
    for _ in range(4):  # follow redirects manually, validating every hop
        await _assert_public(url)
        resp = await http.get(url, timeout=20, allow_redirects=False)
        if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("location"):
            url = urljoin(url, resp.headers["location"])
            continue
        return url, resp
    raise UnsafeURL("too many redirects")


def _extract(html: str, url: str) -> dict:
    meta = trafilatura.extract_metadata(html, default_url=url)
    body = trafilatura.extract(html, url=url, output_format="html", include_images=True, include_links=True,
                               include_tables=True, include_comments=False, favor_recall=True)
    return {
        "title": getattr(meta, "title", None),
        "author": getattr(meta, "author", None),
        "date": getattr(meta, "date", None),
        "sitename": getattr(meta, "sitename", None),
        "image": getattr(meta, "image", None),
        "description": getattr(meta, "description", None),
        "body": body,
    }


async def read_article(url: str) -> dict:
    async def load():
        final_url, resp = await _fetch_public(url)
        if resp.status_code >= 400:
            raise RuntimeError(f"source returned HTTP {resp.status_code}")
        ctype = resp.headers.get("content-type", "")
        if "html" not in ctype:
            raise RuntimeError("source is not an HTML page")
        html = resp.text[:4_000_000]
        data = await asyncio.to_thread(_extract, html, final_url)
        if not data["body"]:
            raise RuntimeError("could not extract readable content (the page may need JavaScript)")
        body = sanitize_html(data["body"], base_url=final_url)
        # trafilatura wraps everything in <html><body>…; unwrapped by the sanitiser. Drop the repeated title.
        text = re.sub(r"<[^>]+>", " ", body)
        words = len(text.split())
        date = data["date"]
        try:
            date = datetime.fromisoformat(date).date().isoformat() if date else None
        except ValueError:
            pass
        return {
            "url": final_url, "domain": domain_of(final_url), "title": clean(data["title"]) or final_url,
            "author": clean(data["author"]) or None, "date": date, "sitename": clean(data["sitename"]) or domain_of(final_url),
            "image": data["image"], "description": clean(data["description"]) or None,
            "html": body, "words": words, "minutes": max(1, round(words / 230)),
        }

    return await cache.remember(f"web:article:v1:{url}", ARTICLE_TTL, load)
