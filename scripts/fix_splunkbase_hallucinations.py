#!/usr/bin/env python3
"""Fix hallucinated Splunkbase app IDs across UC sidecars.

Verified against the live Splunkbase API + curated catalog at
data/splunkbase-catalog.json. Two classes of correction:

1. *ID swap* - wrong ID for a real app. Replace every wrong_id
   reference with the correct_id (URL and inline mentions).
2. *Removal* - the claimed app does not exist on Splunkbase at all.
   Per-UC bespoke prose rewrite removes the false ID and replaces
   with verified guidance.

Idempotent: re-running on already-fixed sidecars is a no-op.

The mapping below was validated on the live Splunkbase REST API on
2026-05-11. Every "correct_id" returned HTTP 200 with a matching
title; every removed reference returned HTTP 404 *or* mapped to a
completely unrelated product (e.g. ID 4022 is "TA-metricator-hec-for-
nmon", not "Splunk Add-on for Cisco ACI" as ~80 UCs claimed).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ID_CORRECTIONS: dict[str, tuple[str, str]] = {
    "1567": ("3549", "Splunk Add-on for Salesforce"),
    "1664": ("3418", "Splunk Add-on for NetApp Data ONTAP"),
    "1759": ("1658", "Splunk Add-on for NetFlow"),
    "1810": ("3215", "Splunk Add-on for VMware"),
    "2812": ("1352", "App for Cisco Network Data (TA-cisco_ios)"),
    "2946": ("2934", "Splunk Add-on for Infoblox"),
    "3303": ("4496", "Splunk Connect for Docker"),
    "3491": ("1841", "Splunk IT Service Intelligence"),
    "3890": ("3471", "Cisco Splunk Add-on for AppDynamics"),
    "4022": ("1897", "Cisco ACI Add-on for Splunk Enterprise (deprecated)"),
    "4291": ("1918", "Arista Networks Telemetry For Splunk"),
    "4309": ("1897", "Cisco ACI Add-on for Splunk Enterprise (deprecated)"),
    "4495": ("1918", "Arista Networks Telemetry For Splunk"),
    "4844": ("5089", "Splunk Add-on for VMware Metrics"),
    "4856": ("4241", "VMware NSX-T Splunk App"),
    "5076": ("3103", "TA for Nutanix Prism"),
    "5380": ("5089", "Splunk Add-on for VMware Metrics"),
    "5596": ("6254", "Splunk Add-on for GitHub"),
    "5598": ("6254", "Splunk Add-on for GitHub"),
    "5953": ("7828", "Cisco Intersight Add-on for Splunk"),
    "6797": ("1918", "Arista Networks Telemetry For Splunk"),
    "6876": ("1917", "Cisco Nexus 9k Add-on for Splunk Enterprise (deprecated)"),
}

REMOVE_IDS: set[str] = {
    "361",
    "2814",
    "2926",
    "4347",
    "5263",
    "5715",
}


def swap_id_references(text: str, wrong_id: str, correct_id: str) -> str:
    """Replace every reference of ``wrong_id`` with ``correct_id``.

    Handles every form that occurs in this corpus, in order:

    1. Markdown link text ``[<id>](.../app/<id>)`` - rewrite both halves.
    2. URL only ``splunkbase.splunk.com/app/<id>``.
    3. Bold ``**<id>**``.
    4. ``Splunkbase <id>`` (with or without bold/backticks).
    5. ``(Splunkbase 1234)`` or ``(1234)`` inside a clear app context.
    6. Multi-ID prereq lists: ``releases <id> (<vendor>)``, ``release <id>``,
       ``TA <id>``, ``Splunk_TA_<x> <id>``, ``add-on <id>``, ``app <id>``.

    Skips bare numbers that are not preceded by an app-context cue, so that
    e.g. ``RFC 4291`` is left alone.
    """
    wid = re.escape(wrong_id)

    md_link_pat = re.compile(
        r"\[\s*(?:\*\*\s*)?Splunkbase\s+(?:\*\*\s*)?\`?" + wid + r"\`?(?:\s*\*\*)?\s*\]"
        r"\(\s*(?:https?://)?splunkbase\.splunk\.com/app/" + wid + r"\s*\)"
    )
    text = md_link_pat.sub(
        f"[Splunkbase {correct_id}](https://splunkbase.splunk.com/app/{correct_id})", text
    )
    md_link_short_pat = re.compile(
        r"\[\s*\`?" + wid + r"\`?\s*\]\(\s*(?:https?://)?splunkbase\.splunk\.com/app/" + wid + r"\s*\)"
    )
    text = md_link_short_pat.sub(
        f"[{correct_id}](https://splunkbase.splunk.com/app/{correct_id})", text
    )
    md_link_mismatch_pat = re.compile(
        r"\[\s*\`?" + wid + r"\`?\s*\]\(\s*(?:https?://)?splunkbase\.splunk\.com/app/(\d+)\s*\)"
    )
    text = md_link_mismatch_pat.sub(lambda m: f"[{m.group(1)}](https://splunkbase.splunk.com/app/{m.group(1)})", text)

    url_pat = re.compile(r"(splunkbase\.splunk\.com/app/)" + wid + r"(?![0-9])")
    text = url_pat.sub(r"\g<1>" + correct_id, text)

    bold_pat = re.compile(r"\*\*" + wid + r"\*\*")
    text = bold_pat.sub(correct_id, text)

    inline_pat = re.compile(r"(\bSplunkbase\s+)" + wid + r"(?![0-9])", re.IGNORECASE)
    text = inline_pat.sub(r"\g<1>" + correct_id, text)

    paren_pat = re.compile(r"(\(\s*)" + wid + r"(\s*\))")
    text = paren_pat.sub(r"\g<1>" + correct_id + r"\g<2>", text)

    contextual_pat = re.compile(
        r"(?P<cue>\b(?:releases?|TA|add-on|app|version|build|install(?:ing|ed)?|confirm|"
        r"Splunk_TA_[A-Za-z0-9_\-]+|`?Splunk_TA_[A-Za-z0-9_\-]+`?)\s+)"
        + wid + r"(?![0-9])",
        re.IGNORECASE,
    )
    text = contextual_pat.sub(lambda m: m.group("cue") + correct_id, text)

    ta_comma_pat = re.compile(
        r"(?P<cue>`?Splunk_TA_[A-Za-z0-9_\-]+`?\s*,\s*)" + wid + r"(?![0-9])",
        re.IGNORECASE,
    )
    text = ta_comma_pat.sub(lambda m: m.group("cue") + correct_id, text)

    backtick_pat = re.compile(r"`" + wid + r"`")
    text = backtick_pat.sub(correct_id, text)

    paren_with_suffix_pat = re.compile(r"(\bSplunkbase\s+)" + wid + r"(\s*[,;)])", re.IGNORECASE)
    text = paren_with_suffix_pat.sub(r"\g<1>" + correct_id + r"\g<2>", text)

    return text


REMOVAL_REWRITES: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "361": [
        (
            re.compile(
                r"Splunk\s+Enterprise\s+(?:9\.x|10\.x|[0-9]+\.x|\d+\.\d+)?\s*"
                r"\(\[?Splunkbase\s+361\]?\(?https?://splunkbase\.splunk\.com/app/361\)?\)?",
                re.IGNORECASE,
            ),
            "Splunk Enterprise",
        ),
        (
            re.compile(
                r"\[Splunkbase\s+361\]\(https?://splunkbase\.splunk\.com/app/361\)"
                r"\s+packaging\s+for\s+on-prem\s+Enterprise",
                re.IGNORECASE,
            ),
            "Splunk Enterprise admin role configuration",
        ),
    ],
    "2814": [
        (
            re.compile(
                r"(?:optional\s+)?\*?\*?Splunk\s+Add-on\s+for\s+Cisco\s+Unified\s+Contact\s+Center\*?\*?\s*"
                r"\(\[?Splunkbase\s+2814\]?(?:\(?https?://splunkbase\.splunk\.com/app/2814\)?)?\)?",
                re.IGNORECASE,
            ),
            "**Splunk DB Connect** ([Splunkbase 2686](https://splunkbase.splunk.com/app/2686)) for UCCE/UCCX Informix database extracts",
        ),
        (
            re.compile(
                r"\*?\*?Splunk\s+Add-on\s+for\s+Cisco\s+UCCE/UCCX\*?\*?\s*"
                r"\(\*?\*?2814\*?\*?\)",
                re.IGNORECASE,
            ),
            "**Splunk DB Connect** (Splunkbase 2686)",
        ),
        (
            re.compile(r"\(Splunkbase\s+2814\)", re.IGNORECASE),
            "(no Splunkbase add-on; use Splunk DB Connect 2686)",
        ),
        (
            re.compile(r"https?://splunkbase\.splunk\.com/app/2814", re.IGNORECASE),
            "https://splunkbase.splunk.com/app/2686",
        ),
    ],
    "2926": [
        (
            re.compile(
                r"\bSplunk\s+Add-on\s+for\s+Microsoft\s+SQL\s+Server\s*"
                r"\(\[?Splunkbase\s+2926\]?\(?https?://splunkbase\.splunk\.com/app/2926\)?\)?",
                re.IGNORECASE,
            ),
            "Splunk Add-on for Microsoft SQL Server ([Splunkbase 2648](https://splunkbase.splunk.com/app/2648))",
        ),
        (
            re.compile(
                r"\bSplunk(?:base)?\s+(?:Add-on\s+for\s+)?Workday\s*"
                r"(?:RaaS\s*)?\(\[?Splunkbase\s+2926\]?\(?https?://splunkbase\.splunk\.com/app/2926\)?\)?",
                re.IGNORECASE,
            ),
            "Workday RaaS modular inputs (custom; no official Splunkbase add-on for Workday)",
        ),
        (
            re.compile(r"\(Splunkbase\s+2926\)", re.IGNORECASE),
            "(custom modular input - no official Splunkbase add-on)",
        ),
        (
            re.compile(r"\[Splunkbase\s+2926\]\(https?://splunkbase\.splunk\.com/app/2926\)", re.IGNORECASE),
            "(custom modular input - no official Splunkbase add-on)",
        ),
        (
            re.compile(r"https?://splunkbase\.splunk\.com/app/2926", re.IGNORECASE),
            "https://splunkbase.splunk.com/app/2648",
        ),
    ],
    "4347": [
        (
            re.compile(
                r"Splunk\s+Industrial\s+Asset\s+Intelligence\s*"
                r"\(\[?Splunkbase\s+4347\]?\(?https?://splunkbase\.splunk\.com/app/4347\)?\)?",
                re.IGNORECASE,
            ),
            "Splunk Industrial Asset Intelligence (legacy product; no current Splunkbase add-on)",
        ),
        (
            re.compile(r"\(Splunkbase\s+4347\)", re.IGNORECASE),
            "(legacy product, no current Splunkbase add-on)",
        ),
        (
            re.compile(r"\[Splunkbase\s+4347\]\(https?://splunkbase\.splunk\.com/app/4347\)", re.IGNORECASE),
            "legacy product (no Splunkbase add-on)",
        ),
        (
            re.compile(r"https?://splunkbase\.splunk\.com/app/4347", re.IGNORECASE),
            "https://www.splunk.com/en_us/blog/industries/introducing-splunk-industrial-asset-intelligence.html",
        ),
    ],
    "5263": [
        (
            re.compile(
                r"Splunk\s+Add-on\s+for\s+Dell\s+EMC\s+PowerEdge\s*"
                r"\(\[?Splunkbase\s+5263\]?\(?https?://splunkbase\.splunk\.com/app/5263\)?\)?",
                re.IGNORECASE,
            ),
            "Dell iDRAC SNMP/syslog (via Splunk Connect for Syslog or SC4SNMP)",
        ),
        (
            re.compile(r"\*?\*?Dell\*?\*?\s+\*?\*?PowerEdge\*?\*?\s+add-on\s+\(5263\)", re.IGNORECASE),
            "**Dell iDRAC** SNMP/syslog collector (via SC4Syslog or SC4SNMP - no dedicated PowerEdge Splunkbase add-on)",
        ),
        (
            re.compile(r"PowerEdge\s+TA\s+\(5263\)", re.IGNORECASE),
            "Dell iDRAC SNMP/syslog collector (no dedicated PowerEdge Splunkbase add-on)",
        ),
        (
            re.compile(r"\(Splunkbase\s+5263\)", re.IGNORECASE),
            "(via iDRAC SNMP/syslog - no dedicated PowerEdge add-on)",
        ),
        (
            re.compile(r"https?://splunkbase\.splunk\.com/app/5263", re.IGNORECASE),
            "https://www.dell.com/support/kbdoc/en-us/000178021/dell-idrac-snmp-and-syslog-configuration",
        ),
    ],
    "5715": [
        (
            re.compile(
                r"Splunk\s+Real\s+User\s+Monitoring\s*"
                r"\(\[?Splunkbase\s+5715\]?\(?https?://splunkbase\.splunk\.com/app/5715\)?\)?",
                re.IGNORECASE,
            ),
            "Splunk Real User Monitoring (part of Splunk Observability Cloud; not a separate Splunkbase add-on)",
        ),
        (
            re.compile(r"\(Splunkbase\s+5715\)", re.IGNORECASE),
            "(part of Splunk Observability Cloud)",
        ),
    ],
}


SCAN_FIELDS = (
    "app",
    "dataSources",
    "implementation",
    "detailedImplementation",
    "description",
    "value",
    "knownFalsePositives",
    "visualization",
    "spl",
    "cimSpl",
    "title",
    "grandmaExplanation",
    "exclusions",
    "evidence",
    "schema",
    "dataModelAcceleration",
)

NESTED_LIST_FIELDS = (
    "references",
    "evidence",
    "exclusions",
    "schema",
)

NESTED_STRING_LIST_FIELDS = (
    "equipmentModels",
    "equipment",
    "dataSources",
    "prerequisiteUseCases",
)


def fix_slash_separated(text: str) -> str:
    """Rewrite ``A/B/C`` runs of IDs when any is in ID_CORRECTIONS.

    Examples
    --------
    ``4022/4856/1810`` -> ``1897/4241/3215``
    Bare 3-5 digit numbers separated only by ``/`` qualify; mixed alpha sequences
    (e.g. ``v4022/r2``) are skipped.
    """
    pat = re.compile(r"(?<![A-Za-z0-9])(\d{3,5}(?:/\d{3,5}){1,})(?![A-Za-z0-9])")

    def repl(m: re.Match[str]) -> str:
        ids = m.group(1).split("/")
        new_ids = [ID_CORRECTIONS.get(i, (i, ""))[0] or i for i in ids]
        return "/".join(new_ids)

    return pat.sub(repl, text)


def _apply_string_fixes(s: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    new_s = s
    for wrong_id, (correct_id, label) in ID_CORRECTIONS.items():
        if re.search(r"\b" + wrong_id + r"\b", new_s):
            next_s = swap_id_references(new_s, wrong_id, correct_id)
            if next_s != new_s:
                changes.append(f"swap {wrong_id} -> {correct_id} ({label})")
                new_s = next_s
    next_s = fix_slash_separated(new_s)
    if next_s != new_s:
        changes.append("rewrite slash-separated ID list")
        new_s = next_s
    for remove_id in REMOVE_IDS:
        patterns = REMOVAL_REWRITES.get(remove_id, [])
        for pat, repl in patterns:
            next_s = pat.sub(repl, new_s)
            if next_s != new_s:
                changes.append(f"remove {remove_id} via pattern")
                new_s = next_s
    return new_s, changes


def fix_uc(payload: dict) -> tuple[dict, list[str]]:
    """Apply ID corrections to one UC sidecar payload.

    Returns (new_payload, list_of_change_descriptions).
    """
    changes: list[str] = []
    for field in SCAN_FIELDS:
        v = payload.get(field)
        if not isinstance(v, str) or not v:
            continue
        new_v, sub_changes = _apply_string_fixes(v)
        if new_v != v:
            payload[field] = new_v
            for c in sub_changes:
                changes.append(f"{field}: {c}")
    for field in NESTED_LIST_FIELDS:
        items = payload.get(field)
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for k, val in list(item.items()):
                if not isinstance(val, str):
                    continue
                new_val, sub_changes = _apply_string_fixes(val)
                if new_val != val:
                    item[k] = new_val
                    for c in sub_changes:
                        changes.append(f"{field}[{idx}].{k}: {c}")
    for field in NESTED_STRING_LIST_FIELDS:
        items = payload.get(field)
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items):
            if not isinstance(item, str):
                continue
            new_val, sub_changes = _apply_string_fixes(item)
            if new_val != item:
                items[idx] = new_val
                for c in sub_changes:
                    changes.append(f"{field}[{idx}]: {c}")
    return payload, changes


def main(argv: list[str] | None = None) -> int:
    write = "--write" in (argv or sys.argv[1:])
    total_changed = 0
    total_changes = 0
    for p in sorted((ROOT / "content").glob("cat-*/UC-*.json")):
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        new_payload, changes = fix_uc(payload)
        if changes:
            total_changed += 1
            total_changes += len(changes)
            uc_id = payload.get("id", "?")
            print(f"UC-{uc_id} ({len(changes)} fix{'es' if len(changes) > 1 else ''}):")
            for c in changes:
                print(f"  - {c}")
            if write:
                p.write_text(json.dumps(new_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print()
    print(f"Files affected: {total_changed}")
    print(f"Total corrections: {total_changes}")
    print(f"{'WROTE' if write else 'DRY-RUN'} (pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
