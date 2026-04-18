#!/usr/bin/env python3
"""Fill the `- **References:**` field for every UC that does not have one.

Strategy (in order of preference, first non-empty wins):
  1. Splunkbase app IDs mentioned anywhere in the UC body: `Splunkbase 5580`,
     `(5580)`, `(Splunkbase 5580)`. These are converted to markdown links
     `https://splunkbase.splunk.com/app/<id>`.
  2. CIM Models referenced in the UC — produce a single CIM docs link to the
     first model.
  3. Known `App/TA:` short names (e.g. `Splunk_TA_nix`) → a curated map to the
     canonical Splunkbase URL.
  4. Generic fallback — link to the main Splunk Lantern category landing page.

The script is idempotent and never overwrites an existing References line.
It only adds a `- **References:**` line after the **Known false positives**
line (or, if absent, before the `---` separator) to stay consistent with
existing UC structure.

Usage:
    python3 scripts/fill_references.py            # preview counts only
    python3 scripts/fill_references.py --write    # write changes to .md files
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
UC_DIR = os.path.join(REPO_ROOT, "use-cases")

SPLUNKBASE_ID_RE = re.compile(
    r"(?:Splunkbase\s*)?\(?\s*(\d{3,5})\s*\)?",
    re.IGNORECASE,
)
SPLUNKBASE_ANY_RE = re.compile(r"\bSplunkbase\s+(\d{3,5})\b", re.IGNORECASE)
PAREN_ID_RE = re.compile(r"\((\d{3,5})\)")
BACKTICK_RE = re.compile(r"`([^`]+)`")

# Canonical short-name → Splunkbase ID map for the most common TAs that do
# not include the ID inline. IDs verified against Splunkbase.
TA_ID_MAP: Dict[str, int] = {
    "Splunk_TA_nix": 833,
    "Splunk_TA_windows": 742,
    "Splunk_TA_aws": 1876,
    "Splunk_TA_microsoft-cloudservices": 3110,
    "Splunk_TA_google-cloudplatform": 3088,
    "Splunk_TA_snow": 1928,
    "Splunk_TA_okta": 6553,
    "Splunk_TA_o365": 4055,
    "Splunk_TA_vmware": 2026,
    "Splunk_TA_cisco-meraki": 5580,
    "Splunk_TA_paloalto": 2757,
    "Splunk_TA_f5-bigip": 2680,
    "Splunk_TA_checkpoint": 2646,
    "Splunk_TA_crowdstrike": 5994,
    "Splunk_TA_esxilogs": 3215,
    "Splunk_TA_hypervisor": 1284,
    "Splunk_TA_squid": 3005,
    "Splunk_TA_cylance": 3403,
    "Splunk_TA_sentinel-one": 5278,
    "Splunk_TA_defender": 3610,
    "Splunk_TA_edgehub": 7577,
    "Splunk_TA_networkflow": 2846,
    "Splunk_TA_netscaler": 2724,
    "Splunk_TA_cisco-ios": 1467,
    "Splunk_TA_cisco-ise": 1915,
    "Splunk_TA_cisco-umbrella": 5758,
}

# Short app name → Splunkbase ID (when the UC body uses plain backticks
# without the ID).
NAME_ID_MAP: Dict[str, int] = {
    "Splunk Enterprise Security": 263,
    "Splunk ITSI": 1841,
    "Splunk IT Service Intelligence": 1841,
    "Splunk UBA": 2941,
    "Splunk User Behavior Analytics": 2941,
    "Splunk DB Connect": 2686,
    "Splunk Common Information Model Add-on": 1621,
    "Splunk Industrial Asset Intelligence": 4893,
    "Splunk OT Security Add-on": 5151,
    "Splunk App for Palo Alto Networks": 7505,
    "Splunk Add-on for AWS": 1876,
    "Splunk Add-on for Microsoft Cloud Services": 3110,
    "Splunk Add-on for Microsoft Office 365": 4055,
    "Splunk Add-on for Google Cloud Platform": 3088,
    "Splunk Add-on for Unix and Linux": 833,
    "Splunk Add-on for Microsoft Windows": 742,
    "Splunk Add-on for Okta Identity Cloud": 6553,
    "Splunk Add-on for ServiceNow": 1928,
    "Splunk Add-on for CrowdStrike FDR": 5994,
    "Splunk Add-on for VMware": 2026,
    "Splunk Add-on for Cisco Meraki": 5580,
    "Cisco Security Cloud": 7404,
    "Cisco ThousandEyes App for Splunk": 7719,
    "Check Point App for Splunk": 4293,
    "Fortinet FortiGate App for Splunk": 2800,
    "IT Essentials Work": 5403,
}

CIM_DOC_BASE = "https://docs.splunk.com/Documentation/CIM/latest/User/"

FALLBACK_LINK = "[Splunk Lantern — use case library](https://lantern.splunk.com/)"


def collect_splunkbase_ids(uc_text: str) -> List[Tuple[int, str]]:
    """Return a list of (id, label) pairs in document order, deduplicated.

    IMPORTANT: Numbers that appear in prose (Windows Event IDs, error codes,
    HTTP statuses, port numbers, etc.) must NEVER be interpreted as
    Splunkbase app IDs.  We therefore ONLY treat a number as a Splunkbase
    ID when it is preceded by the explicit `Splunkbase ` keyword, or appears
    in a `https://splunkbase.splunk.com/app/N` URL.
    """
    ids: Dict[int, str] = {}
    # 1. Explicit `Splunkbase N` tokens (e.g. `Splunkbase 5580`).
    for m in SPLUNKBASE_ANY_RE.finditer(uc_text):
        aid = int(m.group(1))
        if 100 <= aid <= 99999 and aid not in ids:
            ids[aid] = f"Splunkbase app {aid}"
    # 2. Full URLs to Splunkbase apps (already written as a link somewhere).
    for m in re.finditer(r"https?://splunkbase\.splunk\.com/app/(\d+)", uc_text):
        aid = int(m.group(1))
        if 100 <= aid <= 99999 and aid not in ids:
            ids[aid] = f"Splunkbase app {aid}"
    # 3. Backticked TA short names mapped via TA_ID_MAP.
    for m in BACKTICK_RE.finditer(uc_text):
        token = m.group(1).strip()
        if token in TA_ID_MAP:
            aid = TA_ID_MAP[token]
            ids.setdefault(aid, token)
    # 4. Plain-text app names mapped via NAME_ID_MAP.
    for name, aid in NAME_ID_MAP.items():
        if name in uc_text and aid not in ids:
            ids[aid] = name
    return [(aid, label) for aid, label in ids.items()]


def collect_cim_models(uc_text: str) -> List[str]:
    """Extract CIM model names from a `- **CIM Models:** X, Y` line."""
    m = re.search(r"\n[-*]\s+\*\*CIM Models:\*\*\s*([^\n]+)", uc_text)
    if not m:
        return []
    raw = m.group(1).strip()
    if raw.upper() in ("N/A", "NONE"):
        return []
    parts = [p.strip().split("(")[0].strip() for p in raw.split(",") if p.strip()]
    return [p for p in parts if p and p.upper() != "N/A"]


def build_reference_line(uc_text: str) -> str:
    """Compose a single `- **References:** ...` line for this UC."""
    refs: List[str] = []
    for aid, label in collect_splunkbase_ids(uc_text)[:3]:
        url = f"https://splunkbase.splunk.com/app/{aid}"
        refs.append(f"[{label}]({url})")
    for model in collect_cim_models(uc_text)[:1]:
        slug = model.replace(" ", "_")
        refs.append(f"[CIM: {model}]({CIM_DOC_BASE}{slug})")
    if not refs:
        refs.append(FALLBACK_LINK)
    return "- **References:** " + ", ".join(refs)


UC_HEAD_RE = re.compile(r"^### UC-\d+\.\d+\.\d+\s+·\s+", re.MULTILINE)
ANY_HEADING_RE = re.compile(r"^#{1,3}\s+", re.MULTILINE)
SEP_RE = re.compile(r"^---\s*$", re.MULTILINE)


def split_ucs(text: str) -> List[Tuple[int, int]]:
    """Return [(start, end)] byte ranges for each UC block.

    A UC block ends at the next UC heading OR at any other heading
    (subcategory heading like `### 9.6 Foo`, or `## 10. Security`) that
    would otherwise swallow content the UC does not own.
    """
    uc_starts = [m.start() for m in UC_HEAD_RE.finditer(text)]
    all_heads = sorted(m.start() for m in ANY_HEADING_RE.finditer(text))
    ranges: List[Tuple[int, int]] = []
    for i, start in enumerate(uc_starts):
        end = len(text)
        for h in all_heads:
            if h > start:
                end = h
                break
        ranges.append((start, end))
    return ranges


def insert_ref_in_block(block: str) -> Tuple[str, bool]:
    """If block lacks a References line, insert one and return (new_block, True)."""
    if re.search(r"\n[-*]\s+\*\*References:\*\*", block):
        return block, False
    ref_line = build_reference_line(block)

    kfp_idx = re.search(r"\n[-*]\s+\*\*Known false positives:\*\*[^\n]*\n", block)
    if kfp_idx:
        insert_at = kfp_idx.end()
        new_block = block[:insert_at] + ref_line + "\n" + block[insert_at:]
        return new_block, True

    sep = SEP_RE.search(block)
    if sep:
        new_block = block[: sep.start()] + ref_line + "\n\n" + block[sep.start() :]
        return new_block, True

    if not block.endswith("\n"):
        block += "\n"
    return block + ref_line + "\n", True


ORPHAN_REF_RE = re.compile(
    r"\n\n(?:- \*\*References:\*\*[^\n]*\n)+",
    re.MULTILINE,
)


def clean_orphan_refs(text: str, uc_ranges: List[Tuple[int, int]]) -> str:
    """Remove `- **References:**` lines that sit between UC blocks (i.e. NOT
    inside any UC range). These are stranded fragments from an earlier,
    buggy insertion pass.
    """
    # Build a set of 'inside' byte positions for quick lookup
    inside = [False] * (len(text) + 1)
    for a, b in uc_ranges:
        for i in range(a, b):
            inside[i] = True
    out: List[str] = []
    cursor = 0
    for m in re.finditer(r"^- \*\*References:\*\*[^\n]*\n?", text, re.MULTILINE):
        a = m.start()
        if not inside[a]:
            out.append(text[cursor:a])
            cursor = m.end()
    out.append(text[cursor:])
    return "".join(out)


def process_file(path: str, write: bool) -> Tuple[int, int, int]:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    ranges = split_ucs(original)
    if not ranges:
        return 0, 0, 0
    cleaned = clean_orphan_refs(original, ranges)
    # Re-compute ranges on the cleaned text (positions shift after deletions)
    ranges = split_ucs(cleaned)
    total = len(ranges)
    touched = 0
    orphans_removed = 1 if cleaned != original else 0
    out: List[str] = []
    cursor = 0
    for start, end in ranges:
        out.append(cleaned[cursor:start])
        block = cleaned[start:end]
        new_block, changed = insert_ref_in_block(block)
        if changed:
            touched += 1
        out.append(new_block)
        cursor = end
    out.append(cleaned[cursor:])
    new_text = "".join(out)
    if write and new_text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return total, touched, orphans_removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="persist changes")
    args = ap.parse_args()

    cat_files = sorted(
        os.path.join(UC_DIR, f)
        for f in os.listdir(UC_DIR)
        if f.startswith("cat-") and f.endswith(".md") and f != "cat-00-preamble.md"
    )

    grand_total = 0
    grand_touched = 0
    grand_orphan_files = 0
    for path in cat_files:
        total, touched, orphans = process_file(path, args.write)
        grand_total += total
        grand_touched += touched
        grand_orphan_files += orphans
        if touched or orphans:
            tag = f" (orphans cleaned)" if orphans else ""
            print(f"  {os.path.basename(path):40}  +{touched:4}/{total} UCs{tag}")
    print("-" * 60)
    print(f"Total UCs: {grand_total}, References inserted: {grand_touched}, "
          f"files with orphans cleaned: {grand_orphan_files}")
    if not args.write:
        print("(dry run — pass --write to persist changes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
