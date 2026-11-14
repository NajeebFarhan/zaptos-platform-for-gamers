"""Generic adapter for WooCommerce shops via the public Store API.

`/wp-json/wc/store/v1/products?search=` is the same endpoint the shop's own
block-based storefront uses, and returns structured prices, stock and ratings.
"""

from app.core.text import clean
from app.prices.models import Offer
from app.prices.stores.base import Store, StoreError


class WooStore(Store):
    def __init__(self, id: str, name: str, home: str, color: str, kind: str = "PC Specialist"):
        self.id, self.name, self.home, self.color, self.kind = id, name, home, color, kind

    async def search(self, http, query, limit=24):
        resp = await http.get(
            f"{self.home}/wp-json/wc/store/v1/products",
            params={"search": query, "per_page": min(limit, 50)},
            headers={"Accept": "application/json"},
        )
        self.check(resp)
        try:
            data = resp.json()
        except ValueError as exc:
            raise StoreError("invalid JSON") from exc
        if not isinstance(data, list):
            raise StoreError("unexpected payload")

        offers: list[Offer] = []
        for p in data:
            prices = p.get("prices") or {}
            unit = 10 ** int(prices.get("currency_minor_unit") or 0)
            rng = prices.get("price_range") or {}
            raw = rng.get("min_amount") if rng else prices.get("price")
            try:
                price = int(raw) / unit if raw else None
                regular = int(prices.get("regular_price") or 0) / unit
            except (TypeError, ValueError):
                continue
            if not price:
                continue
            try:
                rating = float(p.get("average_rating") or 0) or None
            except ValueError:
                rating = None
            images = p.get("images") or []
            brands = p.get("brands") or []
            offers.append(
                Offer(
                    store=self.id,
                    title=clean(p.get("name")),
                    url=p.get("permalink") or self.home,
                    price=price,
                    mrp=regular if regular > price else None,
                    rating=rating,
                    rating_count=p.get("review_count") or None,
                    image=(images[0].get("thumbnail") or images[0].get("src")) if images else None,
                    in_stock=p.get("is_in_stock"),
                    brand=clean(brands[0].get("name")) if brands else None,
                )
            )
        return offers[:limit]
