import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

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


@router.get("/deals")
async def deals(refresh: bool = False):
    return await service.deals(refresh=refresh)
