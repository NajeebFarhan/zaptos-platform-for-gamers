import html as _html
import json
import re

_PRICE_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def parse_price(value) -> float | None:
    """'₹1,17,150.00' -> 117150.0 ; handles Indian digit grouping and entities."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    text = _html.unescape(str(value)).replace("\xa0", " ")
    m = _PRICE_RE.search(text)
    if not m:
        return None
    try:
        num = float(m.group(0).replace(",", ""))
    except ValueError:
        return None
    return num if num > 0 else None


def parse_count(value) -> int | None:
    """'1,234 ratings' / '(146)' / '1.2K' -> int."""
    if value is None:
        return None
    text = str(value).strip().upper().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*([KM])?", text)
    if not m:
        return None
    num = float(m.group(1))
    if m.group(2) == "K":
        num *= 1_000
    elif m.group(2) == "M":
        num *= 1_000_000
    n = int(num)
    return n if n > 0 else None


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", _html.unescape(text)).strip()


def extract_json_after(source: str, marker: str):
    """Decode the JSON value that follows e.g. 'window.__INITIAL_STATE__ ='."""
    idx = source.find(marker)
    if idx < 0:
        return None
    idx = source.find("=", idx + len(marker))
    if idx < 0:
        return None
    idx += 1
    while idx < len(source) and source[idx] in " \t\r\n":
        idx += 1
    try:
        value, _ = json.JSONDecoder().raw_decode(source, idx)
        return value
    except json.JSONDecodeError:
        return None
