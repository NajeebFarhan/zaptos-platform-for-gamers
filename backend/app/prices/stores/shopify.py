"""Generic adapter for Shopify shops via the predictive-search JSON endpoint."""

from app.core.text import clean, parse_price
from app.prices.models import Offer
from app.prices.stores.base import Store, StoreError


class ShopifyStore(Store):
    def __init__(self, id: str, name: str, home: str, color: str, kind: str = "PC Specialist"):
        self.id, self.name, self.home, self.color, self.kind = id, name, home, color, kind

    async def search(self, http, query, limit=24):
        resp = await http.get(
            f"{self.home}/search/suggest.json",
            params={
                "q": query,
                "resources[type]": "product",
                "resources[limit]": 10,
                "resources[options][unavailable_products]": "last",
            },
            headers={"Accept": "application/json"},
        )
        self.check(resp)
        try:
            payload = resp.json()
        except ValueError as exc:
            raise StoreError("unexpected payload") from exc
        return self.parse(payload, limit)

    def parse(self, payload, limit: int = 24) -> list[Offer]:
        """Decoded predictive-search payload -> offers. Pure, so it can be tested against saved responses."""
        try:
            products = payload["resources"]["results"]["products"]
        except (KeyError, TypeError) as exc:
            raise StoreError("unexpected payload") from exc

        offers: list[Offer] = []
        for p in products:
            price = parse_price(p.get("price_min") or p.get("price"))
            if not price:
                continue
            mrp = parse_price(p.get("compare_at_price_max"))
            url = (p.get("url") or "").split("?")[0]
            image = p.get("image") or (p.get("featured_image") or {}).get("url")
            offers.append(
                Offer(
                    store=self.id,
                    title=clean(p.get("title")),
                    url=self.home + url if url.startswith("/") else url,
                    price=price,
                    mrp=mrp if mrp and mrp > price else None,
                    image=image,
                    in_stock=p.get("available"),
                    brand=clean(p.get("vendor")) or None,
                )
            )
        return offers[:limit]
