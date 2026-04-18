#!/usr/bin/env python3
"""One-shot remediation for MITRE ATT&CK field taxonomy violations.

Runs through every `use-cases/cat-*.md` and rewrites each
`- **MITRE ATT&CK:** ...` line to contain only canonical MITRE tokens
(`Txxxx`, `Txxxx.yyy`, `TAxxxx`). Non-canonical payloads are handled as:

* **CVE identifiers** — hoisted to a new `- **CVEs:**` line inserted
  immediately before the MITRE line (or appended to an existing one).
* **Parenthetical prose** (`T1078 (Valid Accounts)`) — stripped; only the
  bare technique ID is kept.
* **UUIDs / free-form tokens** — dropped silently (usually ESCU detection
  IDs that leaked during an earlier import).
* **Empty MITRE label** — rewritten to `N/A (mirrored content — no ATT&CK
  mapping provided)` so downstream parsers see a deterministic value.

The script is idempotent: a second run produces zero changes. Run with
`--dry-run` to preview rewrites without touching the working tree.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import List, Tuple

REPO = pathlib.Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"

RE_MITRE_LINE = re.compile(
    r"^(?P<indent>-[ \t]*)\*\*MITRE ATT&CK:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_CVE_LINE = re.compile(
    r"^-[ \t]*\*\*CVEs:\*\*[ \t]*(?P<body>[^\n]*)$",
    re.MULTILINE,
)
RE_CVE_TOKEN = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)
RE_MITRE_TOKEN = re.compile(r"^(?:TA\d{4}|T\d{4}(?:\.\d{3})?)$")
RE_PARENTHETICAL = re.compile(r"\s*\([^)]*\)\s*$")

EMPTY_REPLACEMENT = "N/A (mirrored content — no ATT&CK mapping provided)"


def _tokenize(body: str) -> List[str]:
    return [tok.strip() for tok in body.split(",") if tok.strip()]


def _classify_token(tok: str) -> Tuple[str, str]:
    """Return `(bucket, canonical_value)`.

    Buckets: `mitre`, `cve`, `strip` (drop), or `prose` (parenthetical
    prose already stripped to bare ID).
    """
    if RE_CVE_TOKEN.match(tok):
        return "cve", tok.upper()
    if RE_MITRE_TOKEN.match(tok):
        return "mitre", tok
    stripped = RE_PARENTHETICAL.sub("", tok).strip()
    if stripped and RE_MITRE_TOKEN.match(stripped):
        return "mitre", stripped
    return "strip", tok


def _rewrite_mitre_block(text: str) -> Tuple[str, int]:
    """Rewrite every MITRE line; return `(new_text, change_count)`."""

    changes = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal changes
        body = match.group("body").strip()
        indent = match.group("indent")

        if not body:
            replacement = f"{indent}**MITRE ATT&CK:** {EMPTY_REPLACEMENT}"
            if replacement != match.group(0):
                changes += 1
            return replacement

        if re.match(r"^N/?A(\s*\([^)]+\))?\s*$", body, re.IGNORECASE) and re.match(
            r"^N/?A\s*\([^)]+\)\s*$", body, re.IGNORECASE
        ):
            return match.group(0)

        tokens = _tokenize(body)
        mitre: List[str] = []
        cves: List[str] = []
        for tok in tokens:
            bucket, value = _classify_token(tok)
            if bucket == "mitre" and value not in mitre:
                mitre.append(value)
            elif bucket == "cve" and value not in cves:
                cves.append(value)

        if not mitre and not cves:
            replacement = f"{indent}**MITRE ATT&CK:** {EMPTY_REPLACEMENT}"
        elif mitre:
            replacement = f"{indent}**MITRE ATT&CK:** {', '.join(mitre)}"
        else:
            replacement = f"{indent}**MITRE ATT&CK:** {EMPTY_REPLACEMENT}"

        if cves:
            cve_line = f"{indent}**CVEs:** {', '.join(cves)}"
            replacement = f"{cve_line}\n{replacement}"

        if replacement != match.group(0):
            changes += 1
        return replacement

    new_text = RE_MITRE_LINE.sub(_repl, text)
    return new_text, changes


def _merge_preexisting_cves(text: str) -> str:
    """If a UC already has a `- **CVEs:**` line AND we just added another
    immediately after it, collapse them into one. The rewrite pass
    inserts `CVEs:` *above* the MITRE line, so this only matters for
    UCs that previously carried an explicit `CVEs:` field (none today,
    but we guard for future content).
    """
    lines = text.splitlines(keepends=True)
    out: List[str] = []
    i = 0
    while i < len(lines):
        cur = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if (
            RE_CVE_LINE.match(cur.rstrip("\n"))
            and RE_CVE_LINE.match(nxt.rstrip("\n"))
        ):
            body_a = RE_CVE_LINE.match(cur.rstrip("\n")).group("body").strip()
            body_b = RE_CVE_LINE.match(nxt.rstrip("\n")).group("body").strip()
            combined: List[str] = []
            for tok in _tokenize(body_a) + _tokenize(body_b):
                if tok.upper() not in (c.upper() for c in combined):
                    combined.append(tok.upper())
            indent = re.match(r"^(-[ \t]*)", cur).group(1)
            out.append(f"{indent}**CVEs:** {', '.join(combined)}\n")
            i += 2
            continue
        out.append(cur)
        i += 1
    return "".join(out)


def process_file(path: pathlib.Path, write: bool) -> int:
    original = path.read_text(encoding="utf-8")
    rewritten, changes = _rewrite_mitre_block(original)
    if changes == 0:
        return 0
    rewritten = _merge_preexisting_cves(rewritten)
    if write:
        path.write_text(rewritten, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the number of rewrites per file without saving.",
    )
    args = parser.parse_args()

    total = 0
    for md in sorted(USE_CASES.glob("cat-*.md")):
        changes = process_file(md, write=not args.dry_run)
        if changes:
            total += changes
            action = "would update" if args.dry_run else "updated"
            print(f"  {action} {md.name}: {changes} MITRE line(s)")
    print(
        f"\n{'(dry-run) ' if args.dry_run else ''}Total MITRE lines rewritten: {total}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
