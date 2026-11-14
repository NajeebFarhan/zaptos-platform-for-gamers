from app.prices.stores.amazon import Amazon
from app.prices.stores.base import Store, StoreBlocked, StoreError
from app.prices.stores.flipkart import Flipkart
from app.prices.stores.mdcomputers import MDComputers
from app.prices.stores.nationalpc import NationalPC
from app.prices.stores.reliance import RelianceDigital
from app.prices.stores.shopify import ShopifyStore
from app.prices.stores.vedant import VedantComputers
from app.prices.stores.woocommerce import WooStore

STORES: list[Store] = [
    Amazon(),
    Flipkart(),
    RelianceDigital(),
    MDComputers(),
    WooStore("primeabgb", "PrimeABGB", "https://www.primeabgb.com", "#e11d48"),
    VedantComputers(),
    WooStore("pcstudio", "PC Studio", "https://www.pcstudio.in", "#0ea5e9"),
    WooStore("ezpz", "EZPZ Solutions", "https://ezpzsolutions.in", "#22c55e"),
    ShopifyStore("elitehubs", "EliteHubs", "https://elitehubs.com", "#a855f7"),
    NationalPC(),
]

STORE_MAP = {s.id: s for s in STORES}

__all__ = ["STORES", "STORE_MAP", "Store", "StoreBlocked", "StoreError"]
