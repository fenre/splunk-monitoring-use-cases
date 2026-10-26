"""``generate-uc-review-report`` — roll the UC review ledger up into a fix queue.

Reads the per-UC triage / deep / adjudication records, the committed
deterministic summary, and recomputes the scripted-lane checks for each queued
UC, then writes:

* ``reports/uc-review/summary.json`` — coverage, verdicts and severities per
  tier and category, deterministic check counts, recurring blocker quotes.
* ``reports/uc-review/fix-queue.json`` — one entry per reviewed UC, ranked by
  severity x criticality, with each finding assigned to a fix lane
  (``scripted``, ``lift`` or ``human``).
* ``docs/uc-review-findings.md`` — the human-readable report.

The authoritative model record for a UC is its adjudication record when one
exists, else its deep record, else its triage record. Output contains no
timestamps, so reruns over the same ledger are byte-identical.

Usage::

    python -m splunk_uc generate-uc-review-report
    python -m splunk_uc generate-uc-review-report --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from splunk_uc.review._ledger import (
    CONTENT_DIR,
    REPO_ROOT,
    REVIEW_ROOT,
    content_sha256,
    iter_sidecars,
    iter_tier_records,
    uc_id_of,
)

SUMMARY_PATH = REVIEW_ROOT / "summary.json"
FIX_QUEUE_PATH = REVIEW_ROOT / "fix-queue.json"
DOC_PATH = REPO_ROOT / "docs" / "uc-review-findings.md"
DETERMINISTIC_SUMMARY = REVIEW_ROOT / "deterministic-summary.json"
GENERATOR = "python3 -m splunk_uc generate-uc-review-report"

SEVERITY_WEIGHT = {"blocker": 100, "needs_verification": 5, "major": 10, "minor": 1}
CRITICALITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}
TIER_AUTHORITY = ("adjudication", "deep", "triage")
SCRIPTED_CHECK_PREFIXES = (
    "template_v2:",
    "template_v1:",
    "premium_app_pillar_mismatch",
    "cim_models_",
    "splunkbase_deprecated",
)
WORST_LIMIT = 100
RECURRING_MIN_UCS = 3


def fix_lane(item: dict[str, Any], *, firewalled: bool) -> str:
    """``human`` for firewalled fields, ``scripted`` for mechanical checks, else ``lift``."""
    if firewalled:
        return "human"
    check = str(item.get("check", ""))
    if check.startswith(SCRIPTED_CHECK_PREFIXES):
        return "scripted"
    return "lift"


def uc_score(record: dict[str, Any], criticality: str | None) -> int:
    total = sum(
        SEVERITY_WEIGHT.get(str(f.get("severity")), 0)
        for f in record.get("findings", []) + record.get("firewalled_field_flags", [])
    )
    return total * CRITICALITY_WEIGHT.get(str(criticality), 1)


def _short(text: str, limit: int = 220) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def deterministic_findings(path: Path, uc: dict[str, Any]) -> list[dict[str, Any]]:
    """Cluster- and spelling-free deterministic findings (stable without the gitignored JSONL)."""
    from splunk_uc.audits import text_quality

    record = text_quality.review_uc(path, uc, skeleton_index=None, min_cluster=50, spelling={})
    return record["findings"]


def load_tier(tier: str, root: Path) -> dict[str, dict[str, Any]]:
    return {r["uc_id"]: r for r in iter_tier_records(tier, root=root) if "uc_id" in r}


def build(
    *, root: Path = REVIEW_ROOT, content_dir: Path = CONTENT_DIR
) -> tuple[dict[str, Any], dict[str, Any]]:
    sidecars = {uc_id_of(uc): (path, uc) for path, uc in iter_sidecars(content_dir=content_dir)}
    tiers = {tier: load_tier(tier, root) for tier in TIER_AUTHORITY}

    category_totals = Counter(path.parent.name for path, _ in sidecars.values())
    coverage: dict[str, dict[str, int]] = {
        cat: {"ucs": n, **dict.fromkeys(TIER_AUTHORITY, 0), "stale": 0}
        for cat, n in sorted(category_totals.items())
    }
    verdicts: dict[str, Counter[str]] = {tier: Counter() for tier in TIER_AUTHORITY}
    severities: dict[str, Counter[str]] = {tier: Counter() for tier in TIER_AUTHORITY}
    dimension_counts: Counter[str] = Counter()
    firewalled_counts: Counter[str] = Counter()
    blocker_quotes: dict[str, set[str]] = defaultdict(set)
    queue: list[dict[str, Any]] = []

    for uc_id, (path, uc) in sorted(sidecars.items()):
        cat = path.parent.name
        sha = content_sha256(uc)
        authoritative = None
        for tier in TIER_AUTHORITY:
            record = tiers[tier].get(uc_id)
            if record is None:
                continue
            coverage[cat][tier] += 1
            verdicts[tier][str(record.get("verdict"))] += 1
            for item in record.get("findings", []) + record.get("firewalled_field_flags", []):
                severities[tier][str(item.get("severity"))] += 1
            if authoritative is None:
                authoritative = (tier, record)
        if authoritative is None:
            continue
        tier, record = authoritative
        stale = record.get("content_sha256") != sha
        if stale:
            coverage[cat]["stale"] += 1

        items: list[dict[str, Any]] = []
        for finding in record.get("findings", []):
            dimension_counts[f"{finding.get('dimension')}:{finding.get('severity')}"] += 1
            items.append(
                {
                    "field": finding.get("field"),
                    "dimension": finding.get("dimension"),
                    "severity": finding.get("severity"),
                    "lane": fix_lane(finding, firewalled=False),
                    "explanation": _short(finding.get("explanation", "")),
                    **(
                        {"evidence_url": finding["evidence_url"]}
                        if finding.get("evidence_url")
                        else {}
                    ),
                    **(
                        {"evidence_ref": finding["evidence_ref"]}
                        if finding.get("evidence_ref")
                        else {}
                    ),
                }
            )
            if finding.get("severity") == "blocker" and finding.get("quote"):
                blocker_quotes[_short(finding["quote"], 160)].add(uc_id)
        for flag in record.get("firewalled_field_flags", []):
            firewalled_counts[f"{flag.get('field')}:{flag.get('severity')}"] += 1
            items.append(
                {
                    "field": flag.get("field"),
                    "dimension": "firewalled",
                    "severity": flag.get("severity"),
                    "lane": "human",
                    "explanation": _short(flag.get("issue", "")),
                    **({"evidence_url": flag["evidence_url"]} if flag.get("evidence_url") else {}),
                }
            )
        scripted = [
            f["check"]
            for f in deterministic_findings(path, uc)
            if fix_lane(f, firewalled=False) == "scripted"
        ]
        items.sort(key=lambda i: (-SEVERITY_WEIGHT.get(str(i["severity"]), 0), str(i["field"])))
        queue.append(
            {
                "uc_id": uc_id,
                "file": f"content/{cat}/{path.name}",
                "category": cat,
                "title": uc.get("title"),
                "criticality": uc.get("criticality"),
                "status": uc.get("status"),
                "tier": tier,
                "model": record.get("model"),
                "verdict": record.get("verdict"),
                "stale": stale,
                "score": uc_score(record, uc.get("criticality")),
                "counts": dict(
                    Counter(str(i["severity"]) for i in items if i["lane"] != "scripted")
                ),
                "lanes": dict(Counter(i["lane"] for i in items)),
                "scripted_checks": sorted(set(scripted)),
                "items": items,
            }
        )

    queue.sort(key=lambda q: (-q["score"], q["uc_id"]))
    det_summary: dict[str, Any] = {}
    if DETERMINISTIC_SUMMARY.is_file() and root == REVIEW_ROOT:
        det_summary = json.loads(DETERMINISTIC_SUMMARY.read_text(encoding="utf-8"))
    recurring = sorted(
        (
            {"quote": quote, "ucs": len(ids), "examples": sorted(ids)[:5]}
            for quote, ids in blocker_quotes.items()
            if len(ids) >= RECURRING_MIN_UCS
        ),
        key=lambda r: (-r["ucs"], r["quote"]),
    )
    summary = {
        "$comment": f"Generated by `{GENERATOR}`; do not hand-edit.",
        "schema_version": "1.0",
        "ucs_total": len(sidecars),
        "ucs_model_reviewed": len(queue),
        "coverage": coverage,
        "verdicts": {t: dict(sorted(c.items())) for t, c in verdicts.items()},
        "severities": {t: dict(sorted(c.items())) for t, c in severities.items()},
        "authoritative_dimensions": dict(sorted(dimension_counts.items())),
        "firewalled": dict(sorted(firewalled_counts.items())),
        "recurring_blocker_quotes": recurring[:50],
        "deterministic": {
            "ucs": det_summary.get("ucs"),
            "ucs_with_findings": det_summary.get("ucs_with_findings"),
            "by_severity": det_summary.get("by_severity", {}),
            "by_check": det_summary.get("by_check", {}),
        },
    }
    fix_queue = {
        "$comment": f"Generated by `{GENERATOR}`; do not hand-edit.",
        "schema_version": "1.0",
        "weights": {"severity": SEVERITY_WEIGHT, "criticality": CRITICALITY_WEIGHT},
        "lanes": {
            "scripted": "mechanical families fixed by reviewed scripts (plan Phase 6a)",
            "lift": "prose fixed through lift-prompt --findings + lift-validate --require-handcraft (6b)",
            "human": "firewalled fields (spl, cimSpl, compliance, classification, title) for human PRs (6c)",
        },
        "queue": queue,
    }
    return summary, fix_queue


def render_markdown(summary: dict[str, Any], fix_queue: dict[str, Any]) -> str:
    lines = [
        "# UC text-quality review findings",
        "",
        f"<!-- Generated by `{GENERATOR}`; do not hand-edit. -->",
        "<!-- Inputs: `reports/uc-review/**`, `content/**/*.json` · Refresh cadence: PR -->",
        "",
        "Roll-up of the UC text-quality review ledger under `reports/uc-review/`. "
        "Grading contract: [`docs/uc-text-review-rubric.md`](uc-text-review-rubric.md). "
        "Calibration: [`reports/uc-review/calibration/decision.md`](../reports/uc-review/calibration/decision.md).",
        "",
        "## Coverage",
        "",
        f"{summary['ucs_model_reviewed']} of {summary['ucs_total']} UCs have at least one model review.",
        "",
        "| Category | UCs | Triage | Deep | Adjudication | Stale |",
        "|---|---|---|---|---|---|",
    ]
    for cat, row in summary["coverage"].items():
        if any(row[t] for t in TIER_AUTHORITY):
            lines.append(
                f"| {cat} | {row['ucs']} | {row['triage']} | {row['deep']} | {row['adjudication']} | {row['stale']} |"
            )
    lines += [
        "",
        "## Verdicts by tier",
        "",
        "| Tier | ok | polish | rewrite | incorrect |",
        "|---|---|---|---|---|",
    ]
    for tier in TIER_AUTHORITY:
        v = summary["verdicts"][tier]
        if v:
            lines.append(
                f"| {tier} | {v.get('ok', 0)} | {v.get('polish', 0)} | {v.get('rewrite', 0)} | {v.get('incorrect', 0)} |"
            )

    det = summary["deterministic"]
    if det.get("ucs"):
        lines += [
            "",
            "## Deterministic pre-pass",
            "",
            f"`audit-text-quality` flags {det['ucs_with_findings']} of {det['ucs']} UCs. Top checks:",
            "",
            "| Check | Findings |",
            "|---|---|",
        ]
        for check, count in sorted(det["by_check"].items(), key=lambda kv: -kv[1])[:20]:
            lines.append(f"| `{check}` | {count} |")

    if summary["recurring_blocker_quotes"]:
        lines += [
            "",
            "## Recurring blockers",
            "",
            "Blocker quotes repeated across UCs usually mean one wrong fact copied many times; "
            "fixing the source (a guide or a generator) fixes them all.",
            "",
            "| UCs | Quote | Examples |",
            "|---|---|---|",
        ]
        for row in summary["recurring_blocker_quotes"][:25]:
            quote = row["quote"].replace("|", "\\|")
            lines.append(f"| {row['ucs']} | {quote} | {', '.join(row['examples'])} |")

    if summary["firewalled"]:
        lines += [
            "",
            "## Firewalled-field issues (human lane)",
            "",
            "| Field:severity | Count |",
            "|---|---|",
        ]
        for key, count in sorted(summary["firewalled"].items(), key=lambda kv: -kv[1])[:20]:
            lines.append(f"| `{key}` | {count} |")

    queue = fix_queue["queue"]
    lines += [
        "",
        f"## Fix queue — worst {min(WORST_LIMIT, len(queue))} UCs",
        "",
        "Score = sum of severity weights (blocker 100, major 10, needs_verification 5, minor 1) "
        "x criticality weight (critical 4 … low 1). Full queue: `reports/uc-review/fix-queue.json`.",
        "",
        "| # | UC | Criticality | Verdict | Score | Blocker | Major | Lanes | Top issue |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, item in enumerate(queue[:WORST_LIMIT], start=1):
        top = item["items"][0]["explanation"] if item["items"] else ""
        top = _short(top, 140).replace("|", "\\|")
        lanes = ", ".join(f"{k} {v}" for k, v in sorted(item["lanes"].items()))
        lines.append(
            f"| {rank} | [{item['uc_id']}](../{item['file']}) | {item['criticality']} | {item['verdict']} | "
            f"{item['score']} | {item['counts'].get('blocker', 0)} | {item['counts'].get('major', 0)} | "
            f"{lanes} | {top} |"
        )
    lines.append("")
    return "\n".join(lines)


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc generate-uc-review-report",
        description="Roll the UC review ledger up into summary.json, fix-queue.json and docs/uc-review-findings.md.",
    )
    parser.add_argument(
        "--check", action="store_true", help="Exit 1 if the committed outputs are stale"
    )
    args = parser.parse_args(argv)

    summary, fix_queue = build()
    outputs = {
        SUMMARY_PATH: _dump(summary),
        FIX_QUEUE_PATH: _dump(fix_queue),
        DOC_PATH: render_markdown(summary, fix_queue),
    }
    if args.check:
        stale = [
            str(p.relative_to(REPO_ROOT))
            for p, text in outputs.items()
            if not p.is_file() or p.read_text(encoding="utf-8") != text
        ]
        if stale:
            print("generate-uc-review-report: stale outputs: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("generate-uc-review-report: outputs up to date")
        return 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"Wrote {path.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
