import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CACHE_DB = DATA_DIR / "cache.sqlite3"

# How long scraped data stays fresh (seconds)
PRICE_TTL = int(os.getenv("PRICE_TTL", 30 * 60))
EMPTY_PRICE_TTL = int(os.getenv("EMPTY_PRICE_TTL", 10 * 60))
GUIDE_SEARCH_TTL = int(os.getenv("GUIDE_SEARCH_TTL", 6 * 3600))
WIKI_TTL = int(os.getenv("WIKI_TTL", 24 * 3600))
ARTICLE_TTL = int(os.getenv("ARTICLE_TTL", 24 * 3600))

# Per-store time budget for one search
STORE_TIMEOUT = float(os.getenv("STORE_TIMEOUT", 20))

# Warm up the "best offers" cache in the background on startup
WARM_DEALS_ON_STARTUP = os.getenv("WARM_DEALS_ON_STARTUP", "1") == "1"

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
