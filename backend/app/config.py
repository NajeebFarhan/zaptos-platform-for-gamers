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

# Browser origins allowed to call the API (comma-separated, exact, no trailing slash).
# The production frontend is a Cloudflare Worker; local dev is the Vite server.
FRONTEND_URL = "https://zaptos-platform-for-gamers.najeebmazumdar.workers.dev"
CORS_ORIGINS = [
    o.strip().rstrip("/")
    for o in os.getenv("CORS_ORIGINS", f"{FRONTEND_URL},http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
# Cloudflare preview deploys get their own subdomain: https://<version>-zaptos-platform-for-gamers.najeebmazumdar.workers.dev
# Set CORS_ORIGIN_REGEX to an empty string to turn this off.
CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX", r"https://([a-z0-9-]+-)?zaptos-platform-for-gamers\.najeebmazumdar\.workers\.dev"
) or None
