#!/usr/bin/env python3
"""Audit ``monitoringType`` arrays across every UC sidecar in the JSON SSOT.

Checks performed:

1. ``monitoring-type-empty`` (MED) — ``monitoringType`` is missing or
   empty.
2. ``monitoring-type-unknown-token`` (LOW) — value contains a
   non-canonical monitoring category. The schema enum already enforces
   most spellings; this catch is a safety net for legacy edits that
   sneak in via direct JSON manipulation.
3. ``monitoring-type-security-mismatch`` (HIGH) — UC carries genuine
   ``attackTechniques`` (canonical ``Txxxx``/``TAxxxx`` tokens, NOT
   ``N/A (...)``) yet ``monitoringType`` does not include ``Security``.
   ATT&CK maps adversary behaviour; if the UC detects an ATT&CK
   technique it is, by definition, at least partly security.

Pre-v8.2.0 this walked ``use-cases/cat-*.md`` and parsed
``- **Monitoring type:**`` lines. The JSON SSOT is the only backend now.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from typing import NamedTuple

from splunk_uc.audits._uc_walk import get_list_field, iter_uc_sidecars

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
    "Physical",
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
TOKEN_NORMALISATION = {
    "Operational": "Operations",
}


class Finding(NamedTuple):
    severity: str
    kind: str
    uc_id: str
    file: str
    message: str
    snippet: str = ""


def _has_real_mitre_mapping(payload: dict) -> bool:
    techniques = get_list_field(payload, "attackTechniques")
    for tok in techniques:
        if not isinstance(tok, str):
            continue
        s = tok.strip()
        if RE_MITRE_NA.match(s):
            continue
        if RE_MITRE_TOKEN.match(s):
            return True
    return False


def _check_uc(uc_id: str, file: str, payload: dict) -> list[Finding]:
    findings: list[Finding] = []
    tokens = [t for t in get_list_field(payload, "monitoringType") if isinstance(t, str)]

    if not tokens:
        findings.append(
            Finding(
                severity="MED",
                kind="monitoring-type-empty",
                uc_id=uc_id,
                file=file,
                message=(
                    "`monitoringType` missing or empty. Set one or more "
                    "canonical categories (e.g., `Security`, "
                    "`Performance`, `Availability`)."
                ),
            )
        )
        return findings

    unknown = [t for t in tokens if t not in CANONICAL_TOKENS]
    if unknown:
        advice_bits: list[str] = []
        for tok in unknown:
            if tok in TOKEN_NORMALISATION:
                advice_bits.append(f"'{tok}' -> '{TOKEN_NORMALISATION[tok]}'")
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
                snippet=", ".join(tokens),
            )
        )

    has_security = any(t.lower() == "security" for t in tokens)
    if _has_real_mitre_mapping(payload) and not has_security:
        findings.append(
            Finding(
                severity="HIGH",
                kind="monitoring-type-security-mismatch",
                uc_id=uc_id,
                file=file,
                message=(
                    "UC has a genuine MITRE attackTechniques mapping but"
                    " `monitoringType` does not include `Security`."
                    " ATT&CK describes adversary behaviour - add"
                    " `Security` (multi-label is fine) or remove the"
                    " ATT&CK mapping if the behaviour is purely"
                    " operational."
                ),
                snippet=", ".join(tokens),
            )
        )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit monitoringType across the JSON SSOT.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit non-zero when any HIGH finding is reported.",
    )
    args = parser.parse_args(argv)

    all_findings: list[Finding] = []
    sidecar_count = 0
    for path, payload in iter_uc_sidecars():
        sidecar_count += 1
        uc_id = f"UC-{payload.get('id', '<unknown>')}"
        all_findings.extend(_check_uc(uc_id, path.name, payload))

    print("=" * 72)
    print("Monitoring-type audit (content/cat-*/UC-*.json)")
    print("=" * 72)
    print(f"Sidecars scanned: {sidecar_count}")
    by_sev = Counter(f.severity for f in all_findings)
    print("Findings by severity: " + ", ".join(f"{k}={v}" for k, v in sorted(by_sev.items())))
    by_kind = Counter(f.kind for f in all_findings)
    print("\nFindings by category:")
    for kind, count in sorted(by_kind.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:4d}  {kind}")

    if all_findings:
        print("\nFINDINGS:")
        print("-" * 72)
        severity_order = {"HIGH": 0, "MED": 1, "LOW": 2}
        for f in sorted(
            all_findings,
            key=lambda x: (severity_order.get(x.severity, 99), x.file, x.uc_id),
        ):
            print(f"[{f.severity}] [{f.kind}] {f.uc_id} ({f.file}): {f.message}")
            if f.snippet:
                print(f"        snippet: {f.snippet[:200]}")

    if args.check and by_sev.get("HIGH", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
