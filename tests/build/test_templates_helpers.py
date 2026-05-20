"""Hermetic tests for ``tools/build/templates/_helpers.py``.

Targets the gaps left by the template tests (landing/category/
regulation): the mini Markdown renderer, JSON-LD builders
(TechArticle, HowTo, CollectionPage, WebSite), criticality /
difficulty / wave labels, truncate, first_paragraph, split_steps,
and asset_url path-prefix logic.
"""

from __future__ import annotations

import json

import pytest

from build.templates import _helpers as h


# ---------------------------------------------------------------------------
# escape / attr — primitives that the templates lean on heavily
# ---------------------------------------------------------------------------


class TestEscapeAndAttr:
    def test_escape_none_returns_empty(self):
        assert h.escape(None) == ""

    def test_escape_non_string_coerced_via_str(self):
        assert h.escape(42) == "42"
        assert h.escape(3.14) == "3.14"
        assert h.escape(True) == "True"

    def test_escape_quotes_and_brackets(self):
        assert h.escape('<b>"x"</b>') == "&lt;b&gt;&quot;x&quot;&lt;/b&gt;"

    def test_attr_delegates_to_escape(self):
        assert h.attr(None) == ""
        assert h.attr("&'\"<>") == h.escape("&'\"<>")


# ---------------------------------------------------------------------------
# slug — covers branch 115->111 (last_dash already true)
# ---------------------------------------------------------------------------


class TestSlug:
    def test_basic_slug(self):
        assert h.slug("Network Monitoring") == "network-monitoring"

    def test_empty_returns_default(self):
        assert h.slug("") == "category"

    def test_consecutive_non_alnum_collapses_to_single_dash(self):
        """Branch ``elif not last_dash`` false arm — second non-alnum
        char doesn't emit a second dash."""
        assert h.slug("foo!!!bar") == "foo-bar"

    def test_trailing_non_alnum_stripped(self):
        assert h.slug("foo bar!!") == "foo-bar"

    def test_all_non_alnum_returns_default(self):
        """If every char strips out, the ``s or "category"`` final
        fallback fires."""
        assert h.slug("!!!") == "category"

    def test_leading_and_trailing_dashes_stripped(self):
        assert h.slug(" __foo__ ") == "foo"

    def test_uppercase_normalised(self):
        assert h.slug("HELLO") == "hello"


# ---------------------------------------------------------------------------
# sort_key
# ---------------------------------------------------------------------------


class TestSortKey:
    def test_numeric_chunks_sort_naturally(self):
        keys = sorted(["1.10.1", "1.2.1", "1.1.1"], key=h.sort_key)
        assert keys == ["1.1.1", "1.2.1", "1.10.1"]

    def test_alpha_chunks_sort_alphabetically_after_numeric(self):
        """Tuple shape ``(0, int)`` < ``(1, str)`` so numerics win."""
        keys = sorted(["foo", "1.2"], key=h.sort_key)
        assert keys == ["1.2", "foo"]

    def test_none_and_empty_handled(self):
        assert h.sort_key(None) == ((1, ""),)
        assert h.sort_key("") == ((1, ""),)


# ---------------------------------------------------------------------------
# render_markdown — the mini Markdown renderer
# ---------------------------------------------------------------------------


class TestRenderMarkdown:
    def test_empty_returns_empty(self):
        """Covers line 184/185 short-circuit."""
        assert h.render_markdown("") == ""
        assert h.render_markdown(None) == ""

    def test_emits_single_paragraph(self):
        out = h.render_markdown("Hello world.")
        assert out == "<p>Hello world.</p>"

    def test_paragraph_with_only_blank_lines_flushes_nothing(self):
        """``_flush_para`` ``if text:`` false arm — buffer has only
        blank strings."""
        out = h.render_markdown("   \n   ")
        assert out == ""

    def test_two_paragraphs_separated_by_blank_line(self):
        out = h.render_markdown("First.\n\nSecond.")
        assert "<p>First.</p>" in out
        assert "<p>Second.</p>" in out

    def test_fenced_code_block_with_language(self):
        """Covers fence-open + code-line accumulation + fence-close
        (lines 211-227)."""
        md = "```spl\nindex=foo | head 1\n```"
        out = h.render_markdown(md)
        assert '<pre><code class="lang-spl">' in out
        assert "index=foo | head 1" in out
        assert "</code></pre>" in out

    def test_fenced_code_block_without_language(self):
        out = h.render_markdown("```\nplain\n```")
        # No class attribute when no language.
        assert "<pre><code>plain</code></pre>" in out

    def test_fence_inside_paragraph_flushes_buffers(self):
        """Open fence after a paragraph must flush the paragraph and
        any open list — covers the ``_flush_para()`` + ``_flush_list()``
        calls at the top of the fence branch."""
        md = "para line\n\n- item\n```\ncode\n```\nafter"
        out = h.render_markdown(md)
        assert "<p>para line</p>" in out
        assert "<ul>" in out and "<li>item</li>" in out
        assert "<pre><code>code</code></pre>" in out
        assert "<p>after</p>" in out

    def test_bullet_list(self):
        out = h.render_markdown("- first\n- second")
        assert "<ul>" in out and "</ul>" in out
        assert "<li>first</li>" in out
        assert "<li>second</li>" in out

    def test_numbered_list(self):
        out = h.render_markdown("1. one\n2. two")
        assert "<ol>" in out and "</ol>" in out

    def test_list_kind_switch_closes_previous(self):
        """``if in_list_kind and in_list_kind != kind: _flush_list()``
        — UL followed by OL closes the UL before opening the OL."""
        out = h.render_markdown("- a\n- b\n1. one\n2. two")
        # Both lists present and properly closed.
        assert out.count("<ul>") == 1
        assert out.count("</ul>") == 1
        assert out.count("<ol>") == 1
        assert out.count("</ol>") == 1
        # Order: UL first, OL second.
        assert out.find("<ul>") < out.find("<ol>")

    def test_paragraph_after_list_closes_list(self):
        """``if in_list_kind: _flush_list()`` — a non-list line
        after a list flushes the list."""
        out = h.render_markdown("- item\nparagraph")
        assert "<ul>" in out and "</ul>" in out
        assert "<p>paragraph</p>" in out
        # Order: list closes before paragraph.
        assert out.find("</ul>") < out.find("<p>paragraph</p>")

    def test_inline_link_with_safe_scheme(self):
        out = h.render_markdown("Visit [Splunk](https://splunk.com).")
        assert 'href="https://splunk.com"' in out
        assert 'target="_blank"' in out
        assert 'rel="noopener noreferrer"' in out

    def test_link_with_unsafe_scheme_rejected_to_plain_text(self):
        """``javascript:`` is not in ``_SAFE_LINK_SCHEMES`` — covers
        line 274 (return escape(label))."""
        out = h.render_markdown("Click [here](javascript:alert(1)).")
        assert "<a " not in out
        assert "here" in out

    def test_link_with_relative_scheme(self):
        out = h.render_markdown("[Foo](/path).")
        assert 'href="/path"' in out
        # Relative links don't get noopener target.
        assert "target=" not in out

    def test_link_with_data_scheme_rejected(self):
        out = h.render_markdown("[x](data:text/html,<x>)")
        assert "<a " not in out

    def test_inline_code(self):
        out = h.render_markdown("Run `index=foo`.")
        assert "<code>index=foo</code>" in out

    def test_bold_and_italic(self):
        out = h.render_markdown("**bold** and *italic*.")
        assert "<strong>bold</strong>" in out
        assert "<em>italic</em>" in out

    def test_autolink(self):
        out = h.render_markdown("Visit https://splunk.com today.")
        assert 'href="https://splunk.com"' in out

    def test_dangerous_chars_in_link_label_are_escaped(self):
        out = h.render_markdown("[<x>](https://x.com)")
        assert "&lt;x&gt;" in out
        assert "<x>" not in out


# ---------------------------------------------------------------------------
# jsonld_breadcrumb / jsonld_techarticle / jsonld_howto /
# jsonld_collection_page / jsonld_website / jsonld_script
# ---------------------------------------------------------------------------


class TestJsonldBuilders:
    def test_breadcrumb_positions_are_1_indexed(self):
        out = h.jsonld_breadcrumb([("Home", "/"), ("X", "/x/")])
        assert out["@type"] == "BreadcrumbList"
        positions = [it["position"] for it in out["itemListElement"]]
        assert positions == [1, 2]

    def test_techarticle_minimal_payload(self):
        out = h.jsonld_techarticle(
            headline="X", description="Y", url="https://x/",
            site_name="Site", site_url="https://site/",
            date_modified="2026-05-20",
        )
        assert out["@type"] == "TechArticle"
        assert out["dateModified"] == "2026-05-20"
        assert "keywords" not in out
        assert "hasPart" not in out

    def test_techarticle_with_keywords_emits_csv(self):
        out = h.jsonld_techarticle(
            headline="X", description="Y", url="/", site_name="S", site_url="/",
            date_modified="2026-05-20",
            keywords=["a", "b", "c"],
        )
        assert out["keywords"] == "a, b, c"

    def test_techarticle_with_code_sample_emits_has_part(self):
        """Covers branch 366->368 (the ``if code_sample:`` arm)."""
        out = h.jsonld_techarticle(
            headline="X", description="Y", url="/",
            site_name="S", site_url="/",
            date_modified="2026-05-20",
            code_sample="index=foo | head 1",
            code_sample_language="spl",
        )
        assert out["proficiencyLevel"] == "Expert"
        assert out["hasPart"]["@type"] == "SoftwareSourceCode"
        assert out["hasPart"]["programmingLanguage"] == "spl"
        assert out["hasPart"]["text"] == "index=foo | head 1"

    def test_howto_returns_none_for_zero_or_one_step(self):
        assert h.jsonld_howto(name="x", description="y", steps=[]) is None
        assert h.jsonld_howto(name="x", description="y",
                              steps=[("s1", "t1")]) is None

    def test_howto_emits_steps_with_positions(self):
        out = h.jsonld_howto(
            name="X", description="Y",
            steps=[("step 1", "text 1"), ("step 2", "text 2")],
        )
        assert out["@type"] == "HowTo"
        assert out["step"][0]["position"] == 1
        assert out["step"][1]["position"] == 2
        assert "totalTime" not in out

    def test_howto_with_total_time_iso(self):
        out = h.jsonld_howto(
            name="X", description="Y",
            steps=[("a", "t"), ("b", "t")],
            total_time_iso="PT15M",
        )
        assert out["totalTime"] == "PT15M"

    def test_collection_page_member_urls_pass_through(self):
        out = h.jsonld_collection_page(
            name="X", description="Y", url="/",
            site_name="S", site_url="/",
            member_urls=["/a/", "/b/"],
            date_modified="2026-05-20",
        )
        assert out["mainEntity"]["numberOfItems"] == 2
        assert [el["url"] for el in out["mainEntity"]["itemListElement"]] == [
            "/a/", "/b/"
        ]

    def test_website_payload(self):
        out = h.jsonld_website(
            name="X", description="Y", url="https://example.com",
        )
        assert out["@type"] == "WebSite"
        assert out["alternateName"] == "Splunk UCs"
        assert "potentialAction" in out

    def test_script_emits_one_script_per_payload(self):
        payloads = [
            {"@context": "x", "@type": "T1"},
            {"@context": "x", "@type": "T2"},
        ]
        out = h.jsonld_script(*payloads)
        assert out.count('<script type="application/ld+json">') == 2

    def test_script_skips_empty_payloads(self):
        out = h.jsonld_script({}, {"@type": "T"}, None)
        assert out.count('<script type="application/ld+json">') == 1

    def test_script_escapes_dangerous_closing_tag(self):
        """The defensive ``body.replace("</", "<\\/")`` covers the case
        where a literal ``</`` ends up in any string value (e.g. an
        embedded ``</script>`` snippet)."""
        out = h.jsonld_script({"@type": "T", "x": "</script>"})
        assert "</script><" not in out.split("<script", 1)[1].split(">", 1)[1]
        assert "<\\/script>" in out


# ---------------------------------------------------------------------------
# criticality_label / difficulty_label / wave_label
# ---------------------------------------------------------------------------


class TestLabels:
    def test_criticality_known_keys(self):
        for value, (label, mod) in {
            "critical": ("Critical", "crit"),
            "high": ("High", "high"),
            "medium": ("Medium", "med"),
            "low": ("Low", "low"),
        }.items():
            assert h.criticality_label(value) == (label, mod)

    def test_criticality_unknown_falls_back_to_value_and_unk(self):
        assert h.criticality_label("weird") == ("weird", "unk")

    def test_criticality_empty_falls_back_to_em_dash(self):
        assert h.criticality_label(None) == ("—", "unk")
        assert h.criticality_label("") == ("—", "unk")

    def test_difficulty_known_keys(self):
        for value, (label, mod) in {
            "beginner": ("Beginner", "beg"),
            "intermediate": ("Intermediate", "int"),
            "advanced": ("Advanced", "adv"),
            "expert": ("Expert", "exp"),
        }.items():
            assert h.difficulty_label(value) == (label, mod)

    def test_difficulty_unknown_falls_back_to_value(self):
        assert h.difficulty_label("ninja") == ("ninja", "unk")
        assert h.difficulty_label(None) == ("—", "unk")

    def test_wave_known_keys(self):
        assert h.wave_label("crawl") == ("Crawl", "crawl")
        assert h.wave_label("walk") == ("Walk", "walk")
        assert h.wave_label("run") == ("Run", "run")

    def test_wave_returns_none_for_empty_or_none(self):
        assert h.wave_label(None) is None
        assert h.wave_label("") is None

    def test_wave_returns_none_for_unknown(self):
        """Dict lookup miss returns ``None`` (the dict default)."""
        assert h.wave_label("dash") is None


# ---------------------------------------------------------------------------
# truncate / first_paragraph
# ---------------------------------------------------------------------------


class TestTruncate:
    def test_returns_empty_for_none(self):
        """Covers line 557 (``if text is None: return ""``)."""
        assert h.truncate(None, 100) == ""

    def test_passes_through_when_under_limit(self):
        assert h.truncate("short", 100) == "short"

    def test_truncates_with_ellipsis_when_over_limit(self):
        out = h.truncate("hello world", 6)
        # n=6 → keep first 5 chars + "…"
        assert out == "hello…"
        assert len(out) == 6

    def test_rstrips_before_ellipsis(self):
        # "hello   world", n=8 → first 7 chars = "hello  ", rstrip => "hello"
        out = h.truncate("hello   world", 8)
        assert out == "hello…"

    def test_coerces_non_string_input(self):
        assert h.truncate(12345, 3) == "12…"


class TestFirstParagraph:
    def test_returns_empty_for_blank(self):
        """Covers lines 566/567."""
        assert h.first_paragraph("") == ""
        assert h.first_paragraph(None) == ""

    def test_takes_first_paragraph_only(self):
        out = h.first_paragraph("para 1\n\npara 2")
        assert out == "para 1"

    def test_strips_inline_code(self):
        assert h.first_paragraph("Use `index=foo`.") == "Use index=foo."

    def test_strips_bold(self):
        assert h.first_paragraph("Use **foo**.") == "Use foo."

    def test_strips_italic(self):
        assert h.first_paragraph("Use *foo*.") == "Use foo."

    def test_strips_link_keeping_label(self):
        assert h.first_paragraph("See [docs](https://x).") == "See docs."

    def test_collapses_whitespace(self):
        assert h.first_paragraph("a\n\tb   c") == "a b c"

    def test_truncates_to_max_chars(self):
        out = h.first_paragraph("x" * 500, max_chars=80)
        assert len(out) <= 80


# ---------------------------------------------------------------------------
# split_steps
# ---------------------------------------------------------------------------


class TestSplitSteps:
    def test_empty_md_returns_empty_list(self):
        """Covers line 585 (``if not md: return []``)."""
        assert h.split_steps("") == []
        assert h.split_steps(None) == []

    def test_no_step_header_returns_empty_list(self):
        """``if not steps: return []`` (line 605/606)."""
        assert h.split_steps("Just a paragraph.\nAnother line.") == []

    def test_recognises_step_with_em_dash(self):
        md = "Step 1 — Foo\nbody one\n\nStep 2 — Bar\nbody two"
        out = h.split_steps(md)
        assert len(out) == 2
        assert out[0][0] == "Foo"
        assert "body one" in out[0][1]
        assert out[1][0] == "Bar"

    def test_recognises_step_with_period(self):
        md = "Step 1. Foo\nbody"
        out = h.split_steps(md)
        # Single-step input still produces one step (the buffer flush at
        # the end catches it).
        assert out == [("Foo", "body")]

    def test_falls_back_to_step_number_when_name_blank(self):
        """``current_name = (m.group(2).strip() or f"Step {m.group(1)}")``."""
        md = "Step 1.\nbody one\nStep 2.\nbody two"
        out = h.split_steps(md)
        assert out[0][0] == "Step 1"
        assert out[1][0] == "Step 2"

    def test_drops_steps_with_empty_body(self):
        """``[(n, t) for ... if t]`` removes empty-body steps."""
        md = "Step 1 — A\n\nStep 2 — B\nbody"
        out = h.split_steps(md)
        # Step 1 has no body, only Step 2 survives.
        assert out == [("B", "body")]

    def test_strips_fenced_spl_to_placeholder(self):
        """Covers the cleanup re.sub for ```\\n...\\n```."""
        md = "Step 1 — Run\n```\nindex=foo\n```\nthen check"
        out = h.split_steps(md)
        text = out[0][1]
        assert "[SPL]" in text
        assert "index=foo" not in text

    def test_strips_inline_backticks(self):
        md = "Step 1 — Run\nuse `index=foo` here"
        out = h.split_steps(md)
        assert "`" not in out[0][1]

    def test_truncates_long_name_and_body(self):
        name = "X" * 200
        body = "y" * 800
        md = f"Step 1 — {name}\n{body}"
        out = h.split_steps(md)
        assert len(out[0][0]) <= 80
        assert len(out[0][1]) <= 600


# ---------------------------------------------------------------------------
# asset_url
# ---------------------------------------------------------------------------


class TestAssetUrl:
    def test_empty_filename_returns_empty(self):
        """Covers line 631/632."""
        assert h.asset_url("") == ""

    def test_root_absolute_filename_passes_through(self):
        """Covers line 633/634."""
        assert h.asset_url("/already/absolute/path.css") == "/already/absolute/path.css"

    def test_default_returns_root_absolute_assets_path(self):
        """Default fallback at line 640."""
        assert h.asset_url("styles.deadbeef.css") == "/assets/styles.deadbeef.css"

    def test_with_site_url_subpath_prepends_path(self):
        """Covers branches 635->640 and the ``if base_path:`` arm at 638."""
        out = h.asset_url(
            "styles.css",
            site_url="https://user.github.io/repo",
        )
        assert out == "/repo/assets/styles.css"

    def test_with_site_url_no_subpath_falls_through_to_default(self):
        """``urlparse(...).path`` is empty for a bare host → fallback
        ``/assets/...``."""
        assert h.asset_url("x.css", site_url="https://example.com") == "/assets/x.css"

    def test_with_site_url_trailing_slash_stripped(self):
        out = h.asset_url("x.css", site_url="https://user.github.io/repo/")
        assert out == "/repo/assets/x.css"
