#!/usr/bin/env python3
"""Audit alignment between `CIM Models:` declarations and `CIM SPL:` blocks.

Rules enforced
--------------

1. **`cim-models-nonstandard-token`** (LOW) — the `CIM Models:` line uses
   a non-canonical spelling of a known datamodel (e.g., `Network
   Traffic` instead of `Network_Traffic`, or `Ticket Management` instead
   of `Ticket_Management`). Fix is mechanical.
2. **`cim-spl-datamodel-missing`** (MED) — the UC has a non-`N/A` CIM
   Models line and a `CIM SPL:` block, but the SPL does not reference
   any `datamodel=...` or `FROM datamodel=...` clause. In a CIM SPL
   block we expect a `tstats`/`pivot` query against the declared model.
3. **`cim-spl-datamodel-mismatch`** (HIGH) — the CIM SPL references a
   datamodel that is not listed in the declared `CIM Models:` field.
   Either the declaration is wrong or the SPL is copy-pasted from a
   different UC.

The audit is advisory (no file edits). The `fix_cim_spl_alignment.py`
companion script handles the mechanical rewrites surfaced here.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import Counter
from typing import Iterable, List, NamedTuple, Set, Tuple

REPO = pathlib.Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"

RE_UC_HEAD = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE)
RE_CIM_MODELS = re.compile(
    r"^-[ \t]*\*\*CIM Models:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_CIM_SPL_BLOCK = re.compile(
    r"^-[ \t]*\*\*CIM SPL:\*\*[ \t]*\n```spl\n(?P<spl>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)
# datamodel=Foo or datamodel=Foo.Bar  (case-insensitive, tolerates back-ticks).
RE_DATAMODEL = re.compile(
    r"datamodel[ \t]*=[ \t]*`?(?P<name>[A-Za-z][A-Za-z0-9_ ]*)",
    re.IGNORECASE,
)

# Canonical CIM datamodel identifiers (underscore form used in tstats).
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
}
# Common non-canonical spellings that should normalise to canonical form.
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


def _iter_uc_blocks(text: str) -> Iterable[Tuple[str, str]]:
    matches = list(RE_UC_HEAD.finditer(text))
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield uc_id, text[start:end]


def _extract_declared_models(value: str) -> Tuple[Set[str], List[str]]:
    """Return `(canonical_set, nonstandard_spellings_seen)`.

    The `CIM Models:` field in practice contains lots of free-form
    prose like `"Intrusion_Detection (detections) + custom"`, so we
    scan the raw string for canonical/nonstandard datamodel names
    instead of trying to tokenise the grammar.
    """
    canonical: Set[str] = set()
    nonstandard: List[str] = []
    # First strip parenthetical qualifiers so matches don't include them.
    stripped = re.sub(r"\([^)]*\)", "", value)

    # Find every canonical datamodel name (whole-word match, case-sensitive
    # because CIM names use proper casing).
    for name in sorted(CANONICAL_DATAMODELS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", stripped):
            canonical.add(name)

    # Then find common non-canonical spellings and record them for the
    # normalisation finding.
    for bad, good in TOKEN_NORMALISATION.items():
        if re.search(rf"\b{re.escape(bad)}\b", stripped):
            nonstandard.append(bad)
            canonical.add(good)

    return canonical, nonstandard


def _extract_datamodels_from_spl(spl: str) -> Set[str]:
    names: Set[str] = set()
    for m in RE_DATAMODEL.finditer(spl):
        raw = m.group("name").strip().split(".")[0].strip()
        raw = raw.replace(" ", "_")
        names.add(raw)
    return names


def _check_uc(uc_id: str, file: str, body: str) -> List[Finding]:
    findings: List[Finding] = []
    cim_match = RE_CIM_MODELS.search(body)
    if not cim_match:
        return findings

    declared_value = cim_match.group("body").strip()
    if not declared_value or declared_value.lower() in {"n/a", "na"}:
        return findings

    declared_canonical, nonstandard = _extract_declared_models(declared_value)

    if nonstandard:
        repl = [
            f"'{t}' → '{TOKEN_NORMALISATION[t]}'"
            for t in nonstandard
            if t in TOKEN_NORMALISATION
        ]
        if repl:
            findings.append(
                Finding(
                    severity="LOW",
                    kind="cim-models-nonstandard-token",
                    uc_id=uc_id,
                    file=file,
                    message=(
                        "Non-canonical CIM model token(s): "
                        + ", ".join(repl)
                        + ". Use underscore-separated names for tstats"
                        " compatibility."
                    ),
                    snippet=declared_value,
                )
            )

    spl_match = RE_CIM_SPL_BLOCK.search(body)
    if not spl_match:
        return findings

    spl_text = spl_match.group("spl")
    used_models = _extract_datamodels_from_spl(spl_text)

    if not used_models:
        findings.append(
            Finding(
                severity="MED",
                kind="cim-spl-datamodel-missing",
                uc_id=uc_id,
                file=file,
                message=(
                    "CIM SPL block present but contains no `datamodel=...`"
                    " reference. A CIM SPL should query against the"
                    " declared CIM datamodel (tstats or pivot)."
                ),
                snippet=declared_value,
            )
        )
        return findings

    declared_or_empty = declared_canonical or set()
    mismatched = {
        m for m in used_models if m in CANONICAL_DATAMODELS and m not in declared_or_empty
    }
    if mismatched:
        findings.append(
            Finding(
                severity="HIGH",
                kind="cim-spl-datamodel-mismatch",
                uc_id=uc_id,
                file=file,
                message=(
                    "CIM SPL references datamodel(s) "
                    + ", ".join(sorted(mismatched))
                    + " that are not declared in `CIM Models:` "
                    + f"({declared_value!r})."
                    " Align the declaration with the SPL, or update the"
                    " SPL to match the intended datamodel."
                ),
                snippet=", ".join(sorted(used_models)),
            )
        )

    return findings


def audit_file(path: pathlib.Path) -> List[Finding]:
    text = path.read_text(encoding="utf-8")
    findings: List[Finding] = []
    for uc_id, body in _iter_uc_blocks(text):
        findings.extend(_check_uc(uc_id, path.name, body))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit CIM Models vs CIM SPL alignment across use-cases/cat-*.md."
        )
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
    print("CIM ↔ SPL alignment audit (use-cases/cat-*.md)")
    print("=" * 72)
    print(f"Files scanned: {len(files)}")
    by_sev = Counter(f.severity for f in all_findings)
    print(
        "Findings by severity: "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_sev.items()))
    )
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
