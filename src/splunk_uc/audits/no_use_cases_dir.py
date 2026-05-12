#!/usr/bin/env python3
"""Block any reintroduction of the legacy ``use-cases/`` markdown corpus.

The legacy ``use-cases/cat-*.md`` tree was retired in v8.2.0 (see
``docs/migration-status.md``). The JSON SSOT under
``content/cat-NN-<slug>/UC-X.Y.Z.json`` is now the single source of truth.

This audit is the structural guard rail that prevents the dual-content
mess from reappearing. It enforces two invariants:

1. **No directory.** ``use-cases/`` MUST NOT exist under the repo root.
   If it reappears the audit hard-fails.

2. **No new path references.** Tracked files MUST NOT contain
   ``use-cases/`` filesystem path references unless the file is on the
   explicit historical/migration allowlist below. The audit strips
   the two known-safe substrings before scanning each line:

   * ``splunk-monitoring-use-cases`` — the GitHub repo name.
   * Non-repo external URLs (``https?://...`` containing
     ``/use-cases/`` as a path component on third-party sites such as
     ``https://tetragon.io/docs/use-cases/``).

   What's left is treated as a real path reference and fails the
   audit unless the file is allowlisted.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-no-use-cases-dir

Exit ``0`` when the repo is clean, ``2`` on any violation. The
``--list-allowlist`` flag prints the allowlist for reviewers, ``--check``
is accepted as an alias for the default behaviour so this slots into
existing CI patterns.

Maintenance: when a NEW file legitimately needs a historical reference
(e.g. a new ADR documenting the migration), add it to
:data:`ALLOWLIST_PATHS` in this module and explain in the commit
message *why* the historical reference is needed. New active code MUST
NOT use ``use-cases/`` as a real path.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Files that may legitimately reference ``use-cases/`` as historical /
# migration / changelog context. Every entry must be a posix-style
# repo-relative path. Add new entries with care — they should be either
# (a) immutable history (CHANGELOG, ADRs, release notes) or
# (b) docstrings/comments in active code that explain the v8.2.0
# migration. Active *code paths* must not appear here.
ALLOWLIST_PATHS: frozenset[str] = frozenset(
    {
        # ── Repository config / governance ────────────────────────────────
        ".github/CODEOWNERS",
        ".gitleaks.toml",
        # ── Immutable history ──────────────────────────────────────────────
        "CHANGELOG.md",
        "ROADMAP.md",
        "api/README.md",
        "data/audit-baselines/uc-structure-json.txt",
        # ── Migration / architecture documentation ────────────────────────
        "docs/adr/0001-markdown-as-source-of-truth.md",
        "docs/adr/0007-json-as-source-of-truth.md",
        "docs/api-versioning.md",
        "docs/baselines-howto.md",
        "docs/category-files-and-names.md",
        "docs/ci-architecture.md",
        "docs/feasibility-spike-results.md",
        "docs/migration-build-parity.md",
        "docs/migration-status.md",
        "docs/handoff-phase6-tier2.md",
        "docs/health-check-2026-progress.md",
        "docs/replication-guide.md",
        "docs/scripts-taxonomy.md",
        "docs/splunk-apps-use-cases-comparison.md",
        "docs/url-scheme.md",
        "docs/use-cases-burndown.md",
        # ── Release notes embedded in the SPA ─────────────────────────────
        "index.html",
        # ── Tooling docs / READMEs that document removed scripts ──────────
        "content/README.md",
        "scripts/README.md",
        # ── Active code with historical comments only (no real refs) ──────
        "scripts/parse_uc_catalog.py",
        "src/scripts/02-filters.js",
        "src/splunk_uc/audits/_uc_walk.py",
        "src/splunk_uc/audits/changelog_uc_refs.py",
        "src/splunk_uc/audits/cim_spl_alignment.py",
        "src/splunk_uc/audits/known_fp.py",
        "src/splunk_uc/audits/links.py",
        "src/splunk_uc/audits/monitoring_type.py",
        "src/splunk_uc/audits/no_use_cases_dir.py",
        "src/splunk_uc/audits/non_technical_sync.py",
        "src/splunk_uc/audits/placeholders.py",
        "src/splunk_uc/audits/repo_consistency.py",
        "src/splunk_uc/audits/spl_duplicates.py",
        "src/splunk_uc/audits/spl_grammar.py",
        "src/splunk_uc/audits/spl_hallucinations.py",
        "src/splunk_uc/audits/uc_ids.py",
        "src/splunk_uc/audits/uc_structure.py",
        # ── New Phase 6 implementations with historical-path comments ────
        "src/splunk_uc/feasibility/validate_exemplar_uc.py",
        # ── CLI dispatcher registry mentions every verb name + help string ──
        "src/splunk_uc/_registry.py",
        # ── CI / Make targets that DOCUMENT the guard itself ─────────────
        ".github/workflows/validate.yml",
        "Makefile",
        # ── AGENTS.md advertises the verb in its quick-commands list ─────
        "AGENTS.md",
        "tools/build/build.py",
        "tools/build/enrichment.py",
        "tools/build/parse_content.py",
        "tools/validate/validate_md.py",
        # ── Tests with intentional comments referencing migration ─────────
        "tests/golden/compliance-mappings.yaml",
        "tests/sandbox/validate.test.mjs",
        # PR-5 (2026-05-12) added a ``"Legacy use-cases/ guard"`` critical
        # step name to this partition test contract. The literal substring
        # has to be the contract because that is exactly what is matched
        # against the workflow step name. The accompanying comment block
        # documents the v8.2.0 retirement of the original verb.
        "tests/build/test_validate_workflow_partition.py",
        # ── This audit module — the allowlist itself mentions the path ────
        "tests/scripts/test_audit_no_use_cases_dir.py",
    }
)

# Strip the GitHub repo name (which contains the literal "use-cases" by
# coincidence) before the directory-reference check.
_REPO_NAME_RE = re.compile(r"splunk-monitoring-use-cases/?")

# Strip non-repo external URLs that happen to contain ``/use-cases/`` as
# part of a third-party path, e.g. ``https://tetragon.io/docs/use-cases/``.
# We deliberately exclude the published GitHub Pages mirror and the raw
# GitHub source tree (those would always be the repo URL after the
# previous strip).
_EXTERNAL_URL_RE = re.compile(r"https?://[A-Za-z0-9._-]+(?:/[A-Za-z0-9._%/+-]*)?/use-cases/")

# After stripping the safe patterns, a real reference to the legacy dir
# looks like ``use-cases/`` not preceded by an alphanumeric run (so we
# don't false-positive on words like "phase-use-cases" if they ever
# appear).
_DIR_REF_RE = re.compile(r"(?<![A-Za-z0-9_.-])use-cases/")


def _git_tracked_files() -> list[Path]:
    """Return every git-tracked file under the repo (posix-relative)."""
    out = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        text=True,
    )
    return [REPO_ROOT / line for line in out.splitlines() if line]


def _scan_file(path: Path) -> list[tuple[int, str]]:
    """Return ``(line_no, line)`` pairs containing real ``use-cases/`` refs."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Binary files (icons, fonts) don't contribute path references.
        return []
    findings: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        scrubbed = _REPO_NAME_RE.sub("", line)
        scrubbed = _EXTERNAL_URL_RE.sub("", scrubbed)
        if _DIR_REF_RE.search(scrubbed):
            findings.append((i, line.rstrip()))
    return findings


def _check_directory_absent() -> list[str]:
    """Hard fail if ``use-cases/`` exists under the repo root."""
    target = REPO_ROOT / "use-cases"
    if target.exists():
        return [
            "FATAL: The legacy directory `use-cases/` has reappeared at "
            f"{target.relative_to(REPO_ROOT)} — this corpus was retired "
            "in v8.2.0. See docs/migration-status.md."
        ]
    return []


def _check_path_references() -> list[str]:
    """Walk every tracked file and flag stray ``use-cases/`` references."""
    issues: list[str] = []
    for abs_path in _git_tracked_files():
        if not abs_path.is_file():
            continue
        rel_posix = abs_path.relative_to(REPO_ROOT).as_posix()
        if rel_posix in ALLOWLIST_PATHS:
            continue
        # Skip known generated artefacts that live under the build
        # output tree (``dist/``) — they are regenerated from the SSOT
        # and not committed.
        if rel_posix.startswith("dist/"):
            continue
        findings = _scan_file(abs_path)
        if not findings:
            continue
        for line_no, line in findings:
            snippet = line.strip()
            if len(snippet) > 140:
                snippet = snippet[:137] + "..."
            issues.append(f"{rel_posix}:{line_no}: {snippet}")
    return issues


def _print_allowlist() -> None:
    print("# use-cases/ historical-reference allowlist")
    print("#")
    print("# Defined in src/splunk_uc/audits/no_use_cases_dir.py.")
    print("# Add a new entry only for immutable history (CHANGELOG, ADRs,")
    print("# release notes) or active-code docstrings/comments that")
    print("# explain the v8.2.0 migration.")
    for p in sorted(ALLOWLIST_PATHS):
        print(p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Block reintroduction of the legacy use-cases/ markdown corpus. "
            "Hard-fails if the directory reappears or if any non-allowlisted "
            "tracked file gains a use-cases/ path reference."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Accepted for parity with other freshness gates; this audit "
            "is read-only and the default behaviour already exits "
            "non-zero on drift."
        ),
    )
    parser.add_argument(
        "--list-allowlist",
        action="store_true",
        help="Print the historical-reference allowlist and exit 0.",
    )
    args = parser.parse_args(argv)
    _ = args.check  # Accepted as a no-op alias.

    if args.list_allowlist:
        _print_allowlist()
        return 0

    issues: list[str] = []
    issues.extend(_check_directory_absent())
    issues.extend(_check_path_references())

    if not issues:
        print(
            "OK: no use-cases/ directory and no stray path references "
            f"({len(ALLOWLIST_PATHS)} historical files allowlisted)."
        )
        return 0

    print("Legacy use-cases/ guard found violations:")
    print("=========================================")
    for line in issues:
        print(f"  - {line}")
    print()
    print(
        f"Total: {len(issues)} violation(s). Either remove the reference "
        "or, for legitimate historical context, add the file to "
        "ALLOWLIST_PATHS in src/splunk_uc/audits/no_use_cases_dir.py "
        "with a justification in the commit message."
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
