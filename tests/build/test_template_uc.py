"""Tests for ``tools/build/templates/uc.py`` — per-UC HTML / JSON / Markdown twins.

The module was at **4.77% line coverage** in ``data/baselines/coverage-v9.1.0.json``
as of v9.1.0 — second of the two zero-or-near-zero coverage surfaces called
out in §P16 of ``docs/health-check-2026-progress.md``.

Strategy
--------

The module exposes three top-level entry points — ``render_html``,
``render_index_json``, ``render_markdown_twin`` — each driven by a
``CatalogUC`` (catalog-wire-format dict) plus its parent
``CatalogCategory`` / ``CatalogSubcategory`` and a
``_helpers.RenderContext``. One representative-UC fixture exercises
roughly 60-70% of the module in one pass.

Each test is hermetic (no I/O, no fixtures on disk), so the runtime stays
well under 1 second.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build.templates import _helpers, uc as uc_template  # noqa: E402


@pytest.fixture
def render_ctx() -> _helpers.RenderContext:
    """A deterministic RenderContext suitable for byte-stable assertions."""
    return _helpers.RenderContext(
        asset_styles="styles.abcd1234.css",
        asset_app_js="app.abcd1234.js",
        build_id="abcd1234",
        generated_at="2026-05-18T12:00:00Z",
        version="9.1.0",
        uc_reverse_prereq={"UC-1.1.1": ("UC-1.1.2", "UC-1.1.3")},
        uc_title_index={
            "UC-1.1.0": ("Prereq Title", "crawl"),
            "UC-1.1.1": ("Self Title", "walk"),
        },
    )


@pytest.fixture
def sample_uc() -> dict:
    """A representative CatalogUC that touches every conditional branch
    in ``render_html`` / ``render_index_json`` / ``render_markdown_twin``."""
    return {
        "i": "1.1.1",
        "n": "Detect anomalous root login bursts",
        "v": "Catch identity-provider compromise within five minutes.",
        "ge": "We watch for sudden bursts of root logins from new locations.",
        "c": "high",
        "f": "intermediate",
        "wv": "walk",
        "pre": ["UC-1.1.0"],
        "t": "Splunk Add-on for Cisco ISE (`Splunk_TA_cisco_ise`)",
        "d": "ise:syslog, ise:auth",
        "sapp": [
            {
                "id": 1907,
                "name": "Splunk Add-on for Cisco ISE",
                "url": "https://splunkbase.splunk.com/app/1907",
                "role": "primary",
            }
        ],
        "ta_link": {
            "name": "Splunk Add-on for Cisco ISE",
            "url": "https://splunkbase.splunk.com/app/1907",
            "id": 1907,
        },
        "premium": ["ES"],
        "q": 'index=ise sourcetype="ise:auth" user=root | stats count by src_ip',
        "qs": "| tstats count from datamodel=Authentication.Failed_Auth by user",
        "a": ["Authentication"],
        "dma": "Authentication",
        "m": "1. Onboard ISE syslog\n2. Map to CIM Authentication\n3. Schedule the SPL",
        "md": "# Detect anomalous root login bursts\n\nFull narrative paragraph one.\n\nFull narrative paragraph two.",
        "z": "Single-value panel + 7-day timechart by src_ip.",
        "script": "",
        "mtype": ["Anomaly", "Audit"],
        "kfp": "Bursty service accounts and break-glass exercises.",
        "refs": "* [Splunk ISE TA](https://splunkbase.splunk.com/app/1907)\n",
        "mitre": ["T1078.004", "T1003"],
        "dtype": "anomaly",
        "sdomain": "identity",
        "reqf": "user, src_ip, event_id",
        "status": "production",
        "reviewed": "2026-05-01",
        "sver": ["9.0", "9.1"],
        "rby": "security-team",
        "e": ["cisco-ise"],
        "em": ["ise-3500"],
        "hw": "Cisco ISE 3.x",
        "ind": "Financial Services",
        "pillar": "Security",
        "regs": ["gdpr"],
        "cmp": [
            {
                "regulation": "gdpr",
                "version": "2016/679",
                "clause": "Art. 32(1)(b)",
                "mode": "satisfies",
                "assurance": "partial",
                "assurance_rationale": "Detects root-login anomalies.",
            }
        ],
        "escu": False,
        "_qt": "silver",
        "_qg": "silver",
    }


@pytest.fixture
def cat() -> dict:
    return {"i": 1, "n": "Identity & Access", "src": "content/cat-01-identity-access/"}


@pytest.fixture
def sub() -> dict:
    return {"i": "1.1", "n": "Authentication", "u": []}


# ---------------------------------------------------------------------------
# render_html
# ---------------------------------------------------------------------------


class TestRenderHtml:
    def test_returns_non_empty_html_with_doctype(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert isinstance(html, str)
        assert html.startswith("<!DOCTYPE html>") or html.lstrip().lower().startswith("<!doctype")

    def test_includes_uc_id_and_title(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "UC-1.1.1" in html
        assert "Detect anomalous root login bursts" in html

    def test_includes_canonical_link_and_json_alternate(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert 'rel="canonical"' in html
        assert "/uc/UC-1.1.1/" in html
        assert 'type="application/json"' in html
        assert "/uc/UC-1.1.1/index.json" in html

    def test_includes_markdown_alternate(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert 'type="text/markdown"' in html
        assert "/uc/UC-1.1.1/uc.md" in html

    def test_includes_jsonld_techarticle(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert '"@type": "TechArticle"' in html or '"@type":"TechArticle"' in html
        assert '"@type": "BreadcrumbList"' in html or '"@type":"BreadcrumbList"' in html

    def test_includes_breadcrumb_links(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "Identity &amp; Access" in html
        assert "Authentication" in html
        assert "Browse" in html

    def test_includes_criticality_and_difficulty_badges(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "badge-crit-high" in html or "high" in html.lower()
        assert "intermediate" in html.lower()

    def test_includes_wave_badge_when_present(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "Wave:" in html
        assert "Walk" in html or "walk" in html

    def test_omits_wave_badge_when_absent(self, sample_uc, cat, sub, render_ctx):
        no_wave = dict(sample_uc)
        no_wave.pop("wv")
        html = uc_template.render_html(no_wave, cat, sub, "identity-access", ctx=render_ctx)
        # ``badge-wave-`` appears in the embedded CSS bundle as a class
        # selector; what we care about is that the rendered span is gone.
        assert '<span class="badge badge-wave-' not in html
        assert "Wave:" not in html

    def test_includes_spl_block(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "sourcetype=&quot;ise:auth&quot;" in html or "ise:auth" in html

    def test_includes_cim_spl_block_when_present(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "tstats" in html
        assert "Authentication" in html

    def test_includes_mitre_techniques(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "T1078.004" in html
        assert "T1003" in html

    def test_includes_regulations(self, sample_uc, cat, sub, render_ctx):
        """The HTML page renders the regulation IDs as badges. Per-clause
        detail (``cmp[]``) only appears in the JSON twin — see
        ``TestRenderIndexJson.test_fields_block_strips_empties``."""
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "gdpr" in html.lower()
        assert "Compliance" in html  # section header
        assert '<span class="badge">gdpr</span>' in html

    def test_includes_known_false_positives(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "Bursty service accounts" in html

    def test_includes_references(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "splunkbase.splunk.com/app/1907" in html

    def test_escapes_xss_in_title(self, cat, sub, render_ctx):
        """XSS payloads in the title must be HTML-escaped wherever they
        land in user-visible HTML. They may legitimately appear inside
        ``<script type="application/ld+json">`` payloads (the browser does
        NOT execute JSON-LD scripts; the ``</`` -> ``<\\/`` rewrite in
        ``_helpers.jsonld_script()`` prevents accidental tag closure).

        The assertion strips JSON-LD blocks and asserts the escaped form
        is what reaches the visible markup."""
        import re

        evil_uc = {
            "i": "9.9.9",
            "n": '<script>alert("XSS")</script>',
            "v": "Test",
        }
        html = uc_template.render_html(evil_uc, cat, sub, "identity-access", ctx=render_ctx)
        visible = re.sub(
            r'<script type="application/ld\+json">.*?</script>',
            "",
            html,
            flags=re.DOTALL,
        )
        assert "<script>alert" not in visible
        assert "&lt;script&gt;" in visible

    def test_minimal_uc_does_not_crash(self, cat, sub, render_ctx):
        minimal = {"i": "1.1.99", "n": "Minimal UC"}
        html = uc_template.render_html(minimal, cat, sub, "identity-access", ctx=render_ctx)
        assert "UC-1.1.99" in html
        assert "Minimal UC" in html

    def test_includes_implementation_section(self, sample_uc, cat, sub, render_ctx):
        html = uc_template.render_html(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "Onboard ISE syslog" in html
        assert "Map to CIM Authentication" in html


# ---------------------------------------------------------------------------
# render_index_json
# ---------------------------------------------------------------------------


class TestRenderIndexJson:
    def test_returns_dict_with_required_keys(self, sample_uc, cat, sub, render_ctx):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert isinstance(payload, dict)
        for key in ("$schema", "version", "id", "shortId", "title", "url", "html", "json", "markdown"):
            assert key in payload, f"missing key: {key}"

    def test_id_carries_uc_prefix_and_shortid_does_not(self, sample_uc, cat, sub, render_ctx):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert payload["id"] == "UC-1.1.1"
        assert payload["shortId"] == "1.1.1"

    def test_urls_anchor_to_site_url(self, sample_uc, cat, sub, render_ctx):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        site = render_ctx.site_url
        assert payload["url"].startswith(site)
        assert payload["json"].startswith(site) and payload["json"].endswith("index.json")
        assert payload["markdown"].startswith(site) and payload["markdown"].endswith("uc.md")

    def test_category_and_subcategory_blocks_populated(self, sample_uc, cat, sub, render_ctx):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert payload["category"]["id"] == 1
        assert payload["category"]["slug"] == "identity-access"
        assert payload["category"]["name"] == "Identity & Access"
        assert payload["subcategory"]["id"] == "1.1"
        assert payload["subcategory"]["name"] == "Authentication"

    def test_fields_block_strips_empties(self, sample_uc, cat, sub, render_ctx):
        # Add a couple of empty fields to the sample to prove they're stripped.
        sample_uc_with_empties = dict(sample_uc)
        sample_uc_with_empties["empty_string"] = ""
        sample_uc_with_empties["empty_list"] = []
        sample_uc_with_empties["null_field"] = None
        payload = uc_template.render_index_json(
            sample_uc_with_empties, cat, sub, "identity-access", ctx=render_ctx
        )
        assert "empty_string" not in payload["fields"]
        assert "empty_list" not in payload["fields"]
        assert "null_field" not in payload["fields"]
        # Non-empty fields survive.
        assert payload["fields"]["i"] == "1.1.1"
        assert payload["fields"]["c"] == "high"

    def test_implementation_ordering_includes_wave_and_prereqs(self, sample_uc, cat, sub, render_ctx):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "implementationOrdering" in payload
        ordering = payload["implementationOrdering"]
        assert ordering["wave"] == "walk"
        assert ordering["prerequisiteUseCases"] == ["UC-1.1.0"]

    def test_implementation_ordering_includes_enabled_by_from_reverse_index(
        self, sample_uc, cat, sub, render_ctx
    ):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert payload["implementationOrdering"]["enabledBy"] == ["UC-1.1.2", "UC-1.1.3"]

    def test_implementation_ordering_absent_when_no_ordering_fields(self, cat, sub, render_ctx):
        minimal = {"i": "9.9.9", "n": "No ordering"}
        payload = uc_template.render_index_json(minimal, cat, sub, "identity-access", ctx=render_ctx)
        assert "implementationOrdering" not in payload

    def test_self_prerequisite_is_filtered_out(self, cat, sub, render_ctx):
        # ``pre`` containing the UC's own id is a content-author mistake;
        # the template must silently filter it.
        weird = {"i": "1.1.1", "n": "Self-cycle", "pre": ["UC-1.1.1", "UC-1.1.0"], "wv": "crawl"}
        payload = uc_template.render_index_json(weird, cat, sub, "identity-access", ctx=render_ctx)
        assert payload["implementationOrdering"]["prerequisiteUseCases"] == ["UC-1.1.0"]

    def test_invalid_wave_is_dropped(self, cat, sub, render_ctx):
        # Use an id that is NOT in the fixture's ``uc_reverse_prereq`` index,
        # so ``enabledBy`` won't be populated and the absence of a valid wave
        # is the only ordering signal under test.
        uc = {"i": "9.9.99", "n": "Bad wave", "wv": "sprint"}
        payload = uc_template.render_index_json(uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "implementationOrdering" not in payload

    def test_payload_is_json_serialisable(self, sample_uc, cat, sub, render_ctx):
        payload = uc_template.render_index_json(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        round_tripped = json.loads(json.dumps(payload, sort_keys=True))
        assert round_tripped == payload


# ---------------------------------------------------------------------------
# render_markdown_twin
# ---------------------------------------------------------------------------


class TestRenderMarkdownTwin:
    def test_returns_markdown_string(self, sample_uc, cat, sub, render_ctx):
        md = uc_template.render_markdown_twin(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert isinstance(md, str)
        assert md.startswith("# UC-1.1.1")

    def test_includes_plain_language_block(self, sample_uc, cat, sub, render_ctx):
        md = uc_template.render_markdown_twin(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert sample_uc["ge"] in md

    def test_includes_section_headers(self, sample_uc, cat, sub, render_ctx):
        md = uc_template.render_markdown_twin(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert "## Value" in md
        assert "## SPL" in md
        assert "## Implementation" in md
        assert "## MITRE ATT&CK" in md

    def test_emits_no_html_tags(self, sample_uc, cat, sub, render_ctx):
        md = uc_template.render_markdown_twin(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        # Pure-markdown contract — no <tag> sequences (allow `<`/`>` in inline code
        # but reject angle-bracket HTML-tag patterns).
        import re

        assert not re.search(r"<[a-z][a-z0-9]*[\s/>]", md), (
            f"render_markdown_twin emitted HTML tags: {md[:200]}"
        )

    def test_deterministic_byte_stable(self, sample_uc, cat, sub, render_ctx):
        md1 = uc_template.render_markdown_twin(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        md2 = uc_template.render_markdown_twin(sample_uc, cat, sub, "identity-access", ctx=render_ctx)
        assert md1 == md2

    def test_minimal_uc_renders_without_error(self, cat, sub, render_ctx):
        minimal = {"i": "1.1.99", "n": "Minimal UC"}
        md = uc_template.render_markdown_twin(minimal, cat, sub, "identity-access", ctx=render_ctx)
        assert "# UC-1.1.99" in md
        assert "Minimal UC" in md


# ---------------------------------------------------------------------------
# Coverage uplift — targeted edge-case tests for the remaining branches
# left after the representative-UC suite above.
# ---------------------------------------------------------------------------


class TestMarkdownTwinEdgeCases:
    """Drive the defensive branches in ``render_markdown_twin``."""

    def test_quick_facts_skipped_when_no_facts(self, cat, sub, render_ctx):
        """Branch 356->365: ``if facts:`` false arm — minimal UC where
        ``_add_fact()`` never appends a row."""
        uc = {"i": "9.9.99", "n": "Bare UC"}
        empty_cat = {"i": "", "n": ""}
        empty_sub = {"i": "", "n": ""}
        md = uc_template.render_markdown_twin(
            uc, empty_cat, empty_sub, "identity-access", ctx=render_ctx
        )
        assert "## Quick facts" not in md

    def test_add_fact_rejects_whitespace_only_value(self, cat, sub, render_ctx):
        """Line 329-330: ``if not value: return`` — a whitespace-only
        string trims to empty and never lands as a fact row."""
        uc = {"i": "1.1.99", "n": "X", "status": "   "}
        md = uc_template.render_markdown_twin(
            uc, cat, sub, "identity-access", ctx=render_ctx
        )
        assert "| Status |" not in md

    def test_pre_skips_blank_entries(self, cat, sub, render_ctx):
        """Line 371-372: ``if not p_str: continue`` — pre-list entry
        that's only whitespace is silently dropped."""
        uc = {"i": "1.1.99", "n": "X", "pre": ["UC-1.1.0", "  "]}
        md = uc_template.render_markdown_twin(
            uc, cat, sub, "identity-access", ctx=render_ctx
        )
        assert "UC-1.1.0" in md
        # Exactly one bullet — the blank one was dropped.
        pre_section = md.split("## Prerequisite use cases", 1)[1].split("##", 1)[0]
        assert pre_section.count("- [") == 1

    def test_kfp_as_list_renders_bullets(self, cat, sub, render_ctx):
        """Lines 427-430: defensive branch when ``kfp`` is a list/tuple
        of items (forward-compat with structured falsePositives)."""
        uc = {
            "i": "1.1.99",
            "n": "X",
            "kfp": ["First case", "   ", "Second case"],
        }
        md = uc_template.render_markdown_twin(
            uc, cat, sub, "identity-access", ctx=render_ctx
        )
        assert "## Known false positives" in md
        assert "- First case" in md
        assert "- Second case" in md

    def test_mitre_skips_blank_entries(self, cat, sub, render_ctx):
        """Branch 441->439: ``if t_str:`` false arm — a blank MITRE entry
        is dropped from the list."""
        uc = {"i": "1.1.99", "n": "X", "mitre": ["T1078", "   ", "T1003"]}
        md = uc_template.render_markdown_twin(
            uc, cat, sub, "identity-access", ctx=render_ctx
        )
        mitre_section = md.split("## MITRE ATT&CK", 1)[1].split("##", 1)[0]
        assert "- T1078" in mitre_section
        assert "- T1003" in mitre_section
        assert mitre_section.count("- ") == 2

    def test_regs_skips_blank_entries(self, cat, sub, render_ctx):
        """Branch 451->449: ``if r_str:`` false arm."""
        uc = {"i": "1.1.99", "n": "X", "regs": ["gdpr", "  ", "hipaa"]}
        md = uc_template.render_markdown_twin(
            uc, cat, sub, "identity-access", ctx=render_ctx
        )
        regs_section = md.split("## Regulations", 1)[1].split("##", 1)[0]
        assert regs_section.count("- ") == 2

    def test_refs_as_list_renders_bullets(self, cat, sub, render_ctx):
        """Lines 463-471: defensive branch when ``refs`` is a list/tuple
        (legacy markdown-corpus shape) instead of the wire-format CSV
        string."""
        uc = {
            "i": "1.1.99",
            "n": "X",
            "refs": ["[A](https://a)", "   ", "[B](https://b)"],
        }
        md = uc_template.render_markdown_twin(
            uc, cat, sub, "identity-access", ctx=render_ctx
        )
        assert "## References" in md
        refs_section = md.split("## References", 1)[1].split("---", 1)[0]
        assert "- [A](https://a)" in refs_section
        assert "- [B](https://b)" in refs_section


class TestRenderHtmlEdgeCases:
    """Drive defensive branches across the various ``_section_*`` helpers."""

    def test_quick_facts_omitted_when_all_fields_empty(self, render_ctx):
        """Line 527-528: ``_section_quick_facts`` returns ``""`` when
        no rows accumulated."""
        uc = {"i": "9.9.99", "n": "Bare"}
        empty_cat = {"i": "", "n": ""}
        empty_sub = {"i": "", "n": ""}
        html = uc_template.render_html(
            uc, empty_cat, empty_sub, "x", ctx=render_ctx
        )
        assert "<h2>Quick facts</h2>" not in html

    def test_implementation_ordering_omitted_when_no_signals(self, cat, sub, render_ctx):
        """Branches inside ``_section_implementation_ordering``:
        ``pre`` empty + ``enables`` empty -> section omitted."""
        uc = {"i": "9.9.99", "n": "X"}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Implementation ordering" not in html

    def test_implementation_ordering_pre_only(self, cat, sub, render_ctx):
        """Branch 622 (pre is truthy) but enables empty."""
        uc = {"i": "9.9.99", "n": "X", "pre": ["UC-1.1.0"]}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Implementation ordering" in html
        assert "Implement first (prerequisites)" in html
        assert "Enables" not in html

    def test_implementation_ordering_enables_only(self, cat, sub, render_ctx):
        """Branch 631 (enables truthy) when pre is empty — uses the
        reverse-prereq index baked into the fixture (UC-1.1.1 enables
        UC-1.1.2 and UC-1.1.3)."""
        uc = {"i": "1.1.1", "n": "X"}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Implementation ordering" in html
        assert "Enables" in html
        assert "Implement first" not in html
        assert "UC-1.1.2" in html

    def test_implementation_ordering_pre_filters_self_reference(self, cat, sub, render_ctx):
        """Line 614: ``pre = [p for p in pre if p != self_full]`` — when
        the UC lists itself in ``pre`` (data error), it must not render
        a self-link.

        The fixture's ``uc_reverse_prereq`` has ``UC-1.1.1`` enabling
        other UCs, so the section will still render via the ``enables``
        path even after self-cycle is filtered."""
        uc = {"i": "1.1.1", "n": "X", "pre": ["UC-1.1.1"]}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Implementation ordering" in html
        # The "Implement first" subsection is omitted because the only
        # entry was the self-reference (now filtered).
        assert "Implement first (prerequisites)" not in html

    def test_implementation_ordering_pre_as_string_treated_as_empty(self, cat, sub, render_ctx):
        """Branch 609->614: ``isinstance(pre_raw, (list, tuple))`` false
        arm — a malformed string ``pre`` value falls through to the empty
        list (defensive guard against schema drift)."""
        uc = {"i": "9.9.99", "n": "X", "pre": "UC-1.1.0"}  # string, not list
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        # The implementation-ordering section is omitted entirely because
        # pre is treated as empty and there is no reverse-enables entry
        # for UC-9.9.99.
        assert "Implementation ordering" not in html

    def test_implementation_ordering_pre_skips_non_string(self, cat, sub, render_ctx):
        """``[p for p in pre_raw if isinstance(p, str) ...]`` — non-string
        entries are skipped."""
        uc = {"i": "9.9.99", "n": "X", "pre": ["UC-1.1.0", 123, None, "  "]}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Implementation ordering" in html
        prereq_block = html.split("Implement first (prerequisites)", 1)[1].split(
            "</ul>", 1
        )[0]
        assert prereq_block.count("<li>") == 1
        assert "UC-1.1.0" in prereq_block

    def test_uc_chip_omits_wave_badge_for_unknown_wave(self, render_ctx):
        """Branch 655->666: ``if pair is not None:`` false arm — when
        ``wave_label`` returns ``None`` (unknown wave), the chip emits
        no wave badge."""
        ctx = _helpers.RenderContext(
            asset_styles="s.css",
            asset_app_js="a.js",
            build_id="b",
            generated_at="2026-05-20",
            version="9.1.0",
            uc_reverse_prereq={"UC-1.1.1": ("UC-1.1.2",)},
            # uc-1.1.2 mapped to an UNKNOWN wave ('sprint' is not in
            # _WAVE_TOOLTIPS) — render_uc_chip must not crash and must
            # not emit a chip-wave span.
            uc_title_index={"UC-1.1.2": ("Downstream UC", "sprint")},
        )
        uc = {"i": "1.1.1", "n": "X"}
        cat = {"i": 1, "n": "Cat"}
        sub = {"i": "1.1", "n": "Sub", "u": []}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=ctx)
        # Chip exists for UC-1.1.2 but with no wave badge.
        chip_block = html.split("Enables", 1)[1].split("</section>", 1)[0]
        assert "UC-1.1.2" in chip_block
        assert "chip-wave" not in chip_block

    def test_dma_spl_dma_only_no_qs(self, cat, sub, render_ctx):
        """Branch 697->699: ``if dma:`` true / ``if qs:`` false — only
        the markdown summary renders, no code block."""
        uc = {"i": "9.9.99", "n": "X", "dma": "Use the Authentication model."}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Data model acceleration" in html
        assert "Use the Authentication model." in html
        # ``qs`` not provided, so no ``lang-spl`` code block in the DMA
        # section. (There may be one elsewhere from regular SPL, but
        # this UC has no ``q`` either.)
        dma_section = html.split("Data model acceleration", 1)[1].split("</section>", 1)[0]
        assert "lang-spl" not in dma_section

    def test_dma_spl_qs_only_no_dma(self, cat, sub, render_ctx):
        """Branch 699->705: ``if dma:`` false / ``if qs:`` true — only
        the code block renders."""
        uc = {"i": "9.9.99", "n": "X", "qs": "| tstats count from datamodel=Auth"}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Data model acceleration" in html
        assert "tstats count" in html

    def test_regulations_mitre_regs_only(self, cat, sub, render_ctx):
        """Branch 748 true / 755 false — regs present, mitre absent."""
        uc = {"i": "9.9.99", "n": "X", "regs": ["gdpr", "hipaa"]}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Compliance" in html
        assert "<h3>Regulations</h3>" in html
        assert "<h3>MITRE" not in html

    def test_regulations_mitre_mitre_only(self, cat, sub, render_ctx):
        """Branch 748 false / 755 true — mitre present, regs absent."""
        uc = {"i": "9.9.99", "n": "X", "mitre": ["T1078"]}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Compliance" in html
        assert "<h3>MITRE" in html
        assert "<h3>Regulations</h3>" not in html

    def test_regulations_mitre_skips_blank_mitre_entries(self, cat, sub, render_ctx):
        """Line 760: ``if not label: continue`` — empty-string MITRE
        entries are filtered."""
        uc = {"i": "9.9.99", "n": "X", "mitre": ["T1078", "", "T1003"]}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        mitre_block = html.split("MITRE", 1)[1].split("</ul>", 1)[0]
        # Exactly two list items rendered.
        assert mitre_block.count("<li>") == 2

    def test_apps_with_sapp_only_no_ta_link(self, cat, sub, render_ctx):
        """Branch 774->790: ``if ta_name:`` false arm — sapp entries
        still render."""
        uc = {
            "i": "9.9.99",
            "n": "X",
            "sapp": [
                {"id": 1, "name": "App One", "url": "https://x/1"},
                {"id": 2, "name": "App Two"},  # no URL — covers line 805
                {"id": 3, "name": "", "url": "https://x/3"},  # no name — line 795
                {"id": 4, "name": "App Four", "url": "https://x/4", "desc": "extras"},
            ],
        }
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Splunkbase apps" in html
        assert "App One" in html
        assert "App Two" in html
        assert "App Four" in html
        assert "extras" in html
        # Empty-name entry is dropped.
        apps_block = html.split("Splunkbase apps", 1)[1].split("</section>", 1)[0]
        # primary TA <em> badge absent because ta_link wasn't supplied.
        assert "primary TA" not in apps_block

    def test_apps_with_ta_link_without_url_renders_plain_text(self, cat, sub, render_ctx):
        """Lines 785-789: ``if ta_url:`` false arm — TA name without
        a URL renders as plain text with the ``(primary TA)`` suffix."""
        uc = {
            "i": "9.9.99",
            "n": "X",
            "ta_link": {"name": "Bare TA"},  # no url
        }
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        apps_block = html.split("Splunkbase apps", 1)[1].split("</section>", 1)[0]
        assert "Bare TA" in apps_block
        assert "primary TA" in apps_block
        # No <a href> for the TA entry because the URL was missing.
        ta_li = apps_block.split("<li>", 1)[1].split("</li>", 1)[0]
        assert "<a href=" not in ta_li

    def test_full_narrative_with_implementation_collapses_into_details(
        self, cat, sub, render_ctx
    ):
        """Lines 827-838: when both ``m`` and ``md`` are present AND
        ``md`` starts with 'Prerequisites', collapse the long version
        into a ``<details>`` element."""
        uc = {
            "i": "9.9.99",
            "n": "X",
            "m": "Short ordered steps.",
            "md": "Prerequisites: Splunk ES + ISE TA.\n\nFull narrative.",
        }
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Detailed walkthrough" in html
        assert "<details>" in html
        assert "Show full narrative" in html

    def test_full_narrative_renders_inline_without_implementation(
        self, cat, sub, render_ctx
    ):
        """The non-details arm of the full-narrative section — when ``m``
        is absent, the long markdown renders inline."""
        uc = {
            "i": "9.9.99",
            "n": "X",
            "md": "Prerequisites: just a single block.",
        }
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        assert "Detailed walkthrough" in html
        assert "<details>" not in html

    def test_provenance_with_reviewed_only(self, cat, sub, render_ctx):
        """Branch 855->857: ``if rby:`` false arm."""
        uc = {"i": "9.9.99", "n": "X", "reviewed": "2026-05-01"}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        prov = html.split("Provenance", 1)[1].split("</section>", 1)[0]
        assert "Last reviewed" in prov
        assert "Reviewer:" not in prov
        assert "Splunk versions:" not in prov

    def test_provenance_with_reviewer_only(self, cat, sub, render_ctx):
        """Branch 853->855 + 857->859 hybrid: ``rby`` only."""
        uc = {"i": "9.9.99", "n": "X", "rby": "ops-team"}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        prov = html.split("Provenance", 1)[1].split("</section>", 1)[0]
        assert "Reviewer: ops-team" in prov
        assert "Last reviewed" not in prov

    def test_provenance_with_sver_only(self, cat, sub, render_ctx):
        """Branch 857->859 with just ``sver`` populated."""
        uc = {"i": "9.9.99", "n": "X", "sver": "9.1, 9.2"}
        html = uc_template.render_html(uc, cat, sub, "x", ctx=render_ctx)
        prov = html.split("Provenance", 1)[1].split("</section>", 1)[0]
        assert "Splunk versions" in prov
        assert "Reviewer:" not in prov
