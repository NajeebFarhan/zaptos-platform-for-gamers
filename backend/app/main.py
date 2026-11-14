import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api import guides, prices
from app.config import CORS_ORIGINS, WARM_DEALS_ON_STARTUP
from app.core.http import http
from app.prices import service as price_service

log = logging.getLogger("uvicorn.error")  # shares uvicorn's handler so messages show in the console


async def _warm_deals():
    await asyncio.sleep(2)
    try:
        await price_service.deals()
        log.info("best offers cache warmed")
    except Exception as exc:  # never crash the app because a store is down
        log.warning("could not warm deals: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await http.start()
    task = asyncio.create_task(_warm_deals()) if WARM_DEALS_ON_STARTUP else None
    yield
    if task:
        task.cancel()
    await http.close()


app = FastAPI(title="Zaptos API", version="1.0.0", lifespan=lifespan,
              description="Gaming hardware price comparison across Indian stores + game guides.")
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"])

app.include_router(prices.router)
app.include_router(guides.router)


@app.get("/api/health")
async def health():
    return {"ok": True}
