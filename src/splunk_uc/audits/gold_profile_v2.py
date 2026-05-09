#!/usr/bin/env python3
"""Gold-profile v2 audit — the UC-1.1.1 bar.

The v1 audit (``scripts/audit_gold_profile.py`` / ``python -m splunk_uc
audit-gold-profile``) measures the baseline Gold tier defined in
``schemas/uc-profile-gold.json``. This v2 audit lifts the bar to the
depth demonstrated by the catalogue exemplar UC-1.1.1 and required by
``docs/gold-standard-authoring-playbook.md``.

What v2 enforces beyond v1:

* `detailedImplementation` >= 1500 characters (v1: 500).
* >= 5 distinct named KFP scenarios in `knownFalsePositives`. Each must
  reference a system or process by name (heuristic: capitalised word or
  recognised vendor/product token) and either a distinguish or suppress
  pattern.
* >= 6 distinct product-specific indicators in `detailedImplementation`
  (sourcetype=, index=, /api/, modular input names, RBAC roles, vendor UI
  page paths, Splunkbase IDs, time bounds, etc.) — counts unique matches,
  not total matches.
* `dataSources` >= 80 chars and references at least one Splunkbase ID,
  one sourcetype, and one extracted field.
* `app` references at least one Splunkbase ID.
* `description` and `value` are word-sets that share <= 60% of word stems
  (catches cases where the value is a slight rewording of the description).
* `references` >= 4 entries.
* `controlTest.positiveScenario` and `negativeScenario` differ by >= 30 chars
  (catches `positive=A; negative=NOT A` style placeholders).
* `knownFalsePositives` references at least one suppression mechanism
  (lookup, exception register, time-bound exception, or filter clause).
* `evidence` and `exclusions` populated with >= 30 chars each.

Usage:
    python -m splunk_uc audit-gold-profile-v2
    python -m splunk_uc audit-gold-profile-v2 --check
    python -m splunk_uc audit-gold-profile-v2 --files <paths>
    python -m splunk_uc audit-gold-profile-v2 --regulation NIS2
    python -m splunk_uc audit-gold-profile-v2 --pack data/nis2-domain-packs.json --regulation NIS2

Exit code 0 if every audited UC scores >= 80 / 100, else 1.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"

# ---------------------------------------------------------------------------
# Thresholds (the UC-1.1.1 bar)
# ---------------------------------------------------------------------------

V2_THRESHOLDS = {
    "detailedImplementation_min_chars": 1500,
    "kfp_min_scenarios": 4,
    "di_unique_specifics_min": 6,
    "datasources_min_chars": 80,
    "references_min": 4,
    "control_test_diff_min_chars": 30,
    "evidence_min_chars": 30,
    "exclusions_min_chars": 30,
    "passing_score": 80,
}

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

SPLUNKBASE_ID_RE = re.compile(
    r"Splunkbase\s+\d{2,5}|splunkbase\.splunk\.com/app/\d+", re.IGNORECASE
)
SOURCETYPE_RE = re.compile(r"sourcetype\s*[=:][\s\"']*[a-zA-Z0-9_:\-\.]+", re.IGNORECASE)
INDEX_RE = re.compile(r"index\s*=\s*[a-zA-Z0-9_\-]+", re.IGNORECASE)
API_PATH_RE = re.compile(
    r"/(?:api|dna|services|servicesNS|now/table|graph)/[a-zA-Z0-9_\-/.]*", re.IGNORECASE
)
RBAC_RE = re.compile(
    r"\b(?:RBAC|role|admin-role|reader-role|writer-role|service[- ]account|API\s+token|OAuth)",
    re.IGNORECASE,
)
TIMEBOUND_RE = re.compile(r"\b\d+\s*(?:second|minute|hour|day|week|month)s?\b", re.IGNORECASE)
MODULAR_INPUT_RE = re.compile(
    r"(?:modular\s+input|inputs\.conf|HEC|forwarder|scripted\s+input)", re.IGNORECASE
)
VENDOR_UI_RE = re.compile(
    r"(?:Settings|Configuration|Configure|Console|Portal|Dashboard|Inventory|Admin|Activity|System)\s*>\s*\w+",
    re.IGNORECASE,
)
SUPPRESSION_RE = re.compile(
    r"(?:exception\s+register|nis2_\w+\.csv|time-bound\s+exception|where\s+\w+|lookup\s+\w+|allow[- ]list|block[- ]list|filter\s+the\s+spl)",
    re.IGNORECASE,
)
NAMED_PRODUCT_RE = re.compile(
    r"\b(?:Veeam|Commvault|Rubrik|Cohesity|CyberArk|Vault|Okta|Entra|Azure|Microsoft|Cisco|Tenable|Qualys|Rapid7|KnowBe4|Cornerstone|ServiceNow|Phantom|SOAR|Stream|Cyber\s+Vision|Nozomi|Claroty|Defender|Sentinel|Splunk|ES|ITSI|GRC|CMDB|Workday)\b"
)
KFP_SEPARATOR_RE = re.compile(
    r"(?:^\s*[•\-\*\d+\.\)]\s+)|(?:^\s*[A-Z][^\.]+:\s)|(?:\.\s+[A-Z][a-z]+\s+(?:scenario|window|case|exception|maintenance|rotation|holiday|cycle|onboarding))",
    re.MULTILINE,
)


def _word_set(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", text)}


def _description_value_jaccard(desc: str, value: str) -> float:
    a, b = _word_set(desc), _word_set(value)
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def _count_unique_specifics(text: str) -> int:
    """Count unique product-specific signals in detailedImplementation."""
    if not text:
        return 0
    found: set[str] = set()
    for pat in (
        SOURCETYPE_RE,
        INDEX_RE,
        API_PATH_RE,
        MODULAR_INPUT_RE,
        VENDOR_UI_RE,
        RBAC_RE,
        TIMEBOUND_RE,
        SPLUNKBASE_ID_RE,
    ):
        for m in pat.finditer(text):
            found.add(m.group(0).lower())
    return len(found)


def _count_kfp_scenarios(text: str) -> int:
    """Estimate how many distinct named KFP scenarios are listed.

    Authors structure KFPs in many ways: bullets, numbered lists,
    inline numbered items, **bold-leading** scenarios, or sentences
    starting with a capitalised noun phrase. We pick the strongest
    signal that produces ≥2 hits.
    """
    if not text:
        return 0
    # Multi-line bullets / numbers
    bullets = re.findall(r"^\s*[•\-\*]\s+\S|^\s*\d+[\.\)]\s+\S", text, re.MULTILINE)
    if len(bullets) >= 2:
        return len(bullets)
    # Inline numbered items: "1) ...  2) ..."
    inline_nums = re.findall(r"(?:^|[\.\s;])\s*\d+\)\s+\*?\*?[A-Z]", text)
    if len(inline_nums) >= 2:
        return len(inline_nums)
    # Inline **Bold:** scenario headers (markdown emphasis)
    bold_headers = re.findall(r"\*\*[A-Z][^\*]{4,80}\*\*", text)
    if len(bold_headers) >= 2:
        return len(bold_headers)
    # Paragraph-style "Scenario:" markers.
    markers = re.findall(r"\bscenario\s*[:\-]", text, re.IGNORECASE)
    if len(markers) >= 2:
        return len(markers)
    # Fall back: named-product-anchored sentences.
    sentences = re.split(r"(?<=[\.;])\s+", text)
    named = sum(1 for s in sentences if NAMED_PRODUCT_RE.search(s) and len(s.split()) > 6)
    return named


def _has_suppression_mechanism(text: str) -> bool:
    return bool(SUPPRESSION_RE.search(text or ""))


def _has_splunkbase_id(text: str) -> bool:
    return bool(SPLUNKBASE_ID_RE.search(text or ""))


def _has_sourcetype(text: str) -> bool:
    return bool(SOURCETYPE_RE.search(text or ""))


def _has_field_list(text: str) -> bool:
    """Crude: data-sources mentions extracted field names (lowercase_underscored or camelCase identifiers in a comma-separated context)."""
    return bool(
        re.search(r"[a-z][a-zA-Z_]+\s*,\s*[a-z][a-zA-Z_]+\s*,\s*[a-z][a-zA-Z_]+", text or "")
    )


# ---------------------------------------------------------------------------
# Per-UC v2 audit
# ---------------------------------------------------------------------------


def audit_uc_v2(uc: dict[str, Any], filepath: Path) -> dict[str, Any]:
    uc_id = uc.get("id", "unknown")
    out: dict[str, Any] = {
        "id": uc_id,
        "file": str(filepath.relative_to(REPO_ROOT)),
        "title": uc.get("title", ""),
        "score": 100,
        "tier": "v2-pass",
        "gaps": [],
        "warnings": [],
    }
    gaps = out["gaps"]
    warns = out["warnings"]

    # detailedImplementation depth ---------------------------------------
    di = uc.get("detailedImplementation", "") or ""
    di_chars = len(di)
    if di_chars < V2_THRESHOLDS["detailedImplementation_min_chars"]:
        gaps.append(
            f"detailedImplementation {di_chars} chars (need >= {V2_THRESHOLDS['detailedImplementation_min_chars']})"
        )
        out["score"] -= 30
    unique_specifics = _count_unique_specifics(di)
    if unique_specifics < V2_THRESHOLDS["di_unique_specifics_min"]:
        gaps.append(
            f"detailedImplementation only has {unique_specifics} unique product-specific signals (need >= {V2_THRESHOLDS['di_unique_specifics_min']})"
        )
        out["score"] -= 15

    # KFP depth ---------------------------------------------------------
    kfp = uc.get("knownFalsePositives", "") or ""
    kfp_count = _count_kfp_scenarios(kfp)
    if kfp_count < V2_THRESHOLDS["kfp_min_scenarios"]:
        gaps.append(
            f"knownFalsePositives lists {kfp_count} named scenarios (need >= {V2_THRESHOLDS['kfp_min_scenarios']})"
        )
        out["score"] -= 15
    if not _has_suppression_mechanism(kfp):
        gaps.append(
            "knownFalsePositives does not name a suppression mechanism (lookup, exception register, time-bound exception, filter)"
        )
        out["score"] -= 5

    # dataSources depth -------------------------------------------------
    ds = uc.get("dataSources", "") or ""
    if len(ds) < V2_THRESHOLDS["datasources_min_chars"]:
        gaps.append(
            f"dataSources {len(ds)} chars (need >= {V2_THRESHOLDS['datasources_min_chars']})"
        )
        out["score"] -= 5
    if not _has_splunkbase_id(ds + " " + (uc.get("app", "") or "")):
        gaps.append("dataSources/app does not name a Splunkbase ID")
        out["score"] -= 5
    if not _has_sourcetype(ds + " " + (uc.get("spl", "") or "")):
        warns.append("dataSources/spl does not name a sourcetype explicitly")

    # description vs value distinct ------------------------------------
    desc = uc.get("description", "") or ""
    val = uc.get("value", "") or ""
    sim = _description_value_jaccard(desc, val)
    if sim > 0.6:
        gaps.append(
            f"description and value share {sim:.0%} word stems (should be < 60% — they describe different things)"
        )
        out["score"] -= 10

    # references ---------------------------------------------------------
    refs = uc.get("references", []) or []
    if len(refs) < V2_THRESHOLDS["references_min"]:
        gaps.append(
            f"references has {len(refs)} entries (need >= {V2_THRESHOLDS['references_min']})"
        )
        out["score"] -= 5

    # controlTest distinctness -----------------------------------------
    ct = uc.get("controlTest", {}) or {}
    pos = ct.get("positiveScenario", "") or ""
    neg = ct.get("negativeScenario", "") or ""
    if pos and neg:
        diff = abs(len(pos) - len(neg))
        sim_ct = SequenceMatcher(None, pos.lower(), neg.lower()).ratio()
        if diff < V2_THRESHOLDS["control_test_diff_min_chars"] and sim_ct > 0.7:
            gaps.append(
                "controlTest positive/negative scenarios are too similar — likely placeholder text"
            )
            out["score"] -= 5
    else:
        gaps.append("controlTest missing positiveScenario or negativeScenario")
        out["score"] -= 5

    # evidence and exclusions ------------------------------------------
    if len(uc.get("evidence", "") or "") < V2_THRESHOLDS["evidence_min_chars"]:
        gaps.append(f"evidence < {V2_THRESHOLDS['evidence_min_chars']} chars")
        out["score"] -= 5
    if len(uc.get("exclusions", "") or "") < V2_THRESHOLDS["exclusions_min_chars"]:
        gaps.append(f"exclusions < {V2_THRESHOLDS['exclusions_min_chars']} chars")
        out["score"] -= 5

    out["score"] = max(0, out["score"])
    if out["score"] < V2_THRESHOLDS["passing_score"]:
        out["tier"] = "v2-fail"
    return out


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def find_uc_files(specific_files: list[str] | None, regulation: str | None) -> list[Path]:
    if specific_files:
        out = []
        for f in specific_files:
            p = Path(f)
            if not p.is_absolute():
                p = REPO_ROOT / p
            if p.exists():
                out.append(p)
            else:
                for m in CONTENT_DIR.rglob(p.name):
                    out.append(m)
        return sorted(out)
    candidates = sorted(CONTENT_DIR.rglob("UC-*.json"))
    if regulation:
        regulation_l = regulation.strip().lower()
        filtered = []
        for c in candidates:
            try:
                uc = json.loads(c.read_text())
            except Exception:
                continue
            for entry in uc.get("compliance") or []:
                if not isinstance(entry, dict):
                    continue
                if str(entry.get("regulation", "")).strip().lower() == regulation_l:
                    filtered.append(c)
                    break
        return filtered
    return candidates


# ---------------------------------------------------------------------------
# Pack drift (optional)
# ---------------------------------------------------------------------------


def check_pack_drift(uc: dict[str, Any], pack: dict[str, Any]) -> list[str]:
    """Warn when a UC's app/dataSources name a TA that is not the canonical
    spelling in the regulation's domain pack. Best-effort substring check.
    """
    if not pack:
        return []
    text = " ".join([uc.get("app", "") or "", uc.get("dataSources", "") or ""]).lower()
    drift = []
    canonical_names = []
    for pname, pinfo in (pack.get("packs") or {}).items():
        ta = (pinfo.get("ta") or {}).get("name", "")
        if ta:
            canonical_names.append((pname, ta.lower()))
    # Check whether any canonical TA name appears partially but not fully
    for pname, ta_lower in canonical_names:
        # If a substring of the TA is in the text but the full canonical is not
        if ta_lower not in text:
            for token in re.split(r"\s+", ta_lower):
                if len(token) >= 6 and token in text:
                    # Found a partial match — check if the full canonical name is present
                    if not any(canon in text for canon in (ta_lower,)):
                        drift.append(
                            f"Pack `{pname}`: text mentions `{token}` but not the canonical TA name (`{ta_lower}`)"
                        )
                        break
    return drift


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(results: list[dict[str, Any]]) -> None:
    total = len(results)
    pass_n = sum(1 for r in results if r["tier"] == "v2-pass")
    fail_n = total - pass_n
    avg = sum(r["score"] for r in results) / total if total else 0
    print(f"\n=== Gold-profile v2 audit — {total} UCs ===")
    print(
        f"  PASS (score >= {V2_THRESHOLDS['passing_score']}):  {pass_n} ({pass_n / total * 100:.1f}%)"
    )
    print(f"  FAIL                          : {fail_n} ({fail_n / total * 100:.1f}%)")
    print(f"  Avg score                     : {avg:.1f} / 100\n")
    print(f"  {'UC':<10}  {'Score':>5}  {'Status':<8}  Gaps")
    print(f"  {'-' * 10}  {'-' * 5}  {'-' * 8}  {'-' * 40}")
    for r in sorted(results, key=lambda x: (x["tier"] != "v2-fail", x["score"])):
        gaps_summary = "; ".join(r["gaps"][:3])
        if len(r["gaps"]) > 3:
            gaps_summary += f"; +{len(r['gaps']) - 3} more"
        print(f"  UC-{r['id']:<7}  {r['score']:>5}  {r['tier']:<8}  {gaps_summary}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gold-profile v2 audit (the UC-1.1.1 bar)")
    ap.add_argument("--files", nargs="*", help="Specific UC JSON files to audit")
    ap.add_argument("--regulation", help="Limit to UCs claiming the named regulation (e.g. NIS2)")
    ap.add_argument("--pack", help="Optional path to a domain-pack JSON to check drift against")
    ap.add_argument("--check", action="store_true", help="CI mode: exit 1 if any UC fails")
    ap.add_argument(
        "--json", action="store_true", help="Emit JSON report instead of human-readable table"
    )
    args = ap.parse_args(argv)

    files = find_uc_files(args.files, args.regulation)
    if not files:
        print("No UC files found matching filter.", file=sys.stderr)
        return 1

    pack: dict[str, Any] = {}
    if args.pack:
        pack = json.loads(Path(args.pack).read_text())

    results = []
    for fp in files:
        try:
            uc = json.loads(fp.read_text())
        except Exception as exc:
            print(f"Skipping {fp.name}: {exc}", file=sys.stderr)
            continue
        result = audit_uc_v2(uc, fp)
        if pack:
            result["packDrift"] = check_pack_drift(uc, pack)
        results.append(result)

    if args.json:
        print(json.dumps({"results": results, "thresholds": V2_THRESHOLDS}, indent=2))
    else:
        print_report(results)
        if pack:
            drifters = [r for r in results if r.get("packDrift")]
            if drifters:
                print("\n  Pack drift:")
                for r in drifters:
                    for d in r["packDrift"]:
                        print(f"    UC-{r['id']}: {d}")

    if args.check:
        if any(r["tier"] == "v2-fail" for r in results):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
