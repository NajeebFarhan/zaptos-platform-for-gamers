"""Structured Valorant data from the community valorant-api.com (agents, maps, weapons)."""

import re

from app.config import WIKI_TTL
from app.core.cache import cache
from app.core.http import http

BASE = "https://valorant-api.com/v1"


def _plain(text: str | None) -> str | None:
    """Drop Riot's in-game styling tags, e.g. '<debuffred>lethal damage</>'."""
    return re.sub(r"</?[a-zA-Z]*>", "", text).strip() if text else text


async def _get(path: str, params: dict | None = None):
    async def load():
        resp = await http.get(f"{BASE}/{path}", params=params, headers={"Accept": "application/json"})
        resp.raise_for_status()
        return resp.json().get("data", [])

    return await cache.remember(f"valapi:{path}:{params}", WIKI_TTL, load)


async def agents() -> list[dict]:
    data = await _get("agents", {"isPlayableCharacter": "true"})
    out = []
    for a in sorted(data, key=lambda a: a["displayName"]):
        role = (a.get("role") or {}).get("displayName")
        out.append({
            "title": a["displayName"],
            "wiki_title": a["displayName"],
            "image": a.get("displayIcon"),
            "portrait": a.get("fullPortrait"),
            "background": a.get("background"),
            "colors": ["#" + c[:6] for c in (a.get("backgroundGradientColors") or [])],
            "subtitle": role,
            "tags": {"Role": [role]} if role else {},
            "description": _plain(a.get("description")),
            "abilities": [
                {"slot": ab.get("slot"), "name": ab.get("displayName"), "description": _plain(ab.get("description")),
                 "icon": ab.get("displayIcon")}
                for ab in a.get("abilities") or [] if ab.get("displayName")
            ],
        })
    return out


async def maps() -> list[dict]:
    data = await _get("maps")
    out = []
    for m in data:
        # skip range / tutorial maps that have no tactical description
        if not m.get("tacticalDescription") and m["displayName"] not in ("Breeze",):
            continue
        out.append({
            "title": m["displayName"],
            "wiki_title": m["displayName"],
            "image": m.get("listViewIcon") or m.get("splash"),
            "portrait": m.get("splash"),
            "subtitle": m.get("tacticalDescription") or m.get("coordinates"),
            "tags": {"Sites": [m["tacticalDescription"]]} if m.get("tacticalDescription") else {},
        })
    return sorted(out, key=lambda m: m["title"])


async def weapons() -> list[dict]:
    data = await _get("weapons")
    out = []
    for w in data:
        cat = (w.get("category") or "").replace("EEquippableCategory::", "")
        cat = {"SMG": "SMG", "Rifle": "Rifle", "Shotgun": "Shotgun", "Sniper": "Sniper", "Heavy": "Heavy",
               "Sidearm": "Sidearm", "Melee": "Melee"}.get(cat, cat)
        cost = (w.get("shopData") or {}).get("cost")
        stats = w.get("weaponStats") or {}
        out.append({
            "title": w["displayName"],
            "wiki_title": w["displayName"],
            "image": w.get("displayIcon"),
            "subtitle": f"{cat} · {cost} creds" if cost else cat,
            "tags": {"Type": [cat]},
            "stats": {k: stats.get(k) for k in ("fireRate", "magazineSize", "reloadTimeSeconds", "equipTimeSeconds")
                      if stats.get(k) is not None},
        })
    order = ["Sidearm", "SMG", "Shotgun", "Rifle", "Sniper", "Heavy", "Melee"]
    return sorted(out, key=lambda w: (order.index(w["tags"]["Type"][0]) if w["tags"]["Type"][0] in order else 9, w["title"]))


async def agent(name: str) -> dict | None:
    for a in await agents():
        if a["title"].lower() == name.lower():
            return a
    return None
