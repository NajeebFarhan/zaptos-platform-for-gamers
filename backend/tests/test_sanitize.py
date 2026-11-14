"""Everything scraped from other sites is rendered in the app, so the sanitiser is a security boundary."""

import pytest

from app.guides.sanitize import sanitize_html


def clean(html, base="https://site.example/a/b"):
    return sanitize_html(html, base_url=base)


class TestDangerousContent:
    @pytest.mark.parametrize("html", [
        "<script>alert(1)</script>",
        "<style>body{display:none}</style>",
        "<iframe src='https://evil.example'></iframe>",
        "<object data='x'></object>",
        "<embed src='x'>",
        "<form action='https://evil.example'><input name=password></form>",
        "<svg onload=alert(1)><circle/></svg>",
        "<math><mi>x</mi></math>",
        "<video src=x onerror=alert(1)></video>",
        "<template><script>1</script></template>",
    ])
    def test_dropped_with_their_content(self, html):
        out = clean(f"<p>keep</p>{html}")
        assert "keep" in out
        for needle in ("script", "alert", "iframe", "evil", "<form", "<svg", "<style", "<object", "<embed", "onerror"):
            assert needle not in out

    def test_script_nested_inside_allowed_markup(self):
        out = clean("<div><p>a<script>steal()</script>b</p></div>")
        assert "steal" not in out
        assert "a" in out and "b" in out

    def test_event_handlers_and_style_are_stripped(self):
        out = clean('<p onclick="evil()" style="position:fixed" class="x" id="y">text</p>')
        assert out == "<p>text</p>"

    @pytest.mark.parametrize("href", [
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "  javascript:alert(1)",
        "java\nscript:alert(1)",
        "vbscript:msgbox(1)",
        "data:text/html,<script>alert(1)</script>",
        "ftp://files.example/x",
        "file:///etc/passwd",
    ])
    def test_unsafe_link_schemes_lose_their_href(self, href):
        out = clean(f'<a href="{href}">click</a>')
        assert "href" not in out
        assert "click" in out
        assert "alert" not in out.lower().replace("&lt;", "")

    def test_unsafe_images_are_removed(self):
        assert "<img" not in clean('<img src="data:image/png;base64,AAAA">')
        assert "<img" not in clean('<img src="javascript:alert(1)">')
        assert "<img" not in clean("<img>")

    def test_only_allowlisted_attributes_survive(self):
        out = clean('<img src="//cdn.example/a.png" alt="pic" onerror="x()" srcset="evil 2x" width=1>')
        assert 'src="https://cdn.example/a.png"' in out
        assert 'alt="pic"' in out
        assert "onerror" not in out and "srcset" not in out and "width" not in out


class TestWellFormedContent:
    def test_keeps_structure_and_text(self):
        html = "<h2>Title</h2><p>Some <b>bold</b> and <em>italic</em></p><ul><li>one</li></ul>"
        assert clean(html) == html

    def test_tables_keep_spans(self):
        out = clean('<table><tr><td colspan="2" style="x">cell</td></tr></table>')
        assert 'colspan="2"' in out and "style" not in out

    def test_unknown_tags_are_unwrapped_not_dropped(self):
        assert clean("<custom-tag>inner <b>text</b></custom-tag>") == "inner <b>text</b>"

    def test_relative_links_are_resolved_against_the_page(self):
        assert 'href="https://site.example/guide/x"' in clean('<a href="/guide/x">g</a>')
        assert 'href="https://site.example/a/rel"' in clean('<a href="rel">g</a>')

    def test_protocol_relative_links_become_https(self):
        assert 'href="https://cdn.example/p"' in clean('<a href="//cdn.example/p">g</a>')

    def test_our_own_guide_routes_pass_through(self):
        assert 'href="/guides/valorant/wiki?title=Jett"' in clean('<a href="/guides/valorant/wiki?title=Jett">Jett</a>')

    def test_empty_input(self):
        assert clean("") == ""
