#!/usr/bin/env python3
"""Audit ``knownFalsePositives`` fields for import/parsing artefacts.

Walks the JSON SSOT (``content/cat-*/UC-*.json``) and surfaces three
classes of issue:

1. ``known-fp-pipe-stub`` (HIGH) — the literal ``|`` character as the
   value. ESCU/YAML import artefact where a YAML block scalar indicator
   (``known_false_positives: |``) collapsed to a single pipe when the
   body was stripped.
2. ``known-fp-empty`` (MED) — the field is present but the value is
   empty.
3. ``known-fp-placeholder`` (LOW) — the value is a short filler token
   like ``-``, ``.``, ``TBD``, ``TODO``, or ``None``.

Pre-v8.2.0 this walked ``use-cases/cat-*.md``.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import NamedTuple

from splunk_uc.audits._uc_walk import get_text_field, iter_uc_sidecars

PLACEHOLDER_VALUES = {"-", ".", "...", "tbd", "todo", "fixme", "xxx", "none"}


class Finding(NamedTuple):
    severity: str
    kind: str
    uc_id: str
    file: str
    message: str
    snippet: str = ""


def _classify(value: str) -> tuple[str, str, str]:
    """Return ``(severity, kind, message)`` for the FP value, or
    ``("", "", "")`` if the value is acceptable."""
    stripped = value.strip()
    if stripped == "|":
        return (
            "HIGH",
            "known-fp-pipe-stub",
            "`knownFalsePositives` holds a literal `|` - a YAML-import"
            " artefact. Replace with a real description or"
            " `N/A (no documented false positives)`.",
        )
    if not stripped:
        return (
            "MED",
            "known-fp-empty",
            "`knownFalsePositives` is blank. Add a real description or"
            " `N/A (no documented false positives)`.",
        )
    if stripped.lower() in PLACEHOLDER_VALUES:
        return (
            "LOW",
            "known-fp-placeholder",
            f"`knownFalsePositives` uses a placeholder value ({stripped!r})."
            " Replace with a real description or"
            " `N/A (no documented false positives)`.",
        )
    return "", "", ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit knownFalsePositives across the JSON SSOT.",
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
        # `knownFalsePositives` is OPTIONAL in the schema; only audit
        # when the key is actually present so we don't raise a
        # known-fp-empty against UCs that simply omit the field.
        if "knownFalsePositives" not in payload:
            continue
        value = get_text_field(payload, "knownFalsePositives")
        sev, kind, msg = _classify(value)
        if sev:
            all_findings.append(
                Finding(
                    severity=sev,
                    kind=kind,
                    uc_id=f"UC-{payload.get('id', '<unknown>')}",
                    file=path.name,
                    message=msg,
                    snippet=value,
                )
            )

    print("=" * 72)
    print("knownFalsePositives audit (content/cat-*/UC-*.json)")
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
        )[:30]:
            print(f"[{f.severity}] [{f.kind}] {f.uc_id} ({f.file}): {f.message}")
            if f.snippet:
                print(f"        snippet: {f.snippet[:120]}")
        if len(all_findings) > 30:
            print(f"... and {len(all_findings) - 30} more (output truncated)")

    if args.check and by_sev.get("HIGH", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
