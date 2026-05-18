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
