from fastapi import APIRouter, HTTPException, Query

from app.guides import service, web
from app.guides.games import GAMES, public

router = APIRouter(prefix="/api/guides", tags=["guides"])


def _game(game_id: str) -> dict:
    try:
        return service.get_game(game_id)
    except KeyError:
        raise HTTPException(404, f"unknown game '{game_id}'")


@router.get("/games")
async def games():
    return {"games": [public(g) for g in GAMES.values()]}


@router.get("/article")
async def article(url: str = Query(..., max_length=2000)):
    try:
        return await web.read_article(url)
    except web.UnsafeURL as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Couldn't load that article: {exc}")


@router.get("/{game_id}")
async def game(game_id: str):
    return public(_game(game_id))


@router.get("/{game_id}/roster/{roster_id}")
async def roster(game_id: str, roster_id: str):
    g = _game(game_id)
    try:
        return {"items": await service.roster(g, roster_id)}
    except KeyError:
        raise HTTPException(404, f"unknown roster '{roster_id}'")
    except Exception as exc:
        raise HTTPException(502, f"wiki unavailable: {exc}")


@router.get("/{game_id}/wiki")
async def wiki_page(game_id: str, title: str = Query(..., min_length=1, max_length=200)):
    g = _game(game_id)
    try:
        return await service.entity(g, title)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"wiki unavailable: {exc}")


@router.get("/{game_id}/related")
async def related(game_id: str, title: str = Query(..., max_length=200)):
    return {"results": await service.related_guides(_game(game_id), title)}


@router.get("/{game_id}/search")
async def search(game_id: str, q: str = Query(..., min_length=2, max_length=120)):
    return await service.search(_game(game_id), q)


@router.get("/{game_id}/topic/{topic_id}")
async def topic(game_id: str, topic_id: str):
    g = _game(game_id)
    try:
        return await service.topic(g, topic_id)
    except KeyError:
        raise HTTPException(404, f"unknown topic '{topic_id}'")
    except Exception as exc:
        raise HTTPException(502, f"search unavailable: {exc}")


@router.get("/{game_id}/latest")
async def latest(game_id: str):
    try:
        return {"items": await web.latest_guides(_game(game_id))}
    except Exception:
        return {"items": []}
