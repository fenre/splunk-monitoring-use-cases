"""Hermetic tests for ``tools/build/templates/regulation.py``.

Covers ``render_html`` (per-framework page), ``render_index_json``
(per-framework JSON twin), ``render_index_html`` (regulations
landing page), ``render_index_payload`` (regulations landing JSON
twin), and the internal helpers (``_framework_description``,
``_render_facts``, ``_render_grouped_ucs``, ``_render_breadcrumb``).
"""

from __future__ import annotations

from typing import Any

import pytest

from build.templates import _helpers, regulation


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


def _fw(**overrides) -> dict[str, Any]:
    base = {
        "id": "gdpr",
        "name": "General Data Protection Regulation",
        "shortName": "GDPR",
        "tier": 1,
        "jurisdiction": ["EU", "EEA"],
        "tags": ["privacy", "data-protection"],
        "aliases": ["EU GDPR"],
        "versions": [
            {"version": "2016/679",
             "authoritativeUrl": "https://eur-lex.europa.eu/eli/reg/2016/679/oj"},
        ],
    }
    base.update(overrides)
    return base


def _uc(uc_id: str, cat: int, **overrides) -> dict[str, Any]:
    base = {
        "i": uc_id,
        "n": f"UC {uc_id}",
        "v": f"Detect activity {uc_id}.",
        "c": "high",
        "f": "medium",
        "cat": cat,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _framework_description
# ---------------------------------------------------------------------------


class TestFrameworkDescription:
    def test_includes_uc_count_and_name(self):
        desc = regulation._framework_description(_fw(), uc_count=42)
        assert "42" in desc
        assert "General Data Protection Regulation" in desc

    def test_appends_jurisdiction_when_present(self):
        desc = regulation._framework_description(_fw(), uc_count=5)
        assert "Jurisdiction: EU, EEA." in desc

    def test_appends_tags_when_present(self):
        desc = regulation._framework_description(_fw(), uc_count=5)
        assert "Topics: privacy, data-protection." in desc

    def test_omits_jurisdiction_when_missing(self):
        fw = _fw(jurisdiction=[])
        desc = regulation._framework_description(fw, uc_count=5)
        assert "Jurisdiction" not in desc

    def test_omits_tags_when_missing(self):
        fw = _fw(tags=[])
        desc = regulation._framework_description(fw, uc_count=5)
        assert "Topics" not in desc

    def test_falls_back_to_short_then_id_then_default(self):
        """Name resolution: ``name or shortName or id or "this framework"``."""
        desc1 = regulation._framework_description(
            {"shortName": "X", "id": "x"}, uc_count=1
        )
        assert "mapped to X." in desc1
        desc2 = regulation._framework_description({"id": "x"}, uc_count=1)
        assert "mapped to x." in desc2
        desc3 = regulation._framework_description({}, uc_count=1)
        assert "mapped to this framework." in desc3

    def test_truncates_at_240_chars(self):
        fw = _fw(tags=["topic"] * 100)
        desc = regulation._framework_description(fw, uc_count=1)
        assert len(desc) <= 240


# ---------------------------------------------------------------------------
# _render_facts
# ---------------------------------------------------------------------------


class TestRenderFacts:
    def test_emits_all_fact_rows_when_present(self):
        html = regulation._render_facts(_fw())
        assert html.startswith('<dl class="facts">')
        assert "<dt>Name</dt><dd>General Data Protection Regulation</dd>" in html
        assert "<dt>Short name</dt><dd>GDPR</dd>" in html
        assert "<dt>Jurisdiction</dt><dd>EU, EEA</dd>" in html
        assert "<dt>Topics</dt><dd>privacy, data-protection</dd>" in html
        assert "<dt>Also known as</dt><dd>EU GDPR</dd>" in html
        assert "<dt>Authoritative source</dt>" in html
        assert "2016/679" in html
        assert html.endswith("</dl>")

    def test_skips_short_name_row_when_equal_to_name(self):
        fw = _fw(shortName="General Data Protection Regulation")
        html = regulation._render_facts(fw)
        assert "<dt>Short name</dt>" not in html

    def test_skips_optional_rows_when_absent(self):
        """Bare framework with only an id — no jurisdiction/tags/aliases/versions."""
        fw = {"id": "x"}
        html = regulation._render_facts(fw)
        assert "<dt>Name</dt>" not in html  # no `name` field set
        assert "<dt>Jurisdiction</dt>" not in html
        assert "<dt>Topics</dt>" not in html
        assert "<dt>Also known as</dt>" not in html
        assert "<dt>Authoritative source</dt>" not in html
        assert "<dt>Latest version</dt>" not in html

    def test_version_with_no_url_falls_back_to_latest_version_row(self):
        """``elif ver:`` arm — version present but no authoritativeUrl."""
        fw = _fw(versions=[{"version": "1.0"}])
        html = regulation._render_facts(fw)
        assert "<dt>Latest version</dt><dd>1.0</dd>" in html

    def test_version_with_empty_url_and_empty_version_emits_nothing(self):
        """Neither ``if url`` nor ``elif ver`` fires."""
        fw = _fw(versions=[{}])
        html = regulation._render_facts(fw)
        assert "<dt>Authoritative source</dt>" not in html
        assert "<dt>Latest version</dt>" not in html

    def test_authoritative_link_uses_latest_versions_entry(self):
        fw = _fw(versions=[
            {"version": "old", "authoritativeUrl": "https://old.example/"},
            {"version": "new", "authoritativeUrl": "https://new.example/"},
        ])
        html = regulation._render_facts(fw)
        assert "https://new.example/" in html
        assert "https://old.example/" not in html
        assert "new" in html

    def test_escapes_field_values(self):
        fw = _fw(
            name="<unsafe>",
            shortName="<short>",
            jurisdiction=["<juris>"],
            tags=["<tag>"],
            aliases=["<alias>"],
            versions=[{"version": "<ver>", "authoritativeUrl": "https://x?a=1&b=2"}],
        )
        html = regulation._render_facts(fw)
        assert "&lt;unsafe&gt;" in html
        assert "&lt;short&gt;" in html
        assert "&lt;juris&gt;" in html
        assert "&lt;tag&gt;" in html
        assert "&lt;alias&gt;" in html
        assert "&lt;ver&gt;" in html
        # URL escaping for the `&` inside the href attribute.
        assert "a=1&amp;b=2" in html


# ---------------------------------------------------------------------------
# _render_grouped_ucs
# ---------------------------------------------------------------------------


class TestRenderGroupedUcs:
    def test_returns_empty_state_when_no_grouped_ucs(self):
        html = regulation._render_grouped_ucs(
            [], cat_slug_for={}, cat_name_for={}, ctx=_ctx()
        )
        assert "No use cases mapped to this framework yet." in html

    def test_skips_ucs_without_cat(self):
        """``if cat_id is None: continue`` — only UCs with a `cat`
        field show up."""
        ucs = [_uc("1.1.1", cat=1), {"i": "9.9.9", "n": "no-cat"}]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={1: "net"},
            cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        assert "UC-1.1.1" in html
        assert "no-cat" not in html

    def test_groups_by_cat_id_and_sorts(self):
        ucs = [
            _uc("3.1.1", cat=3),
            _uc("1.1.1", cat=1),
            _uc("2.1.1", cat=2),
        ]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={1: "a", 2: "b", 3: "c"},
            cat_name_for={1: "Alpha", 2: "Beta", 3: "Gamma"},
            ctx=_ctx(),
        )
        pos_alpha = html.find("Alpha")
        pos_beta = html.find("Beta")
        pos_gamma = html.find("Gamma")
        assert 0 < pos_alpha < pos_beta < pos_gamma

    def test_emits_per_category_link_when_cat_slug_known(self):
        ucs = [_uc("1.1.1", cat=1)]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={1: "network"},
            cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        assert '/category/network/' in html

    def test_omits_category_link_when_slug_unknown(self):
        ucs = [_uc("1.1.1", cat=99)]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={},  # no slug for cat 99
            cat_name_for={},  # no name either
            ctx=_ctx(),
        )
        # Fallback name is "Category 99".
        assert "Category 99" in html
        # No drill-down link.
        assert "/category/" not in html

    def test_skips_uc_without_id(self):
        ucs = [_uc("1.1.1", cat=1), {"cat": 1, "n": "Headless"}]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={1: "net"},
            cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        assert "UC-1.1.1" in html
        assert "Headless" not in html

    def test_uc_title_falls_back_to_id_when_n_missing(self):
        ucs = [{"i": "1.1.1", "cat": 1}]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={1: "net"}, cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        assert "uc-title\">1.1.1<" in html

    def test_cat_id_is_coerced_to_int(self):
        """``grouped.setdefault(int(cat_id), [])`` coerces stringy
        ids so they merge with int-keyed ones."""
        ucs = [_uc("1.1.1", cat=1), _uc("1.2.1", cat="1")]
        html = regulation._render_grouped_ucs(
            ucs,
            cat_slug_for={1: "net"}, cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        # Two UCs in a single section.
        assert html.count("<h2>Network") == 1
        assert "(2)" in html


# ---------------------------------------------------------------------------
# _render_breadcrumb (private duplicate of category version)
# ---------------------------------------------------------------------------


class TestRenderBreadcrumb:
    def test_marks_last_item_as_current_page(self):
        items = [
            ("Home", "https://example.com/"),
            ("Regulations", "https://example.com/regulation/"),
            ("GDPR", "https://example.com/regulation/gdpr/"),
        ]
        html = regulation._render_breadcrumb(items)
        assert 'aria-current="page"' in html
        assert html.count('aria-current="page"') == 1

    def test_single_item_breadcrumb(self):
        html = regulation._render_breadcrumb([("Solo", "/")])
        assert 'aria-current="page"' in html


# ---------------------------------------------------------------------------
# render_index_json (per-framework JSON twin)
# ---------------------------------------------------------------------------


class TestRenderIndexJson:
    def test_emits_schema_envelope_and_lists(self):
        ucs = [_uc("1.1.1", cat=1), _uc("2.1.1", cat=2)]
        out = regulation.render_index_json(
            _fw(),
            slug="gdpr",
            ucs=ucs,
            cat_slug_for={1: "net", 2: "sec"},
            cat_name_for={1: "Network", 2: "Security"},
            ctx=_ctx(),
        )
        assert out["$schema"] == "/schemas/v2/regulation.schema.json"
        assert out["version"] == "2.0.0"
        assert out["id"] == "gdpr"
        assert out["slug"] == "gdpr"
        assert out["name"] == "General Data Protection Regulation"
        assert out["shortName"] == "GDPR"
        assert out["tier"] == 1
        assert out["jurisdiction"] == ["EU", "EEA"]
        assert out["tags"] == ["privacy", "data-protection"]
        assert out["aliases"] == ["EU GDPR"]
        assert out["useCaseCount"] == 2
        assert out["categoryCount"] == 2
        assert out["generatedAt"] == "2026-05-20T17:00:00Z"

    def test_categories_sorted_by_id(self):
        ucs = [_uc("3.1.1", cat=3), _uc("1.1.1", cat=1), _uc("2.1.1", cat=2)]
        out = regulation.render_index_json(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "a", 2: "b", 3: "c"},
            cat_name_for={1: "A", 2: "B", 3: "C"},
            ctx=_ctx(),
        )
        assert [c["id"] for c in out["categories"]] == [1, 2, 3]

    def test_optional_list_fields_default_to_empty(self):
        out = regulation.render_index_json(
            {"id": "x"},  # no jurisdiction/tags/aliases
            slug="x", ucs=[],
            cat_slug_for={}, cat_name_for={},
            ctx=_ctx(),
        )
        assert out["jurisdiction"] == []
        assert out["tags"] == []
        assert out["aliases"] == []

    def test_id_falls_back_to_slug_when_missing(self):
        out = regulation.render_index_json(
            {"name": "X", "shortName": "X"},  # no `id`
            slug="x-slug", ucs=[],
            cat_slug_for={}, cat_name_for={},
            ctx=_ctx(),
        )
        assert out["id"] == "x-slug"

    def test_name_falls_back_to_short_when_missing(self):
        out = regulation.render_index_json(
            {"id": "x", "shortName": "X-Short"},
            slug="x", ucs=[],
            cat_slug_for={}, cat_name_for={}, ctx=_ctx(),
        )
        assert out["name"] == "X-Short"

    def test_short_falls_back_to_name_then_id(self):
        out1 = regulation.render_index_json(
            {"id": "x", "name": "X-Name"},  # no shortName
            slug="x", ucs=[],
            cat_slug_for={}, cat_name_for={}, ctx=_ctx(),
        )
        assert out1["shortName"] == "X-Name"
        out2 = regulation.render_index_json(
            {"id": "x"},  # no name or shortName
            slug="x", ucs=[],
            cat_slug_for={}, cat_name_for={}, ctx=_ctx(),
        )
        assert out2["shortName"] == "x"

    def test_ucs_without_cat_excluded_from_payload(self):
        ucs = [
            _uc("1.1.1", cat=1),
            {"i": "9.9.9", "n": "no-cat"},  # no `cat`
        ]
        out = regulation.render_index_json(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "net"}, cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        all_ids = [u["shortId"] for cat in out["categories"] for u in cat["useCases"]]
        assert "1.1.1" in all_ids
        assert "9.9.9" not in all_ids
        # `useCaseCount` still counts the input list — it's not filtered.
        assert out["useCaseCount"] == 2

    def test_uc_payload_carries_canonical_fields(self):
        ucs = [_uc("1.1.1", cat=1)]
        out = regulation.render_index_json(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "net"}, cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        uc = out["categories"][0]["useCases"][0]
        assert uc["id"] == "UC-1.1.1"
        assert uc["shortId"] == "1.1.1"
        assert uc["title"] == "UC 1.1.1"
        assert uc["criticality"] == "high"
        assert uc["difficulty"] == "medium"
        assert uc["url"] == "https://example.com/uc/UC-1.1.1/"
        assert uc["json"] == "https://example.com/uc/UC-1.1.1/index.json"
        assert len(uc["value"]) <= 200

    def test_headless_ucs_inside_cat_excluded(self):
        ucs = [_uc("1.1.1", cat=1), {"cat": 1, "n": "Headless"}]
        out = regulation.render_index_json(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "net"}, cat_name_for={1: "Network"},
            ctx=_ctx(),
        )
        cat = out["categories"][0]
        assert cat["useCaseCount"] == 1
        assert cat["useCases"][0]["shortId"] == "1.1.1"


# ---------------------------------------------------------------------------
# render_html (per-framework HTML page)
# ---------------------------------------------------------------------------


class TestRenderHtml:
    def test_emits_well_formed_document(self):
        ucs = [_uc("1.1.1", cat=1), _uc("2.1.1", cat=2)]
        html = regulation.render_html(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "net", 2: "sec"},
            cat_name_for={1: "Network", 2: "Security"},
            ctx=_ctx(),
        )
        assert html.startswith("<!DOCTYPE html>")
        assert "<title>GDPR mappings · Example</title>" in html
        assert 'rel="canonical" href="https://example.com/regulation/gdpr/"' in html
        assert 'rel="alternate" type="application/json"' in html
        # Facts block emitted.
        assert "<dt>Name</dt>" in html
        # Both grouped sections present.
        assert "<h2>Network" in html
        assert "<h2>Security" in html
        # UC count and category count in muted lede.
        assert "2 use cases" in html
        assert "2 categories" in html
        # JSON-LD.
        assert "CollectionPage" in html
        assert "BreadcrumbList" in html
        assert html.rstrip().endswith("</html>")

    def test_uses_id_when_name_missing(self):
        """``name or shortName or id`` cascade — bare framework with
        only id still renders."""
        ucs = [_uc("1.1.1", cat=1)]
        html = regulation.render_html(
            {"id": "x"}, slug="x", ucs=ucs,
            cat_slug_for={1: "n"}, cat_name_for={1: "N"},
            ctx=_ctx(),
        )
        # Heading falls back to the id "x".
        assert "<h1>x</h1>" in html

    def test_short_falls_back_to_name_when_short_missing(self):
        ucs = []
        html = regulation.render_html(
            {"id": "x", "name": "Long Name"},
            slug="x", ucs=ucs,
            cat_slug_for={}, cat_name_for={},
            ctx=_ctx(),
        )
        # Title uses short_name fallback → "Long Name mappings".
        assert "Long Name mappings" in html

    def test_no_grouped_ucs_yields_empty_state(self):
        html = regulation.render_html(
            _fw(), slug="gdpr", ucs=[],
            cat_slug_for={}, cat_name_for={},
            ctx=_ctx(),
        )
        assert "No use cases mapped to this framework yet." in html

    def test_member_urls_skips_ucs_without_id(self):
        ucs = [_uc("1.1.1", cat=1), {"cat": 1, "n": "Headless"}]
        html = regulation.render_html(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "n"}, cat_name_for={1: "N"},
            ctx=_ctx(),
        )
        # Headless contributes nothing to JSON-LD `itemListElement`.
        assert "UC-1.1.1" in html
        assert "Headless" not in html

    def test_category_count_is_distinct(self):
        ucs = [
            _uc("1.1.1", cat=1),
            _uc("1.1.2", cat=1),
            _uc("2.1.1", cat=2),
        ]
        html = regulation.render_html(
            _fw(), slug="gdpr", ucs=ucs,
            cat_slug_for={1: "a", 2: "b"},
            cat_name_for={1: "A", 2: "B"},
            ctx=_ctx(),
        )
        # 3 UCs but only 2 distinct categories.
        assert "3 use cases" in html
        assert "2 categories" in html

    def test_prefetch_link_emitted_when_asset_styles_set(self):
        html = regulation.render_html(
            _fw(), slug="gdpr", ucs=[],
            cat_slug_for={}, cat_name_for={},
            ctx=_ctx(asset_styles="styles.deadbeef.css"),
        )
        assert 'rel="prefetch"' in html
        assert "styles.deadbeef.css" in html

    def test_no_prefetch_link_when_asset_styles_blank(self):
        html = regulation.render_html(
            _fw(), slug="gdpr", ucs=[],
            cat_slug_for={}, cat_name_for={},
            ctx=_ctx(asset_styles=""),
        )
        assert 'rel="prefetch"' not in html


# ---------------------------------------------------------------------------
# render_index_html (regulations landing page)
# ---------------------------------------------------------------------------


class TestRenderIndexHtml:
    def test_emits_one_row_per_framework(self):
        frameworks = [
            (_fw(), "gdpr", 42),
            (_fw(id="ccpa", name="California Consumer Privacy Act",
                 shortName="CCPA", jurisdiction=["US-CA"]), "ccpa", 17),
        ]
        html = regulation.render_index_html(frameworks=frameworks, ctx=_ctx())
        assert html.startswith("<!DOCTYPE html>")
        assert "<title>Regulations · Example</title>" in html
        assert "GDPR" in html
        assert "CCPA" in html
        assert ">42 UCs<" in html
        assert ">17 UCs<" in html
        # Lede summarises totals.
        assert "2 frameworks" in html
        assert "59 mapped use cases" in html
        # Each row hrefs into the framework page.
        assert "/regulation/gdpr/" in html
        assert "/regulation/ccpa/" in html

    def test_jurisdiction_dash_fallback_when_empty(self):
        frameworks = [
            (_fw(jurisdiction=[]), "gdpr", 1),
        ]
        html = regulation.render_index_html(frameworks=frameworks, ctx=_ctx())
        assert "uc-value\">—<" in html

    def test_jurisdictions_joined_with_comma(self):
        frameworks = [(_fw(), "gdpr", 1)]
        html = regulation.render_index_html(frameworks=frameworks, ctx=_ctx())
        assert "EU, EEA" in html

    def test_short_name_falls_back_to_name_then_id(self):
        frameworks = [
            ({"id": "x", "name": "Long Name"}, "x", 1),
            ({"id": "y"}, "y", 1),
        ]
        html = regulation.render_index_html(frameworks=frameworks, ctx=_ctx())
        # First framework: shortName falls back to name.
        assert ">Long Name<" in html
        # Second framework: short and name both fall back to id.
        assert ">y<" in html

    def test_empty_framework_list_still_renders_lede(self):
        html = regulation.render_index_html(frameworks=[], ctx=_ctx())
        assert "0 frameworks" in html
        assert "0 mapped use cases" in html


# ---------------------------------------------------------------------------
# render_index_payload (regulations landing JSON twin)
# ---------------------------------------------------------------------------


class TestRenderIndexPayload:
    def test_emits_schema_envelope_and_totals(self):
        frameworks = [
            (_fw(), "gdpr", 42),
            (_fw(id="ccpa", name="CCPA", shortName="CCPA"), "ccpa", 17),
        ]
        out = regulation.render_index_payload(frameworks=frameworks, ctx=_ctx())
        assert out["$schema"] == "/schemas/v2/regulation-index.schema.json"
        assert out["version"] == "2.0.0"
        assert out["url"] == "https://example.com/regulation/"
        assert out["json"] == "https://example.com/regulation/index.json"
        assert out["frameworkCount"] == 2
        assert out["useCaseTotal"] == 59
        assert out["generatedAt"] == "2026-05-20T17:00:00Z"
        assert len(out["frameworks"]) == 2

    def test_per_framework_payload_carries_canonical_fields(self):
        frameworks = [(_fw(), "gdpr", 42)]
        out = regulation.render_index_payload(frameworks=frameworks, ctx=_ctx())
        item = out["frameworks"][0]
        assert item["id"] == "gdpr"
        assert item["slug"] == "gdpr"
        assert item["shortName"] == "GDPR"
        assert item["name"] == "General Data Protection Regulation"
        assert item["tier"] == 1
        assert item["jurisdiction"] == ["EU", "EEA"]
        assert item["tags"] == ["privacy", "data-protection"]
        assert item["aliases"] == ["EU GDPR"]
        assert item["useCaseCount"] == 42
        assert item["url"] == "https://example.com/regulation/gdpr/"
        assert item["json"] == "https://example.com/regulation/gdpr/index.json"

    def test_id_falls_back_to_slug(self):
        out = regulation.render_index_payload(
            frameworks=[({"shortName": "X"}, "x-slug", 1)], ctx=_ctx()
        )
        assert out["frameworks"][0]["id"] == "x-slug"

    def test_optional_list_fields_default_to_empty(self):
        out = regulation.render_index_payload(
            frameworks=[({"id": "x"}, "x", 1)], ctx=_ctx()
        )
        item = out["frameworks"][0]
        assert item["jurisdiction"] == []
        assert item["tags"] == []
        assert item["aliases"] == []

    def test_empty_framework_list_returns_zero_totals(self):
        out = regulation.render_index_payload(frameworks=[], ctx=_ctx())
        assert out["frameworkCount"] == 0
        assert out["useCaseTotal"] == 0
        assert out["frameworks"] == []
