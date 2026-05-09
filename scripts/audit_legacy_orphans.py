#!/usr/bin/env python3
"""Audit: find UC IDs in legacy ``use-cases/`` markdown that have no JSON SSOT counterpart.

Repo-overhaul plan §P1 step 7 (2026-05-09): the legacy
``use-cases/cat-*.md`` tree is being burned down in three phases
(documented in ``docs/use-cases-burndown.md``). Phase A ends when
every UC ID in legacy markdown also has a sidecar under
``content/cat-*-*/UC-X.Y.Z.json``. This script is the gate that
proves we're at zero orphans before Phase B (the rename to
``content-legacy/``).

Why a separate auditor? ``audit_uc_structure.py`` validates the
JSON SSOT — it has no opinion about what's in ``use-cases/``.
``audit_uc_ids.py`` validates ID uniqueness within the SSOT.
This auditor is the *coverage* check: every UC the legacy tree
claims must be reproducible from JSON.

Modes
-----

``--report`` (default): emit the diagnostic to stdout — counts +
list of orphans grouped by subcategory. Always exits 0.

``--check``: exit non-zero if at least one orphan exists. Use this
mode to gate the burndown's Phase A acceptance criteria. The
expected steady state during Phase A is ``--check`` exit 1; once
all orphans are migrated, it should flip to exit 0 and
``--check`` becomes the freeze point for Phase B.

``--baseline N``: exit non-zero only if the orphan count exceeds
``N``. Used in CI during Phase A so adding more orphans is blocked
while the burndown is active. The current baseline is **0**: Phase A
is complete (2026-05-09) and the legacy tree has zero orphans, so
``--check`` and ``--baseline 0`` now have equivalent semantics. The
``--baseline`` flag is retained for two reasons: (a) pre-Phase-B PR
backporting where someone may add a legacy-only UC by accident, and
(b) so downstream forks running an earlier branch can still bound
their tolerated count to a known number.

The auditor never modifies files. It is purely diagnostic.
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_ROOT = REPO_ROOT / "use-cases"
SSOT_ROOT = REPO_ROOT / "content"

# Lock the inventory to the diagnostic captured in
# docs/use-cases-burndown.md. Phase A migration completed 2026-05-09;
# all 20 orphans listed in the diagnostic now have JSON SSOT
# sidecars. Adding to this list (i.e. raising the constant) is
# explicitly NOT allowed without first re-running the diagnostic
# and updating both the doc and the test that pins this number.
EXPECTED_ORPHAN_COUNT_AT_BASELINE = 0

# UC ID syntax: X.Y.Z where each segment is one or more digits.
_UC_ID_RE = re.compile(r"UC-(\d+\.\d+\.\d+)\b")
_HEADING_TITLE_RE = re.compile(
    r"#+\s*UC-(\d+\.\d+\.\d+)\s*[·•\-]\s*([^\n]+)"
)


def collect_legacy_ids() -> set[str]:
    """Walk ``use-cases/cat-*.md`` and ``use-cases/cat-*/UC-*.md``;
    return the set of UC IDs they reference. Empty if the legacy
    tree has been deleted (Phase C).
    """
    if not LEGACY_ROOT.is_dir():
        return set()
    ids: set[str] = set()
    for path in sorted(LEGACY_ROOT.glob("cat-*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        ids.update(m.group(1) for m in _UC_ID_RE.finditer(text))
    for path in sorted(LEGACY_ROOT.glob("cat-*/UC-*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        ids.update(m.group(1) for m in _UC_ID_RE.finditer(text))
    return ids


def collect_ssot_ids() -> set[str]:
    """Walk ``content/cat-*-*/UC-*.json``; return their UC IDs."""
    if not SSOT_ROOT.is_dir():
        return set()
    ids: set[str] = set()
    for path in sorted(SSOT_ROOT.glob("cat-*/UC-*.json")):
        m = re.search(r"UC-(\d+\.\d+\.\d+)\.json$", path.name)
        if m:
            ids.add(m.group(1))
    return ids


def collect_orphan_titles() -> dict[str, str]:
    """Extract titles for orphan UCs from the legacy markdown headings."""
    titles: dict[str, str] = {}
    if not LEGACY_ROOT.is_dir():
        return titles
    for path in sorted(LEGACY_ROOT.glob("cat-*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in _HEADING_TITLE_RE.finditer(text):
            uc_id, title = m.group(1), m.group(2).strip()
            titles.setdefault(uc_id, title)
    return titles


def report(orphans: set[str], titles: dict[str, str]) -> None:
    if not orphans:
        print("OK: every UC ID in use-cases/ has a JSON SSOT counterpart.")
        return
    print(f"Found {len(orphans)} orphan UC IDs (in legacy markdown but not in JSON SSOT):")
    by_subcat: dict[str, list[str]] = collections.defaultdict(list)
    for uc in orphans:
        subcat = ".".join(uc.split(".", 2)[:2])
        by_subcat[subcat].append(uc)

    def _idx_key(uc: str) -> int:
        return int(uc.split(".")[-1])

    for subcat in sorted(by_subcat, key=lambda s: tuple(int(p) for p in s.split("."))):
        ucs = sorted(by_subcat[subcat], key=_idx_key)
        print(f"  Subcategory {subcat}:")
        for uc in ucs:
            title = titles.get(uc, "(no title)")
            print(f"    UC-{uc:<10} {title}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="audit_legacy_orphans.py",
        description="Find UCs in use-cases/ markdown that have no JSON SSOT counterpart.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--report",
        action="store_true",
        help="Emit the diagnostic to stdout (always exits 0). Default mode.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any orphan exists. Used as the burndown Phase B freeze gate.",
    )
    mode.add_argument(
        "--baseline",
        type=int,
        metavar="N",
        help="Exit 1 if the orphan count exceeds N. Used during Phase A.",
    )
    args = p.parse_args(argv)

    legacy = collect_legacy_ids()
    ssot = collect_ssot_ids()
    orphans = legacy - ssot
    titles = collect_orphan_titles()

    if args.check:
        if orphans:
            print(f"::error::{len(orphans)} legacy-only UC IDs remain. See docs/use-cases-burndown.md.")
            report(orphans, titles)
            return 1
        print("OK: zero orphans — Phase A complete; safe to proceed to Phase B.")
        return 0

    if args.baseline is not None:
        if len(orphans) > args.baseline:
            print(
                f"::error::orphan count grew: {len(orphans)} > baseline {args.baseline}. "
                "Either migrate the new orphans or update the baseline (with reasoning) in "
                "docs/use-cases-burndown.md and the EXPECTED_ORPHAN_COUNT_AT_BASELINE constant."
            )
            report(orphans, titles)
            return 1
        print(
            f"OK: orphan count {len(orphans)} ≤ baseline {args.baseline}. "
            "(Lower baseline as you migrate to ratchet down.)"
        )
        return 0

    report(orphans, titles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
