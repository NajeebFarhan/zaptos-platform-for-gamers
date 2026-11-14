import pytest

from app.core.text import clean, extract_json_after, parse_count, parse_price


@pytest.mark.parametrize("raw, expected", [
    ("₹1,17,150.00", 117150.0),  # Indian digit grouping
    ("₹1,299.50", 1299.5),
    ("Rs. 2,499", 2499.0),
    ("&#8377;4,999", 4999.0),  # HTML entity for ₹
    ("\xa0₹ 899", 899.0),
    (1999, 1999.0),
    (49.5, 49.5),
    ("1499", 1499.0),
])
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "free", "Currently unavailable", 0, -5, "0", "₹0.00"])
def test_parse_price_rejects_non_prices(raw):
    assert parse_price(raw) is None


@pytest.mark.parametrize("raw, expected", [
    ("1,234 ratings", 1234),
    ("(146)", 146),
    ("1.2K", 1200),
    ("3M ratings", 3_000_000),
    ("87", 87),
])
def test_parse_count(raw, expected):
    assert parse_count(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "no ratings yet", "0", "(0)"])
def test_parse_count_rejects_empty(raw):
    assert parse_count(raw) is None


def test_clean_collapses_whitespace_and_unescapes():
    assert clean("  Zotac \n RTX&nbsp;5060 &amp; more\t ") == "Zotac RTX 5060 & more"
    assert clean(None) == ""
    assert clean("") == ""


class TestExtractJson:
    def test_reads_value_after_marker_and_ignores_what_follows(self):
        src = 'junk; window.__S__ = {"a": [1, 2], "b": {"c": "}"}}; window.other = 1;'
        assert extract_json_after(src, "window.__S__") == {"a": [1, 2], "b": {"c": "}"}}

    def test_tolerates_whitespace_around_equals(self):
        assert extract_json_after("window.__S__\n=\n  [1,2]", "window.__S__") == [1, 2]

    @pytest.mark.parametrize("src", [
        "nothing here",
        "window.__S__ without assignment",
        'window.__S__ = {"broken": ',
        "window.__S__ = not json",
    ])
    def test_returns_none_instead_of_raising(self, src):
        assert extract_json_after(src, "window.__S__") is None
