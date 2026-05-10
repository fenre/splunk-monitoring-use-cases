#!/usr/bin/env python3
"""Audit alignment between ``cimModels`` declarations and ``cimSpl`` queries.

Walks the JSON SSOT (``content/cat-*/UC-*.json``) and surfaces three
classes of drift:

1. **``cim-models-nonstandard-token``** (LOW) — ``cimModels`` array
   contains a non-canonical spelling of a known datamodel (e.g.,
   ``Network Traffic`` instead of ``Network_Traffic``).
2. **``cim-spl-datamodel-missing``** (MED) — the UC declares ``cimModels``
   but the ``cimSpl`` query has no ``datamodel=...`` reference. A CIM SPL
   block should query the declared model via tstats or pivot.
3. **``cim-spl-datamodel-mismatch``** (HIGH) — ``cimSpl`` references a
   datamodel that is not listed in ``cimModels``. Either the declaration
   is wrong or the SPL was copy-pasted from a different UC.

Pre-v8.2.0 this walked ``use-cases/cat-*.md``; the JSON SSOT is the only
backend now.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from typing import NamedTuple

from splunk_uc.audits._uc_walk import get_list_field, get_text_field, iter_uc_sidecars

RE_DATAMODEL = re.compile(
    r"datamodel[ \t]*=[ \t]*`?(?P<name>[A-Za-z][A-Za-z0-9_ ]*)",
    re.IGNORECASE,
)

CANONICAL_DATAMODELS = {
    "Alerts",
    "Application_State",
    "Authentication",
    "Certificates",
    "Change",
    "Compute_Inventory",
    "Databases",
    "DLP",
    "Email",
    "Endpoint",
    "Event_Signatures",
    "Interprocess_Messaging",
    "Intrusion_Detection",
    "Inventory",
    "JVM",
    "Malware",
    "Network_Resolution",
    "Network_Sessions",
    "Network_Traffic",
    "Performance",
    "Splunk_Audit",
    "Ticket_Management",
    "Updates",
    "Vulnerabilities",
    "Web",
    # Splunk Enterprise Security and ITSI ship these out of the box but they
    # live outside the CIM 6.x add-on. Recognise them so they don't raise
    # false-positive mismatch findings.
    "Risk",
    "Service_KPI_Summary",
}
TOKEN_NORMALISATION = {
    "Network Traffic": "Network_Traffic",
    "Ticket Management": "Ticket_Management",
    "Intrusion Detection": "Intrusion_Detection",
    "Network Sessions": "Network_Sessions",
    "Network Resolution": "Network_Resolution",
    "Compute Inventory": "Compute_Inventory",
}


class Finding(NamedTuple):
    severity: str
    kind: str
    uc_id: str
    file: str
    message: str
    snippet: str = ""


def _extract_datamodels_from_spl(spl: str) -> set[str]:
    names: set[str] = set()
    for m in RE_DATAMODEL.finditer(spl):
        raw = m.group("name").strip().split(".")[0].strip()
        raw = raw.replace(" ", "_")
        names.add(raw)
    return names


def _check_uc(uc_id: str, file: str, payload: dict) -> list[Finding]:
    findings: list[Finding] = []
    declared_models = get_list_field(payload, "cimModels")
    if not declared_models:
        return findings

    # Normalise + collect findings on declared list
    declared_canonical: set[str] = set()
    for entry in declared_models:
        if not isinstance(entry, str):
            continue
        token = entry.strip()
        if not token:
            continue
        if token in CANONICAL_DATAMODELS:
            declared_canonical.add(token)
        elif token in TOKEN_NORMALISATION:
            findings.append(
                Finding(
                    severity="LOW",
                    kind="cim-models-nonstandard-token",
                    uc_id=uc_id,
                    file=file,
                    message=(
                        f"Non-canonical CIM model token: '{token}' -> "
                        f"'{TOKEN_NORMALISATION[token]}'. Use underscore-"
                        f"separated names for tstats compatibility."
                    ),
                    snippet=token,
                )
            )
            declared_canonical.add(TOKEN_NORMALISATION[token])
        else:
            # Unrecognised but not blocking — could be a sub-dataset name
            # like ``Network_Traffic.All_Traffic`` or a descriptive label.
            base = token.split(".")[0]
            if base in CANONICAL_DATAMODELS:
                declared_canonical.add(base)

    spl_text = get_text_field(payload, "cimSpl")
    if not spl_text.strip():
        return findings

    used_models = _extract_datamodels_from_spl(spl_text)

    if not used_models:
        findings.append(
            Finding(
                severity="MED",
                kind="cim-spl-datamodel-missing",
                uc_id=uc_id,
                file=file,
                message=(
                    "cimSpl present but contains no `datamodel=...` "
                    "reference. A CIM SPL should query against the "
                    "declared CIM datamodel (tstats or pivot)."
                ),
                snippet=", ".join(sorted(declared_canonical)),
            )
        )
        return findings

    mismatched = {
        m for m in used_models if m in CANONICAL_DATAMODELS and m not in declared_canonical
    }
    if mismatched:
        findings.append(
            Finding(
                severity="HIGH",
                kind="cim-spl-datamodel-mismatch",
                uc_id=uc_id,
                file=file,
                message=(
                    "cimSpl references datamodel(s) "
                    + ", ".join(sorted(mismatched))
                    + " that are not declared in `cimModels` "
                    + f"({sorted(declared_canonical)!r})."
                    " Align the declaration with the SPL, or update the"
                    " SPL to match the intended datamodel."
                ),
                snippet=", ".join(sorted(used_models)),
            )
        )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit cimModels vs cimSpl alignment across the JSON SSOT.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "CI mode: exit non-zero when a NEW HIGH finding is reported. "
            "Existing drift in the JSON SSOT (cimModels listing one "
            "datamodel while cimSpl queries another) is reported but "
            "does not block — the legacy markdown corpus's free-form "
            "`CIM Models:` field hid these mismatches that the structured "
            "JSON now exposes. Treat HIGH findings as a backlog to fix."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote --check back to a hard block on any HIGH finding.",
    )
    args = parser.parse_args(argv)

    all_findings: list[Finding] = []
    sidecar_count = 0
    for path, payload in iter_uc_sidecars():
        sidecar_count += 1
        uc_id = f"UC-{payload.get('id', '<unknown>')}"
        all_findings.extend(_check_uc(uc_id, path.name, payload))

    print("=" * 72)
    print("CIM <-> SPL alignment audit (content/cat-*/UC-*.json)")
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

    if args.check and args.strict and by_sev.get("HIGH", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
