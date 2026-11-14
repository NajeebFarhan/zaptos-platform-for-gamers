"""Allow-list HTML sanitiser for scraped content.

Everything we render from other sites goes through here: unknown tags are
unwrapped, dangerous ones dropped with their content, and attributes are
reduced to a safe minimum with http(s)-only URLs. (The frontend runs
DOMPurify on top as a second layer.)
"""

from urllib.parse import urljoin, urlparse

from selectolax.lexbor import LexborHTMLParser

ALLOWED = {
    "p", "br", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "b", "strong", "i", "em", "u", "a", "img",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "blockquote", "figure", "figcaption",
    "dl", "dt", "dd", "code", "pre", "span", "div", "small", "sup", "sub", "hr", "kbd",
}
DROP = (
    "script", "style", "noscript", "iframe", "object", "embed", "form", "input", "button", "select",
    "textarea", "svg", "math", "video", "audio", "source", "link", "meta", "template", "canvas", "nav",
    "footer", "header", "aside",
)
ATTRS = {"a": {"href", "title"}, "img": {"src", "alt"}, "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"}}


def _safe_url(value: str | None, base: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.startswith("//"):
        value = "https:" + value
    if value.startswith("/guides/"):
        return value  # our own SPA routes (rewritten wiki links)
    if base:
        value = urljoin(base, value)
    scheme = urlparse(value).scheme.lower()
    return value if scheme in ("http", "https") else None


def sanitize_html(html: str, base_url: str | None = None) -> str:
    tree = LexborHTMLParser(f"<div id='__root'>{html}</div>")
    root = tree.css_first("#__root")
    if root is None:
        return ""
    for sel in DROP:
        for node in root.css(sel):
            node.decompose()

    for node in list(root.traverse(include_text=False)):
        if node is root or node.tag in ("-text", "_text", "-comment", "_comment"):
            continue
        tag = node.tag
        if tag not in ALLOWED:
            node.unwrap()
            continue
        allowed = ATTRS.get(tag, set())
        attrs = dict(node.attributes)
        for name in attrs:
            if name not in allowed:
                del node.attrs[name]
        if tag == "a":
            href = _safe_url(attrs.get("href"), base_url)
            if href:
                node.attrs["href"] = href
            elif "href" in node.attrs:
                del node.attrs["href"]
        elif tag == "img":
            src = _safe_url(attrs.get("src"), base_url)
            if not src or src.startswith("data:"):
                node.decompose()
            else:
                node.attrs["src"] = src
    return root.inner_html or ""
