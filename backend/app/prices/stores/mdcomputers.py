from selectolax.lexbor import LexborHTMLParser

from app.core.text import clean, parse_price
from app.prices.models import Offer
from app.prices.stores.base import Store


class MDComputers(Store):
    id = "mdcomputers"
    name = "MD Computers"
    home = "https://mdcomputers.in"
    color = "#f59e0b"

    async def search(self, http, query, limit=24):
        resp = await http.get(
            f"{self.home}/index.php",
            params={"route": "product/search", "search": query, "limit": 50},
        )
        tree = LexborHTMLParser(self.check(resp))
        offers: list[Offer] = []
        for card in tree.css("div.product-grid-item"):
            link = card.css_first(".product-entities-title a")
            if not link:
                continue
            new = card.css_first(".price .ins") or card.css_first(".price")
            price = parse_price(new.text()) if new else None
            if not price:
                continue
            old = card.css_first(".price .del")
            mrp = parse_price(old.text()) if old else None
            img = card.css_first("img")
            text = card.text().lower()
            offers.append(
                Offer(
                    store=self.id,
                    title=clean(link.text()),
                    url=link.attributes.get("href") or self.home,
                    price=price,
                    mrp=mrp if mrp and mrp > price else None,
                    image=(img.attributes.get("data-src") or img.attributes.get("src")) if img else None,
                    in_stock=False if "out of stock" in text else None,
                )
            )
            if len(offers) >= limit:
                break
        return offers
