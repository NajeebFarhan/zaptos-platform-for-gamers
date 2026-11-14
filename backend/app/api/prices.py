import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.prices import service
from app.prices.catalog import CATEGORIES, TRENDING
from app.prices.stores import STORES

router = APIRouter(prefix="/api/prices", tags=["prices"])


def _clean_query(q: str) -> str:
    q = " ".join(q.split())
    if len(q) < 2:
        raise HTTPException(400, "query too short")
    if len(q) > 120:
        raise HTTPException(400, "query too long")
    return q


@router.get("/meta")
async def meta():
    return {"stores": [s.info() for s in STORES], "categories": CATEGORIES, "trending": TRENDING, "currency": "INR"}


@router.get("/search")
async def search(q: str = Query(..., description="product to look for"), refresh: bool = False):
    return await service.search(_clean_query(q), refresh=refresh)


@router.get("/search/stream")
async def search_stream(request: Request, q: str, refresh: bool = False):
    """Server-sent events: one `store` event per store as it finishes, then `result`."""
    query = _clean_query(q)

    async def events():
        async for event in service.search_stream(query, refresh=refresh):
            if await request.is_disconnected():
                break
            yield f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


class TrackItem(BaseModel):
    key: str = Field(..., max_length=64)
    title: str = Field(..., min_length=2, max_length=400)
    query: str | None = Field(None, max_length=400)
    urls: list[str] = Field(default_factory=list, max_length=20)


class TrackRequest(BaseModel):
    items: list[TrackItem] = Field(..., max_length=60)


@router.post("/track")
async def track(body: TrackRequest, refresh: bool = False):
    """Latest prices for wishlist items. The wishlist itself lives in the browser."""
    items = []
    for it in body.items:
        query = " ".join((it.query or it.title).split())
        if len(query) > 120:  # long product title used as the query: keep the leading, most specific words
            query = query[:120].rsplit(" ", 1)[0]
        if len(query) < 2:
            continue
        items.append({"key": it.key, "query": query, "title": it.title, "urls": it.urls})
    return await service.track(items, refresh=refresh)


@router.get("/deals")
async def deals(refresh: bool = False):
    return await service.deals(refresh=refresh)
