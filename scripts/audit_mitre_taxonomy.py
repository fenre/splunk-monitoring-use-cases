#!/usr/bin/env python3
"""Audit ``- **MITRE ATT&CK:**`` fields for taxonomy violations.

The MITRE ATT&CK field is a *reference taxonomy*, not a free-text bag.
Each entry must match the canonical technique-ID format:

    Enterprise matrix:  ``T`` + 4 digits           (e.g. ``T1078``)
    Enterprise sub-technique: ``T`` + 4 digits + ``.`` + 3 digits (``T1003.001``)
    Enterprise tactic label:  ``TAxxxx``           (e.g. ``TA0006``)
    ICS matrix:         ``T`` + 4 digits starting at ``T0800`` (``T0859``)

Anything else is a violation.  The most common abuses we've seen:

1. CVE-IDs smuggled into the MITRE field (``T1190, CVE-2025-33073``).
   CVEs are a separate identifier space and must live in a dedicated
   ``CVEs:`` field so downstream tooling can cross-reference them.

2. Parenthetical free-text after a technique ID — ``T1021 (Remote Services)``.
   The human-readable name belongs in the Value / description, not the
   taxonomy field, because downstream code parses comma-separated IDs.

3. Blank / ``N/A`` entries with no follow-up annotation.  Meta-detection
   UCs are allowed to say ``N/A`` provided they give a brief reason in
   parentheses, e.g. ``N/A (content health monitoring)``.

Severity:
    HIGH  CVE-IDs in MITRE field, non-canonical token (free text, URLs).
    MED   Bare "N/A" with no justification, parenthetical descriptive text.
    LOW   Empty field (no value after the label).

Usage::

    python scripts/audit_mitre_taxonomy.py               # human report
    python scripts/audit_mitre_taxonomy.py --check       # exit 1 on HIGH
    python scripts/audit_mitre_taxonomy.py --json

The audit runs in < 1s across the full catalog.
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
RE_MITRE_LINE = re.compile(
    # Only horizontal whitespace (not \n) between label and body —
    # `\s*` would let the capture hop to the next field's line whenever
    # the MITRE value is blank.
    r"^-[ \t]*\*\*MITRE ATT&CK:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)

# Canonical MITRE tokens accepted verbatim.
RE_VALID_TOKEN = re.compile(
    r"^(?:"
    # TAxxxx tactic id (TA0001 ... TA0043-ish, don't hard-bound it)
    r"TA\d{4}"
    # Txxxx[.yyy] technique/sub-technique (ICS T0xxx, Enterprise T1xxx..T1999)
    r"|T\d{4}(?:\.\d{3})?"
    r")$"
)


@dataclass
class Finding:
    file: str
    uc_id: str
    severity: str
    category: str
    message: str
    snippet: str = ""

    def human(self) -> str:
        s = (
            f"[{self.severity}] [{self.category}] {self.uc_id} "
            f"({os.path.basename(self.file)}): {self.message}"
        )
        if self.snippet:
            s += f"\n        snippet: {self.snippet.strip()[:200]}"
        return s


def _iter_uc_blocks(text: str) -> Iterable[Tuple[str, str, int, int]]:
    matches = list(RE_UC_HEAD.finditer(text))
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield uc_id, text[start:end], start, end


def _tokenize_mitre_body(body: str) -> List[str]:
    """Split the MITRE line body on commas, discarding empty splits.

    Keeps each token's inner whitespace so we can surface the offending
    text in the finding message.  Does not attempt to tokenise inside
    parentheses; parenthetical content is treated as part of the token
    so the validator flags it as free text.
    """

    if not body:
        return []
    raw = [chunk.strip() for chunk in body.split(",")]
    return [r for r in raw if r]


def _check_mitre_line(uc_id: str, file: str, body_text: str) -> List[Finding]:
    findings: List[Finding] = []
    body = body_text.strip()

    if not body:
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity="LOW",
                category="mitre-empty",
                message=(
                    "`MITRE ATT&CK:` label present but no value. Either "
                    "provide technique IDs or write `N/A (<brief reason>)` "
                    "for meta-detections."
                ),
                snippet=body_text.strip()[:200],
            )
        )
        return findings

    # "N/A (reason)" pattern: allowed, provided the parens are non-empty.
    if re.match(r"^N/?A(\s*\([^)]+\))?\s*$", body, re.IGNORECASE):
        if not re.match(r"^N/?A\s*\([^)]+\)\s*$", body, re.IGNORECASE):
            findings.append(
                Finding(
                    file=file,
                    uc_id=uc_id,
                    severity="MED",
                    category="mitre-na-unjustified",
                    message=(
                        "`MITRE ATT&CK:` is `N/A` without a parenthesised "
                        "reason. Write `N/A (<why this UC has no technique>)` "
                        "so reviewers know the classification was intentional."
                    ),
                    snippet=body_text.strip()[:200],
                )
            )
        return findings

    tokens = _tokenize_mitre_body(body)
    if not tokens:
        return findings

    cve_tokens: List[str] = []
    url_tokens: List[str] = []
    paren_tokens: List[str] = []
    bad_tokens: List[str] = []

    for tok in tokens:
        upper = tok.upper()
        # CVE-YYYY-NNNN or CVE-YYYY-NNNNNN etc.
        if re.match(r"^CVE-\d{4}-\d{4,7}$", upper):
            cve_tokens.append(tok)
            continue
        # Looks like a URL
        if re.match(r"^https?://", tok):
            url_tokens.append(tok)
            continue
        # Contains parenthetical prose: T1021 (Remote Services)
        if "(" in tok or ")" in tok:
            paren_tokens.append(tok)
            continue
        if RE_VALID_TOKEN.match(upper):
            continue
        bad_tokens.append(tok)

    if cve_tokens:
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity="HIGH",
                category="mitre-cve-mixed",
                message=(
                    f"CVE identifiers smuggled into MITRE ATT&CK field "
                    f"({', '.join(cve_tokens)}). Move CVEs to a dedicated "
                    "`CVEs:` field — they are not ATT&CK techniques."
                ),
                snippet=body_text.strip()[:200],
            )
        )
    if url_tokens:
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity="HIGH",
                category="mitre-url-in-field",
                message=(
                    f"URL in MITRE ATT&CK field ({', '.join(url_tokens)}). "
                    "Put documentation links in the `References:` field."
                ),
                snippet=body_text.strip()[:200],
            )
        )
    if paren_tokens:
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity="MED",
                category="mitre-parenthetical-prose",
                message=(
                    f"Free-text description after technique ID: "
                    f"{', '.join(paren_tokens)}. Downstream parsers split on "
                    "commas — keep only the bare `Txxxx[.yyy]` IDs."
                ),
                snippet=body_text.strip()[:200],
            )
        )
    if bad_tokens:
        findings.append(
            Finding(
                file=file,
                uc_id=uc_id,
                severity="HIGH",
                category="mitre-invalid-token",
                message=(
                    f"Non-canonical MITRE token(s): {', '.join(bad_tokens)}. "
                    "Each token must be `Txxxx`, `Txxxx.yyy`, or `TAxxxx`."
                ),
                snippet=body_text.strip()[:200],
            )
        )
    return findings


def audit_file(path: str) -> List[Finding]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    findings: List[Finding] = []
    for uc_id, body, _s, _e in _iter_uc_blocks(text):
        m = RE_MITRE_LINE.search(body)
        if not m:
            continue
        findings.extend(_check_mitre_line(uc_id, path, m.group("body")))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Exit 1 if any HIGH finding")
    ap.add_argument("--json", action="store_true", help="JSON output")
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
        print("MITRE ATT&CK taxonomy audit (use-cases/cat-*.md)")
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
