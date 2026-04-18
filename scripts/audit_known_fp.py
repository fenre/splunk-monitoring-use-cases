#!/usr/bin/env python3
"""Audit `Known false positives:` fields for import/parsing artefacts.

Checks performed
----------------
1. **`known-fp-pipe-stub`** (HIGH) — the literal `|` character as the
   FP value. This is an ESCU/YAML import artefact where a YAML block
   scalar indicator (`known_false_positives: |`) collapsed to a single
   pipe when the body was stripped. It carries no information and
   actively misleads readers.
2. **`known-fp-empty`** (MED) — the label is present but the value is
   empty.
3. **`known-fp-placeholder`** (LOW) — the value is a short filler token
   like `-`, `.`, `TBD`, `TODO`, or `None` (which in the Known-FP
   context is ambiguous — prefer `N/A (no documented false positives)`
   or a real description).
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
RE_FP_LINE = re.compile(
    r"^-[ \t]*\*\*Known false positives:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)

PLACEHOLDER_VALUES = {"-", ".", "…", "tbd", "todo", "fixme", "xxx"}


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


def _classify(value: str) -> Tuple[str, str, str]:
    """Return `(severity, kind, message)` for the FP value, or `('', '', '')`
    if the value is considered acceptable."""
    stripped = value.strip()
    if stripped == "|":
        return (
            "HIGH",
            "known-fp-pipe-stub",
            "`Known false positives:` holds a literal `|` — a YAML-import"
            " artefact. Replace with a real description or"
            " `N/A (no documented false positives)`.",
        )
    if not stripped:
        return (
            "MED",
            "known-fp-empty",
            "`Known false positives:` label present but value is blank."
            " Add a real description or"
            " `N/A (no documented false positives)`.",
        )
    if stripped.lower() in PLACEHOLDER_VALUES:
        return (
            "LOW",
            "known-fp-placeholder",
            f"`Known false positives:` uses a placeholder value ({stripped!r})."
            " Replace with a real description or"
            " `N/A (no documented false positives)`.",
        )
    return "", "", ""


def audit_file(path: pathlib.Path) -> List[Finding]:
    text = path.read_text(encoding="utf-8")
    findings: List[Finding] = []
    for uc_id, body in _iter_uc_blocks(text):
        m = RE_FP_LINE.search(body)
        if not m:
            continue
        sev, kind, msg = _classify(m.group("body"))
        if sev:
            findings.append(
                Finding(
                    severity=sev,
                    kind=kind,
                    uc_id=uc_id,
                    file=path.name,
                    message=msg,
                    snippet=m.group("body"),
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Known false positives fields across use-cases/cat-*.md."
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
    print("Known false positives audit (use-cases/cat-*.md)")
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
