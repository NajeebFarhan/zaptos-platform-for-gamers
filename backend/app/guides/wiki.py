"""Fandom wiki content via the MediaWiki API (the sanctioned way to read wikis).

Content is CC BY-SA; every page we return carries attribution + source link.
"""

import hashlib
import re
from urllib.parse import quote, unquote

from selectolax.lexbor import LexborHTMLParser

from app.config import WIKI_TTL
from app.core.cache import cache
from app.core.http import http
from app.core.text import clean
from app.guides.sanitize import sanitize_html

SKIP_SECTIONS = {
    "gallery", "references", "navigation", "update history", "patch history", "change history", "cosmetics",
    "agent cosmetics", "other cosmetics", "buddies", "player cards", "sprays", "weapon skins", "quotes",
    "voice-overs", "voice lines", "videos", "see also", "external links", "audio", "skins", "media",
    "other languages", "change log", "changelog", "version history", "official", "notes", "sources",
    "skin gallery", "hero cosmetics", "titles", "player titles", "flex",
}
MAX_SECTIONS = 14
MAX_SECTION_CHARS = 60_000


async def api(host: str, params: dict) -> dict:
    # No "Accept: application/json" here: Fandom's edge 403s a Chrome fingerprint sending it.
    resp = await http.get(f"https://{host}/api.php", params={"format": "json", "formatversion": 2, **params})
    resp.raise_for_status()
    return resp.json()


async def category_members(host: str, category: str) -> list[str]:
    async def load():
        titles: list[str] = []
        params = {"action": "query", "list": "categorymembers", "cmtitle": f"Category:{category}",
                  "cmlimit": 500, "cmnamespace": 0}
        for _ in range(5):
            data = await api(host, params)
            titles += [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
            cont = data.get("continue", {}).get("cmcontinue")
            if not cont:
                break
            params["cmcontinue"] = cont
        return titles

    return await cache.remember(f"wiki:cat:{host}:{category}", WIKI_TTL, load)


async def page_images(host: str, titles: list[str], size: int = 320) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]

        async def load(chunk=chunk):
            data = await api(host, {"action": "query", "titles": "|".join(chunk), "prop": "pageimages",
                                    "pithumbsize": size, "pilicense": "any", "redirects": 1})
            q = data.get("query", {})
            back = {r["to"]: r["from"] for r in q.get("redirects", [])}
            res = {}
            for p in q.get("pages", []):
                src = (p.get("thumbnail") or {}).get("source")
                if src:
                    res[back.get(p["title"], p["title"])] = src
            return res

        key = f"wiki:img:{host}:{size}:{hashlib.md5('|'.join(chunk).encode()).hexdigest()}"
        out.update(await cache.remember(key, WIKI_TTL, load))
    return out


async def search(host: str, query: str, limit: int = 8) -> list[dict]:
    async def load():
        data = await api(host, {"action": "query", "list": "search", "srsearch": query, "srlimit": limit,
                                "srnamespace": 0, "srprop": "snippet"})
        hits = data.get("query", {}).get("search", [])
        titles = [h["title"] for h in hits]
        images = await page_images(host, titles, 200) if titles else {}
        return [{"title": h["title"], "snippet": clean(re.sub(r"<[^>]+>", "", h.get("snippet", ""))),
                 "image": images.get(h["title"])} for h in hits]

    return await cache.remember(f"wiki:search:{host}:{query.lower()}:{limit}", WIKI_TTL, load)


# ------------------------------------------------------------------ page

def _img_src(img) -> str | None:
    src = img.attributes.get("data-src") or img.attributes.get("src")
    if not src or src.startswith("data:"):
        return None
    return src


def _infobox(tree) -> dict | None:
    box = tree.css_first(".portable-infobox")
    if box is None:
        return None
    title_el = box.css_first(".pi-title")
    image = None
    img = box.css_first(".pi-image img") or box.css_first("img")
    if img is not None:
        image = _img_src(img)
    rows = []
    for item in box.css(".pi-data"):
        label = item.css_first(".pi-data-label")
        value = item.css_first(".pi-data-value")
        if label is None or value is None:
            continue
        for br in value.css("br"):
            br.replace_with(", ")
        text = clean(value.text(separator=" "))
        text = re.sub(r"\s+,", ",", text).strip(" ,")
        if text and len(text) < 300:
            rows.append({"label": clean(label.text()), "value": text})
        if len(rows) >= 18:
            break
    box.decompose()
    return {"title": clean(title_el.text()) if title_el else None, "image": image, "rows": rows}


def _flatten_tabbers(root) -> None:
    """Fandom tabbers -> plain stacked content with the tab label as a heading."""
    for tabber in root.css(".wds-tabber, .tabber"):
        labels = [clean(t.text()) for t in tabber.css(".wds-tabs__tab-label, .wds-tabs__tab")]
        panels = tabber.css(".wds-tab__content, .tabbertab")
        parts = []
        for i, panel in enumerate(panels):
            label = labels[i] if i < len(labels) else ""
            parts.append((f"<h4>{label}</h4>" if label else "") + (panel.html or ""))
        new = LexborHTMLParser("<div>" + "".join(parts) + "</div>").css_first("div")
        if new is not None:
            tabber.insert_before(new)
        tabber.decompose()


def _rewrite_links(root, game_id: str, host: str) -> None:
    for a in root.css("a[href]"):
        href = a.attributes.get("href") or ""
        if href.startswith("/wiki/"):
            title = unquote(href[len("/wiki/"):].split("#")[0]).replace("_", " ")
            if ":" in title:  # File:, Category:, Special: ...
                a.unwrap()
                continue
            a.attrs["href"] = f"/guides/{game_id}/wiki/{quote(title)}"
        elif href.startswith("#"):
            a.unwrap()


async def page(game: dict, title: str) -> dict:
    host = game["wiki"]

    async def load():
        data = await api(host, {"action": "parse", "page": title, "prop": "text|displaytitle|sections",
                                "redirects": 1, "disableeditsection": 1, "disabletoc": 1})
        if "error" in data:
            raise LookupError(data["error"].get("info", "page not found"))
        parsed = data["parse"]
        tree = LexborHTMLParser(parsed["text"])
        root = tree.css_first(".mw-parser-output") or tree.body

        for sel in ("script", "style", ".navbox", "table.navbox", ".toc", "#toc", ".mw-editsection", "sup.reference",
                    ".reference", ".references", ".mw-references-wrap", ".noprint", ".printfooter", ".mbox",
                    ".ambox", ".notice", ".hatnote", ".dablink", ".mw-empty-elt", ".wikia-gallery", ".gallery",
                    "figure.mw-halign-right audio", ".audio-button", ".mobile-hide-section"):
            for node in root.css(sel):
                node.decompose()

        infobox = _infobox(root)
        _flatten_tabbers(root)
        for img in root.css("img"):
            src = _img_src(img)
            if src:
                img.attrs["src"] = src
        _rewrite_links(root, game["id"], host)

        # split into sections at <h2>; cap each section on element boundaries so markup stays intact
        sections: list[dict] = []
        current = {"title": "Overview", "html": [], "size": 0, "truncated": False}
        for child in root.iter(include_text=False):
            if child.tag == "h2":
                heading = clean(child.text())
                if current["html"] and heading.lower() != current["title"].lower():
                    sections.append(current)
                    current = {"title": heading, "html": [], "size": 0, "truncated": False}
                continue
            chunk = child.html or ""
            if current["size"] + len(chunk) > MAX_SECTION_CHARS:
                current["truncated"] = True
                continue
            current["html"].append(chunk)
            current["size"] += len(chunk)
        if current["html"]:
            sections.append(current)

        out_sections, used_ids = [], set()
        for s in sections:
            if s["title"].lower() in SKIP_SECTIONS:
                continue
            html = sanitize_html("".join(s["html"]))
            if len(re.sub(r"<[^>]+>", "", html).strip()) < 20:
                continue
            sid = re.sub(r"[^a-z0-9]+", "-", s["title"].lower()).strip("-") or "section"
            while sid in used_ids:
                sid += "-2"
            used_ids.add(sid)
            out_sections.append({"id": sid, "title": s["title"], "html": html, "truncated": s["truncated"]})
            if len(out_sections) >= MAX_SECTIONS:
                break

        page_title = parsed.get("title", title)
        image = infobox["image"] if infobox and infobox.get("image") else None
        if not image:
            image = (await page_images(host, [page_title])).get(page_title)
        return {
            "title": page_title,
            "image": image,
            "infobox": infobox,
            "sections": out_sections,
            "source": {"name": game["wiki_name"], "url": f"https://{host}/wiki/{quote(page_title.replace(' ', '_'))}",
                       "license": "CC BY-SA 3.0", "license_url": "https://www.fandom.com/licensing"},
        }

    return await cache.remember(f"wiki:page:v2:{host}:{title.lower()}", WIKI_TTL, load)
