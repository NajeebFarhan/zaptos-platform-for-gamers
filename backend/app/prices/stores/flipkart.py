from app.core.text import clean, extract_json_after
from app.prices.models import Offer
from app.prices.stores.base import Store, StoreError


def _image(media) -> str | None:
    try:
        url = media["images"][0]["url"]
    except (KeyError, IndexError, TypeError):
        return None
    url = url.replace("{@width}", "416").replace("{@height}", "416").replace("{@quality}", "70")
    return url.replace("http://", "https://", 1)


class Flipkart(Store):
    id = "flipkart"
    name = "Flipkart"
    home = "https://www.flipkart.com"
    kind = "Marketplace"
    color = "#2874f0"

    async def search(self, http, query, limit=24):
        resp = await http.get(f"{self.home}/search", params={"q": query})
        return self.parse(self.check(resp), limit)

    def parse(self, text: str, limit: int = 24) -> list[Offer]:
        """Search-results HTML -> offers. Pure, so it can be tested against saved pages."""
        state = extract_json_after(text, "window.__INITIAL_STATE__")
        if not state:
            raise StoreError("no embedded state")

        nodes: list[dict] = []

        def walk(o):
            if isinstance(o, dict):
                if "pricing" in o and "titles" in o:
                    nodes.append(o)
                    return
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(state.get("pageDataV4", {}))

        offers: list[Offer] = []
        seen: set[str] = set()
        for p in nodes:
            pid = p.get("id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            titles = p.get("titles") or {}
            title = clean(titles.get("newTitle") or titles.get("title"))
            if titles.get("subtitle") and len(title) < 30:
                title = f"{title} {clean(titles['subtitle'])}"
            if not title:
                continue

            pricing = p.get("pricing") or {}
            price = mrp = None
            if isinstance(pricing.get("finalPrice"), dict):
                price = pricing["finalPrice"].get("value")
            if isinstance(pricing.get("mrp"), dict):
                mrp = pricing["mrp"].get("value")
            for entry in pricing.get("prices") or []:
                if entry.get("strikeOff"):
                    mrp = mrp or entry.get("value")
                else:
                    price = price or entry.get("value")
            if not price:
                continue

            rating = p.get("rating") or {}
            avg = rating.get("average") or None
            cnt = rating.get("count") or None
            state_ = ((p.get("availability") or {}).get("displayState") or "").upper()

            url = p.get("baseUrl") or ""
            offers.append(
                Offer(
                    store=self.id,
                    title=title,
                    url=self.home + url if url.startswith("/") else url,
                    price=float(price),
                    mrp=float(mrp) if mrp and mrp > price else None,
                    rating=float(avg) if avg else None,
                    rating_count=int(cnt) if cnt else None,
                    image=_image(p.get("media")),
                    in_stock=state_ == "IN_STOCK" if state_ else None,
                )
            )
            if len(offers) >= limit:
                break
        return offers
