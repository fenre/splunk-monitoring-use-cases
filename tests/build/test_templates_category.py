"""Hermetic tests for ``tools/build/templates/category.py``.

Covers ``render_html`` (HTML page), ``render_index_json`` (JSON twin),
and the four private helpers (``_category_default_desc``,
``_render_quick_facts``, ``_render_subcategory``, ``_render_breadcrumb``).
"""

from __future__ import annotations

from typing import Any

import pytest

from build.templates import _helpers, category


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ctx(**overrides) -> _helpers.RenderContext:
    kwargs = dict(
        site_url="https://example.com",
        site_name="Example UC Site",
        site_short="Example",
        site_tagline="Example tagline.",
        asset_styles="",
        repo_url="https://github.com/example/repo",
        generated_at="2026-05-20T17:00:00Z",
    )
    kwargs.update(overrides)
    return _helpers.RenderContext(**kwargs)


def _cat(**overrides) -> dict:
    """One-category dict in catalog wire format."""
    base = {
        "i": 1,
        "n": "Network",
        "s": [
            {
                "i": "1.1",
                "n": "Routing",
                "u": [
                    {"i": "1.1.1", "n": "OSPF down",
                     "v": "Detect when an OSPF neighbour goes down.",
                     "c": "critical", "f": "easy",
                     "mtype": ["raw"], "regs": ["pci-dss"],
                     "a": ["Network_Traffic"]},
                    {"i": "1.1.2", "n": "BGP flapping",
                     "v": "Detect repeated BGP session state changes.",
                     "c": "high", "f": "medium"},
                ],
            },
            {
                "i": "1.2",
                "n": "Switching",
                "u": [
                    {"i": "1.2.1", "n": "STP topology change",
                     "v": "Spanning tree convergence event."},
                ],
            },
        ],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _category_default_desc
# ---------------------------------------------------------------------------


class TestCategoryDefaultDesc:
    def test_includes_category_name_and_total_uc_count(self):
        cat = _cat()
        desc = category._category_default_desc("Network", cat)
        assert "Network" in desc
        assert "3" in desc  # 2 + 1 = 3 UCs across the two subcategories
        assert "Splunk" in desc

    def test_zero_uc_count_when_no_subs(self):
        desc = category._category_default_desc("Empty", {"s": []})
        assert "Empty" in desc
        assert "0 curated" in desc


# ---------------------------------------------------------------------------
# _render_quick_facts
# ---------------------------------------------------------------------------


class TestRenderQuickFacts:
    def test_returns_empty_when_no_quick(self):
        assert category._render_quick_facts({}) == ""
        assert category._render_quick_facts({"quick": None}) == ""

    def test_returns_empty_when_quick_is_not_dict(self):
        """``quick`` declared as ``str`` in CategoryMeta — a string
        value short-circuits the dict-only branch."""
        assert category._render_quick_facts({"quick": "scalar value"}) == ""

    def test_emits_dl_for_str_values(self):
        meta = {"quick": {"OS": "Linux", "Vendor": "Cisco"}}
        html = category._render_quick_facts(meta)
        assert html.startswith('<dl class="facts">')
        assert "<dt>OS</dt><dd>Linux</dd>" in html
        assert "<dt>Vendor</dt><dd>Cisco</dd>" in html
        assert html.endswith("</dl>")

    def test_emits_comma_joined_list_values(self):
        meta = {"quick": {"Apps": ["TA-foo", "TA-bar"]}}
        html = category._render_quick_facts(meta)
        assert "<dd>TA-foo, TA-bar</dd>" in html

    def test_skips_empty_values(self):
        meta = {"quick": {"OS": "", "Vendor": "Cisco"}}
        html = category._render_quick_facts(meta)
        assert "<dt>OS</dt>" not in html
        assert "<dt>Vendor</dt>" in html

    def test_list_value_filters_falsy_items(self):
        meta = {"quick": {"Apps": ["A", "", None, "B"]}}
        html = category._render_quick_facts(meta)
        assert "<dd>A, B</dd>" in html

    def test_escapes_label_and_value(self):
        meta = {"quick": {"<key>": "<value>"}}
        html = category._render_quick_facts(meta)
        assert "&lt;key&gt;" in html
        assert "&lt;value&gt;" in html


# ---------------------------------------------------------------------------
# _render_subcategory
# ---------------------------------------------------------------------------


class TestRenderSubcategory:
    def test_emits_section_with_anchor_and_rows(self):
        sub = {
            "i": "1.1", "n": "Routing",
            "u": [
                {"i": "1.1.1", "n": "OSPF down",
                 "v": "Detect when an OSPF neighbour goes down.",
                 "c": "critical"},
            ],
        }
        html = category._render_subcategory(sub, _ctx())
        assert '<section id="routing">' in html
        assert "<h2>Routing" in html
        assert "(1)" in html
        assert "UC-1.1.1" in html
        assert "OSPF down" in html
        assert "OSPF neighbour" in html
        # criticality badge:
        assert "badge-" in html
        assert html.endswith("</section>")

    def test_returns_empty_string_when_no_ucs(self):
        sub = {"i": "1.1", "n": "Routing", "u": []}
        assert category._render_subcategory(sub, _ctx()) == ""

    def test_skips_uc_without_id(self):
        sub = {"i": "1.1", "n": "Routing", "u": [
            {"i": "1.1.1", "n": "Has ID"},
            {"n": "Headless"},  # no `i`
        ]}
        html = category._render_subcategory(sub, _ctx())
        assert "UC-1.1.1" in html
        assert "Headless" not in html

    def test_anchor_falls_back_to_default_when_name_blank(self):
        """``_helpers.slug("")`` returns ``"category"`` (its own
        default), so a blank ``sub_name`` resolves to that — the
        ``or f"sub-{sub_id}"`` fallback inside the renderer is only
        reachable if ``slug()`` ever returned an empty string."""
        sub = {"i": "1.9", "n": "", "u": [{"i": "1.9.1", "n": "X"}]}
        html = category._render_subcategory(sub, _ctx())
        assert 'id="category"' in html

    def test_uc_title_falls_back_to_id_when_n_missing(self):
        sub = {"i": "1.1", "n": "Routing", "u": [
            {"i": "1.1.1"},  # no name
        ]}
        html = category._render_subcategory(sub, _ctx())
        # Title falls back to uc_id ("1.1.1").
        assert "uc-title\">1.1.1<" in html

    def test_ucs_sorted_by_numeric_id(self):
        sub = {"i": "1.1", "n": "Routing", "u": [
            {"i": "1.1.10", "n": "Tenth"},
            {"i": "1.1.2",  "n": "Second"},
            {"i": "1.1.1",  "n": "First"},
        ]}
        html = category._render_subcategory(sub, _ctx())
        pos_first = html.find("First")
        pos_second = html.find("Second")
        pos_tenth = html.find("Tenth")
        assert 0 < pos_first < pos_second < pos_tenth


# ---------------------------------------------------------------------------
# _render_breadcrumb
# ---------------------------------------------------------------------------


class TestRenderBreadcrumb:
    def test_marks_last_item_as_current_page(self):
        items = [
            ("Home", "https://example.com/"),
            ("Browse", "https://example.com/browse/"),
            ("Network", "https://example.com/category/network/"),
        ]
        html = category._render_breadcrumb(items)
        assert '<nav aria-label="Breadcrumb"' in html
        assert 'aria-current="page"' in html
        # Only the LAST item carries the current-page attribute.
        assert html.count('aria-current="page"') == 1
        # The last item is rendered as plain text (no `<a>`).
        last_segment = html.rsplit('<li', 1)[-1]
        assert "<a " not in last_segment

    def test_renders_one_item_as_aria_current(self):
        items = [("Only", "https://example.com/")]
        html = category._render_breadcrumb(items)
        assert 'aria-current="page"' in html
        # Single-item list still produces a valid breadcrumb element.
        assert "<ol>" in html and "</ol>" in html

    def test_escapes_names_and_urls(self):
        items = [
            ("Home", "https://example.com/?a=1&b=2"),
            ("<unsafe>", "https://example.com/x"),
        ]
        html = category._render_breadcrumb(items)
        assert "&lt;unsafe&gt;" in html
        # `&` in URL attr is escaped.
        assert "a=1&amp;b=2" in html


# ---------------------------------------------------------------------------
# render_index_json
# ---------------------------------------------------------------------------


class TestRenderIndexJson:
    def test_emits_schema_envelope_and_subcategories(self):
        out = category.render_index_json(
            _cat(),
            cat_slug="network",
            cat_meta={"desc": "Network telemetry.", "icon": "📡"},
            ctx=_ctx(),
        )
        assert out["$schema"] == "/schemas/v2/category.schema.json"
        assert out["version"] == "2.0.0"
        assert out["id"] == 1
        assert out["slug"] == "network"
        assert out["name"] == "Network"
        assert out["url"] == "https://example.com/category/network/"
        assert out["html"] == out["url"]
        assert out["json"].endswith("/index.json")
        assert out["description"] == "Network telemetry."
        assert out["icon"] == "📡"
        assert out["useCaseCount"] == 3
        assert out["generatedAt"] == "2026-05-20T17:00:00Z"
        assert len(out["subcategories"]) == 2

    def test_each_uc_carries_canonical_fields(self):
        out = category.render_index_json(
            _cat(), cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        # First subcategory's first UC.
        uc = out["subcategories"][0]["useCases"][0]
        assert uc["id"] == "UC-1.1.1"
        assert uc["shortId"] == "1.1.1"
        assert uc["title"] == "OSPF down"
        assert uc["criticality"] == "critical"
        assert uc["difficulty"] == "easy"
        assert uc["url"] == "https://example.com/uc/UC-1.1.1/"
        assert uc["json"] == "https://example.com/uc/UC-1.1.1/index.json"
        assert uc["monitoringTypes"] == ["raw"]
        assert uc["regulations"] == ["pci-dss"]
        assert uc["dataModels"] == ["Network_Traffic"]

    def test_optional_list_fields_default_to_empty(self):
        """When ``mtype`` / ``regs`` / ``a`` are absent, the JSON twin
        emits ``[]`` (covers the ``or []`` fallback)."""
        out = category.render_index_json(
            _cat(), cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        # Second UC has no mtype/regs/a.
        uc = out["subcategories"][0]["useCases"][1]
        assert uc["monitoringTypes"] == []
        assert uc["regulations"] == []
        assert uc["dataModels"] == []

    def test_subcategory_without_ucs_is_excluded(self):
        cat = _cat()
        cat["s"].append({"i": "1.9", "n": "Empty", "u": []})
        out = category.render_index_json(
            cat, cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        # The empty subcategory is NOT present in the payload.
        ids = [s["id"] for s in out["subcategories"]]
        assert "1.9" not in ids

    def test_subcategory_with_only_headless_ucs_is_excluded(self):
        """``if not uc_id: continue`` filters every UC out, then
        ``if uc_list:`` also drops the subcategory."""
        cat = _cat()
        cat["s"].append({"i": "1.9", "n": "Headless", "u": [{"n": "no-id"}]})
        out = category.render_index_json(
            cat, cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        ids = [s["id"] for s in out["subcategories"]]
        assert "1.9" not in ids

    def test_guide_field_propagated_when_present(self):
        cat = _cat()
        cat["s"][0]["g"] = {"slug": "routing-guide", "title": "Routing"}
        out = category.render_index_json(
            cat, cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        first = out["subcategories"][0]
        assert first["guide"] == {"slug": "routing-guide", "title": "Routing"}

    def test_guide_field_absent_when_g_missing(self):
        out = category.render_index_json(
            _cat(), cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        for sub in out["subcategories"]:
            assert "guide" not in sub

    def test_quick_facts_passthrough_when_dict(self):
        out = category.render_index_json(
            _cat(),
            cat_slug="network",
            cat_meta={"quick": {"OS": "Linux"}},
            ctx=_ctx(),
        )
        assert out["quickFacts"] == {"OS": "Linux"}

    def test_quick_facts_defaults_to_empty_dict(self):
        out = category.render_index_json(
            _cat(), cat_slug="network", cat_meta={}, ctx=_ctx(),
        )
        assert out["quickFacts"] == {}

    def test_uc_value_is_truncated_to_200(self):
        long_v = "x" * 500
        cat = {
            "i": 1, "n": "X",
            "s": [{"i": "1.1", "n": "Sub", "u": [
                {"i": "1.1.1", "n": "T", "v": long_v}
            ]}],
        }
        out = category.render_index_json(
            cat, cat_slug="x", cat_meta={}, ctx=_ctx(),
        )
        v = out["subcategories"][0]["useCases"][0]["value"]
        assert len(v) <= 200


# ---------------------------------------------------------------------------
# render_html — end-to-end
# ---------------------------------------------------------------------------


class TestRenderHtml:
    def test_emits_well_formed_document(self):
        html = category.render_html(
            _cat(),
            cat_slug="network",
            cat_meta={"desc": "Network telemetry.",
                      "quick": {"OS": "Linux"},
                      "icon": "📡"},
            ctx=_ctx(),
        )
        assert html.startswith("<!DOCTYPE html>")
        assert "<title>Network · Example</title>" in html
        assert 'rel="canonical" href="https://example.com/category/network/"' in html
        assert 'rel="alternate" type="application/json"' in html
        assert "Network telemetry." in html
        # Quick-facts block emitted.
        assert "OS</dt><dd>Linux</dd>" in html
        # Both subcategories rendered.
        assert "<h2>Routing" in html
        assert "<h2>Switching" in html
        # UC count + sub count in muted lede line.
        assert "3 use cases" in html
        assert "2 subcategories" in html
        # JSON-LD payload includes CollectionPage and BreadcrumbList.
        assert "CollectionPage" in html
        assert "BreadcrumbList" in html
        # Closing tag.
        assert html.rstrip().endswith("</html>")

    def test_no_description_falls_back_to_default(self):
        html = category.render_html(
            _cat(),
            cat_slug="network",
            cat_meta={},  # no `desc`
            ctx=_ctx(),
        )
        # Fallback default mentions "Splunk Enterprise" + UC count.
        assert "Network use cases for Splunk Enterprise" in html

    def test_prefetch_link_emitted_when_asset_styles_set(self):
        html = category.render_html(
            _cat(),
            cat_slug="network",
            cat_meta={},
            ctx=_ctx(asset_styles="styles.deadbeef.css"),
        )
        assert 'rel="prefetch"' in html
        assert "styles.deadbeef.css" in html

    def test_no_prefetch_link_when_asset_styles_blank(self):
        html = category.render_html(
            _cat(),
            cat_slug="network",
            cat_meta={},
            ctx=_ctx(asset_styles=""),
        )
        assert 'rel="prefetch"' not in html

    def test_subcategory_with_no_ucs_does_not_emit_a_section(self):
        """``_render_subcategory`` returns ``""`` when ``u`` is empty
        and the joiner ``"\\n".join(... if sub.get("u"))`` strips them
        out of the page body."""
        cat = _cat()
        cat["s"].append({"i": "1.9", "n": "Empty", "u": []})
        html = category.render_html(
            cat, cat_slug="network", cat_meta={}, ctx=_ctx()
        )
        assert "<h2>Empty" not in html

    def test_member_urls_skips_uc_without_id(self):
        """Inside ``render_html`` the ``member_urls`` JSON-LD list is
        built from every UC carrying a non-empty ``i`` — covers the
        false arm of branch 59→54."""
        cat = {
            "i": 1, "n": "Net",
            "s": [{"i": "1.1", "n": "Sub", "u": [
                {"i": "1.1.1", "n": "Real"},
                {"n": "Headless"},  # no `i`
            ]}],
        }
        html = category.render_html(
            cat, cat_slug="net", cat_meta={}, ctx=_ctx()
        )
        # Real UC is in the page; Headless is not.
        assert "UC-1.1.1" in html
        assert "Headless" not in html

    def test_sub_count_counts_only_subs_with_ucs(self):
        cat = _cat()
        cat["s"].append({"i": "1.9", "n": "Empty", "u": []})
        html = category.render_html(
            cat, cat_slug="network", cat_meta={}, ctx=_ctx()
        )
        # Still 2, not 3.
        assert "2 subcategories" in html
