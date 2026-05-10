#!/usr/bin/env python3
"""Audit the JSON SSOT for placeholder and scaffolding text.

Flags patterns that indicate unfinished or templated content:

1. Literal placeholder markers inside UC fields — ``TBD``, ``FIXME``, ``TODO``,
   ``XXX``, angle-bracketed ALL-CAPS placeholders (``<YOUR_INDEX>`` style),
   ``example.com``, ``"calculated_value"`` stubs.

2. Blank / punctuation-only ``knownFalsePositives`` entries.

3. Generic ``control theme N`` / ``indicator N`` titles — common
   templated-content artefacts.

Pre-v8.2.0 this walked ``use-cases/cat-*.md``; the JSON SSOT
(``content/cat-*/UC-*.json``) is the only backend now.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass

from splunk_uc.audits._uc_walk import iter_uc_sidecars

# Fields swept for placeholder text. Order matters only for output
# stability; we union all matches.
PROSE_FIELDS = (
    "title",
    "description",
    "value",
    "implementation",
    "detailedImplementation",
    "visualization",
    "knownFalsePositives",
    "dataSources",
    "app",
    "exclusions",
    "evidence",
)
SPL_FIELDS = ("spl", "cimSpl")

PLACEHOLDER_FP_VALUES = {
    "|",
    "—",
    "-",
    "–",  # noqa: RUF001 — dash characters are the audit target
    "none",
    "n/a",
    "na",
    "tbd",
    "todo",
    "none identified",
    "none known",
}


@dataclass
class Finding:
    file: str
    uc_id: str
    severity: str
    category: str
    message: str
    snippet: str = ""

    def human(self) -> str:
        s = f"[{self.severity}] [{self.category}] {self.uc_id} ({self.file}): {self.message}"
        if self.snippet:
            s += f"\n        snippet: {self.snippet.strip()[:160]}"
        return s


_MARKERS: list[tuple[str, re.Pattern[str], str, str, bool]] = [
    # (category, pattern, severity, message, is_spl_safe)
    # is_spl_safe=False means: this pattern shouldn't fire on SPL fields
    # (because some keywords are legitimate inside SPL — e.g. variable
    # names that happen to contain TODO).
    (
        "literal-tbd",
        re.compile(r"\b(?:TBD|FIXME|XXX+)\b"),
        "HIGH",
        "Literal placeholder marker (TBD/FIXME/XXX) present in UC content.",
        False,
    ),
    (
        "literal-todo",
        re.compile(r"\bTODO\b"),
        "HIGH",
        "Literal TODO marker present in UC content.",
        False,
    ),
    (
        "example-com",
        re.compile(r"\bexample\.(?:com|org|net)\b", re.IGNORECASE),
        "MED",
        "Reference to example.com/example.org — replace with concrete vendor/URL or drop.",
        False,
    ),
    (
        "angle-placeholder",
        re.compile(
            r"<\s*(?:YOUR|REPLACE|PUT|ENTER|INSERT|FILL|TODO|TBD)[A-Z0-9_\- ]*\s*>",
            re.IGNORECASE,
        ),
        "HIGH",
        "Angle-bracketed placeholder token (<YOUR_...>, <REPLACE_ME>) left in content.",
        True,
    ),
    (
        "calculated-value",
        re.compile(r'"\s*calculated[_\- ]?value\s*"', re.IGNORECASE),
        "HIGH",
        'Literal `"calculated_value"` stub in SPL — replace with real eval expression.',
        True,
    ),
    (
        "control-theme-n",
        re.compile(
            r"\b(?:control theme|control point|control indicator|indicator)\s+(?:N|\d+)\b",
            re.IGNORECASE,
        ),
        "HIGH",
        'Templated title pattern ("control theme N", "indicator N") - content clearly '
        "not finalised.",
        False,
    ),
]


def _check_text(uc_id: str, file: str, field: str, text: str, allow_spl: bool) -> list[Finding]:
    findings: list[Finding] = []
    for cat, pat, sev, msg, is_spl_safe in _MARKERS:
        if not allow_spl and not is_spl_safe and field in SPL_FIELDS:
            continue
        m = pat.search(text)
        if not m:
            continue
        snippet = text[max(0, m.start() - 40) : m.end() + 40]
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity=sev,
                category=cat,
                message=f"[{field}] {msg}",
                snippet=snippet.replace("\n", " | "),
            )
        )
    return findings


def _check_known_fp(uc_id: str, file: str, payload: dict) -> list[Finding]:
    if "knownFalsePositives" not in payload:
        return []
    raw = payload.get("knownFalsePositives")
    if not isinstance(raw, str):
        return []
    text = raw.strip()
    if not text:
        return [
            Finding(
                file=file,
                uc_id=uc_id,
                severity="MED",
                category="known-fp-blank",
                message="`knownFalsePositives` is empty (label-only).",
                snippet="",
            )
        ]
    stripped = text.rstrip(".").strip()
    if stripped in PLACEHOLDER_FP_VALUES or stripped.lower() in PLACEHOLDER_FP_VALUES:
        return [
            Finding(
                file=file,
                uc_id=uc_id,
                severity="MED",
                category="known-fp-placeholder",
                message=(
                    "`knownFalsePositives` has placeholder-only content "
                    f"({stripped!r}). List real noise sources or remove the field."
                ),
                snippet=text[:160],
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Exit 1 if any HIGH finding")
    ap.add_argument("--json", action="store_true", help="JSON output for tooling")
    ap.add_argument(
        "--severity",
        choices=["HIGH", "MED", "LOW"],
        default="HIGH",
        help="Minimum severity threshold for the --check exit code (default: HIGH)",
    )
    args = ap.parse_args(argv)

    all_findings: list[Finding] = []
    sidecar_count = 0
    for path, payload in iter_uc_sidecars():
        sidecar_count += 1
        uc_id = f"UC-{payload.get('id', '<unknown>')}"
        for field in PROSE_FIELDS:
            v = payload.get(field)
            if isinstance(v, str) and v:
                all_findings.extend(_check_text(uc_id, path.name, field, v, allow_spl=False))
        for field in SPL_FIELDS:
            v = payload.get(field)
            if isinstance(v, str) and v:
                all_findings.extend(_check_text(uc_id, path.name, field, v, allow_spl=True))
        all_findings.extend(_check_known_fp(uc_id, path.name, payload))

    if args.json:
        print(json.dumps([asdict(f) for f in all_findings], indent=2))
    else:
        print("=" * 72)
        print("Placeholder audit (content/cat-*/UC-*.json)")
        print("=" * 72)
        print(f"Sidecars scanned: {sidecar_count}")
        counts: dict[str, int] = {}
        for f in all_findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        print("Findings by severity: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        print()
        by_cat: dict[str, int] = {}
        for f in all_findings:
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        print("Findings by category:")
        for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            print(f"  {v:4d}  {k}")
        print()
        if all_findings:
            print("FINDINGS (first 50 shown):")
            print("-" * 72)
            for f in all_findings[:50]:
                print(f.human())
            if len(all_findings) > 50:
                print(f"... and {len(all_findings) - 50} more")

    if not args.check:
        return 0
    severity_order = {"HIGH": 3, "MED": 2, "LOW": 1}
    thresh = severity_order[args.severity]
    n_fail = sum(1 for f in all_findings if severity_order[f.severity] >= thresh)
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
