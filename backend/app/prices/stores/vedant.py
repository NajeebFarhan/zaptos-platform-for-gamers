from selectolax.lexbor import LexborHTMLParser

from app.core.text import clean, parse_price
from app.prices.models import Offer
from app.prices.stores.base import Store


class VedantComputers(Store):
    id = "vedant"
    name = "Vedant Computers"
    home = "https://www.vedantcomputers.com"
    color = "#0d9488"

    async def search(self, http, query, limit=24):
        resp = await http.get(
            f"{self.home}/index.php",
            params={"route": "product/search", "search": query, "limit": 50},
        )
        tree = LexborHTMLParser(self.check(resp))
        offers: list[Offer] = []
        for card in tree.css(".product-layout"):
            link = card.css_first(".name a")
            if not link:
                continue
            new = card.css_first(".price-new") or card.css_first(".price-normal")
            price = parse_price(new.text()) if new else None
            if not price:
                continue
            old = card.css_first(".price-old")
            mrp = parse_price(old.text()) if old else None
            img = card.css_first(".image img")
            classes = (card.attributes.get("class") or "").lower()
            labels = " ".join(label.text().lower() for label in card.css(".product-label"))
            out = "out-of-stock" in classes or "out of stock" in labels
            url = (link.attributes.get("href") or self.home).split("?")[0]
            offers.append(
                Offer(
                    store=self.id,
                    title=clean(link.text()),
                    url=url,
                    price=price,
                    mrp=mrp if mrp and mrp > price else None,
                    image=(img.attributes.get("data-src") or img.attributes.get("src")) if img else None,
                    in_stock=False if out else None,
                )
            )
            if len(offers) >= limit:
                break
        return offers
