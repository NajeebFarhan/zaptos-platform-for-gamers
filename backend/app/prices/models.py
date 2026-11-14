from pydantic import BaseModel


class Offer(BaseModel):
    store: str  # store id
    title: str
    url: str
    price: float  # INR
    mrp: float | None = None  # list price / "M.R.P." in INR
    rating: float | None = None  # out of 5
    rating_count: int | None = None
    image: str | None = None
    in_stock: bool | None = None
    brand: str | None = None


class ProductGroup(BaseModel):
    """One product, priced across several stores (the trivago-style row)."""

    id: str
    title: str
    brand: str | None = None
    image: str | None = None
    images: list[str] = []  # fallbacks, best first
    kind: str | None = None  # gpu, console, mouse...
    offers: list[Offer]  # one per store, cheapest first
    best: Offer
    store_count: int
    min_price: float
    max_price: float
    savings: float  # max store price - best price
    savings_pct: float
    mrp: float | None = None
    discount_pct: float | None = None  # best price vs MRP
    rating: float | None = None  # review-count-weighted average across stores
    rating_count: int = 0
    relevance: float = 0
    deal_score: float = 0
