#!/usr/bin/env python3
"""Audit `Monitoring type:` fields across every UC in `use-cases/cat-*.md`.

Checks performed:

1. **`monitoring-type-empty`** (MED) — the `Monitoring type:` label is
   present but the value is blank.
2. **`monitoring-type-unknown-token`** (LOW) — the value contains a
   non-canonical monitoring category (e.g., `Operational` where we mean
   `Operations`). Canonical tokens are defined by the catalog-level
   convention; unknowns are surfaced so they can be normalised.
3. **`monitoring-type-security-mismatch`** (HIGH) — the UC carries a
   genuine `MITRE ATT&CK:` technique mapping (canonical `Txxxx`/`TAxxxx`
   tokens, not `N/A (...)`) yet `Monitoring type:` does NOT include
   `Security`. ATT&CK maps adversary behaviour; if the UC detects an
   ATT&CK technique it is, by definition, at least partly security.

The audit is advisory today (it does not mutate markdown). Use the
output to drive the mechanical fix pass tracked as `fix-monitoring`.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import Counter
from typing import Iterable, List, NamedTuple, Tuple

REPO = pathlib.Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"

RE_UC_HEAD = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE)
RE_MON_LINE = re.compile(
    r"^-[ \t]*\*\*Monitoring type:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_MITRE_LINE = re.compile(
    r"^-[ \t]*\*\*MITRE ATT&CK:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_MITRE_TOKEN = re.compile(r"^(?:TA\d{4}|T\d{4}(?:\.\d{3})?)$")
RE_MITRE_NA = re.compile(r"^N/?A(\s*\([^)]+\))?\s*$", re.IGNORECASE)

CANONICAL_TOKENS = {
    "Analytics",
    "Anomaly",
    "Audit",
    "Availability",
    "Business",
    "Capacity",
    "Change",
    "Compliance",
    "Configuration",
    "Cost",
    "Data Quality",
    "DevSecOps",
    "Fault",
    "Fraud",
    "Governance",
    "Inventory",
    "Operations",
    "Patient Safety",
    "Performance",
    "Physical Security",
    "Quality",
    "Reliability",
    "Resilience",
    "Revenue Assurance",
    "Risk",
    "Safety",
    "Security",
    "Trading",
    "Vulnerability",
}
# Common near-misses that should be normalised to the canonical token.
TOKEN_NORMALISATION = {
    "Operational": "Operations",
    "Physical": "Physical Security",
}


class Finding(NamedTuple):
    severity: str
    kind: str
    uc_id: str
    file: str
    message: str
    snippet: str = ""


def _iter_uc_blocks(text: str) -> Iterable[Tuple[str, str]]:
    matches = list(RE_UC_HEAD.finditer(text))
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield uc_id, text[start:end]


def _has_real_mitre_mapping(body: str) -> bool:
    m = RE_MITRE_LINE.search(body)
    if not m:
        return False
    value = m.group("body").strip()
    if not value or RE_MITRE_NA.match(value):
        return False
    for tok in (t.strip() for t in value.split(",")):
        if tok and RE_MITRE_TOKEN.match(tok):
            return True
    return False


def _check_monitoring_line(
    uc_id: str,
    file: str,
    body: str,
) -> List[Finding]:
    findings: List[Finding] = []
    mon_match = RE_MON_LINE.search(body)
    if not mon_match:
        # No label at all — outside this linter's scope (another audit
        # owns UC structure completeness).
        return findings

    raw_value = mon_match.group("body").strip()

    if not raw_value:
        findings.append(
            Finding(
                severity="MED",
                kind="monitoring-type-empty",
                uc_id=uc_id,
                file=file,
                message=(
                    "`Monitoring type:` label present but value is blank."
                    " Fill in one or more canonical categories (e.g.,"
                    " `Security`, `Performance`, `Availability`)."
                ),
            )
        )
        return findings

    tokens = [t.strip() for t in raw_value.split(",") if t.strip()]
    unknown = [t for t in tokens if t not in CANONICAL_TOKENS]
    if unknown:
        advice_bits: List[str] = []
        for tok in unknown:
            if tok in TOKEN_NORMALISATION:
                advice_bits.append(f"'{tok}' → '{TOKEN_NORMALISATION[tok]}'")
            else:
                advice_bits.append(f"'{tok}'")
        findings.append(
            Finding(
                severity="LOW",
                kind="monitoring-type-unknown-token",
                uc_id=uc_id,
                file=file,
                message=(
                    "Non-canonical monitoring-type token(s): "
                    + ", ".join(advice_bits)
                    + ". Canonical set: "
                    + ", ".join(sorted(CANONICAL_TOKENS))
                    + "."
                ),
                snippet=raw_value,
            )
        )

    has_security = any(t.lower() == "security" for t in tokens)
    if _has_real_mitre_mapping(body) and not has_security:
        findings.append(
            Finding(
                severity="HIGH",
                kind="monitoring-type-security-mismatch",
                uc_id=uc_id,
                file=file,
                message=(
                    "UC has a genuine MITRE ATT&CK mapping but"
                    " `Monitoring type:` does not include `Security`."
                    " ATT&CK describes adversary behaviour — add"
                    " `Security` (multi-label is fine) or remove the"
                    " ATT&CK mapping if the behaviour is purely"
                    " operational."
                ),
                snippet=raw_value,
            )
        )

    return findings


def audit_file(path: pathlib.Path) -> List[Finding]:
    text = path.read_text(encoding="utf-8")
    findings: List[Finding] = []
    for uc_id, body in _iter_uc_blocks(text):
        findings.extend(_check_monitoring_line(uc_id, path.name, body))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Monitoring type fields across use-cases/cat-*.md."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit non-zero when any HIGH finding is reported.",
    )
    args = parser.parse_args()

    all_findings: List[Finding] = []
    files = sorted(USE_CASES.glob("cat-*.md"))
    for md in files:
        all_findings.extend(audit_file(md))

    print("=" * 72)
    print("Monitoring-type audit (use-cases/cat-*.md)")
    print("=" * 72)
    print(f"Files scanned: {len(files)}")
    by_sev = Counter(f.severity for f in all_findings)
    print(
        "Findings by severity: "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_sev.items()))
    )
    by_kind = Counter(f.kind for f in all_findings)
    print("\nFindings by category:")
    for kind, count in sorted(
        by_kind.items(), key=lambda kv: (-kv[1], kv[0])
    ):
        print(f"  {count:4d}  {kind}")

    if all_findings:
        print("\nFINDINGS:")
        print("-" * 72)
        severity_order = {"HIGH": 0, "MED": 1, "LOW": 2}
        for f in sorted(
            all_findings,
            key=lambda x: (severity_order.get(x.severity, 99), x.file, x.uc_id),
        ):
            print(
                f"[{f.severity}] [{f.kind}] {f.uc_id} ({f.file}): {f.message}"
            )
            if f.snippet:
                print(f"        snippet: {f.snippet[:200]}")

    if args.check and by_sev.get("HIGH", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
