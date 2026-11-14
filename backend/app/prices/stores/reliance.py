from app.core.text import clean, extract_json_after
from app.prices.models import Offer
from app.prices.stores.base import Store, StoreError


class RelianceDigital(Store):
    id = "reliance"
    name = "Reliance Digital"
    home = "https://www.reliancedigital.in"
    kind = "Electronics"
    color = "#e42529"

    async def search(self, http, query, limit=24):
        resp = await http.get(f"{self.home}/products", params={"q": query})
        return self.parse(self.check(resp), limit)

    def parse(self, text: str, limit: int = 24) -> list[Offer]:
        """Search-results HTML -> offers. Pure, so it can be tested against saved pages."""
        state = extract_json_after(text, "window.__INITIAL_STATE__")
        if not state:
            raise StoreError("no embedded state")
        items = (((state.get("productListingPage") or {}).get("productlists") or {}).get("items")) or []

        offers: list[Offer] = []
        for it in items:
            if it.get("type") != "product":
                continue
            price_info = it.get("price") or {}
            price = (price_info.get("effective") or {}).get("min")
            mrp = (price_info.get("marked") or {}).get("min")
            if not price:
                continue
            url = it.get("url") or f"/product/{it.get('slug')}/"
            url = url.split("?")[0]
            medias = it.get("medias") or []
            rating = it.get("rating") or None
            offers.append(
                Offer(
                    store=self.id,
                    title=clean(it.get("name")),
                    url=self.home + url if url.startswith("/") else url,
                    price=float(price),
                    mrp=float(mrp) if mrp and mrp > price else None,
                    rating=float(rating) if rating else None,
                    image=medias[0].get("url") if medias else None,
                    in_stock=bool(it.get("sellable")),
                    brand=(it.get("brand") or {}).get("name"),
                )
            )
            if len(offers) >= limit:
                break
        return offers
