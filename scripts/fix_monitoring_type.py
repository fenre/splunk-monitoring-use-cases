#!/usr/bin/env python3
"""One-shot remediation for `Monitoring type:` findings.

Addresses the categories flagged by `audit_monitoring_type.py`:

1. **`monitoring-type-unknown-token`** — normalise non-canonical tokens
   in place (`Operational` → `Operations`, `Physical` → `Physical
   Security`). Preserves surrounding whitespace and sibling tokens.

2. **`monitoring-type-security-mismatch`** — prepend `Security` to the
   monitoring type for any UC whose `MITRE ATT&CK:` line carries a
   canonical technique/tactic ID. ATT&CK describes adversary behaviour,
   so a UC with a real technique ID is at minimum a security use case.

The script is idempotent: a second run produces zero changes. Use
`--dry-run` to preview counts without touching the working tree.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import List, Tuple

REPO = pathlib.Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"

RE_UC_HEAD = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE)
RE_MITRE_LINE = re.compile(
    r"^-[ \t]*\*\*MITRE ATT&CK:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_MON_LINE = re.compile(
    r"^(?P<prefix>-[ \t]*\*\*Monitoring type:\*\*[ \t]*)(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_MITRE_TOKEN = re.compile(r"^(?:TA\d{4}|T\d{4}(?:\.\d{3})?)$")
RE_MITRE_NA = re.compile(r"^N/?A(\s*\([^)]+\))?\s*$", re.IGNORECASE)

TOKEN_NORMALISATION = {
    "Operational": "Operations",
    "Physical": "Physical Security",
}


def _has_real_mitre_mapping(uc_body: str) -> bool:
    m = RE_MITRE_LINE.search(uc_body)
    if not m:
        return False
    value = m.group("body").strip()
    if not value or RE_MITRE_NA.match(value):
        return False
    for tok in (t.strip() for t in value.split(",")):
        if tok and RE_MITRE_TOKEN.match(tok):
            return True
    return False


def _normalise_tokens(tokens: List[str]) -> Tuple[List[str], bool]:
    changed = False
    out: List[str] = []
    for tok in tokens:
        canonical = TOKEN_NORMALISATION.get(tok, tok)
        if canonical != tok:
            changed = True
        if canonical not in out:
            out.append(canonical)
    return out, changed


def _apply_fixes_to_block(uc_body: str) -> Tuple[str, int, int]:
    """Return `(rewritten_body, token_fixes, security_fixes)`."""

    mon_match = RE_MON_LINE.search(uc_body)
    if not mon_match:
        return uc_body, 0, 0

    prefix = mon_match.group("prefix")
    body = mon_match.group("body").strip()
    if not body:
        return uc_body, 0, 0

    tokens = [t.strip() for t in body.split(",") if t.strip()]
    normalised, token_changed = _normalise_tokens(tokens)

    sec_changed = False
    if _has_real_mitre_mapping(uc_body):
        has_security = any(t.lower() == "security" for t in normalised)
        if not has_security:
            normalised = ["Security"] + normalised
            sec_changed = True

    if not token_changed and not sec_changed:
        return uc_body, 0, 0

    new_line = f"{prefix}{', '.join(normalised)}"
    start, end = mon_match.start(), mon_match.end()
    rewritten = uc_body[:start] + new_line + uc_body[end:]
    return rewritten, int(token_changed), int(sec_changed)


def _rewrite_file(text: str) -> Tuple[str, int, int]:
    matches = list(RE_UC_HEAD.finditer(text))
    if not matches:
        return text, 0, 0

    pieces: List[str] = []
    total_token = 0
    total_sec = 0
    cursor = 0
    for i, m in enumerate(matches):
        block_start = m.start()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        pieces.append(text[cursor:block_start])
        block = text[block_start:block_end]
        rewritten, tok_fix, sec_fix = _apply_fixes_to_block(block)
        total_token += tok_fix
        total_sec += sec_fix
        pieces.append(rewritten)
        cursor = block_end
    pieces.append(text[cursor:])
    return "".join(pieces), total_token, total_sec


def process_file(path: pathlib.Path, write: bool) -> Tuple[int, int]:
    original = path.read_text(encoding="utf-8")
    rewritten, tok_fix, sec_fix = _rewrite_file(original)
    if tok_fix == 0 and sec_fix == 0:
        return 0, 0
    if write:
        path.write_text(rewritten, encoding="utf-8")
    return tok_fix, sec_fix


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the rewrite counts per file without saving.",
    )
    args = parser.parse_args()

    grand_token = 0
    grand_sec = 0
    for md in sorted(USE_CASES.glob("cat-*.md")):
        tok_fix, sec_fix = process_file(md, write=not args.dry_run)
        if tok_fix or sec_fix:
            grand_token += tok_fix
            grand_sec += sec_fix
            action = "would update" if args.dry_run else "updated"
            print(
                f"  {action} {md.name}: token_norm={tok_fix}, "
                f"security_mismatch={sec_fix}"
            )
    print(
        f"\n{'(dry-run) ' if args.dry_run else ''}"
        f"Totals: token normalisations={grand_token}, "
        f"security-mismatch fixes={grand_sec}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
