import asyncio

from app.config import WIKI_TTL
from app.core.cache import cache
from app.guides import valorant, web, wiki
from app.guides.games import GAMES


def get_game(game_id: str) -> dict:
    game = GAMES.get(game_id)
    if not game:
        raise KeyError(game_id)
    return game


async def roster(game: dict, roster_id: str) -> list[dict]:
    spec = next((r for r in game["roster"] if r["id"] == roster_id), None)
    if spec is None:
        raise KeyError(roster_id)

    if spec["source"] == "valorant":
        return await {"agents": valorant.agents, "maps": valorant.maps, "weapons": valorant.weapons}[spec["kind"]]()

    async def load():
        host = game["wiki"]
        if "titles" in spec:
            titles = list(spec["titles"])
        else:
            titles = await wiki.category_members(host, spec["category"])
        exclude = {t.lower() for t in spec.get("exclude", [])}
        titles = [t for t in titles if "/" not in t and t.lower() not in exclude]

        # tag each entry using the tag categories (element, role, rarity...)
        tags: dict[str, dict[str, list[str]]] = {t: {} for t in titles}
        jobs = []
        for group in spec.get("tag_groups", []):
            for tag, cat in group["categories"].items():
                jobs.append((group["label"], tag, wiki.category_members(host, cat)))
        results = await asyncio.gather(*(j[2] for j in jobs), return_exceptions=True)
        for (label, tag, _), members in zip(jobs, results):
            if isinstance(members, Exception):
                continue
            for m in members:
                if m in tags:
                    tags[m].setdefault(label, []).append(tag)

        images = await wiki.page_images(host, titles)
        out = []
        for t in titles:
            t_tags = tags.get(t, {})
            out.append({"title": t, "wiki_title": t, "image": images.get(t), "tags": t_tags,
                        "subtitle": " · ".join(v[0] for v in t_tags.values()) if t_tags else None})
        return out

    return await cache.remember(f"roster:v1:{game['id']}:{roster_id}", WIKI_TTL, load)


async def entity(game: dict, title: str) -> dict:
    page = await wiki.page(game, title)
    extra = None
    if game["id"] == "valorant":
        try:
            extra = await valorant.agent(page["title"])
        except Exception:
            extra = None
    return {**page, "agent": extra}


def _guide_query(game: dict, q: str) -> str:
    q = q.strip()
    base = q if game["search_name"].split()[0].lower() in q.lower() else f"{game['search_name']} {q}"
    return base if "guide" in base.lower() else f"{base} guide"


async def search(game: dict, q: str) -> dict:
    wiki_task = asyncio.create_task(wiki.search(game["wiki"], q))
    web_task = asyncio.create_task(web.web_search(_guide_query(game, q)))
    wiki_res, web_res = await asyncio.gather(wiki_task, web_task, return_exceptions=True)
    return {
        "query": q,
        "wiki": wiki_res if isinstance(wiki_res, list) else [],
        "web": web_res if isinstance(web_res, list) else [],
        "errors": [str(e) for e in (wiki_res, web_res) if isinstance(e, Exception)],
    }


async def topic(game: dict, topic_id: str) -> dict:
    spec = next((t for t in game["topics"] if t["id"] == topic_id), None)
    if spec is None:
        raise KeyError(topic_id)
    results = await web.web_search(_guide_query(game, spec["query"]))
    return {"topic": {"id": spec["id"], "label": spec["label"]}, "results": results}


async def related_guides(game: dict, title: str) -> list[dict]:
    try:
        return (await web.web_search(_guide_query(game, title)))[:8]
    except Exception:
        return []
