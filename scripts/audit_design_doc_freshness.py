#!/usr/bin/env python3
"""Audit docs/DESIGN.md freshness.

Non-gating (warns, exits 0 unless --strict). Checks:

1. Every H2 section heading in DESIGN.md matches the canonical list.
2. Every markdown-link reference to a repo file (paths starting with "../"
   or paths without a scheme) resolves to an existing file.

Usage:
    python3 scripts/audit_design_doc_freshness.py [--strict]
"""

from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DESIGN_MD = os.path.join(REPO_ROOT, "docs", "DESIGN.md")

CANONICAL_SECTIONS: List[str] = [
    "1. Purpose and scope",
    "2. Goals and non-goals",
    "3. Target audiences",
    "4. Information architecture",
    "5. Content authoring contract",
    "6. Build pipeline",
    "7. Runtime architecture",
    "8. Quality system",
    "9. Data exports and integrations",
    "10. Release management",
    "11. Governance and contribution model",
    "12. Non-functional properties",
    "13. Reference implementation stack",
    "14. Replication guide",
    "15. Decision log",
    "16. Glossary",
    "17. Extension points",
]

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def read_design() -> str:
    if not os.path.exists(DESIGN_MD):
        print(f"FAIL: {DESIGN_MD} not found", file=sys.stderr)
        sys.exit(2)
    with open(DESIGN_MD, "r", encoding="utf-8") as f:
        return f.read()


def extract_h2_sections(content: str) -> List[str]:
    out: List[str] = []
    for line in content.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            out.append(m.group(1).strip())
    return out


def resolve_link(target: str, doc_dir: str) -> Tuple[bool, str]:
    """Check whether a relative link resolves to a file in the repo."""
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return True, "skip"
    path = target.split("#", 1)[0]
    if not path:
        return True, "skip"
    abs_path = os.path.normpath(os.path.join(doc_dir, path))
    return os.path.exists(abs_path), abs_path


def main() -> int:
    strict = "--strict" in sys.argv
    content = read_design()
    issues: List[str] = []

    sections = extract_h2_sections(content)
    missing = [s for s in CANONICAL_SECTIONS if s not in sections]
    extra = [s for s in sections if s not in CANONICAL_SECTIONS and s != "Table of contents"]
    for s in missing:
        issues.append(f"missing-section: '{s}'")
    for s in extra:
        issues.append(f"extra-section: '{s}'")

    doc_dir = os.path.dirname(DESIGN_MD)
    for target in LINK_RE.findall(content):
        ok, resolved = resolve_link(target, doc_dir)
        if not ok:
            issues.append(f"broken-link: '{target}' -> '{resolved}'")

    if issues:
        print("DESIGN.md freshness issues:")
        for it in issues:
            print(f"  - {it}")
        if strict:
            return 1
        print("(non-gating; pass --strict to fail)")
        return 0

    print(f"OK: DESIGN.md has all {len(CANONICAL_SECTIONS)} canonical sections and all relative links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
