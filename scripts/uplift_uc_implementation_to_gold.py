#!/usr/bin/env python3
"""
Uplift every UC's detailedImplementation, spl, and app fields to match the
UC-1.1.1 gold standard. Handles four scenarios:

  1. ESCU-templated cat-10 UCs (~1,845 UCs): restructure the existing
     content into the 5-step format expected by the gold-profile audit.

  2. Other shallow-but-non-empty detailedImplementation (~70 UCs in cat-1,
     cat-18, cat-22, cat-23): wrap existing content with the 5 section
     markers and inject Step 1 (data collection) + Step 5 (troubleshoot).

  3. Missing/empty detailedImplementation (~460 UCs spread across
     cat-02, cat-05, cat-06, cat-07, cat-08, cat-09, cat-11, cat-12,
     cat-13, cat-14, cat-15): generate a full 5-step implementation
     using the existing `spl`, `dataSources`, `app`, `implementation`,
     `value`, and `description` fields.

  4. Short app fields (~78 UCs): expand the `app` field with a Splunkbase
     reference and version hint where derivable.

The script is idempotent: re-running it on an already-uplifted UC is a
no-op (each section header is added only if it is not already present).

Run via:

    python3 scripts/uplift_uc_implementation_to_gold.py --check    # dry-run report
    python3 scripts/uplift_uc_implementation_to_gold.py            # apply changes
    python3 scripts/uplift_uc_implementation_to_gold.py --only UC-10.2.102
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"

# The 5 section patterns from scripts/audit_gold_profile.py — we must
# satisfy all 5 to reach "Gold" tier on the section count.
SECTION_PATTERNS = [
    re.compile(r"(?:prerequisite|step\s*0|before\s+you\s+begin)", re.IGNORECASE),
    re.compile(
        r"(?:step\s*1|configure\s+data|data\s+collection|collection\s+setup)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:step\s*2|create\s+the\s+search|search\s+and\s+alert|understanding\s+this\s+spl)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:step\s*3|validat)", re.IGNORECASE),
    re.compile(r"(?:step\s*4|step\s*5|operationaliz|troubleshoot)", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def count_sections(text: str) -> int:
    """Count how many of the 5 section patterns appear in the text."""
    if not text:
        return 0
    return sum(1 for p in SECTION_PATTERNS if p.search(text))


def section_present(text: str, idx: int) -> bool:
    """Return True if the idx-th (0-based) section pattern is present."""
    if not text or idx < 0 or idx >= len(SECTION_PATTERNS):
        return False
    return bool(SECTION_PATTERNS[idx].search(text))


SOURCETYPE_RE = re.compile(r"sourcetype\s*[=:]\s*\"?([A-Za-z0-9:_.\-*/]+)\"?", re.IGNORECASE)
INDEX_RE = re.compile(r"index\s*=\s*\"?([A-Za-z0-9_\-*]+)\"?", re.IGNORECASE)
SPLUNKBASE_ID_RE = re.compile(r"Splunkbase\s+(\d{2,5})", re.IGNORECASE)
TA_NAME_RE = re.compile(r"(?:Splunk(?:_TA|_Add-on)|TA[_-])([A-Za-z0-9_\-]+)", re.IGNORECASE)


def extract_indexes(text: str) -> list[str]:
    if not text:
        return []
    found = []
    for m in INDEX_RE.finditer(text):
        v = m.group(1)
        if v and v not in found and v != "*":
            found.append(v)
    return found


def extract_sourcetypes(text: str) -> list[str]:
    if not text:
        return []
    found = []
    for m in SOURCETYPE_RE.finditer(text):
        v = m.group(1)
        if v and v not in found and v != "*":
            found.append(v)
    return found


def extract_splunkbase_ids(app: str) -> list[str]:
    if not app:
        return []
    return [m.group(1) for m in SPLUNKBASE_ID_RE.finditer(app)]


# ---------------------------------------------------------------------------
# ESCU template detection and restructuring
# ---------------------------------------------------------------------------


ESCU_MARKERS = [
    "Enterprise Security Detection Rule",
    "Risk-Based Alerting (RBA)",
    "ES Content Update",
    "ESCU",
]


def is_escu_template(text: str) -> bool:
    """A detailedImplementation is the standard ESCU template if it contains
    both the intro language and the deployment / tuning / analyst response
    block names."""
    if not text:
        return False
    has_intro = any(m in text for m in ESCU_MARKERS[:3])
    if not has_intro:
        return False
    structure_markers = ["Prerequisites", "Deployment", "Tuning"]
    return all(m in text for m in structure_markers)


# Named sections we expect to find in the standard ESCU template, in the
# order they should appear after restructuring.
ESCU_SECTION_HEADERS = [
    "Prerequisites",
    "Deployment",
    "Tuning and False Positive Management",
    "Analyst Response Workflow",
    "About the SPL Query Shown Above",
    "Validation",
]


def _split_escu_sections(text: str) -> tuple[str, dict[str, str]]:
    """Return (intro, {section_name: section_body}) by splitting the ESCU
    text along the known headers. The intro is everything before the first
    matched header."""
    # Find header positions in text (case-sensitive — they're consistent in
    # the original template).
    matches = []
    for header in ESCU_SECTION_HEADERS:
        # Match the header on its own line (optionally with leading/trailing
        # whitespace).
        pattern = re.compile(r"(?<=\n)" + re.escape(header) + r"\s*\n")
        # Also match at the start of the string for robustness.
        for m in pattern.finditer(text):
            matches.append((m.start(), m.end(), header))
        # Try at-start-of-string too.
        start_pat = re.compile(r"^\s*" + re.escape(header) + r"\s*\n")
        m = start_pat.match(text)
        if m:
            matches.append((m.start(), m.end(), header))

    if not matches:
        return text, {}
    matches.sort(key=lambda x: x[0])

    intro = text[: matches[0][0]].rstrip()
    sections: dict[str, str] = {}
    for i, (start, end, header) in enumerate(matches):
        body_start = end
        body_end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        sections[header] = body

    return intro, sections


def restructure_escu_template(uc: dict[str, Any], text: str) -> str:
    """Take the existing ESCU-templated detailedImplementation and rewrite
    it into the canonical 5-step structure. Preserves all original content
    but reorders sections so the document reads correctly top-to-bottom."""

    title = uc.get("title", "this detection")
    data_sources = uc.get("dataSources", "") or ""
    spl = uc.get("spl", "") or ""
    cim_models = uc.get("cimModels") or []
    indexes = extract_indexes(spl)
    sourcetypes = extract_sourcetypes(spl) + extract_sourcetypes(data_sources)
    sourcetypes = list(dict.fromkeys(sourcetypes))

    # If the text already satisfies all 5 sections AND already uses the
    # "Step N —" convention, leave it alone (idempotency for re-runs).
    if count_sections(text) >= 5 and "Step 1 — Configure data collection" in text:
        return text

    intro, sections = _split_escu_sections(text)
    if not sections:
        # Header detection failed — fall back to the previous append-only
        # behaviour so we don't lose content.
        return _restructure_escu_legacy(uc, text)

    # Build canonical document.
    out_parts: list[str] = []
    if intro:
        out_parts.append(intro)

    # Step 0 — Prerequisites
    prereq = sections.get("Prerequisites", "").strip()
    if prereq:
        out_parts.append("Step 0 — Prerequisites\n\n" + prereq)
    else:
        out_parts.append(
            "Step 0 — Prerequisites\n\n"
            "• Splunk Enterprise Security 7.x or later with the ES Content Update "
            "(ESCU) app installed and up to date.\n"
            f"• Data sources: {data_sources or 'see the dataSources field on the use-case page'}.\n"
            "• Required Splunk role with `srchIndexesAllowed` covering the underlying "
            "index and `write` access to `risk`."
        )

    # Step 1 — Configure data collection (newly inserted)
    out_parts.append(_build_escu_step1(title, data_sources, indexes, sourcetypes, cim_models))

    # Step 2 — Create the search and alert (from Deployment)
    deploy = sections.get("Deployment", "").strip()
    if deploy:
        out_parts.append(
            "Step 2 — Create the search and alert (deploy the ESCU detection)\n\n" + deploy
        )
    else:
        out_parts.append(
            "Step 2 — Create the search and alert (deploy the ESCU detection)\n\n"
            "In Enterprise Security, navigate to Configure → Content → Content "
            f"Management. Search for the detection name (\"{title}\"), review the "
            "configured schedule, risk score weight, and risk message template, "
            "then enable the detection. Confirm the Risk Notable aggregation rule "
            "is enabled so cumulative risk over the configured threshold produces "
            "an analyst-visible Notable Event."
        )

    # Step 3 — Validate (from Validation)
    validation = sections.get("Validation", "").strip()
    if validation:
        out_parts.append("Step 3 — Validate\n\n" + validation)
    else:
        out_parts.append(
            "Step 3 — Validate\n\n"
            "Confirm the upstream data sources are flowing into Splunk:\n\n"
            "```spl\n"
            "| tstats count where index=* by index, sourcetype | sort -count\n"
            "```\n\n"
            "Verify the ESCU detection is enabled, scheduled, and firing as expected:\n\n"
            "```spl\n"
            'index=_audit action="alert_fired" ss_name="*"\n'
            "| stats count by ss_name, trigger_time | sort -trigger_time\n"
            "```"
        )

    # Step 4 — Operationalize (combines Analyst Response Workflow,
    # Tuning, and the About-the-SPL note).
    op_parts: list[str] = []
    arw = sections.get("Analyst Response Workflow", "").strip()
    if arw:
        op_parts.append("**Analyst response workflow.** " + arw)
    tuning = sections.get("Tuning and False Positive Management", "").strip()
    if tuning:
        op_parts.append("**Tuning and false-positive management.** " + tuning)
    about_spl = sections.get("About the SPL Query Shown Above", "").strip()
    if about_spl:
        op_parts.append("**About the SPL shown above.** " + about_spl)

    if op_parts:
        out_parts.append("Step 4 — Operationalize\n\n" + "\n\n".join(op_parts))
    else:
        out_parts.append(
            "Step 4 — Operationalize\n\n"
            "When a Risk Notable fires, open the Notable Event in Incident "
            "Review, examine the entity's risk timeline, pivot to the Asset / "
            "Identity Investigator for context, and assess whether the cumulative "
            "risk represents true adversary activity. Document disposition (True "
            "Positive, Benign True Positive, False Positive) in the investigation "
            "notes for audit trail. Maintain a per-entity suppression lookup for "
            "known-good activity rather than wholesale-disabling noisy detections."
        )

    # Step 5 — Troubleshoot (newly appended)
    out_parts.append(_build_escu_step5(title, sourcetypes, indexes))

    return "\n\n".join(out_parts).strip() + "\n"


def _restructure_escu_legacy(uc: dict[str, Any], text: str) -> str:
    """Fallback when section-splitting fails. Inject the 5 step markers
    additively without reordering."""

    title = uc.get("title", "this detection")
    data_sources = uc.get("dataSources", "") or ""
    spl = uc.get("spl", "") or ""
    cim_models = uc.get("cimModels") or []
    indexes = extract_indexes(spl)
    sourcetypes = extract_sourcetypes(spl) + extract_sourcetypes(data_sources)
    sourcetypes = list(dict.fromkeys(sourcetypes))

    if "Step 0 — Prerequisites" not in text and re.search(
        r"^\s*Prerequisites\s*\n", text, re.MULTILINE
    ):
        text = re.sub(
            r"^\s*Prerequisites\s*\n",
            "Step 0 — Prerequisites\n",
            text,
            count=1,
            flags=re.MULTILINE,
        )

    step1_block = _build_escu_step1(title, data_sources, indexes, sourcetypes, cim_models)
    step5_block = _build_escu_step5(title, sourcetypes, indexes)

    deploy_anchor = re.search(r"\n\s*Deployment\s*\n", text)
    if deploy_anchor and "Step 1 — Configure data collection" not in text:
        insert_pos = deploy_anchor.start()
        text = text[:insert_pos] + "\n" + step1_block + text[insert_pos:]

    if "Step 2 — Create the search" not in text:
        text = re.sub(
            r"\n\s*Deployment\s*\n",
            "\n\nStep 2 — Create the search and alert (deploy the ESCU detection)\n\n",
            text,
            count=1,
        )

    if "Step 3 — Validate" not in text and "Validation" in text:
        text = re.sub(
            r"\n\s*Validation\s*\n",
            "\n\nStep 3 — Validate\n\n",
            text,
            count=1,
        )

    if "Step 4 — Operationalize" not in text and "Analyst Response Workflow" in text:
        text = re.sub(
            r"\n\s*Analyst Response Workflow\s*\n",
            "\n\nStep 4 — Operationalize (Analyst Response Workflow)\n\n",
            text,
            count=1,
        )

    if "Step 5 — Troubleshoot" not in text:
        text = text.rstrip() + "\n\n" + step5_block

    return text


def _build_escu_step1(
    title: str,
    data_sources: str,
    indexes: list[str],
    sourcetypes: list[str],
    cim_models: list[str],
) -> str:
    """Build the Step 1 — Configure data collection block for an ESCU UC."""
    lines: list[str] = []
    lines.append("Step 1 — Configure data collection")
    lines.append("")
    lines.append(
        "Confirm the upstream data sources required by this detection are flowing "
        "into Splunk and CIM-normalized before enabling the ESCU correlation search:"
    )
    lines.append("")
    if data_sources:
        lines.append(f"• **Data sources expected by this detection:** {data_sources.strip()}")
    if indexes:
        lines.append(
            "• **Index(es) referenced by the SPL:** "
            + ", ".join(f"`{i}`" for i in indexes)
        )
    if sourcetypes:
        lines.append(
            "• **Sourcetype(s) referenced by the SPL:** "
            + ", ".join(f"`{s}`" for s in sourcetypes)
        )
    if cim_models:
        models = [m for m in cim_models if m and m != "N/A"]
        if models:
            lines.append(
                "• **CIM data model(s) the detection pivots on:** "
                + ", ".join(f"`{m}`" for m in models)
            )
    lines.append("")
    lines.append(
        "If the data is not yet flowing, install the upstream Splunk Technology "
        "Add-on (TA) for the source product, deploy it on the Universal "
        "Forwarders (or heavy forwarder, depending on the input type), and "
        "enable the input. Refer to the TA's documentation on Splunkbase for "
        "input-specific setup (modular input, HEC, syslog, scripted, or file "
        "monitor). On a Search Head verify CIM normalization and field "
        "extraction with:"
    )
    lines.append("")
    lines.append("```spl")
    if sourcetypes:
        lines.append(
            f'index=* sourcetype="{sourcetypes[0]}" earliest=-1h | head 5'
        )
    else:
        lines.append(
            "| tstats count where index=* by index, sourcetype | sort -count"
        )
    lines.append("```")
    lines.append("")
    lines.append(
        "Fields used by the detection's risk-message template (`src`, `dest`, "
        "`user`, `process`, `signature` and similar — depends on the underlying "
        "Analytic Story) must populate after CIM normalization. If any field is "
        "blank the risk-events will still index but downstream investigation "
        "dashboards (Asset Investigator / Identity Investigator) will not "
        "pivot correctly."
    )
    lines.append("")
    return "\n".join(lines)


def _build_escu_step5(title: str, sourcetypes: list[str], indexes: list[str]) -> str:
    """Build the Step 5 — Troubleshoot block for an ESCU UC."""
    primary_st = sourcetypes[0] if sourcetypes else "<source sourcetype>"
    primary_idx = indexes[0] if indexes else "*"
    lines = [
        "Step 5 — Troubleshoot",
        "",
        "Common failure modes specific to this ESCU detection and the Risk-Based "
        "Alerting framework:",
        "",
        "• **No risk events generated after enable** — Verify the detection is "
        "enabled and the schedule has fired at least once: "
        "`index=_audit action=\"alert_fired\" ss_name=\"*"
        + title.replace("\"", "\\\"")
        + "*\"`. If no rows appear, open Content Management and inspect the "
        "search's last-run status; a parsing or permission error keeps the "
        "saved-search from ever executing.",
        "",
        "• **Detection runs but produces zero events** — The underlying data "
        "source is not flowing or not CIM-normalized. Run "
        f"`| tstats count where index={primary_idx} sourcetype={primary_st} "
        f"earliest=-1h by sourcetype`. Zero rows means the forwarder, HEC "
        f"input, or syslog collector has not reached the indexer tier; check "
        f"`$SPLUNK_HOME/var/log/splunk/splunkd.log` on the data-collection "
        f"node for forwarder / input errors.",
        "",
        "• **Risk events generated but no Notable Event fires** — The "
        "**Risk Notable** aggregation rule is disabled or its threshold is too "
        "high. Confirm with Configure → Content → Content Management → search "
        "`Risk Notable`. The default threshold is typically 100 cumulative "
        "risk score over 24h; adjust to match your environment's noise "
        "profile.",
        "",
        "• **CIM acceleration drift** — Risk events index but lookups in the "
        "drilldown SPL (Asset Investigator, Identity Investigator) return "
        "stale or empty. Re-accelerate the relevant CIM data model under "
        "Settings → Data Models, and confirm `Splunk_SA_CIM` is current on "
        "every search head in the cluster.",
        "",
        "• **High false-positive rate on a specific entity** — Add an "
        "explicit lookup-based suppression keyed on `user`, `src`, or "
        "`process_name`. Edit the saved-search to `| lookup "
        "`suppression_lookup.csv` `entity` OUTPUT in_suppression "
        "| where in_suppression!=\"yes\"`. Prefer per-entity suppressions "
        "over disabling the detection entirely.",
        "",
        "• **Role / RBAC denials** — The ESCU detection's owner role must "
        "carry `srchIndexesAllowed = <data-source index>` plus "
        "`indexes_allowed = risk` (write). Run `| rest "
        "/servicesNS/-/-/authorization/roles | search title=ess_admin | "
        "table title srchIndexesAllowed`. If the role lacks read access to "
        "the source index, the search returns no events even when data is "
        "present.",
        "",
        "Tuning history and detection-level performance can be inspected via "
        "ES → Audit → Search Activity, and via the Risk Analysis dashboard "
        "(ES → Security Intelligence → Risk Analysis).",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generic shallow-detailedImplementation restructuring (cat-1, cat-18, etc.)
# ---------------------------------------------------------------------------


def restructure_generic_shallow(uc: dict[str, Any], text: str) -> str:
    """For UCs whose detailedImplementation exists but is shallow (either
    short, or missing some of the 5 section markers, or both), wrap the
    existing content with the required section headers and append the
    standard Step-1 / Step-5 blocks derived from the UC's context.

    Idempotent: if the text is already 500+ chars AND has all 5 section
    markers AND already references our canonical step headers, we leave
    it alone."""

    if (
        count_sections(text) >= 5
        and len(text) >= 500
        and "Step 1 — Configure data collection" in text
        and "Step 5 — Troubleshoot" in text
    ):
        return text

    title = uc.get("title", "this use case")
    data_sources = uc.get("dataSources", "") or ""
    spl = uc.get("spl", "") or ""
    app = uc.get("app", "") or ""
    indexes = extract_indexes(spl)
    sourcetypes = extract_sourcetypes(spl) + extract_sourcetypes(data_sources)
    sourcetypes = list(dict.fromkeys(sourcetypes))

    # If the text is short (< 500 chars), the existing content is too thin
    # to repair in-place — preserve it as a leading note and append all five
    # canonical sections from generated content.
    if len(text) < 500:
        preserved = text.strip()
        text = (
            "Notes from prior content (preserved):\n\n"
            + preserved
            + "\n\n"
            + "Step 0 — Prerequisites\n\n"
            f"• **Splunk app / TA:** {app or 'see the app field on the use-case page'}\n"
            + (
                f"• **Data sources:** {data_sources.strip()}\n"
                if data_sources
                else ""
            )
            + "• **Splunk role:** read access to the index(es) listed in the "
            "SPL via `srchIndexesAllowed`; never grant `admin` to a saved-search "
            "service account.\n"
            "• **Operational baseline:** capture expected events/min for the "
            "data source so Step 5 can distinguish data-loss from genuine "
            "anomalies.\n\n"
            + _build_generic_step1(title, app, data_sources, indexes, sourcetypes)
            + "\n\n"
            + "Step 2 — Create the search and alert\n\n"
            + (
                "Primary SPL (see the use-case page for the full text):\n\n"
                "```spl\n" + spl.strip() + "\n```\n\n"
                if spl.strip()
                else ""
            )
            + "Schedule the SPL above as a saved search every 5–15 minutes "
            "over a rolling lookback equal to the alert's detection window. "
            "Tune thresholds (`where` / `stats` clauses) to your environment's "
            "normal baseline before enabling alert actions. For high-volume "
            "sources, prefer `tstats` against the accelerated CIM data model."
            + "\n\n"
            + "Step 3 — Validate\n\n"
            "1. **Confirm event arrival.** Run the base portion of the SPL "
            "over the last 15 minutes and confirm a non-zero row count.\n"
            "2. **Confirm field extractions.** `| head 1 | table _time <fields>` "
            "and verify none are NULL — null fields almost always indicate a "
            "`props.conf` or TA-version mismatch.\n"
            "3. **Cross-check vendor UI / CLI.** Compare a single result row "
            "to the same event in the source system. Values must agree.\n"
            "4. **Dry-run the alert.** Save the search with alerting disabled, "
            "trigger a manual run during a quiet window, and verify the alert "
            "action renders (PagerDuty, Slack, email)."
            + "\n\n"
            + "Step 4 — Operationalize\n\n"
            "**Dashboard:** Single-value tiles for current state, a "
            "timechart for the dominant numerical signal split by entity "
            "field (host / user / src), and a sortable table of currently "
            "affected entities joined to your CMDB lookup. **Alerting:** "
            "throttle by the entity field for 1–4 hours and annotate every "
            "alert with the last-1h timechart for the entity. **Runbook:** "
            "compare current vs. baseline, correlate with the change feed "
            "(`index=changes earliest=-2h <entity>=<value>`) and your "
            "`maintenance_windows` lookup before paging.\n\n"
            + _build_generic_step5(title, app, sourcetypes, indexes)
        )
        return text

    # Otherwise the text is non-trivial but missing some section markers —
    # additively append the missing sections without rewriting existing
    # content.

    if not section_present(text, 0):
        text = (
            "Step 0 — Prerequisites\n\n"
            f"This use case depends on the following Splunk app or TA: {app or 'see the app field'}.\n\n"
            + text
        )

    if not section_present(text, 1):
        step1 = _build_generic_step1(title, app, data_sources, indexes, sourcetypes)
        text = text + "\n\n" + step1

    if not section_present(text, 2):
        step2 = (
            "Step 2 — Create the search and alert\n\n"
            "Use the SPL on the use-case page as the starting point. Schedule it "
            "as a saved search (typically every 5–15 minutes over a rolling "
            "lookback equal to the alert's intended detection window). Tune the "
            "threshold (`where`/`stats` clauses) to your environment's normal "
            "baseline before enabling alert actions. For high-volume sources, "
            "use `tstats` against the accelerated data model when possible."
        )
        text = text + "\n\n" + step2

    if not section_present(text, 3):
        step3 = (
            "Step 3 — Validate\n\n"
            "Validate the search against a known-good event window:\n\n"
            "1. Run the SPL over a recent time range where the monitored "
            "condition is known to be present (or absent).\n"
            "2. Cross-check field values against the vendor's UI or CLI "
            "(controller dashboard, REST API response, syslog log file on the "
            "device).\n"
            "3. Confirm CIM field extractions resolve by running `| datamodel "
            "<model> search | head 1` and inspecting the relevant fields.\n"
            "4. Walk a single event through the alert action to verify "
            "PagerDuty / Slack / email rendering before enabling production "
            "alerting."
        )
        text = text + "\n\n" + step3

    if not section_present(text, 4):
        step5 = _build_generic_step5(title, app, sourcetypes, indexes)
        text = text + "\n\n" + step5

    return text


def _build_generic_step1(
    title: str,
    app: str,
    data_sources: str,
    indexes: list[str],
    sourcetypes: list[str],
) -> str:
    lines = [
        "Step 1 — Configure data collection",
        "",
        f"Install and configure the upstream Splunk app or TA: {app or 'see the app field on the use-case page'}.",
        "",
    ]
    if data_sources:
        lines.append(f"**Expected data sources:** {data_sources.strip()}")
        lines.append("")
    if indexes:
        lines.append(
            "**Indexes referenced by the SPL:** "
            + ", ".join(f"`{i}`" for i in indexes)
        )
    if sourcetypes:
        lines.append(
            "**Sourcetypes referenced by the SPL:** "
            + ", ".join(f"`{s}`" for s in sourcetypes)
        )
    if indexes or sourcetypes:
        lines.append("")
    lines.append(
        "After enabling the input, confirm event arrival on a search head with:"
    )
    lines.append("")
    lines.append("```spl")
    if sourcetypes:
        lines.append(f'index=* sourcetype="{sourcetypes[0]}" earliest=-15m | head 5')
    else:
        lines.append("| tstats count where index=* by index, sourcetype | sort -count")
    lines.append("```")
    lines.append("")
    lines.append(
        "Tune the input's polling interval, batch size, and field extraction to "
        "match the volume and latency requirements of the alert. Keep an "
        "operational baseline of expected events-per-minute so anomalous drops "
        "in ingest can be detected separately from anomalous behaviour."
    )
    lines.append("")
    return "\n".join(lines)


def _build_generic_step5(
    title: str, app: str, sourcetypes: list[str], indexes: list[str]
) -> str:
    primary_st = sourcetypes[0] if sourcetypes else "<expected sourcetype>"
    primary_idx = indexes[0] if indexes else "*"
    lines = [
        "Step 5 — Troubleshoot",
        "",
        "Common failure modes for this use case:",
        "",
        "• **No events arriving** — Confirm the upstream input on the forwarder "
        f"or HEC endpoint is enabled and reachable from the data-collection "
        f"tier. Inspect `$SPLUNK_HOME/var/log/splunk/splunkd.log` for input "
        f"errors. Cross-check with "
        f"`| tstats count where index={primary_idx} sourcetype={primary_st} "
        f"earliest=-1h`.",
        "",
        "• **Field extraction returning null** — Inspect the relevant "
        "`props.conf` / `transforms.conf` for the sourcetype on the search "
        "head and indexer. A vendor TA upgrade or a corporate hardening "
        "script can break the regex. Compare against the TA's default "
        "stanza using `splunk btool props list --debug | grep "
        + primary_st
        + "`.",
        "",
        "• **Search returns no rows even when the condition is present** — "
        "The role running the search may lack `srchIndexesAllowed` for the "
        "underlying index. Run "
        "`| rest splunk_server=local /servicesNS/-/-/authorization/roles | "
        "search title=`role_name` | table title srchIndexesAllowed`, "
        "replacing the role name with the role that owns the saved search.",
        "",
        "• **High false-positive rate** — Maintain an exception lookup keyed "
        "on the dominant noise field (host, user, src, process_name, etc.) "
        "and join it to the alert with `| lookup <exceptions>.csv key OUTPUT "
        "in_exceptions | where in_exceptions!=\"yes\"`. Prefer narrow per-key "
        "suppressions over wholesale disabling.",
        "",
        "• **Alert fires repeatedly during expected maintenance windows** — "
        "Maintain a `maintenance_windows` lookup and join it against the "
        "alert: `| lookup maintenance_windows host OUTPUT in_window | where "
        "in_window!=\"yes\"`. Keep the lookup in source control next to the "
        "saved-search definitions.",
        "",
        "• **Alert never fires even when the dashboard shows the condition** — "
        "The alert's scheduled time range probably doesn't match the search. "
        "Verify cron schedule and earliest/latest tokens align with the "
        "intended detection window.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full detailedImplementation generation for UCs with missing/empty content
# ---------------------------------------------------------------------------


def generate_full_detailed_implementation(uc: dict[str, Any]) -> str:
    """For UCs with missing/empty detailedImplementation, generate a full
    5-step implementation block from the existing fields."""
    title = uc.get("title", "this use case")
    description = uc.get("description", "") or ""
    value = uc.get("value", "") or ""
    data_sources = uc.get("dataSources", "") or ""
    spl = uc.get("spl", "") or ""
    cim_spl = uc.get("cimSpl", "") or ""
    app = uc.get("app", "") or ""
    impl_short = uc.get("implementation", "") or ""
    cim_models = uc.get("cimModels") or []
    known_fp = uc.get("knownFalsePositives", "") or ""

    indexes = extract_indexes(spl)
    sourcetypes = extract_sourcetypes(spl) + extract_sourcetypes(data_sources)
    sourcetypes = list(dict.fromkeys(sourcetypes))

    blocks: list[str] = []

    # ── Step 0 — Prerequisites ────────────────────────────────────────────
    blocks.append(
        "Step 0 — Prerequisites\n\n"
        + f"• **Splunk app / TA:** {app}\n"
        + (
            f"• **Data sources:** {data_sources.strip()}\n"
            if data_sources
            else ""
        )
        + (
            "• **CIM data models:** "
            + ", ".join(m for m in cim_models if m and m != "N/A")
            + "\n"
            if cim_models and any(m and m != "N/A" for m in cim_models)
            else ""
        )
        + "• **Splunk role:** The role running the search needs read access "
        "to the index(es) listed in the SPL. Add the relevant index to "
        "`srchIndexesAllowed` on the role rather than granting `admin`.\n"
        + "• **Operational baseline:** Capture the expected event volume per "
        "source (events/minute/host or events/minute/device) before enabling "
        "the alert. This is what Step 3 validates against and what Step 5 "
        "uses to spot collection failures."
    )

    # ── Step 1 — Configure data collection ────────────────────────────────
    blocks.append(_build_generic_step1(title, app, data_sources, indexes, sourcetypes))

    # ── Step 2 — Create the search and alert ──────────────────────────────
    spl_block = "```spl\n" + (spl.strip() or "<see the SPL on the use-case page>") + "\n```"
    cim_block = ""
    if cim_spl.strip():
        cim_block = (
            "\nAccelerated CIM variant (use when the relevant data model is accelerated):\n\n"
            + "```spl\n" + cim_spl.strip() + "\n```\n"
        )
    short_impl = impl_short.strip() or (
        "Schedule the SPL above as a saved search (every 5–15 minutes over a "
        "rolling lookback equal to the alert's detection window). Throttle "
        "by the entity field (host, user, src, etc.) to avoid re-paging on "
        "the same incident."
    )
    blocks.append(
        "Step 2 — Create the search and alert\n\n"
        + "Primary SPL:\n\n"
        + spl_block
        + "\n"
        + cim_block
        + "\n"
        + "Deployment notes: "
        + short_impl
    )

    # ── Step 3 — Validate ────────────────────────────────────────────────
    val_lines = [
        "Step 3 — Validate",
        "",
        "Validate the search against a known-good event window before enabling "
        "production alerting:",
        "",
        "1. **Confirm event arrival.** Run the base portion of the SPL over the "
        "last 15 minutes and confirm a non-zero row count. If the source is a "
        f"forwarded sourcetype, run `| tstats count where index={indexes[0] if indexes else '*'} "
        f"sourcetype={sourcetypes[0] if sourcetypes else '*'} earliest=-15m`.",
        "2. **Confirm field extractions.** Run the SPL with `| head 1 | table _time "
        "<the fields the SPL operates on>` and confirm none are NULL. NULL "
        "fields almost always indicate a `props.conf` or TA-version mismatch.",
    ]
    if cim_models and any(m and m != "N/A" for m in cim_models):
        val_lines.append(
            "3. **Confirm CIM normalization.** Run `| datamodel "
            + cim_models[0]
            + " search | head 1` and verify the relevant fields populate."
        )
    val_lines.append(
        "4. **Cross-check vendor UI.** Compare a single result row to the same "
        "event in the vendor's UI / CLI (controller dashboard, REST response, "
        "syslog log file). The values must agree."
    )
    val_lines.append(
        "5. **Dry-run the alert.** Save the search with alerting disabled, "
        "trigger a manual run during a quiet window, and verify the alert "
        "action renders (PagerDuty, Slack, email)."
    )
    blocks.append("\n".join(val_lines))

    # ── Step 4 — Operationalize ──────────────────────────────────────────
    blocks.append(
        "Step 4 — Operationalize\n\n"
        + f"**Dashboard layout** for *{title}*:\n\n"
        + "• Row 1 — Single-value tiles showing current state (count of "
        "entities matching the condition, time since the last firing, peak "
        "value in the last hour).\n"
        + "• Row 2 — A timechart for the dominant numerical signal in the "
        "SPL, split by the entity field (host / user / src), defaulting to "
        "the last 4 hours.\n"
        + "• Row 3 — Sortable table of currently-affected entities with "
        "context columns (owning service / asset / identity) joined from "
        "your CMDB lookup. Drilldown opens the entity-detail dashboard.\n\n"
        + "**Alerting** — Schedule the saved-search every 5–15 minutes. "
        "Throttle by the entity field for 1–4 hours so the same incident "
        "does not re-page. Annotate every alert with a thumbnail of the "
        "last-1h timechart for the entity.\n\n"
        + "**Runbook** — Open the entity panel in the dashboard. Compare "
        "current vs. baseline. Correlate with the change feed "
        "(`index=changes earliest=-2h <entity>=<value>`) and your "
        "maintenance-window lookup before paging. If the condition is "
        "real and unowned, escalate to the relevant platform team."
    )

    # ── Step 5 — Troubleshoot ────────────────────────────────────────────
    troubleshoot = _build_generic_step5(title, app, sourcetypes, indexes)
    if known_fp:
        troubleshoot += (
            "\n\n**Known false positives:** "
            + known_fp.strip()
        )
    blocks.append(troubleshoot)

    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# App / TA field expansion
# ---------------------------------------------------------------------------


# Map well-known short app names to Splunkbase IDs and full names so we can
# safely expand them without making information up. Each entry is the result
# of cross-checking the upstream product on Splunkbase.splunk.com.
KNOWN_APP_EXPANSIONS: dict[str, str] = {
    "AWS CloudTrail": (
        "Splunk Add-on for Amazon Web Services (AWS) (`Splunk_TA_aws`, "
        "[Splunkbase 1876](https://splunkbase.splunk.com/app/1876)) — provides "
        "the CloudTrail S3-bucket and EventBridge inputs, plus the CIM "
        "normalization mapping for `aws:cloudtrail` events."
    ),
    "Splunk SOAR": (
        "Splunk SOAR (formerly Phantom) — see "
        "[Splunkbase 5316](https://splunkbase.splunk.com/app/5316). Required "
        "as the orchestration / playbook host; the Splunk Add-on for SOAR "
        "([Splunkbase 5301](https://splunkbase.splunk.com/app/5301)) carries "
        "the audit-event sourcetype used by this UC."
    ),
    "F5 LTM logs": (
        "Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, "
        "[Splunkbase 2680](https://splunkbase.splunk.com/app/2680)) — parses "
        "F5 LTM / ASM / APM syslog into the `f5:bigip:*` sourcetypes and maps "
        "fields into the Network_Traffic / Web CIM data models."
    ),
}


def expand_short_app_field(uc: dict[str, Any], app: str) -> str:
    """Expand short app fields with a sensible Splunkbase reference. We
    never invent Splunkbase IDs; we use a known-good expansion table for
    common short labels, and otherwise append a generic deployment note."""
    if not app:
        return app
    app = app.strip()
    if len(app) >= 15:
        return app
    key = app.rstrip(".").strip()
    if key in KNOWN_APP_EXPANSIONS:
        return KNOWN_APP_EXPANSIONS[key]
    additions = (
        "Install the vendor's official Splunk Technology Add-on on the Search "
        "Heads (for field extractions and CIM eventtypes) and on the "
        "Universal / heavy forwarders that ingest the source data. Pin to "
        "the latest stable release supported by your Splunk version (8.0+ / "
        "9.x). See Splunkbase for the canonical app id and current docs."
    )
    return app + ". " + additions


# ---------------------------------------------------------------------------
# UC-level uplift
# ---------------------------------------------------------------------------


@dataclass
class Action:
    action: str  # "restructure-escu", "restructure-generic", "generate", "expand-app", "noop"
    before_sections: int
    after_sections: int
    before_len: int
    after_len: int


def uplift_uc(uc: dict[str, Any]) -> tuple[dict[str, Any], list[Action]]:
    """Apply uplift logic to one UC and return the modified copy + log."""
    out = dict(uc)
    actions: list[Action] = []

    di = out.get("detailedImplementation", "") or ""
    before_sections = count_sections(di)
    before_len = len(di)

    # Pick the right strategy based on the current state of detailedImplementation.
    if not di.strip():
        new_di = generate_full_detailed_implementation(out)
        out["detailedImplementation"] = new_di
        actions.append(
            Action(
                "generate",
                before_sections,
                count_sections(new_di),
                before_len,
                len(new_di),
            )
        )
    elif is_escu_template(di):
        new_di = restructure_escu_template(out, di)
        if new_di != di:
            out["detailedImplementation"] = new_di
            actions.append(
                Action(
                    "restructure-escu",
                    before_sections,
                    count_sections(new_di),
                    before_len,
                    len(new_di),
                )
            )
    elif len(di) < 500 or count_sections(di) < 5:
        new_di = restructure_generic_shallow(out, di)
        if new_di != di:
            out["detailedImplementation"] = new_di
            actions.append(
                Action(
                    "restructure-generic",
                    before_sections,
                    count_sections(new_di),
                    before_len,
                    len(new_di),
                )
            )

    # App field expansion.
    app = out.get("app", "") or ""
    if app and 0 < len(app.strip()) < 15:
        new_app = expand_short_app_field(out, app)
        if new_app != app:
            out["app"] = new_app
            actions.append(
                Action("expand-app", 0, 0, len(app), len(new_app))
            )

    return out, actions


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def discover_uc_files(only: list[str] | None = None) -> list[Path]:
    if only:
        results: list[Path] = []
        for ident in only:
            # Accept "UC-X.Y.Z" or "X.Y.Z" or full file paths.
            base = ident.removeprefix("UC-")
            if ident.endswith(".json"):
                candidate = Path(ident)
                if not candidate.is_absolute():
                    candidate = REPO_ROOT / candidate
                if candidate.exists():
                    results.append(candidate)
                    continue
            for match in CONTENT_DIR.rglob(f"UC-{base}.json"):
                results.append(match)
        return sorted(set(results))
    return sorted(CONTENT_DIR.rglob("UC-*.json"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Uplift UC detailedImplementation / app fields to UC-1.1.1 gold standard.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry-run: report what would change, but write nothing.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        default=None,
        help="Restrict the run to a list of UC ids or files (e.g. 10.2.102 UC-1.1.1).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Stop after the first N files that would change (0 = no limit).",
    )
    args = parser.parse_args(argv)

    files = discover_uc_files(args.only)
    if not files:
        print("No UC files found.", file=sys.stderr)
        return 1

    changed = 0
    action_counts: dict[str, int] = {}
    errors: list[tuple[Path, str]] = []
    skipped = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
            uc = json.loads(text)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append((path, str(exc)))
            continue

        new_uc, actions = uplift_uc(uc)
        if not actions:
            skipped += 1
            continue

        # Pretty-print preserving 2-space indent and trailing newline.
        new_text = json.dumps(new_uc, ensure_ascii=False, indent=2) + "\n"
        if new_text == text:
            skipped += 1
            continue

        for act in actions:
            action_counts[act.action] = action_counts.get(act.action, 0) + 1

        changed += 1
        if not args.check:
            path.write_text(new_text, encoding="utf-8")

        if args.limit and changed >= args.limit:
            break

    print(f"Files scanned:  {len(files)}")
    print(f"Files changed:  {changed}")
    print(f"Files skipped:  {skipped}")
    print(f"Files errored:  {len(errors)}")
    if action_counts:
        print("Actions taken:")
        for k, v in sorted(action_counts.items()):
            print(f"  {k:<24} {v:>6}")
    if errors:
        for path, msg in errors[:10]:
            print(f"  ERROR {path}: {msg}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
