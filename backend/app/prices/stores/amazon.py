import re

from selectolax.lexbor import LexborHTMLParser

from app.core.text import clean, parse_count, parse_price
from app.prices.models import Offer
from app.prices.stores.base import Store, StoreBlocked


class Amazon(Store):
    id = "amazon"
    name = "Amazon.in"
    home = "https://www.amazon.in"
    kind = "Marketplace"
    color = "#ff9900"

    async def search(self, http, query, limit=24):
        resp = await http.get(f"{self.home}/s", params={"k": query})
        text = self.check(resp, blocked_markers=("validateCaptcha", "Type the characters you see"))
        tree = LexborHTMLParser(text)
        items = tree.css('div[data-component-type="s-search-result"]')
        if not items:
            # A genuine "no results" page is a full search page. Anything else (e.g. the ~2 KB blank
            # JavaScript challenge Amazon serves to rate-limited clients) is a block, not an empty result.
            if "captcha" in text.lower() or len(text) < 50_000 or tree.css_first("#search, .s-main-slot") is None:
                raise StoreBlocked("bot check page")
            return []

        offers: list[Offer] = []
        for it in items:
            asin = it.attributes.get("data-asin")
            if not asin:
                continue
            # Grid layouts render the brand and the title as two separate <h2>s.
            heads = [clean(h.attributes.get("aria-label") or h.text()) for h in it.css("h2")]
            heads = [re.sub(r"^Sponsored Ad\s*[-–]\s*", "", h) for h in heads if h]
            if not heads:
                continue
            title = max(heads, key=len)
            brand = min(heads, key=len) if len(heads) > 1 else None
            if brand and brand.lower() not in title.lower():
                title = f"{brand} {title}"

            price_el = it.css_first(".a-price:not(.a-text-price) .a-offscreen")
            price = parse_price(price_el.text()) if price_el else None
            if not price:
                continue
            mrp_el = it.css_first(".a-price.a-text-price .a-offscreen")
            mrp = parse_price(mrp_el.text()) if mrp_el else None

            rating = None
            r_el = it.css_first(".a-icon-alt")
            if r_el:
                m = re.search(r"([\d.]+)\s*out of", r_el.text())
                rating = float(m.group(1)) if m else None
            count = None
            c_el = it.css_first('[aria-label$="ratings"], [aria-label$="rating"]')
            if c_el:
                count = parse_count(c_el.attributes.get("aria-label"))
            if count is None:
                c_el = it.css_first('a[href*="customerReviews"] span')
                count = parse_count(c_el.text()) if c_el else None

            img = it.css_first("img.s-image")
            offers.append(
                Offer(
                    store=self.id,
                    title=title,
                    url=f"{self.home}/dp/{asin}",
                    price=price,
                    mrp=mrp if mrp and mrp > price else None,
                    rating=rating,
                    rating_count=count,
                    image=img.attributes.get("src") if img else None,
                    in_stock=True,
                    brand=brand,
                )
            )
            if len(offers) >= limit:
                break
        return offers
