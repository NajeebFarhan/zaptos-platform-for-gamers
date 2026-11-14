from selectolax.lexbor import LexborHTMLParser

from app.core.text import clean, parse_price
from app.prices.models import Offer
from app.prices.stores.base import Store


class NationalPC(Store):
    id = "nationalpc"
    name = "National PC"
    home = "https://nationalpc.in"
    color = "#2563eb"

    async def search(self, http, query, limit=24):
        resp = await http.get(f"{self.home}/search", params={"q": query})
        tree = LexborHTMLParser(self.check(resp))
        offers: list[Offer] = []
        seen: set[str] = set()
        for h3 in tree.css("h3"):
            link = h3.css_first("a[href]")
            if not link:
                continue
            href = link.attributes.get("href") or ""
            if href in seen or href.count("/") < 2:
                continue
            # climb to the product card (the element that also holds image + price)
            card = h3.parent
            for _ in range(4):
                if card is None or card.css_first("img"):
                    break
                card = card.parent
            if card is None:
                continue
            spans = [s for s in card.css("span") if "₹" in (s.text() or "")]
            prices = [parse_price(s.text()) for s in spans]
            prices = [p for p in prices if p]
            if not prices:
                continue
            # struck-through list price, if shown, sits in <s>/<del> or a line-through span
            struck = card.css_first("s, del, .line-through")
            mrp = parse_price(struck.text()) if struck else None
            price = min(p for p in prices if p != mrp) if any(p != mrp for p in prices) else prices[0]
            seen.add(href)
            img = card.css_first("img")
            brand = card.css_first(".npc-card-brand")
            text = card.text().lower()
            offers.append(
                Offer(
                    store=self.id,
                    title=clean(link.text()),
                    url=self.home + href if href.startswith("/") else href,
                    price=price,
                    mrp=mrp if mrp and mrp > price else None,
                    image=img.attributes.get("src") if img else None,
                    in_stock="out of stock" not in text,
                    brand=clean(brand.text()).title() if brand else None,
                )
            )
            if len(offers) >= limit:
                break
        return offers
