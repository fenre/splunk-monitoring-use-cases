#!/usr/bin/env python3
"""Audit use-cases/cat-*.md for placeholder and scaffolding text.

Flags patterns that indicate unfinished or templated content:

1. Literal placeholder markers inside UC fields — ``TBD``, ``FIXME``, ``TODO``,
   ``XXX``, ``PLACEHOLDER``, ``example.com``, ``example.org``, ``<your-...>``,
   angle-bracketed ALL-CAPS placeholders (``<YOUR_INDEX>`` style), and stub
   values like ``"calculated_value"``.

2. Blank / punctuation-only ``Known false positives`` entries — lines that look
   like ``- **Known false positives:** |`` or ``- **Known false positives:** —``.

3. Editorial scaffolding headers inside the catalog that leak internal workflow
   phases (``### 22.12 — per-regulation content fill (Phase 2.3)``).

4. Generic "control theme N" / "point N" / "indicator N" titles — common
   templated-content artefacts in cat-22 long-tail sections.

The linter is structural (line-based) so it will run in well under a second
even on the entire catalog.  False positives are possible inside prose — the
linter is tuned to be conservative and produces MED severity at most.

Usage::

    python scripts/audit_placeholders.py             # human report
    python scripts/audit_placeholders.py --check     # non-zero exit on any HIGH finding
    python scripts/audit_placeholders.py --json      # JSON output
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES = os.path.join(REPO_ROOT, "use-cases", "cat-*.md")

RE_UC_HEAD = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE)
RE_SECTION_HEAD = re.compile(r"^(#{2,4})\s+(.*)$", re.MULTILINE)
RE_SPL_FENCE = re.compile(r"```spl\n(.*?)\n```", re.DOTALL)
RE_FIELD = re.compile(r"^- \*\*(?P<field>[^*]+):\*\*\s*(?P<body>.*)$", re.MULTILINE)


@dataclass
class Finding:
    file: str
    uc_id: str
    severity: str
    category: str
    message: str
    snippet: str = ""

    def human(self) -> str:
        s = f"[{self.severity}] [{self.category}] {self.uc_id} ({os.path.basename(self.file)}): {self.message}"
        if self.snippet:
            s += f"\n        snippet: {self.snippet.strip()[:160]}"
        return s


# ---------------------------------------------------------------------------
# Helpers


def _iter_uc_blocks(text: str) -> Iterable[Tuple[str, str, int, int]]:
    matches = list(RE_UC_HEAD.finditer(text))
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield uc_id, text[start:end], start, end


# ---------------------------------------------------------------------------
# Placeholder markers

# Each pattern is compiled once; names describe what we surface.
_MARKERS: list[Tuple[str, re.Pattern[str], str, str]] = [
    # (category, pattern, severity, message)
    (
        "literal-tbd",
        re.compile(r"\b(?:TBD|FIXME|XXX+)\b"),
        "HIGH",
        "Literal placeholder marker (TBD/FIXME/XXX) present in UC content.",
    ),
    (
        "literal-todo",
        re.compile(r"\bTODO\b"),
        "HIGH",
        "Literal TODO marker present in UC content.",
    ),
    (
        "example-com",
        re.compile(r"\bexample\.(?:com|org|net)\b", re.IGNORECASE),
        "MED",
        "Reference to example.com/example.org — replace with concrete vendor/URL or drop.",
    ),
    (
        "angle-placeholder",
        # e.g. <YOUR_INDEX>, <YOUR-TENANT>, <REPLACE_ME>
        re.compile(r"<\s*(?:YOUR|REPLACE|PUT|ENTER|INSERT|FILL|TODO|TBD)[A-Z0-9_\- ]*\s*>",
                   re.IGNORECASE),
        "HIGH",
        "Angle-bracketed placeholder token (<YOUR_...>, <REPLACE_ME>) left in content.",
    ),
    (
        "calculated-value",
        re.compile(r'"\s*calculated[_\- ]?value\s*"', re.IGNORECASE),
        "HIGH",
        "Literal `\"calculated_value\"` stub in SPL — replace with real eval expression.",
    ),
    (
        "control-theme-n",
        re.compile(
            r"\b(?:control theme|control point|control indicator|indicator)\s+(?:N|\d+)\b",
            re.IGNORECASE,
        ),
        "HIGH",
        "Templated title pattern (\"control theme N\", \"indicator N\") — content clearly "
        "not finalised.",
    ),
]


def _check_markers(uc_id: str, file: str, body: str) -> List[Finding]:
    """Scan UC body for known placeholder markers.

    We restrict the scan to *content* (non-code-fence) sections because markers
    inside SPL fences are typically intentional variables (but we still check
    ``calculated_value``-style stubs that commonly appear in SPL).
    """
    findings: List[Finding] = []
    # Strip out code fences for prose checks
    prose = RE_SPL_FENCE.sub("\n\n", body)
    for cat, pat, sev, msg in _MARKERS:
        # calculated_value/angle-placeholder can legally appear inside SPL;
        # we run them against the *full* body as well.
        scan_text = body if cat in {"calculated-value", "angle-placeholder"} else prose
        m = pat.search(scan_text)
        if not m:
            continue
        snippet = scan_text[max(0, m.start() - 40) : m.end() + 40]
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity=sev,
                category=cat,
                message=msg,
                snippet=snippet.replace("\n", " ¶ "),
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Known-FP scaffolding detection

RE_KNOWN_FP = re.compile(
    r"^-\s*\*\*Known false positives\*\*?:?\*?\*?\s*(?P<body>.*)$",
    re.MULTILINE,
)


def _check_known_fp_blank(uc_id: str, file: str, body: str) -> List[Finding]:
    m = RE_KNOWN_FP.search(body)
    if not m:
        return []
    text = m.group("body").strip()
    # Nothing after the label at all
    if not text:
        return [
            Finding(
                file=file,
                uc_id=uc_id,
                severity="MED",
                category="known-fp-blank",
                message="`Known false positives:` field has no content (label-only line).",
                snippet=m.group(0).strip()[:160],
            )
        ]
    # Placeholder-shaped content: `|`, `—`, `-`, `N/A`, `TBD`, etc.
    stripped = text.rstrip(".").strip()
    if stripped in {"|", "—", "-", "–"} or stripped.lower() in {
        "none",
        "n/a",
        "na",
        "tbd",
        "todo",
        "none identified",
        "none known",
    }:
        return [
            Finding(
                file=file,
                uc_id=uc_id,
                severity="MED",
                category="known-fp-placeholder",
                message=(
                    "`Known false positives:` has placeholder-only content "
                    f"(`{stripped}`). Either list real noise sources or remove the label."
                ),
                snippet=m.group(0).strip()[:160],
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Editorial scaffolding headers

RE_EDITORIAL_HEADER = re.compile(
    r"^(#{2,4})\s+[^\n]*\((?:Phase|Batch|Round|Tranche|Iteration|Pass|Shard)\s*[\d.]+\)",
    re.IGNORECASE | re.MULTILINE,
)


def _check_editorial_headers(file: str, text: str) -> List[Finding]:
    findings: List[Finding] = []
    for m in RE_EDITORIAL_HEADER.finditer(text):
        # Try to attribute to the containing UC if any
        pos = m.start()
        uc_id = "—"
        for uc, body, s, e in _iter_uc_blocks(text):
            if s <= pos < e:
                uc_id = uc
                break
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity="MED",
                category="editorial-scaffolding-header",
                message=(
                    "Header references an internal content-workflow phase "
                    "(Phase N.N, Batch N, ...). These scaffolding markers should "
                    "not leak into the published catalog."
                ),
                snippet=m.group(0).strip()[:160],
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Orchestration


def audit_file(path: str) -> List[Finding]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    findings: List[Finding] = []
    for uc_id, body, _s, _e in _iter_uc_blocks(text):
        findings.extend(_check_markers(uc_id, path, body))
        findings.extend(_check_known_fp_blank(uc_id, path, body))
    findings.extend(_check_editorial_headers(path, text))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
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

    paths = sorted(glob.glob(USE_CASES))
    all_findings: List[Finding] = []
    for p in paths:
        all_findings.extend(audit_file(p))

    if args.json:
        print(json.dumps([asdict(f) for f in all_findings], indent=2))
    else:
        print("=" * 72)
        print("Placeholder audit (use-cases/cat-*.md)")
        print("=" * 72)
        print(f"Files scanned: {len(paths)}")
        counts: dict[str, int] = {}
        for f in all_findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        print(
            "Findings by severity: "
            + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        )
        print()
        by_cat: dict[str, int] = {}
        for f in all_findings:
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        print("Findings by category:")
        for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            print(f"  {v:4d}  {k}")
        print()
        if all_findings:
            print("FINDINGS:")
            print("-" * 72)
            for f in all_findings:
                print(f.human())

    if not args.check:
        return 0
    severity_order = {"HIGH": 3, "MED": 2, "LOW": 1}
    thresh = severity_order[args.severity]
    n_fail = sum(1 for f in all_findings if severity_order[f.severity] >= thresh)
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
