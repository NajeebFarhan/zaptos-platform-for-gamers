"""Cluster listings from different stores into products (the trivago bit).

Every store words titles differently ("ZOTAC Gaming GeForce RTX 5060 AMP 8GB"
vs "Zotac RTX 5060 AMP 8GB GDDR7 Graphics Card (ZT-B50600F-10M)"), so we
normalise titles, extract model tokens, apply hard "these are definitely
different products" rules (brand, product type, model numbers, Ti/Super/Pro
variants, capacities) and then fuzzy-match what's left.

We deliberately prefer leaving two listings apart over merging different
products: showing a wrong "cheapest" price is worse than an extra row.
"""

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from app.prices.models import Offer, ProductGroup

# ---------------------------------------------------------------- vocab

MULTI_BRANDS = {
    "cooler master": "cooler master", "western digital": "western digital", "ant esports": "ant esports",
    "cosmic byte": "cosmic byte", "lian li": "lian li", "be quiet": "be quiet", "turtle beach": "turtle beach",
    "mad catz": "mad catz", "g skill": "gskill", "tp link": "tp-link", "audio technica": "audio-technica",
}
BRANDS = {
    "asus", "rog", "msi", "gigabyte", "aorus", "zotac", "inno3d", "galax", "palit", "pny", "sapphire", "powercolor",
    "xfx", "asrock", "colorful", "evga", "sony", "microsoft", "nintendo", "logitech", "razer", "corsair", "hyperx",
    "steelseries", "redgear", "zebronics", "kingston", "samsung", "crucial", "wd", "seagate", "lg", "benq", "acer",
    "dell", "hp", "lenovo", "alienware", "nzxt", "deepcool", "thermaltake", "noctua", "arctic", "adata", "xpg",
    "gskill", "aoc", "viewsonic", "8bitdo", "fantech", "glorious", "keychron", "thrustmaster", "fanatec", "jbl",
    "sennheiser", "boat", "portronics", "playstation", "xbox", "antec", "montech", "lexar", "sandisk", "teamgroup",
    "gamesir", "flydigi", "wooting", "ducky", "rapoo", "havit", "evofox", "amkette", "cougar", "fractal", "phanteks",
    "segotep", "frontech", "marvel", "biostar", "acer", "predator", "apple", "valve", "meta", "pico", "honeywell",
}
BRAND_ALIASES = {
    "rog": "asus", "aorus": "gigabyte", "wd": "western digital", "xpg": "adata", "playstation": "sony",
    "xbox": "microsoft", "predator": "acer", "alienware": "dell",
}
CHIP_MAKERS = {"nvidia", "amd", "intel", "geforce", "radeon"}

# product type, checked in order (first hit wins)
KINDS: list[tuple[str, tuple[str, ...]]] = [
    ("laptop", ("laptop", "notebook")),
    ("prebuilt", ("desktop pc", "gaming pc", "mini pc", "nuc", "all in one", "workstation")),
    ("mousepad", ("mouse pad", "mousepad", "mouse mat", "desk mat")),
    ("wheel", ("racing wheel", "steering wheel", "driving force", "racing system")),
    ("controller", ("controller", "gamepad", "game pad", "game controller", "joystick", "dualsense", "dualshock",
                    "joy con", "joycon")),
    ("headset", ("headset", "headphone", "earbuds", "earphone", "iem")),
    ("keyboard", ("keyboard",)),
    ("mouse", ("mouse", "mice")),
    ("monitor", ("monitor",)),
    ("chair", ("gaming chair", "chair")),
    ("console", ("console", "game console", "video game console", "gaming console")),
    ("game", ("game", "games", "video game", "game cd", "game disc")),
    ("cpu", ("processor", "desktop cpu")),
    ("motherboard", ("motherboard", "mainboard")),
    ("cooler", ("cpu cooler", "liquid cooler", "aio cooler", "air cooler", "liquid cooling")),
    ("psu", ("power supply", "smps", "psu")),
    ("case", ("cabinet", "pc case", "mid tower", "full tower")),
    ("ssd", ("ssd", "nvme", "solid state")),
    ("hdd", ("hard drive", "hard disk", "hdd")),
    ("ram", ("ram", "memory module", "desktop memory", "ddr5", "ddr4")),
    ("gpu", ("graphics card", "graphic card", "video card", "gpu")),
]
ACCESSORY_HINTS = ("cover", "skin", "sticker", "stand", "dock", "charging station", "charger", "cable",
                   "adapter", "case for", "pouch", "protector", "heatsink", "grip", "cooling fan")

VARIANT = {"ti", "super", "xt", "xtx", "pro", "max", "mini", "lite", "ultra", "plus", "oled", "x3d", "digital", "gre"}

# Brand product lines. A title naming one of these that the other title lacks is a
# different product, even if every other word matches ("RTX 5060 Gaming OC" vs "RTX 5060 Eagle OC").
LINES = {
    "windforce", "eagle", "aero", "aorus", "ventus", "shadow", "inspire", "trio", "suprim", "expert", "tuf",
    "strix", "prime", "dual", "astral", "proart", "amp", "solid", "trinity", "ichill", "swift", "pulse", "nitro",
    "hellhound", "reaper", "legend", "challenger", "phantom", "taichi", "sakura", "battle", "infinity", "twin",
    "lightspeed", "superlight", "viper", "deathadder", "basilisk", "blackshark", "kraken", "barracuda",
    "arctis", "nova", "vengeance", "dominator", "fury", "beast", "trident", "ripjaws", "flare", "blackwidow",
    "huntsman", "apex", "stinger", "flight", "orbit", "evo", "loq", "legion", "omen", "victus", "nitro", "helios",
    "katana", "cyborg", "thin", "stealth", "raider", "zephyrus", "scar", "vivobook", "ideapad", "rs", "elite",
}
OPPOSITES = [({"wired"}, {"wireless", "lightspeed"})]

NOISE = {
    "gaming", "graphics", "graphic", "card", "gpu", "video", "edition", "with", "for", "and", "the", "of", "in", "new",
    "black", "white", "gray", "grey", "silver", "blue", "red", "green", "pink", "purple", "yellow", "orange", "original",
    "india", "warranty", "years", "year", "yr", "oc", "console", "controller", "wireless", "wired", "rgb", "mechanical",
    "keyboard", "mouse", "headset", "monitor", "laptop", "processor", "desktop", "pc", "game", "games", "by", "to",
    "a", "an", "only", "free", "fast", "high", "performance", "official", "series", "version", "model", "fan",
    "fans", "slim", "standard", "pack", "combo", "bundle", "best", "support", "compatible", "ready", "chipset",
    "nvidia", "amd", "intel", "geforce", "radeon", "technology", "cooling", "design", "inch", "sony",
} | CHIP_MAKERS

SPEC_STRIP = re.compile(
    r"\b(?:pcie|pci e|pci express|gen|dlss|usb|hdmi|dp|displayport|bluetooth|bt|wifi|wi fi|version|v)\s*\d+(?:\.\d+)?\b"
    r"|\b\d+\s*bit\b"
)


def normalise(title: str) -> str:
    t = title.lower()
    t = t.replace("&", " and ").replace("’", "'")
    t = re.sub(r"play\s*station\s*(\d)", r"ps\1", t)
    t = re.sub(r"\bxbox\s+series\s+([xs])\b", r"xbox series\1", t)
    t = re.sub(r"[^a-z0-9.+ ]+", " ", t)  # punctuation -> space (keeps 4.5, +)
    t = re.sub(r"\b(single|dual|triple|twin)\s+fans?\b", " ", t)  # "Dual Fan" descriptor != ASUS "Dual" line
    t = re.sub(r"\b(\d+)\s*g\b", r"\1gb", t)  # MSI's "8G" -> "8gb"
    t = re.sub(r"(\d)\s*(gb|tb|hz|w|mm|ms|dpi)\b", r"\1\2", t)  # "8 gb" -> "8gb"
    # memory kits: "32GB x 2" / "(32GBX1)" / "2 x 16GB" -> "2x32gb" / "1x32gb" / "2x16gb"
    t = re.sub(r"\b(\d+)gb\s*x\s*(\d)\b", r"\2x\1gb", t)
    t = re.sub(r"\b(\d)\s*x\s*(\d+)gb\b", r"\1x\2gb", t)
    t = re.sub(r"\b(rtx|gtx|rx|arc|gt)\s*(\d{3,4})(?:\s*(ti|super|xtx|xt|gre))?\b",
               lambda m: " ".join(x for x in m.groups() if x), t)
    t = re.sub(r"\b(\d{4})(ti|super|xtx|xt)\b", r"\1 \2", t)
    t = SPEC_STRIP.sub(" ", t)
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)
    # a lone letter after a model number is part of it: "G502 X" == "G502X", "Series X"
    t = re.sub(r"\b([a-z]+\d+)\s+([a-z])\b(?!\s*\d)", r"\1\2", t)
    return re.sub(r"\s+", " ", t).strip()


_KIT_RE = re.compile(r"\d+x\d+gb")
_CPU_RE = re.compile(r"\b(ryzen \d|core i\d|i[3579] \d{4,5}|core ultra|i[3579]\b)")
_GPU_RE = re.compile(r"\b(rtx|gtx|rx|arc) \d{3,4}")


DOMINANT_KINDS = {"laptop", "prebuilt"}  # their titles list parts as specs ("…16GB RAM 512GB SSD… Laptop")
DEVICE_KINDS = {"mousepad", "wheel", "controller", "headset", "keyboard", "mouse", "monitor", "chair", "console", "game"}


def detect_kind(norm: str) -> str | None:
    """Product type. Whole systems win outright; otherwise the device word that appears *first*
    wins ("Switch 2 Console … with Joy-Con controllers" is a console), and component words
    (ssd, ram, gpu…) only count when no device word is present."""
    padded = f" {norm} "
    if not any(f" {w} " in padded for w in ("laptop", "notebook")):
        # "Intel Core i5-14400F · RTX 5060 · 16GB DDR5 · 1TB SSD" is a whole PC, not an SSD
        if _CPU_RE.search(norm) and _GPU_RE.search(norm) and re.search(r"\b(ssd|ddr\d|\d+gb ram|ram)\b", norm):
            return "prebuilt"
    hits = []
    for kind, words in KINDS:
        tier = 0 if kind in DOMINANT_KINDS else 1 if kind in DEVICE_KINDS else 2
        for w in words:
            pos = padded.find(f" {w} ")
            if pos >= 0:
                hits.append((tier, pos, -len(w), kind))  # longer phrase wins a tie ("mouse pad" > "mouse")
    return min(hits)[3] if hits else None


def detect_brand(norm: str, hint: str | None = None) -> str | None:
    if hint:
        h = normalise(hint)
        h = MULTI_BRANDS.get(h, h)
        if h and h not in CHIP_MAKERS:
            return BRAND_ALIASES.get(h, h)
    padded = f" {norm} "
    for phrase, brand in MULTI_BRANDS.items():
        if f" {phrase} " in padded:
            return brand
    for tok in norm.split()[:6]:
        if tok in BRANDS:
            return BRAND_ALIASES.get(tok, tok)
    return None


def _shape(tok: str) -> str:
    return re.sub(r"[a-z]+", "a", re.sub(r"\d+", "9", tok))


@dataclass
class Features:
    norm: str
    tokens: set[str]
    model: set[str]  # tokens containing digits (minus capacities)
    early: set[str]  # model tokens within the first words (where real model numbers live)
    caps: set[str]  # capacities like 8gb, 1tb
    variants: set[str]
    words: set[str]  # meaningful alphabetic tokens
    kind: str | None
    brand: str | None
    accessory: bool
    clean: str = field(default="")


def features(title: str, brand_hint: str | None = None) -> Features:
    norm = normalise(title)
    toks = norm.split()
    tokset = set(toks)
    caps = {t for t in tokset if re.fullmatch(r"\d+(gb|tb)", t)}
    # model tokens: 3+ digit numbers (5060, 2116) or letter/digit mixes (9800x3d, i5, ps5, g502)
    model = {
        t for t in tokset
        if t not in caps and (re.fullmatch(r"\d{3,}", t) or (any(c.isdigit() for c in t) and any(c.isalpha() for c in t)))
    }
    early = model & set(toks[:8])
    words = {t for t in tokset if t.isalpha() and len(t) > 1 and t not in NOISE and t not in VARIANT}
    kind = detect_kind(norm)
    brand = detect_brand(norm, brand_hint)
    if brand:
        words -= set(brand.split())
        words -= {k for k, v in BRAND_ALIASES.items() if v == brand}
    accessory = any(h in norm for h in ACCESSORY_HINTS) or bool(re.search(r"\bfor (ps\d|xbox|nintendo|switch)", norm))
    clean = " ".join(t for t in toks if t not in NOISE)
    return Features(norm, tokset, model, early, caps, tokset & VARIANT, words, kind, brand, accessory, clean)


def conflict(a: Features, b: Features) -> bool:
    if a.kind and b.kind and a.kind != b.kind:
        return True
    if a.brand and b.brand and a.brand != b.brand:
        return True
    if a.accessory != b.accessory and not (a.kind and b.kind):
        return True
    if a.variants != b.variants:
        return True
    if a.caps and b.caps and not (a.caps & b.caps):
        return True
    a_kits = {t for t in a.model if _KIT_RE.fullmatch(t)}
    b_kits = {t for t in b.model if _KIT_RE.fullmatch(t)}
    if a_kits and b_kits and a_kits != b_kits:
        return True  # 1x32GB stick vs 2x16GB kit
    only_a, only_b = a.early - b.model, b.early - a.model
    if only_a and only_b:
        shapes_a = {_shape(t) for t in only_a}
        if any(_shape(t) in shapes_a for t in only_b):
            return True  # e.g. 5060 vs 5070, 9800x3d vs 7800x3d
    if a.model and b.model and not (a.model & b.model):
        return True
    for left, right in OPPOSITES:
        if (a.tokens & left and b.tokens & right) or (a.tokens & right and b.tokens & left):
            return True
    # each side names something the other doesn't: Ventus vs Shadow, Eagle vs Aero, AMP vs Twin Edge
    da, db = a.words - b.words, b.words - a.words
    if da and db:
        return True
    if (da | db) & LINES:
        return True
    # one title states a product type and the other doesn't, and the untyped one adds new words
    # ("PS5 Disc Drive" must not join "PS5 Console")
    if bool(a.kind) != bool(b.kind):
        untyped_extra = da if not a.kind else db
        if untyped_extra:
            return True
    return False


def similarity(a: Features, b: Features) -> float:
    if conflict(a, b):
        return 0.0
    score = fuzz.token_set_ratio(a.clean, b.clean)
    if a.model & b.model and any(len(t) >= 6 for t in a.model & b.model):
        score += 12  # shared manufacturer part number
    return score


# ---------------------------------------------------------------- grouping

# MD Computers' image CDN refuses hotlinking, so it goes last
IMAGE_PRIORITY = ["amazon", "flipkart", "reliance", "vedant", "primeabgb", "pcstudio", "elitehubs", "ezpz", "nationalpc", "mdcomputers"]
MATCH_THRESHOLD = 85
SAME_STORE_THRESHOLD = 96


_UPPER_BRANDS = {"amd", "msi", "hp", "lg", "aoc", "nzxt", "pny", "xfx", "jbl", "evga", "adata", "xpg", "asus", "rog"}
_SPECIAL_BRANDS = {"hyperx": "HyperX", "steelseries": "SteelSeries", "inno3d": "INNO3D", "zotac": "ZOTAC",
                   "gigabyte": "GIGABYTE", "tp-link": "TP-Link", "8bitdo": "8BitDo", "boat": "boAt",
                   "deepcool": "DeepCool", "gskill": "G.Skill", "benq": "BenQ", "powercolor": "PowerColor"}


def _display_brand(brand: str | None) -> str | None:
    if not brand:
        return None
    if brand in _SPECIAL_BRANDS:
        return _SPECIAL_BRANDS[brand]
    if brand in _UPPER_BRANDS:
        return brand.upper()
    return brand.title()


def _sane_mrp(o: Offer) -> float | None:
    if o.mrp and o.price < o.mrp <= o.price * 3:
        return o.mrp
    return None


def query_features(query: str) -> tuple[set[str], set[str], str | None]:
    norm = normalise(query)
    toks = set(norm.split())
    digit = {t for t in toks if any(c.isdigit() for c in t)}
    alpha = {t for t in toks if t.isalpha() and t not in {"for", "and", "the", "with"}}
    kind = detect_kind(norm)
    if not kind:
        if re.search(r"\b(rtx|gtx|rx|arc) ?\d{3,4}", norm):
            kind = "gpu"
        elif re.search(r"\b(ryzen|core ultra|core i\d|i[3579] \d{4,5})", norm):
            kind = "cpu"
        elif re.search(r"\b(ps\d|xbox series|switch|steam deck)\b", norm):
            kind = "console"
    return digit, alpha, kind


def is_relevant(query_digit: set[str], query_alpha: set[str], f: Features) -> bool:
    if query_digit and not query_digit <= f.tokens:
        # allow "5060" to match "rtx5060"-style fused tokens
        if not all(any(q in t for t in f.tokens) for q in query_digit):
            return False
    if query_alpha:
        hits = sum(1 for q in query_alpha if q in f.tokens or any(t.startswith(q) for t in f.tokens if len(q) >= 4))
        if hits / len(query_alpha) < 0.6:
            return False
    return True


def build_groups(query: str, offers: list[Offer]) -> list[ProductGroup]:
    q_digit, q_alpha, q_kind = query_features(query)
    feats = [(o, features(o.title, o.brand)) for o in offers if o.price and o.title]
    relevant = [(o, f) for o, f in feats if is_relevant(q_digit, q_alpha, f)]
    if len(relevant) >= 3 or not feats:
        feats = relevant

    # cleaner (shorter) titles first make better cluster seeds
    feats.sort(key=lambda of: len(of[1].norm))
    clusters: list[list[tuple[Offer, Features]]] = []
    for o, f in feats:
        best_i, best_s = -1, 0.0
        for i, members in enumerate(clusters):
            scores = []
            ok = True
            for mo, mf in members:
                s = similarity(f, mf)
                if s == 0.0:
                    ok = False
                    break
                # two listings from one store are usually two SKUs: only merge near-identical titles
                if mo.store == o.store and fuzz.token_sort_ratio(f.clean, mf.clean) < SAME_STORE_THRESHOLD:
                    ok = False
                    break
                scores.append(s)
            if not ok or not scores:
                continue
            s = max(scores)
            if s > best_s:
                best_i, best_s = i, s
        if best_i >= 0 and best_s >= MATCH_THRESHOLD:
            clusters[best_i].append((o, f))
        else:
            clusters.append([(o, f)])

    groups = [_to_group(c, q_digit, q_alpha, q_kind, query) for c in clusters]
    groups.sort(key=lambda g: (-g.relevance, g.min_price))
    return groups


def _to_group(members, q_digit, q_alpha, q_kind, query) -> ProductGroup:
    # cheapest in-stock offer per store
    per_store: dict[str, Offer] = {}
    for o, _ in members:
        cur = per_store.get(o.store)
        rank = (o.in_stock is False, o.price)
        if cur is None or rank < (cur.in_stock is False, cur.price):
            per_store[o.store] = o
    offers = sorted(per_store.values(), key=lambda o: (o.in_stock is False, o.price))
    best = offers[0]
    # compare against what you can actually buy; fall back to everything if nothing is in stock
    prices = [o.price for o in offers if o.in_stock is not False] or [o.price for o in offers]

    titled = [o for o, f in members if len(f.norm.split()) >= 4] or [o for o, _ in members]
    title = min(titled, key=lambda o: len(o.title)).title

    # ordered fallbacks: the UI tries the next one if a store blocks hotlinking
    rank = {sid: i for i, sid in enumerate(IMAGE_PRIORITY)}
    images = list(dict.fromkeys(
        o.image for o in sorted(per_store.values(), key=lambda o: rank.get(o.store, 99)) if o.image
    ))
    image = images[0] if images else None

    brands = Counter(f.brand for _, f in members if f.brand)
    kinds = Counter(f.kind for _, f in members if f.kind)
    brand = brands.most_common(1)[0][0] if brands else None
    if not brand:  # CPUs: "AMD Ryzen 7..." — chipmakers are ignored for matching but fine for display
        brand = next((t for t in members[0][1].norm.split()[:3] if t in {"amd", "intel", "nvidia"}), None)
    kind = kinds.most_common(1)[0][0] if kinds else None
    accessory = any(f.accessory for _, f in members)

    # review-count-weighted rating across stores (stores without counts weigh 1)
    rated = [(o.rating, o.rating_count or 1) for o in offers if o.rating]
    total = sum(w for _, w in rated)
    rating = round(sum(r * w for r, w in rated) / total, 2) if rated else None
    rating_count = sum(o.rating_count or 0 for o in offers)

    mrps = [m for m in (_sane_mrp(o) for o in offers) if m]
    mrp = max(mrps) if mrps else None
    discount = round((mrp - best.price) / mrp * 100, 1) if mrp else None
    max_price = max(prices)
    savings = max_price - best.price
    savings_pct = round(savings / max_price * 100, 1) if max_price else 0.0

    # relevance: how well the product answers the query
    ref = members[0][1]
    rel = fuzz.token_set_ratio(normalise(query), ref.norm)
    if q_kind:
        if kind == q_kind:
            rel += 8
        elif kind:
            rel -= 18
        else:
            rel -= 6
    if accessory and not any(h in normalise(query) for h in ACCESSORY_HINTS):
        rel -= 20
    q_norm = set(normalise(query).split())
    rel -= 15 * len(ref.variants - q_norm)  # asked for "5060", this is a "5060 Ti"
    rel += 3 * min(len(offers), 4)
    rel += 2 * math.log10(rating_count + 1)

    deal = 0.0
    if best.price >= 500 and best.in_stock is not False:
        deal = min(discount or 0, 70) * 0.6 + savings_pct * (1.0 if len(offers) > 1 else 0) + ((rating or 3.5) - 3.5) * 6

    gid = hashlib.md5("|".join(sorted(o.url for o in offers)).encode()).hexdigest()[:12]
    return ProductGroup(
        id=gid,
        title=title,
        brand=_display_brand(brand),
        image=image,
        images=images[:4],
        kind="accessory" if accessory else kind,
        offers=offers,
        best=best,
        store_count=len(offers),
        min_price=best.price,
        max_price=max_price,
        savings=savings,
        savings_pct=savings_pct,
        mrp=mrp,
        discount_pct=discount,
        rating=rating,
        rating_count=rating_count,
        relevance=round(rel, 1),
        deal_score=round(deal, 1),
    )
