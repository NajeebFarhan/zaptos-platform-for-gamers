"""Things the backend and the frontend must agree on, checked from the backend's side.

If one fails, a change on one side wasn't mirrored on the other (a new product kind with no label,
a new category that would render a generic icon).
"""

import re
from pathlib import Path

import pytest

from app.prices.catalog import CATEGORIES
from app.prices.matcher import KINDS

FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src"

pytestmark = pytest.mark.skipif(not FRONTEND.is_dir(), reason="frontend sources not present (e.g. inside the API image)")


def object_keys(file: str, name: str) -> set[str]:
    """Keys of `const NAME = { key: ..., "key": ... };` in a frontend source file."""
    src = (FRONTEND / file).read_text(encoding="utf-8")
    block = re.search(rf"{name}\s*=\s*\{{(.*?)\n?\}};", src, re.S)
    assert block, f"could not find {name} in {file}"
    return set(re.findall(r"(?:^|[,{\s])([A-Za-z_]\w*)\s*:", block.group(1)))


def test_every_product_kind_the_backend_can_emit_has_a_label():
    emitted = {kind for kind, _ in KINDS} | {"accessory"}  # build_groups relabels accessories
    labelled = object_keys("lib/format.js", "KIND_LABELS")
    assert emitted - labelled == set(), "backend kinds with no label in frontend/src/lib/format.js"
    assert labelled - emitted == set(), "labels in format.js for kinds the backend never emits"


def test_every_category_has_its_own_icon():
    icons = object_keys("components/CategoryIcon.jsx", "ICONS")
    assert {c["id"] for c in CATEGORIES} - icons == set(), "categories that would fall back to the generic icon"


def test_category_ids_are_unique_and_have_a_query():
    ids = [c["id"] for c in CATEGORIES]
    assert len(ids) == len(set(ids))
    assert all(c["query"].strip() and c["chips"] for c in CATEGORIES)
