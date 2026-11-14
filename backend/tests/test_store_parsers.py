"""Store parsers, run against saved responses (tests/fixtures) so no network is needed.

When a store changes its markup in real life, save the new page over the fixture, see what
breaks here, and fix the parser. `test_live_stores.py` is what tells you it broke.
"""

from types import SimpleNamespace

import pytest

from app.prices.stores import Amazon, Flipkart, RelianceDigital, ShopifyStore, StoreBlocked, StoreError, WooStore
from tests.conftest import fixture_text


def titles(offers):
    return [o.title for o in offers]


class TestAmazon:
    def setup_method(self):
        self.offers = Amazon().parse(fixture_text("amazon_search.html"))

    def test_skips_listings_without_price_or_asin(self):
        assert [o.url.rsplit("/", 1)[1] for o in self.offers] == ["B0AAA11111", "B0BBB22222", "B0DDD44444"]

    def test_brand_and_title_headings_are_joined_and_sponsored_prefix_stripped(self):
        zotac = self.offers[0]
        assert zotac.title == "ZOTAC Gaming GeForce RTX 5060 AMP 8GB GDDR7 Graphics Card"
        assert zotac.brand == "ZOTAC"

    def test_price_mrp_rating_and_image(self):
        zotac = self.offers[0]
        assert (zotac.price, zotac.mrp, zotac.rating, zotac.rating_count) == (41990, 52999, 4.6, 1234)
        assert zotac.image == "https://m.media-amazon.com/images/zotac.jpg"
        assert zotac.url == "https://www.amazon.in/dp/B0AAA11111"

    def test_optional_fields_default_to_none(self):
        mouse = self.offers[1]
        assert (mouse.mrp, mouse.rating, mouse.rating_count, mouse.brand) == (None, None, None, None)

    def test_mrp_below_price_is_dropped(self):
        assert self.offers[2].mrp is None

    def test_limit(self):
        assert len(Amazon().parse(fixture_text("amazon_search.html"), limit=2)) == 2

    def test_bot_check_page_is_blocked_not_empty(self):
        with pytest.raises(StoreBlocked):
            Amazon().parse("<html><body>Enter the characters you see. captcha</body></html>")
        with pytest.raises(StoreBlocked):  # the tiny JS challenge page has no results markup at all
            Amazon().parse("<html><script>challenge()</script></html>")

    def test_genuine_no_results_page_is_empty(self):
        page = '<html><body><div id="search"><div class="s-main-slot"></div></div>' + " " * 60_000 + "</body></html>"
        assert Amazon().parse(page) == []


class TestFlipkart:
    def setup_method(self):
        self.offers = Flipkart().parse(fixture_text("flipkart_search.html"))

    def test_dedupes_by_id_and_skips_priceless(self):
        assert len(self.offers) == 2

    def test_full_listing(self):
        gpu = self.offers[0]
        assert gpu.title == "ZOTAC Gaming GeForce RTX 5060 AMP 8 GB GDDR7 Graphics Card"
        assert (gpu.price, gpu.mrp, gpu.rating, gpu.rating_count, gpu.in_stock) == (42490, 52999, 4.4, 321, True)
        assert gpu.url == "https://www.flipkart.com/zotac-rtx-5060/p/itm1?pid=GPUAAA"

    def test_image_placeholders_are_filled_and_forced_to_https(self):
        assert self.offers[0].image == "https://rukminim2.flixcart.com/image/416/416/x.jpeg?q=70"

    def test_short_title_gets_its_subtitle_and_strike_off_price_becomes_mrp(self):
        mouse = self.offers[1]
        assert mouse.title == "Logitech G502 X Wired Gaming Mouse"
        assert (mouse.price, mouse.mrp, mouse.in_stock) == (4799, 5200, False)
        assert mouse.rating is None

    def test_page_without_state_is_an_error(self):
        with pytest.raises(StoreError):
            Flipkart().parse("<html><body>maintenance</body></html>")

    def test_limit(self):
        assert len(Flipkart().parse(fixture_text("flipkart_search.html"), limit=1)) == 1


class TestReliance:
    def setup_method(self):
        self.offers = RelianceDigital().parse(fixture_text("reliance_search.html"))

    def test_only_priced_products(self):
        assert len(self.offers) == 2

    def test_listing(self):
        ps5 = self.offers[0]
        assert ps5.title == "Sony PS5 Standard SA E Chassis Gaming Console"  # whitespace collapsed
        assert ps5.url == "https://www.reliancedigital.in/product/sony-ps5-standard-123"  # tracking query dropped
        assert (ps5.price, ps5.mrp, ps5.rating, ps5.in_stock, ps5.brand) == (49990, 54990, 4.7, True, "Sony")

    def test_url_from_slug_and_unsellable_means_out_of_stock(self):
        pad = self.offers[1]
        assert pad.url == "https://www.reliancedigital.in/product/ps5-dualsense/"
        assert pad.in_stock is False
        assert pad.mrp is None  # marked == effective: no discount to show

    def test_page_without_state_is_an_error(self):
        with pytest.raises(StoreError):
            RelianceDigital().parse("<html></html>")


class TestWooCommerce:
    store = WooStore("shop", "Shop", "https://shop.example", "#fff")

    def setup_method(self):
        import json
        self.offers = self.store.parse(json.loads(fixture_text("woocommerce_products.json")))

    def test_skips_missing_and_unparseable_prices(self):
        assert len(self.offers) == 2

    def test_minor_units_entities_and_brand(self):
        msi = self.offers[0]
        assert msi.title == "MSI RTX 5060 Ventus 2X OC 8GB & GDDR7"
        assert (msi.price, msi.mrp, msi.rating, msi.rating_count, msi.brand) == (59999, 64999, 4.5, 12, "MSI")
        assert msi.image == "https://shop.example/t.jpg"

    def test_variable_product_uses_cheapest_variant(self):
        var = self.offers[1]
        assert (var.price, var.mrp, var.in_stock) == (4500, 9999, False)
        assert (var.rating, var.rating_count, var.image, var.brand) == (None, None, None, None)

    def test_unexpected_payload(self):
        with pytest.raises(StoreError):
            self.store.parse({"code": "rest_no_route"})


class TestShopify:
    store = ShopifyStore("shop", "Shop", "https://shop.example", "#fff")

    def setup_method(self):
        import json
        self.offers = self.store.parse(json.loads(fixture_text("shopify_suggest.json")))

    def test_skips_zero_price(self):
        assert len(self.offers) == 2

    def test_relative_url_is_made_absolute_and_tracking_params_dropped(self):
        ram = self.offers[0]
        assert ram.url == "https://shop.example/products/corsair-vengeance"
        assert ram.title == "Corsair Vengeance DDR5 32GB (2x16GB) 6000MHz"
        assert (ram.price, ram.mrp, ram.in_stock, ram.brand) == (11499, 13999, True, "Corsair")

    def test_absolute_url_kept_and_bad_mrp_dropped(self):
        other = self.offers[1]
        assert other.url == "https://other.example/p/trident"
        assert other.mrp is None  # compare-at price below price
        assert other.brand is None
        assert other.image == "https://cdn.example/trident.jpg"

    def test_unexpected_payload(self):
        with pytest.raises(StoreError):
            self.store.parse({"error": "nope"})


class FakeHttp:
    """Stands in for HttpClient so the fetch half of `search()` can be tested too."""

    def __init__(self, status=200, text="", payload=None, bad_json=False):
        self.resp = SimpleNamespace(status_code=status, text=text, json=self._json)
        self.payload, self.bad_json, self.requests = payload, bad_json, []

    def _json(self):
        if self.bad_json:
            raise ValueError("not json")
        return self.payload

    async def get(self, url, **kw):
        self.requests.append((url, kw))
        return self.resp


class TestFetching:
    async def test_amazon_sends_the_query_and_parses(self):
        http = FakeHttp(text=fixture_text("amazon_search.html"))
        offers = await Amazon().search(http, "rtx 5060")
        assert http.requests[0][1]["params"] == {"k": "rtx 5060"}
        assert len(offers) == 3

    @pytest.mark.parametrize("status", [403, 429])
    async def test_block_statuses(self, status):
        with pytest.raises(StoreBlocked):
            await Flipkart().search(FakeHttp(status=status), "x")

    async def test_server_error_is_a_store_error_not_a_block(self):
        with pytest.raises(StoreError) as exc:
            await Flipkart().search(FakeHttp(status=500), "x")
        assert not isinstance(exc.value, StoreBlocked)

    async def test_amazon_captcha_marker(self):
        with pytest.raises(StoreBlocked):
            await Amazon().search(FakeHttp(text="<html>... validateCaptcha ...</html>"), "x")

    async def test_json_stores_reject_invalid_json(self):
        with pytest.raises(StoreError):
            await WooStore("s", "S", "https://s.example", "#fff").search(FakeHttp(bad_json=True), "x")
        with pytest.raises(StoreError):
            await ShopifyStore("s", "S", "https://s.example", "#fff").search(FakeHttp(bad_json=True), "x")

    async def test_woocommerce_end_to_end(self):
        import json
        http = FakeHttp(payload=json.loads(fixture_text("woocommerce_products.json")))
        offers = await WooStore("s", "S", "https://s.example", "#fff").search(http, "msi", limit=1)
        assert len(offers) == 1
