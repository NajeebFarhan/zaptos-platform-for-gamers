# LootScout 🎯

A web app for gamers in India with two jobs:

1. **Price comparison (trivago-style) for gaming & PC hardware.** One search fans out to 10 Indian stores in parallel. Matching listings are grouped into a single product row showing the best in-stock price, every store's price, MRP discount, savings vs the priciest store, and a rating combined across stores.
2. **Game guides** for **Valorant, Genshin Impact, Mobile Legends: Bang Bang and CS:GO / CS2**: rosters (agents, characters, heroes, weapons, maps), wiki pages, guide topics found on popular guide sites, and a clean reader view for articles.

**Stack:** React 19 + Tailwind CSS v4 + Vite (frontend) · Python 3.11+ / FastAPI (backend) · curl_cffi, selectolax, rapidfuzz, trafilatura · SQLite cache.

---

## Quick start (Windows)

```powershell
.\start.ps1
```

The first run creates the Python venv and installs npm packages. It then starts the API on `http://127.0.0.1:8000` and the web app on **http://localhost:5173**.

### Manual start (any OS)

```bash
# backend
cd backend
python -m venv .venv
.venv/Scripts/activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to the backend, so no CORS setup is needed in development. Interactive API docs are at `http://127.0.0.1:8000/docs`.

---

## Stores compared (prices in INR)

| Store | Type | How data is read |
|---|---|---|
| Amazon.in | Marketplace | Search results HTML |
| Flipkart | Marketplace | `window.__INITIAL_STATE__` JSON embedded in the search page |
| Reliance Digital | Electronics | `window.__INITIAL_STATE__` JSON |
| MD Computers | PC specialist | Search results HTML (OpenCart) |
| Vedant Computers | PC specialist | Search results HTML (OpenCart) |
| National PC | PC specialist | Search results HTML |
| PrimeABGB | PC specialist | WooCommerce Store API (`/wp-json/wc/store/v1/products`) |
| PC Studio | PC specialist | WooCommerce Store API |
| EZPZ Solutions | PC specialist | WooCommerce Store API |
| EliteHubs | PC specialist | Shopify predictive search JSON |

Croma, Vijay Sales and Games The Shop were evaluated but dropped: they render prices with client-side JavaScript, so they would need a headless browser.

Requests use `curl_cffi` with a real browser TLS fingerprint and are throttled per host (max 2 concurrent requests, 0.4 s minimum gap). Results are cached in SQLite for 30 minutes. If a store fails, the last good (stale) results are shown and labelled as cached in the UI.

### How products are matched across stores

`backend/app/prices/matcher.py` normalises titles (`RTX5060Ti` → `rtx 5060 ti`, `PlayStation 5` → `ps5`, `32GB x 2` → `2x16gb`…). It then treats two listings as **different products** if any of these differ:

- brand
- product type (GPU vs laptop vs console…)
- variant (Ti / Super / Pro / Digital / X3D…)
- model numbers (5060 vs 5070, 9800X3D vs 7800X3D)
- capacity or memory-kit layout (1×32GB vs 2×16GB)
- product line (Ventus vs Shadow, Eagle vs Aero)

Whatever survives is fuzzy-matched with rapidfuzz. The matcher prefers leaving two listings apart over merging different products, because a wrong "cheapest" price is worse than an extra row. The regression tests use real listings:

```bash
cd backend
python -m unittest discover -s tests -t .
```

**Best offers** scans a set of popular queries in the background on startup. It ranks products by discount off MRP (MRPs above 3× the price are ignored), savings across stores and rating.

## Guide sources

| Content | Source |
|---|---|
| Valorant agents, abilities, maps, weapons | [valorant-api.com](https://valorant-api.com) |
| Rosters & wiki pages (all 4 games) | Fandom wikis via the MediaWiki API: VALORANT, Genshin Impact, Mobile Legends and Counter-Strike wikis (CC BY-SA, attributed on every page) |
| Guide search & topic guides | DuckDuckGo HTML results, with popular guide sites (Mobalytics, Dot Esports, ONE Esports, Game8, …) ranked first |
| Latest guides | WordPress REST APIs of Dot Esports, Mobalytics and PCGamesN (falls back to web search when coverage is thin) |
| Reader view | `trafilatura` article extraction, sanitised, always linking back to the publisher |

Scraped HTML is sanitised twice: an allow-list sanitiser on the backend and DOMPurify in the browser. The article reader blocks SSRF: only public http(s) hosts on standard ports are fetched, and every redirect hop is re-validated.

---

## Project layout

```
backend/
  app/
    main.py              FastAPI app, CORS, startup warm-up
    config.py            TTLs and timeouts (env-overridable)
    core/                http client (throttled, browser TLS), SQLite cache, text helpers
    prices/
      stores/            one adapter per store (+ generic WooCommerce / Shopify adapters)
      matcher.py         cross-store product grouping + relevance/deal scoring
      service.py         parallel fan-out, SSE progress stream, stale fallback, deals
      catalog.py         categories, trending searches, deal queries
    guides/
      games.py           the four games: wiki, rosters, guide topics
      wiki.py            MediaWiki client + page cleaning
      valorant.py        valorant-api.com
      web.py             web search, latest guides, article reader (SSRF-safe)
      sanitize.py        allow-list HTML sanitiser
    api/                 /api/prices/* and /api/guides/* routers
  tests/test_matcher.py
frontend/
  src/pages/             Home, Search, Deals, GuidesHome, GameHub, WikiPage, Reader
  src/components/        ProductCard, ProductDrawer, Filters, SearchProgress, SafeHtml…
  src/lib/               API hooks (incl. SSE live search), INR formatting
```

## API overview

| Endpoint | Description |
|---|---|
| `GET /api/prices/meta` | Stores, categories, trending searches |
| `GET /api/prices/search?q=` | Grouped results (add `refresh=true` to bypass the cache) |
| `GET /api/prices/search/stream?q=` | Same, as Server-Sent Events: one `store` event per store, then `result` |
| `GET /api/prices/deals` | Best offers across popular products |
| `GET /api/guides/games` | Supported games |
| `GET /api/guides/{game}/roster/{roster}` | e.g. `valorant/roster/agents`, `genshin-impact/roster/characters` |
| `GET /api/guides/{game}/wiki?title=` | Cleaned wiki page (+ Valorant ability data) |
| `GET /api/guides/{game}/topic/{topic}` | Guides for a topic such as `tier-list` |
| `GET /api/guides/{game}/search?q=` | Wiki + web guide search |
| `GET /api/guides/{game}/latest` | Recent guide articles |
| `GET /api/guides/article?url=` | Reader view of an article |

### Configuration (environment variables)

`PRICE_TTL` (default 1800 s), `GUIDE_SEARCH_TTL` (6 h), `WIKI_TTL` (24 h), `ARTICLE_TTL` (24 h), `STORE_TIMEOUT` (20 s), `WARM_DEALS_ON_STARTUP` (`1`), `CORS_ORIGINS`. For the frontend, set `VITE_API_BASE` if the API is not served from the same origin.

---

## Limitations & responsible use

- **Scrapers break when sites change.** Each store adapter is small and isolated, and a failing store is reported in the UI without breaking the rest.
- **Terms of service.** Several retailers' terms restrict automated access. This project caches aggressively, throttles per host and only reads public search pages. For a production or commercial deployment, use the official programmes instead: Amazon Product Advertising API, Flipkart Affiliate API, and the store-provided feeds.
- **Prices and stock are indicative.** Marketplace listings can come from third-party sellers, and some stores don't expose stock status ("stock unknown" in the UI). Always confirm on the store before buying.
- Product matching is heuristic. Unusual titles may show up as separate rows.
