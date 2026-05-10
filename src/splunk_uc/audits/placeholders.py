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
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from splunk_uc.audits._uc_walk import iter_uc_sidecars

# Default baseline file for accepted (tracked) content debt — e.g. cat-22
# tier-3 long-tail UCs whose titles still read ``"<area> — control theme N"``
# pending SME-quality re-titling. Findings whose ``(uc_id, file, category)``
# triple appears in the baseline are filtered out before the ``--check``
# severity gate runs, so CI fails only on NEW findings (regressions) until
# the backlog is cleared. The baseline is human-readable JSON so reviewers
# can see exactly which UCs are accepted as debt.
DEFAULT_BASELINE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "data"
    / "audits"
    / "placeholders-baseline.json"
)

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


# literal-tbd needs a tighter boundary than ``\b`` because legitimate
# operational notation also contains ``XXX+``-shaped tokens that are NOT
# placeholder markers — most notably:
#
# * IPv6 multicast group notation: ``ff02::1:ffXX:XXXX`` (cat-5 IPv6 UCs)
# * Ticket-template placeholders: ``CHG-XXXX``, ``#XXX`` (change-management UCs)
# * EUI-64 / MAC-style hex grouping: ``XX:XXXX:XXXX``
#
# These are real documented conventions, not unfinished scaffolding. The
# negative look-around requires the surrounding character class to NOT be
# alphanumeric or one of the ticket / address separators (``: # -``) so we
# only match standalone ``TBD`` / ``FIXME`` / ``XXX+`` tokens that sit in
# prose, never inside hex addresses or templated identifiers.
_LITERAL_TBD = re.compile(
    r"(?<![A-Za-z0-9_:#-])(?:TBD|FIXME|XXX+)(?![A-Za-z0-9_:-])"
)


_MARKERS: list[tuple[str, re.Pattern[str], str, str, bool]] = [
    # (category, pattern, severity, message, is_spl_safe)
    # is_spl_safe=False means: this pattern shouldn't fire on SPL fields
    # (because some keywords are legitimate inside SPL — e.g. variable
    # names that happen to contain TODO).
    (
        "literal-tbd",
        _LITERAL_TBD,
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
        # RFC 2606 reserves example.com/.org/.net specifically for
        # documentation. The patterns we surface here (HEC URL placeholders,
        # email recipient placeholders) are the IETF-sanctioned convention
        # for technical instructions — keep MED so they remain visible in
        # reports without breaking CI under default ``--severity HIGH``.
        re.compile(r"\bexample\.(?:com|org|net)\b", re.IGNORECASE),
        "MED",
        "Reference to example.com/example.org/example.net — RFC 2606 docs "
        "convention; verify it is intentional and not a forgotten stub.",
        False,
    ),
    (
        "angle-placeholder",
        # Conventional ``<YOUR_HEC_TOKEN>`` / ``<your-role>`` patterns are
        # the standard documentation convention for user-fillable
        # instructions in implementation guides — the user is expected to
        # substitute real values when they follow the guide. They are NOT
        # unfinished content. Keep them visible in reports at MED so we
        # still catch genuine scaffolding (e.g. a UC where a placeholder
        # leaks into prose), without blocking CI under default
        # ``--severity HIGH``.
        re.compile(
            r"<\s*(?:YOUR|REPLACE|PUT|ENTER|INSERT|FILL|TODO|TBD)[A-Z0-9_\- ]*\s*>",
            re.IGNORECASE,
        ),
        "MED",
        "Angle-bracketed placeholder token (<YOUR_...>, <REPLACE_ME>) — "
        "verify this is a documented user-fillable instruction, not "
        "unfinished content.",
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


def _check_known_fp(
    uc_id: str, file: str, payload: dict[str, object]
) -> list[Finding]:
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


def _load_baseline(path: Path) -> set[tuple[str, str, str]]:
    """Load the accepted-debt baseline.

    Returns the set of ``(uc_id, file, category)`` triples that should be
    filtered out before the severity gate runs. Missing baseline file is
    treated as empty (no findings suppressed) so the audit is safe to run
    on a fresh checkout.
    """
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"WARN: could not read baseline {path}: {exc}; treating as empty",
            file=sys.stderr,
        )
        return set()
    entries = data.get("entries", []) if isinstance(data, dict) else data
    triples: set[tuple[str, str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        uc_id = entry.get("uc_id")
        file = entry.get("file")
        category = entry.get("category")
        if uc_id and file and category:
            triples.add((uc_id, file, category))
    return triples


def _baseline_key(f: Finding) -> tuple[str, str, str]:
    return (f.uc_id, f.file, f.category)


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
    ap.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help=(
            "Path to JSON baseline of accepted (tracked) findings. "
            "Findings matching baseline entries are filtered out before "
            "the --check severity gate. Pass --no-baseline to disable. "
            f"Default: {DEFAULT_BASELINE}"
        ),
    )
    ap.add_argument(
        "--no-baseline",
        action="store_true",
        help="Disable baseline filtering — report ALL findings (useful for audits/regen).",
    )
    ap.add_argument(
        "--write-baseline",
        action="store_true",
        help=(
            "Write the current findings (excluding LOW) to the --baseline "
            "path and exit 0. Use to refresh accepted-debt tracking."
        ),
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

    baseline_path = Path(args.baseline)
    baseline: set[tuple[str, str, str]] = (
        set() if args.no_baseline else _load_baseline(baseline_path)
    )

    if args.write_baseline:
        # Snapshot HIGH+MED findings; LOW is too noisy to baseline.
        new_entries = [
            {"uc_id": f.uc_id, "file": f.file, "category": f.category}
            for f in all_findings
            if f.severity in ("HIGH", "MED")
        ]
        seen: set[tuple[str, str, str]] = set()
        deduped: list[dict[str, str]] = []
        for entry in new_entries:
            key = (entry["uc_id"], entry["file"], entry["category"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)
        deduped.sort(key=lambda e: (e["category"], e["uc_id"], e["file"]))
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(
                {
                    "schema": "placeholders-baseline.v1",
                    "description": (
                        "Accepted (tracked) placeholder-audit findings. "
                        "Each entry is a (uc_id, file, category) triple "
                        "the audit will filter out before the --check "
                        "severity gate. NEW findings beyond this baseline "
                        "still fail CI. Refresh with `splunk_uc "
                        "audit-placeholders --write-baseline`."
                    ),
                    "entry_count": len(deduped),
                    "entries": deduped,
                },
                indent=2,
                sort_keys=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"Wrote {len(deduped)} accepted-debt entries to {baseline_path}",
            file=sys.stderr,
        )
        return 0

    suppressed = [f for f in all_findings if _baseline_key(f) in baseline]
    surfaced = [f for f in all_findings if _baseline_key(f) not in baseline]

    if args.json:
        print(json.dumps([asdict(f) for f in surfaced], indent=2))
    else:
        print("=" * 72)
        print("Placeholder audit (content/cat-*/UC-*.json)")
        print("=" * 72)
        print(f"Sidecars scanned: {sidecar_count}")
        if baseline:
            print(
                f"Baseline: {baseline_path} ({len(baseline)} accepted entries; "
                f"{len(suppressed)} matched + suppressed)"
            )
        elif args.no_baseline:
            print("Baseline: disabled (--no-baseline)")
        else:
            rel = (
                os.path.relpath(baseline_path)
                if baseline_path.exists()
                else f"{baseline_path} (missing)"
            )
            print(f"Baseline: {rel} (empty / not present)")
        counts: dict[str, int] = {}
        for f in surfaced:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        print(
            "Findings by severity: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            if counts
            else "Findings by severity: (none after baseline)"
        )
        print()
        by_cat: dict[str, int] = {}
        for f in surfaced:
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        print("Findings by category:")
        for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            print(f"  {v:4d}  {k}")
        if not by_cat:
            print("  (none after baseline)")
        print()
        if surfaced:
            print("FINDINGS (first 50 shown):")
            print("-" * 72)
            for f in surfaced[:50]:
                print(f.human())
            if len(surfaced) > 50:
                print(f"... and {len(surfaced) - 50} more")

    if not args.check:
        return 0
    severity_order = {"HIGH": 3, "MED": 2, "LOW": 1}
    thresh = severity_order[args.severity]
    n_fail = sum(1 for f in surfaced if severity_order[f.severity] >= thresh)
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
