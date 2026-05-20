"""Hermetic tests for ``tools/build/templates/landing.py``.

Covers the root landing-page renderer and its three section helpers
(``_render_hero``, ``_render_domains``, ``_render_regulations``,
``_render_quick_links``). Tests run against a hand-rolled
``Catalog`` (no real catalog data) and use only ``tmp_path`` —
no network, subprocess, or filesystem outside the temp dir.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from build.parse_content import Catalog
from build.templates import _helpers, landing


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ctx(**overrides) -> _helpers.RenderContext:
    """Build a deterministic RenderContext for HTML assertions."""
    kwargs = dict(
        site_url="https://example.com",
        site_name="Example UC Site",
        site_short="Example",
        site_tagline="The example tagline.",
        asset_styles="",
        repo_url="https://github.com/example/repo",
    )
    kwargs.update(overrides)
    return _helpers.RenderContext(**kwargs)


def _catalog(tmp_path: Path, **overrides) -> Catalog:
    """Empty Catalog the landing renderer can iterate."""
    kwargs = dict(
        project_root=tmp_path,
        categories=[],
        cat_meta={},
        cat_groups={},
        equipment=[],
        regulations={},
        recently_added=[],
        facets={},
    )
    kwargs.update(overrides)
    return Catalog(**kwargs)


# ---------------------------------------------------------------------------
# _render_hero
# ---------------------------------------------------------------------------


class TestRenderHero:
    def test_emits_kicker_and_tagline(self):
        html = landing._render_hero(_ctx(), total_uc=42, total_cat=3, total_regs=0)
        assert '<section class="hero">' in html
        assert "Example</p>" in html  # kicker = site_short
        assert "The example tagline." in html
        assert ">42<" in html
        assert ">3<" in html
        # No regs clause when total_regs == 0.
        assert "regulatory frameworks" not in html

    def test_fallback_h1_when_tagline_blank(self):
        html = landing._render_hero(
            _ctx(site_tagline=""), total_uc=1, total_cat=1, total_regs=0
        )
        assert "Splunk monitoring use cases" in html

    def test_emits_regulations_clause_when_present(self):
        html = landing._render_hero(_ctx(), total_uc=1, total_cat=1, total_regs=12)
        assert "<strong>12</strong> regulatory frameworks" in html

    def test_emits_cta_links_with_site_root(self):
        html = landing._render_hero(_ctx(), total_uc=1, total_cat=1, total_regs=0)
        assert 'href="https://example.com/browse/"' in html
        assert 'href="https://example.com/regulation/"' in html
        assert 'href="https://example.com/api/"' in html
        assert 'href="https://github.com/example/repo"' in html

    def test_thousands_separator_on_uc_count(self):
        """``f'{total_uc:,}'`` adds comma group separators."""
        html = landing._render_hero(_ctx(), total_uc=7_929, total_cat=23, total_regs=60)
        assert ">7,929<" in html


# ---------------------------------------------------------------------------
# _render_card
# ---------------------------------------------------------------------------


class TestRenderCard:
    def test_card_uses_explicit_slug_and_meta_desc(self):
        cat = {
            "i": 1,
            "n": "Network",
            "s": [{"u": [{"i": "1.1.1"}, {"i": "1.1.2"}]}],
        }
        meta = {"1": {"desc": "Routing and switching telemetry."}}
        html = landing._render_card(cat, {1: "network"}, meta, _ctx())
        assert 'href="https://example.com/category/network/"' in html
        assert "Network" in html
        assert "Cat 1" in html
        assert "2 UCs" in html
        assert "Routing and switching telemetry." in html

    def test_card_meta_lookup_supports_int_key(self):
        """``cat_meta.get(cid, {})`` second-chance accepts an int key
        when the str-key lookup misses (covers the ``or cat_meta.get(cid, {})``
        path)."""
        cat = {"i": 7, "n": "Foo", "s": [{"u": [{"i": "7.1.1"}]}]}
        meta_int_key = {7: {"desc": "Int-keyed meta survives."}}
        html = landing._render_card(cat, {7: "foo"}, meta_int_key, _ctx())
        assert "Int-keyed meta survives." in html

    def test_card_falls_back_to_subcategory_count_when_meta_missing(self):
        """When ``cat_meta`` has no entry for the category, the blurb
        falls back to ``"<n> use cases across <m> subcategories."``."""
        cat = {
            "i": 9,
            "n": "Empty",
            "s": [
                {"u": [{"i": "9.1.1"}]},
                {"u": [{"i": "9.2.1"}, {"i": "9.2.2"}]},
            ],
        }
        html = landing._render_card(cat, {9: "empty"}, {}, _ctx())
        assert "3 use cases across 2 subcategories." in html

    def test_card_slug_falls_back_to_slugified_name(self):
        """When ``cat_slug_for`` doesn't contain ``cid``, the renderer
        runs the name through ``_helpers.slug``."""
        cat = {"i": 11, "n": "Hello World", "s": []}
        html = landing._render_card(cat, {}, {}, _ctx())
        # _helpers.slug lower-cases + replaces space with -.
        assert "/category/hello-world/" in html

    def test_card_meta_entry_explicitly_none_uses_fallback(self):
        """Covers ``or cat_meta.get(cid, {}) or {}`` when the str
        lookup returns ``None``."""
        cat = {"i": 4, "n": "X", "s": [{"u": [{"i": "4.1.1"}]}]}
        html = landing._render_card(cat, {4: "x"}, {"4": None}, _ctx())
        assert "1 use cases across 1 subcategories." in html


# ---------------------------------------------------------------------------
# _render_domains
# ---------------------------------------------------------------------------


class TestRenderDomains:
    def test_renders_domain_section_with_label_and_blurb(self):
        cat_by_id = {1: {"i": 1, "n": "Network", "s": []}}
        groups = {"infra": [1]}
        html = landing._render_domains(
            cat_by_id, groups, {1: "network"}, {}, _ctx()
        )
        assert "Browse by domain" in html
        assert "Infrastructure" in html  # the infra label
        assert "<h3>Infrastructure</h3>" in html
        assert "Servers, networks, storage" in html
        assert 'href="https://example.com/category/network/"' in html

    def test_skips_domain_when_group_is_empty(self):
        cat_by_id = {1: {"i": 1, "n": "Network", "s": []}}
        groups = {"infra": [], "security": [1]}
        html = landing._render_domains(
            cat_by_id, groups, {1: "network"}, {}, _ctx()
        )
        # No Infrastructure section emitted.
        assert "<h3>Infrastructure</h3>" not in html
        # Security section IS emitted.
        assert "<h3>Security</h3>" in html

    def test_skips_domain_when_no_cards_resolve(self):
        """If every cid in a group is missing from ``cat_by_id``, the
        domain section is skipped (covers the ``if not cards: continue``
        guard)."""
        cat_by_id = {2: {"i": 2, "n": "Real", "s": []}}
        groups = {"infra": [999, 1000], "security": [2]}
        html = landing._render_domains(cat_by_id, groups, {}, {}, _ctx())
        assert "<h3>Infrastructure</h3>" not in html
        assert "<h3>Security</h3>" in html

    def test_other_section_for_unassigned_categories(self):
        """Categories not listed in any group fall into the ``Other``
        bucket."""
        cat_by_id = {
            1: {"i": 1, "n": "Net", "s": []},
            2: {"i": 2, "n": "Sec", "s": []},
            7: {"i": 7, "n": "Stragg", "s": []},
        }
        groups = {"infra": [1], "security": [2]}
        html = landing._render_domains(
            cat_by_id, groups, {1: "net", 2: "sec", 7: "stragg"}, {}, _ctx()
        )
        assert "<h3>Other</h3>" in html
        # Stragg (cid=7) appears under Other.
        assert html.find("<h3>Other</h3>") < html.find("/category/stragg/")

    def test_no_other_section_when_all_categories_assigned(self):
        cat_by_id = {1: {"i": 1, "n": "Net", "s": []}}
        groups = {"infra": [1]}
        html = landing._render_domains(
            cat_by_id, groups, {1: "net"}, {}, _ctx()
        )
        assert "<h3>Other</h3>" not in html

    def test_cards_sorted_within_domain(self):
        """Within each domain section, cids are sorted via
        ``_helpers.sort_key``."""
        cat_by_id = {
            1: {"i": 1, "n": "A", "s": []},
            2: {"i": 2, "n": "B", "s": []},
            3: {"i": 3, "n": "C", "s": []},
        }
        groups = {"infra": [3, 1, 2]}
        html = landing._render_domains(
            cat_by_id, groups,
            {1: "a", 2: "b", 3: "c"}, {}, _ctx()
        )
        # Order in HTML should be A, B, C (sort by cid).
        pos_a = html.find("/category/a/")
        pos_b = html.find("/category/b/")
        pos_c = html.find("/category/c/")
        assert 0 < pos_a < pos_b < pos_c


# ---------------------------------------------------------------------------
# _render_regulations
# ---------------------------------------------------------------------------


class TestRenderRegulations:
    def test_returns_empty_string_when_no_summaries(self):
        assert landing._render_regulations([], _ctx()) == ""

    def test_emits_card_per_framework_up_to_twelve(self):
        summaries = [
            {
                "id": f"fw{i}",
                "slug": f"fw{i}",
                "shortName": f"FW{i}",
                "name": f"Framework {i}",
                "useCaseCount": 100 + i,
                "tier": 1,
            }
            for i in range(15)
        ]
        html = landing._render_regulations(summaries, _ctx())
        assert "Browse by regulation" in html
        # Exactly 12 cards.
        assert html.count('<a class="card"') == 12
        # The 13th framework is NOT in the output.
        assert "FW12" not in html
        assert "FW11" in html

    def test_skips_summaries_without_slug(self):
        summaries = [
            {"slug": "", "shortName": "NoSlug", "useCaseCount": 1, "tier": 1},
            {"slug": "good", "shortName": "Good", "useCaseCount": 5, "tier": 2},
        ]
        html = landing._render_regulations(summaries, _ctx())
        assert "NoSlug" not in html
        assert "Good" in html

    def test_returns_empty_string_when_all_summaries_have_no_slug(self):
        """``if not cards: return ""`` arm — every framework is
        rejected because none carry a slug."""
        summaries = [
            {"slug": "", "shortName": "A"},
            {"slug": "", "shortName": "B"},
        ]
        assert landing._render_regulations(summaries, _ctx()) == ""

    def test_tier_pill_omitted_for_non_int_tier(self):
        """``isinstance(tier, int)`` false arm — tier missing or a
        string yields no ``Tier <n>`` pill."""
        summaries = [
            {"id": "x", "slug": "x", "shortName": "X", "name": "Ex",
             "useCaseCount": 1, "tier": "one"},
        ]
        html = landing._render_regulations(summaries, _ctx())
        assert "Tier" not in html  # no pill emitted

    def test_falls_back_to_id_when_short_name_missing(self):
        """``str(fw.get("shortName") or fw.get("id") or "")`` —
        when shortName is absent, the framework id is used."""
        summaries = [
            {"id": "fid", "slug": "slug-1", "useCaseCount": 1},
        ]
        html = landing._render_regulations(summaries, _ctx())
        assert "fid" in html

    def test_name_falls_back_to_short_when_missing(self):
        summaries = [
            {"id": "x", "slug": "slug-1", "shortName": "X-Short",
             "useCaseCount": 1},
        ]
        html = landing._render_regulations(summaries, _ctx())
        # Both shortName (in title) and name fallback (in blurb).
        assert html.count("X-Short") >= 2

    def test_uc_count_uses_thousands_separator(self):
        summaries = [
            {"id": "x", "slug": "x", "shortName": "X",
             "name": "X-name", "useCaseCount": 1234},
        ]
        html = landing._render_regulations(summaries, _ctx())
        assert ">1,234 UCs<" in html

    def test_total_summaries_count_is_advertised(self):
        """The intro paragraph mentions
        ``"all {len(summaries)} mapped frameworks"``."""
        summaries = [
            {"id": f"fw{i}", "slug": f"fw{i}", "shortName": f"FW{i}",
             "useCaseCount": 1, "tier": 1}
            for i in range(40)
        ]
        html = landing._render_regulations(summaries, _ctx())
        assert "all 40 mapped frameworks" in html


# ---------------------------------------------------------------------------
# _render_quick_links
# ---------------------------------------------------------------------------


class TestRenderQuickLinks:
    def test_emits_all_eight_quick_links(self):
        html = landing._render_quick_links(_ctx())
        for label in [
            "Catalog index (JSON)",
            "Site manifest (JSON)",
            "Regulations index (JSON)",
            "OpenAPI",
            "Schemas",
            "Sitemap",
            "Atom feed",
            "LLM-friendly index",
        ]:
            assert f">{label}<" in html
        # All URLs are rooted at site_url.
        assert html.count("https://example.com/") == 8


# ---------------------------------------------------------------------------
# render_html — end-to-end smoke
# ---------------------------------------------------------------------------


class TestRenderHtml:
    def test_emits_well_formed_document_with_all_sections(self, tmp_path: Path):
        cat = _catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "Network",
                    "s": [{"u": [{"i": "1.1.1"}, {"i": "1.1.2"}]}],
                },
                {
                    "i": 2, "n": "Security",
                    "s": [{"u": [{"i": "2.1.1"}]}],
                },
            ],
            cat_groups={"infra": [1], "security": [2]},
            cat_meta={"1": {"desc": "Network telemetry."}},
        )
        regs = [
            {"id": "gdpr", "slug": "gdpr", "shortName": "GDPR",
             "name": "General Data Protection Regulation",
             "useCaseCount": 50, "tier": 1},
        ]
        html = landing.render_html(
            cat,
            cat_slug_for={1: "network", 2: "security"},
            regulation_summaries=regs,
            ctx=_ctx(),
        )
        # HTML chrome.
        assert html.startswith("<!DOCTYPE html>")
        assert "<title>Example UC Site</title>" in html
        assert 'name="viewport"' in html
        assert 'rel="canonical" href="https://example.com/"' in html
        # JSON-LD payload emitted.
        assert "BreadcrumbList" in html
        assert "WebSite" in html
        # Hero present.
        assert "<section class=\"hero\">" in html
        # Domain section emitted (Infrastructure label) — both cats present.
        assert ">Infrastructure<" in html
        assert ">Security<" in html
        # Regulations section.
        assert "GDPR" in html
        # Quick links footer.
        assert "Atom feed" in html
        # Footer chrome.
        assert "CC-BY-4.0" in html
        # Closing tag.
        assert html.rstrip().endswith("</html>")

    def test_no_regulations_section_when_summaries_empty(self, tmp_path: Path):
        cat = _catalog(tmp_path)
        html = landing.render_html(
            cat,
            cat_slug_for={},
            regulation_summaries=None,
            ctx=_ctx(),
        )
        assert "Browse by regulation" not in html
        # Hero still says 0 frameworks (no regs_clause).
        assert "regulatory frameworks" not in html

    def test_emits_prefetch_link_when_asset_styles_set(self, tmp_path: Path):
        """``ctx.asset_styles`` triggers a ``<link rel="prefetch">``
        for the fingerprinted styles bundle."""
        cat = _catalog(tmp_path)
        html = landing.render_html(
            cat,
            cat_slug_for={},
            regulation_summaries=None,
            ctx=_ctx(asset_styles="styles.deadbeef.css"),
        )
        assert 'rel="prefetch"' in html
        assert "styles.deadbeef.css" in html

    def test_no_prefetch_link_when_asset_styles_blank(self, tmp_path: Path):
        cat = _catalog(tmp_path)
        html = landing.render_html(
            cat,
            cat_slug_for={},
            regulation_summaries=None,
            ctx=_ctx(asset_styles=""),
        )
        assert 'rel="prefetch"' not in html

    def test_description_mentions_uc_and_cat_counts(self, tmp_path: Path):
        cat = _catalog(
            tmp_path,
            categories=[
                {"i": i, "n": f"Cat{i}",
                 "s": [{"u": [{"i": f"{i}.1.1"}]}]}
                for i in range(1, 4)
            ],
        )
        html = landing.render_html(
            cat,
            cat_slug_for={},
            regulation_summaries=[],
            ctx=_ctx(),
        )
        # ``description`` interpolated into <meta name="description">.
        assert "3 curated Splunk monitoring use cases across 3 domains" in html
