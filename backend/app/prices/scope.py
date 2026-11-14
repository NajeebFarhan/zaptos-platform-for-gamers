"""Keep marketplace results to PC / gaming gear.

Amazon, Flipkart and Reliance Digital sell everything, so a search like "samsung 990 pro"
or "rtx 5060" also returns phones, mobile skins, TVs and soundbars that share a word or a
number with the query. PC-specialist stores only stock PC gear and are not filtered.

A listing is in scope when nothing marks it as clearly non-PC (phones and their
accessories, TVs, appliances, apparel, bags) and something marks it as PC / gaming:
a recognised product type, or PC / gaming vocabulary.
"""

import re

from app.prices.matcher import DEVICE_KINDS, DOMINANT_KINDS, detect_kind, normalise

# ---------------------------------------------------------------- clearly not PC / gaming

# Phone spec lines, matched on the raw title (normalise() turns "5G" into "5gb").
_PHONE_SPEC = re.compile(
    r"\b(?:5g|4g|lte|volte)\b.*\d\s*gb\b"  # "Galaxy A56 5G (Blue, 8GB, 128GB)"
    r"|\d\s*gb\s*ram\b.*\b(?:storage|rom)\b"  # "(Black, 4GB RAM, 64GB Storage)"
    r"|\b(?:storage|rom)\b.*\d\s*gb\s*ram\b"
    r"|\(\s*[a-z][a-z ]+,\s*\d+\s*gb\s*\)\s*\(?\s*\d+\s*gb\s*ram"  # "(Green, 64 GB) 4 GB RAM"
    r"|\bsmart\s*phone\b|\bmobile\s+phone\b|\bfeature\s+phone\b"
    r"|\d+\s*mp\b[^|]*\bcamera|\bcamera\b[^|]*\d+\s*mp\b"
)
# PC words that make a phone-looking spec line a PC after all ("16GB RAM, 512GB Storage" laptops)
_PC_SYSTEM = re.compile(r"\b(?:laptop|notebook|chromebook|desktop|pc|windows|macbook|ssd|ddr\d|nvme|graphics|gpu|"
                        r"router|webcam)\b")

_PHONE_ACCESSORY = re.compile(
    r"\b(?:mobile|phone|smartphone|iphone)(?: \w+){0,3} "
    r"(?:skins?|covers?|cases?|film|guard|protector|holder|stand|mount|charger|lens)\b"
    r"|\bback (?:cover|case|panel)\b|\bflip cover\b|\bscreen (?:guard|protector)\b"
    r"|\btempered glass (?:for|screen)\b|\b(?:edge to edge|full screen) tempered\b"
    r"|\bcharger for mobile\b"
)
# a screen protector or holder for a console / handheld / laptop is still gaming gear
_GAMING_PLATFORM = re.compile(r"\b(?:ps5|ps4|xbox|nintendo|switch|steam deck|rog ally|legion go|laptop|monitor|"
                              r"controller)\b")

_TABLET = re.compile(r"\b(?:tablet|ipad|galaxy tab)\b")
_DRAWING_TABLET = re.compile(r"\b(?:drawing|graphics|graphic|pen|wacom|huion|xp pen)\b")

_NOT_PC = re.compile(
    # TVs and home audio
    r"\b(?:smart|led|qled|oled|android|google|tizen|webos|fire|mini led) tv\b|\btelevision\b"
    r"|\bhome theat(?:re|er)\b|\bparty speaker\b"
    # appliances and personal care
    r"|\brefrigerator\b|\bfridge\b|\bwashing machine\b|\bair conditioner\b|\b(?:split|window) ac\b"
    r"|\b(?:room|desert|tower) cooler\b|\bmicrowave\b|\bmixer grinder\b|\bjuicer\b|\bgeyser\b|\bwater heater\b"
    r"|\b(?:water|air) purifier\b|\bvacuum cleaner\b|\btrimmer\b|\bshaver\b|\bhair (?:dryer|straightener)\b"
    # wearables and phone power
    r"|\bsmart ?watch\b|\b(?:fitness|smart) band\b|\bpower ?bank\b|\b(?:wall|car) charger\b"
    # apparel and bags
    r"|\bt ?shirts?\b|\bhoodies?\b|\bsweatshirts?\b|\bjoggers\b|\bsneakers\b|\bshoes\b"
    r"|\bbackpacks?\b|\b(?:laptop|messenger|sling|duffel|travel|waterproof) bag\b|\bluggage\b"
)

# ---------------------------------------------------------------- clearly PC / gaming

_PC_VOCAB = re.compile(
    r"\b(?:gaming|gamer|gamers|esports?|e sports)\b"
    r"|\b(?:pc|computer|desktop|laptop|notebook|chromebook|macbook)\b"
    r"|\b(?:ps5|ps4|ps3|playstation|xbox|nintendo|switch 2|steam deck|rog ally|legion go|psvr2?)\b"
    r"|\b(?:vr|virtual reality|meta quest|oculus)\b"
    r"|\b(?:ryzen|intel core|core i[3579]|core ultra|geforce|radeon|rtx|gtx)\b|\b(?:cpu|gpu|graphics)\b"
    r"|\b(?:ssd|hdd|nvme|m 2|sata|enclosure|pen ?drive|flash drive|usb drive)\b"
    r"|\b(?:webcam|web camera|microphone|capture card|stream deck|elgato)\b"
    r"|\b(?:router|bluetooth (?:adapter|dongle)|lan card|network (?:card|adapter)|ethernet|usb hub|docking station|kvm)\b"
    # Wi-Fi adapters; Flipkart often lists them as just "150Mbps 802.11N USB Adapter"
    r"|\bwi ?fi (?:usb|adapter|card|dongle|receiver|extender|repeater|range extender|mesh)\b"
    r"|\busb (?:wi ?fi|wireless)\b|\bwireless (?:n )?(?:usb|adapter|card|lan)\b|\busb adapter\b"
    r"|\b\d+ ?mbps\b|\b802\.?11|\bpcie? (?:card|wireless|wirless|wi ?fi|adapter)\b"
    r"|\bretro (?:gaming|games?|console|handheld)\b|\bemulators?\b|\bgame ?stick\b"
    r"|\bthermal (?:paste|compound|pad|grease)\b|\b(?:case|cpu|cabinet|argb|rgb|pwm) fans?\b|\bfans? (?:kit|pack)\b"
    r"|\bkeycaps?\b|\b(?:hdmi|displayport|dp) cable\b|\bheadphones?\b|\bearphones?\b"
)

_SPEAKER = re.compile(r"\b(?:speakers?|soundbar|sound bar|subwoofer)\b")
_PC_SPEAKER = re.compile(r"\b(?:computer|pc|desktop|gaming|multimedia)\b")

# product types whose own name is the strongest signal; the phone rules don't apply to them
# ("Gaming Controller with Phone Holder", "Headset for PC, PS5 & Mobile")
_TRUSTED_KINDS = DEVICE_KINDS | DOMINANT_KINDS


def in_scope(title: str) -> bool:
    """True when a marketplace listing is PC / gaming hardware (or a game / gaming accessory)."""
    raw = title.lower()
    norm = normalise(title)
    kind = detect_kind(norm)

    # A controller or headset "compatible with Android TV" is still a controller. Laptops are not
    # exempt: "Laptop Backpack" is detected as a laptop.
    if kind not in DEVICE_KINDS and _NOT_PC.search(norm):
        return False
    if kind not in _TRUSTED_KINDS:
        if _PHONE_SPEC.search(raw) and not _PC_SYSTEM.search(norm):
            return False
        if _PHONE_ACCESSORY.search(norm) and not _GAMING_PLATFORM.search(norm):
            return False
        if _TABLET.search(norm) and not _DRAWING_TABLET.search(norm):
            return False

    # Bluetooth / party speakers and soundbars are home audio; computer speakers are PC gear.
    # A stray "Laptop" ("Soundbar for Phone/Laptop") doesn't make a speaker a laptop.
    if kind in (None, "laptop") and _SPEAKER.search(norm):
        return bool(_PC_SPEAKER.search(norm))

    return kind is not None or bool(_PC_VOCAB.search(norm))


def filter_offers(offers: list[dict]) -> list[dict]:
    return [o for o in offers if in_scope(o.get("title") or "")]
