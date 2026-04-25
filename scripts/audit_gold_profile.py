#!/usr/bin/env python3
"""Audit UC JSON files against the Gold Standard quality profile.

Measures operational depth, not just field presence. A detailedImplementation
that says "Install the TA and enable the input" five times passes a regex
check and is worthless — this audit catches that.

Usage:
    python3 scripts/audit_gold_profile.py                    # full report
    python3 scripts/audit_gold_profile.py --summary          # table to stdout
    python3 scripts/audit_gold_profile.py --check            # CI: exit 1 if shallow
    python3 scripts/audit_gold_profile.py --files UC-5.13.1.json UC-5.13.2.json
    python3 scripts/audit_gold_profile.py --consolidation-candidates
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
REPORT_DIR = REPO_ROOT / "reports"

# ---------------------------------------------------------------------------
# Tier field requirements
# ---------------------------------------------------------------------------

BRONZE_REQUIRED = {
    "id", "title", "criticality", "difficulty",
    "spl", "description", "value", "dataSources", "app", "implementation",
}

SILVER_REQUIRED = BRONZE_REQUIRED | {
    "monitoringType", "splunkPillar",
    "detailedImplementation", "references", "equipment",
    "grandmaExplanation", "wave", "prerequisiteUseCases",
}

GOLD_REQUIRED = SILVER_REQUIRED | {
    "visualization", "equipmentModels",
}

BRONZE_MIN_LENGTHS = {
    "description": 40, "value": 40, "dataSources": 20, "implementation": 20,
}
SILVER_MIN_LENGTHS = {
    "description": 60, "value": 60, "dataSources": 30,
    "detailedImplementation": 200, "grandmaExplanation": 20,
}
GOLD_MIN_LENGTHS = {
    "description": 80, "value": 80, "dataSources": 40,
    "detailedImplementation": 500, "grandmaExplanation": 20,
}

# ---------------------------------------------------------------------------
# Depth heuristics
# ---------------------------------------------------------------------------

GENERIC_BOILERPLATE_PHRASES = [
    r"install the (?:ta|add-on|app) and (?:configure|enable)",
    r"check (?:splunkd\.log|the logs|your data)",
    r"validate (?:the data|your data|that data)",
    r"create a (?:dashboard|report|alert)",
    r"schedule (?:the|a|this) (?:search|report|alert)",
    r"run the (?:spl|search|query)",
    r"contact (?:support|your admin)",
    r"ensure (?:the|your) (?:ta|add-on|app) is (?:installed|configured)",
]

SECTION_PATTERNS = [
    re.compile(r"(?:prerequisite|step\s*0|before\s+you\s+begin)", re.IGNORECASE),
    re.compile(r"(?:step\s*1|configure\s+data|data\s+collection|collection\s+setup)", re.IGNORECASE),
    re.compile(r"(?:step\s*2|create\s+the\s+search|search\s+and\s+alert|understanding\s+this\s+spl)", re.IGNORECASE),
    re.compile(r"(?:step\s*3|validat)", re.IGNORECASE),
    re.compile(r"(?:step\s*4|step\s*5|operationaliz|troubleshoot)", re.IGNORECASE),
]

PRODUCT_SPECIFIC_INDICATORS = [
    re.compile(r"sourcetype\s*[=:\"]\s*\S+", re.IGNORECASE),
    re.compile(r"index\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"/(?:api|dna|v[12]|rest)/", re.IGNORECASE),
    re.compile(r"inputs\.conf|modular\s+input", re.IGNORECASE),
    re.compile(r"\b(?:GET|POST|PUT)\s+/", re.IGNORECASE),
    re.compile(r"\d+\s*(?:seconds?|minutes?|hours?)\b", re.IGNORECASE),
    re.compile(r"(?:RBAC|role|permission|SUPER-ADMIN|NETWORK-ADMIN)", re.IGNORECASE),
    re.compile(r"(?:Splunkbase|splunkbase)\s+\d{3,}", re.IGNORECASE),
]


def _count_sections(text: str) -> int:
    """Count how many of the 5-step section patterns appear."""
    return sum(1 for p in SECTION_PATTERNS if p.search(text))


def _boilerplate_ratio(text: str) -> float:
    """Estimate what fraction of sentences are generic boilerplate."""
    sentences = re.split(r"[.!?\n]", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    if not sentences:
        return 0.0
    generic_count = 0
    for sentence in sentences:
        for pattern in GENERIC_BOILERPLATE_PHRASES:
            if re.search(pattern, sentence, re.IGNORECASE):
                generic_count += 1
                break
    return generic_count / len(sentences)


def _product_specificity_score(text: str) -> int:
    """Count how many product-specific indicators are present."""
    return sum(1 for p in PRODUCT_SPECIFIC_INDICATORS if p.search(text))


def _has_vendor_ui_reference(text: str) -> bool:
    """Check if the text references a vendor UI for validation."""
    patterns = [
        re.compile(r"(?:compare|verify|check|confirm)\s+(?:against|with|in|to)\s+(?:the\s+)?(?:\w+\s+){0,3}(?:UI|dashboard|console|portal|interface|center|assurance|inventory)", re.IGNORECASE),
        re.compile(r"(?:Catalyst|Meraki|ISE|vCenter|Azure|AWS|GCP|NetApp|Palo\s*Alto)\s+(?:Center|Dashboard|Console|Portal|UI|Manager)", re.IGNORECASE),
    ]
    return any(p.search(text) for p in patterns)


def _has_specific_troubleshooting(text: str) -> bool:
    """Check if troubleshooting mentions product-specific failure modes."""
    troubleshoot_match = re.search(r"(?:troubleshoot|step\s*5|failure|common\s+issue)", text, re.IGNORECASE)
    if not troubleshoot_match:
        return False
    after = text[troubleshoot_match.start():]
    specific_patterns = [
        re.compile(r"(?:no\s+\S+\s+events|no\s+data\s+for)", re.IGNORECASE),
        re.compile(r"(?:NULL|zero|empty|missing)\s+(?:values?|fields?|health)", re.IGNORECASE),
        re.compile(r"(?:fewer|less|more)\s+(?:devices?|events?|records?|hosts?)\s+than", re.IGNORECASE),
        re.compile(r"(?:API|endpoint|input|modular)\s+(?:error|timeout|throttl|429|5\d\d|fail)", re.IGNORECASE),
        re.compile(r"(?:role|permission|access|auth|credential)\s+(?:denied|error|fail|incorrect)", re.IGNORECASE),
    ]
    return any(p.search(after) for p in specific_patterns)


def _description_value_similarity(desc: str, val: str) -> float:
    """Normalized similarity between description and value (0.0 = different, 1.0 = identical)."""
    if not desc or not val:
        return 0.0
    return SequenceMatcher(None, desc.lower(), val.lower()).ratio()


# ---------------------------------------------------------------------------
# UC-level audit
# ---------------------------------------------------------------------------

def audit_uc(uc: dict[str, Any], filepath: Path) -> dict[str, Any]:
    """Audit a single UC. Returns a result dict."""
    uc_id = uc.get("id", "unknown")
    result: dict[str, Any] = {
        "id": uc_id,
        "file": str(filepath.relative_to(REPO_ROOT)),
        "title": uc.get("title", ""),
        "tier": "none",
        "depth_score": 0,
        "gaps": [],
        "warnings": [],
    }
    gaps = result["gaps"]
    warnings = result["warnings"]

    # --- Tier classification ---
    def _has_field(key: str) -> bool:
        v = uc.get(key)
        if v is None:
            return False
        if isinstance(v, str):
            return len(v.strip()) > 0
        if isinstance(v, list):
            return True  # empty list still counts as "present"
        return True

    def _meets_min_length(key: str, min_len: int) -> bool:
        v = uc.get(key, "")
        return isinstance(v, str) and len(v) >= min_len

    # Bronze check
    bronze_ok = True
    for field in BRONZE_REQUIRED:
        if not _has_field(field):
            bronze_ok = False
            gaps.append(f"Missing field: {field}")
    for field, min_len in BRONZE_MIN_LENGTHS.items():
        if _has_field(field) and not _meets_min_length(field, min_len):
            bronze_ok = False
            gaps.append(f"{field} too short (need {min_len}+ chars)")

    if not bronze_ok:
        result["tier"] = "none"
        result["depth_score"] = max(0, 10 - len(gaps) * 2)
        return result

    result["tier"] = "bronze"
    depth = 25  # base for bronze

    # Silver check
    silver_ok = True
    for field in SILVER_REQUIRED - BRONZE_REQUIRED:
        if not _has_field(field):
            silver_ok = False
            gaps.append(f"For Silver: missing {field}")
    for field, min_len in SILVER_MIN_LENGTHS.items():
        if _has_field(field) and not _meets_min_length(field, min_len):
            silver_ok = False
            gaps.append(f"For Silver: {field} too short (need {min_len}+ chars)")

    refs = uc.get("references", [])
    if isinstance(refs, list) and len(refs) < 1:
        silver_ok = False
        gaps.append("For Silver: need at least 1 reference")

    detailed = uc.get("detailedImplementation", "")
    if isinstance(detailed, str) and detailed:
        sections = _count_sections(detailed)
        if sections < 3:
            silver_ok = False
            gaps.append(f"For Silver: detailedImplementation has {sections}/3 required sections")

    if silver_ok:
        result["tier"] = "silver"
        depth = 50

    # Gold check
    gold_ok = silver_ok
    for field in GOLD_REQUIRED - SILVER_REQUIRED:
        if not _has_field(field):
            gold_ok = False
            gaps.append(f"For Gold: missing {field}")
    for field, min_len in GOLD_MIN_LENGTHS.items():
        if _has_field(field) and not _meets_min_length(field, min_len):
            gold_ok = False
            gaps.append(f"For Gold: {field} too short (need {min_len}+ chars)")

    if isinstance(refs, list) and len(refs) < 2:
        gold_ok = False
        gaps.append("For Gold: need at least 2 references")

    if isinstance(detailed, str) and detailed:
        sections = _count_sections(detailed)
        if sections < 4:
            gold_ok = False
            gaps.append(f"For Gold: detailedImplementation has {sections}/5 expected sections")

    if gold_ok:
        result["tier"] = "gold"
        depth = 75

    # --- Depth analysis (applies regardless of tier) ---
    desc = uc.get("description", "")
    value = uc.get("value", "")
    similarity = _description_value_similarity(desc, value)
    if similarity > 0.7:
        warnings.append(f"description and value are {similarity:.0%} similar — they should be distinct")
        depth -= 10

    if isinstance(detailed, str) and detailed:
        boilerplate = _boilerplate_ratio(detailed)
        if boilerplate > 0.5:
            warnings.append(f"detailedImplementation is {boilerplate:.0%} generic boilerplate")
            depth -= 15

        specificity = _product_specificity_score(detailed)
        if specificity >= 5:
            depth += 10
        elif specificity >= 3:
            depth += 5
        elif specificity < 2 and len(detailed) > 300:
            warnings.append("detailedImplementation lacks product-specific terms (sourcetypes, API paths, field names)")
            depth -= 5

        if _has_vendor_ui_reference(detailed):
            depth += 5
        elif result["tier"] == "gold":
            gaps.append("For Gold depth: validation step should reference vendor UI for comparison")

        if _has_specific_troubleshooting(detailed):
            depth += 5
        elif result["tier"] in ("gold", "silver"):
            gaps.append("Troubleshooting should mention product-specific failure modes")

    result["depth_score"] = max(0, min(100, depth))
    return result


# ---------------------------------------------------------------------------
# Consolidation detection
# ---------------------------------------------------------------------------

def find_consolidation_candidates(results: list[dict]) -> list[dict]:
    """Find UCs within the same subcategory with high similarity."""
    by_subcat: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        parts = r["id"].split(".")
        if len(parts) >= 2:
            subcat = f"{parts[0]}.{parts[1]}"
            by_subcat[subcat].append(r)

    candidates = []
    for subcat, ucs in by_subcat.items():
        if len(ucs) < 2:
            continue
        for i, a in enumerate(ucs):
            for b in ucs[i + 1:]:
                title_sim = SequenceMatcher(None, a["title"].lower(), b["title"].lower()).ratio()
                if title_sim > 0.8:
                    candidates.append({
                        "subcategory": subcat,
                        "uc_a": a["id"],
                        "uc_b": b["id"],
                        "title_similarity": round(title_sim, 2),
                        "reason": "High title similarity — potential consolidation candidate",
                    })
    return candidates


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_uc_files(specific_files: list[str] | None = None) -> list[Path]:
    """Find UC JSON files to audit."""
    if specific_files:
        resolved = []
        for f in specific_files:
            p = Path(f)
            if not p.is_absolute():
                p = REPO_ROOT / p
            if p.exists():
                resolved.append(p)
            else:
                for match in CONTENT_DIR.rglob(p.name):
                    resolved.append(match)
        return sorted(resolved)
    return sorted(CONTENT_DIR.rglob("UC-*.json"))


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(results: list[dict], consolidation: list[dict]) -> None:
    """Print a human-readable summary table."""
    tier_counts = defaultdict(int)
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        tier_counts[r["tier"]] += 1
        cat = r["id"].split(".")[0] if "." in r["id"] else "?"
        by_cat[cat].append(r)

    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"Gold Standard Quality Audit — {total} UCs")
    print(f"{'=' * 60}")
    for tier in ("gold", "silver", "bronze", "none"):
        count = tier_counts[tier]
        pct = (count / total * 100) if total else 0
        bar = "\u2588" * int(pct / 2)
        print(f"  {tier:8s}: {count:5d} ({pct:5.1f}%)  {bar}")

    avg_depth = sum(r["depth_score"] for r in results) / total if total else 0
    print(f"\n  Avg depth score: {avg_depth:.1f}/100")

    # Per-category summary
    print(f"\n{'Category':>10s} {'UCs':>5s} {'Gold':>5s} {'Silver':>6s} {'Bronze':>7s} {'Below':>6s} {'AvgDepth':>9s}")
    print(f"  {'-' * 55}")
    for cat_id in sorted(by_cat.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        cat_ucs = by_cat[cat_id]
        n = len(cat_ucs)
        g = sum(1 for r in cat_ucs if r["tier"] == "gold")
        s = sum(1 for r in cat_ucs if r["tier"] == "silver")
        b = sum(1 for r in cat_ucs if r["tier"] == "bronze")
        bl = sum(1 for r in cat_ucs if r["tier"] == "none")
        ad = sum(r["depth_score"] for r in cat_ucs) / n if n else 0
        print(f"  cat-{cat_id:>3s}  {n:5d} {g:5d} {s:6d} {b:7d} {bl:6d} {ad:8.1f}")

    if consolidation:
        print(f"\n  Consolidation candidates: {len(consolidation)}")
        for c in consolidation[:10]:
            print(f"    {c['uc_a']} <-> {c['uc_b']} ({c['title_similarity']:.0%} similar)")
        if len(consolidation) > 10:
            print(f"    ... and {len(consolidation) - 10} more")

    print()


def write_report(results: list[dict], consolidation: list[dict]) -> None:
    """Write JSON report."""
    REPORT_DIR.mkdir(exist_ok=True)
    report = {
        "profile_version": "1.0",
        "total_ucs": len(results),
        "tier_distribution": {
            tier: sum(1 for r in results if r["tier"] == tier)
            for tier in ("gold", "silver", "bronze", "none")
        },
        "avg_depth_score": round(
            sum(r["depth_score"] for r in results) / len(results), 1
        ) if results else 0,
        "ucs": results,
        "consolidation_candidates": consolidation,
    }
    out = REPORT_DIR / "quality-audit.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report written to {out.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit UC JSON against Gold Standard quality profile.")
    parser.add_argument("--check", action="store_true", help="CI mode: exit 1 if any UC has shallow content or falls below Bronze.")
    parser.add_argument("--summary", action="store_true", help="Print human-readable summary table.")
    parser.add_argument("--report", action="store_true", help="Write JSON report to reports/quality-audit.json.")
    parser.add_argument("--files", nargs="+", metavar="FILE", help="Audit specific files only.")
    parser.add_argument("--consolidation-candidates", action="store_true", dest="consolidation", help="List consolidation candidates.")
    args = parser.parse_args()

    # Default: summary + report if no mode specified
    if not (args.check or args.summary or args.report or args.consolidation):
        args.summary = True
        args.report = True

    json_files = find_uc_files(args.files)
    if not json_files:
        print("No UC JSON files found.")
        return 1 if args.check else 0

    results = []
    errors = []
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as fh:
                uc = json.load(fh)
            result = audit_uc(uc, jf)
            results.append(result)
        except (json.JSONDecodeError, KeyError) as exc:
            errors.append({"file": str(jf.relative_to(REPO_ROOT)), "error": str(exc)})

    consolidation = find_consolidation_candidates(results) if (args.consolidation or args.report) else []

    if args.summary:
        print_summary(results, consolidation)

    if args.report:
        write_report(results, consolidation)

    if args.consolidation and not args.summary:
        if consolidation:
            for c in consolidation:
                print(f"{c['uc_a']} <-> {c['uc_b']}: {c['title_similarity']:.0%} similar ({c['reason']})")
        else:
            print("No consolidation candidates found.")

    if args.check:
        shallow = [r for r in results if r["tier"] == "none"]
        high_boilerplate = [r for r in results if any("boilerplate" in w for w in r.get("warnings", []))]
        if shallow or high_boilerplate or errors:
            if shallow:
                print(f"\nFAIL: {len(shallow)} UC(s) below Bronze minimum:")
                for r in shallow[:10]:
                    print(f"  {r['id']}: {', '.join(r['gaps'][:3])}")
            if high_boilerplate:
                print(f"\nWARN: {len(high_boilerplate)} UC(s) with high boilerplate ratio:")
                for r in high_boilerplate[:10]:
                    print(f"  {r['id']}")
            if errors:
                print(f"\nERROR: {len(errors)} file(s) could not be parsed:")
                for e in errors:
                    print(f"  {e['file']}: {e['error']}")
            return 1
        print(f"All {len(results)} UC(s) pass quality checks.")
        return 0

    if errors:
        print(f"\n{len(errors)} file(s) had parse errors.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
