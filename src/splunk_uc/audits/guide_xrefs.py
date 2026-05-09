#!/usr/bin/env python3
"""Audit cross-product guide links in ``docs/guides/*.md`` for drift.

Walks every guide markdown file, extracts every internal markdown link
that targets another file under ``docs/guides/`` (including links written
relative to the guides directory or the repo root), and verifies the
target file exists. Also reports on guides whose markdown links target a
file that *almost* matches an existing guide name — useful when a guide
is renamed and some callers still point at the old slug.

The audit deliberately ignores:

- External http(s) links — those are covered by ``audit-links``.
- Anchor-only links (``[x](#section)``) — within-document only.
- Links to non-guide repo paths (``[x](../../content/foo.json)``) — those
  belong to a different audit if/when one is added.

Usage::

    python -m splunk_uc audit-guide-xrefs [--strict] [--json]

Exit codes:

- ``0`` — no broken cross-product links found.
- ``2`` — at least one broken cross-product link found (gating).
- ``1`` — usage error.

Run via Make: ``make audit-guide-xrefs`` (added in Batch 12).
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from dataclasses import dataclass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(SCRIPT_DIR),
    ),
)
GUIDES_DIR = os.path.join(REPO_ROOT, "docs", "guides")

# Match every markdown link to a .md file. We intentionally cast a wide
# net here and then post-filter in ``_is_guide_target()`` so we can
# exclude links that escape the ``docs/guides/`` directory (e.g. a guide
# linking to ``../regulatory-primer.md`` or ``../../AGENTS.md`` is valid
# but is NOT a guide cross-reference and must be skipped).
LINK_RE = re.compile(
    r"\[([^\]]+)\]"  # link text
    r"\("
    r"([^)\s#?]+\.md)"  # target ending in .md (no spaces, anchors, queries)
    r"(?:#[^)]*)?"  # optional anchor
    r"(?:\?[^)]*)?"  # optional query
    r"\)"
)


def _is_guide_target(target_raw: str) -> bool:
    """Return True if the link target is intended to point at a guide file.

    A guide reference is one of:

    - A bare basename (no ``/``) — resolves against the source guide's
      own directory, which IS ``docs/guides/``.
    - A path containing the ``guides/`` segment somewhere — explicit
      cross-product reference (``docs/guides/foo.md`` or
      ``../guides/foo.md``).

    Anything else (``../regulatory-primer.md``, ``../../AGENTS.md``,
    ``../../content/foo.json``) escapes the guides directory and is the
    responsibility of a different audit.
    """
    if "/" not in target_raw:
        return True
    return "guides/" in target_raw


@dataclass(frozen=True)
class BrokenLink:
    source: str  # repo-relative path of the source guide
    target_raw: str  # the raw target as written in the markdown
    suggestion: str | None  # closest match in docs/guides/, if any


def _existing_guides() -> set[str]:
    """Return the set of canonical guide basenames (e.g. ``aws.md``)."""
    if not os.path.isdir(GUIDES_DIR):
        return set()
    return {
        name for name in os.listdir(GUIDES_DIR) if name.endswith(".md") and not name.startswith(".")
    }


def _normalize(target_raw: str) -> str:
    """Strip leading ``../`` and ``docs/guides/`` from a link target.

    The audit cares only about the basename — guide files all live in a
    single flat directory. Multiple ``../`` prefixes are tolerated to
    cope with legacy authoring patterns.
    """
    target = target_raw
    while target.startswith("../"):
        target = target[3:]
    target = target.removeprefix("docs/guides/")
    return os.path.basename(target)


def _suggest(target: str, existing: set[str]) -> str | None:
    """Return the closest existing guide basename, if any (cutoff 0.6)."""
    matches = difflib.get_close_matches(target, sorted(existing), n=1, cutoff=0.6)
    return matches[0] if matches else None


def collect_broken_links() -> tuple[list[BrokenLink], int]:
    """Return ``(broken, total_links_scanned)``."""
    existing = _existing_guides()
    broken: list[BrokenLink] = []
    total = 0
    if not existing:
        return broken, total
    for fname in sorted(os.listdir(GUIDES_DIR)):
        if not fname.endswith(".md") or fname.startswith("."):
            continue
        path = os.path.join(GUIDES_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        for m in LINK_RE.finditer(text):
            target_raw = m.group(2)
            if not _is_guide_target(target_raw):
                continue
            normalized = _normalize(target_raw)
            total += 1
            if normalized not in existing:
                broken.append(
                    BrokenLink(
                        source=f"docs/guides/{fname}",
                        target_raw=target_raw,
                        suggestion=_suggest(normalized, existing),
                    )
                )
    return broken, total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit-guide-xrefs",
        description=(
            "Audit cross-product guide links in docs/guides/*.md for drift. "
            "Reports markdown links that target a non-existent guide and "
            "suggests the closest match if there is one."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout (one object per broken link).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Reserved for parity with sibling audits — this audit is "
            "always gating on broken links, so --strict is currently a "
            "no-op. Kept so CI invocations stay forward-compatible."
        ),
    )
    args = parser.parse_args(argv)
    _ = args.strict  # explicitly mark as accepted

    broken, total = collect_broken_links()

    if args.json:
        payload = [
            {
                "source": b.source,
                "target": b.target_raw,
                "suggestion": b.suggestion,
            }
            for b in broken
        ]
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 2 if broken else 0

    print("Guide cross-reference audit")
    print("=" * 60)
    print(f"Scanned {total} internal guide links across {len(_existing_guides())} guides.")
    if not broken:
        print("No broken cross-product links found.")
        return 0
    print(f"Found {len(broken)} broken link(s):\n")
    for b in broken:
        suggestion = f"  -> suggest: {b.suggestion}" if b.suggestion else "  -> no close match"
        print(f"  {b.source}: links to '{b.target_raw}'{suggestion}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
