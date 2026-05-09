#!/usr/bin/env python3
"""Roadmap consistency auditor.

Repo-overhaul plan §P11 (2026-05-09).
Relocated to ``splunk_uc.audits.roadmap_consistency`` under §P6, 2026-05-09.

``ROADMAP.md`` is the single
public-facing artefact that explains where the project is going. It is
referenced from the README, the GitHub Pages footer, and (eventually) a
GitHub Project board synced via ``gh project item-add``. If it silently
drifts — sections renamed, links rotted, version numbers stale — the
front-door promise of the project gets quietly weaker over time.

This audit pins three classes of invariant:

1. **Structural integrity.** Every release of the catalogue must land
   with the same six top-level sections (``Current release``,
   ``Previous releases``, ``Next up: vX.Y …``, ``vX.Y+ backlog (no
   fixed date)``, ``Deprecated / declined ideas``, ``How to influence
   the roadmap``). The Project-board sync, the marketing CTA on the
   landing page, and the contributor onboarding flow all depend on
   this skeleton.
2. **Link integrity.** Every repo-relative ``[text](path)`` link in
   ROADMAP.md must resolve on disk. Forward references to
   ``CHANGELOG.md``, ``GOVERNANCE.md``, ``docs/...``, and
   ``scripts/...`` are the project's primary discoverability surface
   for new contributors; link rot here directly costs first-PR
   conversions.
3. **Release-version alignment.** The ``## Current release`` heading
   pins ``vX.Y`` (sometimes ``vX.Y.Z``); the same triple must agree
   with ``VERSION`` and the top entry of ``CHANGELOG.md`` after a
   release. Drift between these three sources of truth is the most
   common roadmap regression in practice, and the gate writes a clear
   remediation hint when it fires.

Modes
-----

``--check`` (CI default)
    Strict structural + link integrity, soft version drift. Exits 1 on
    structural / link failures; exits 0 on version drift but writes a
    warning to stderr. The soft-fail mode lets the audit land today
    even though ROADMAP.md currently advertises ``v7.1`` against a
    live ``VERSION`` of ``9.2.0`` (the maintainer reconciles version
    drift in a content-judgment PR).

``--strict-version``
    Promotes version drift from a warning to a hard failure. Wired in
    after the maintainer brings ROADMAP.md back in sync; tracked under
    ``p11-roadmap-board`` in the migration status doc.

``--export PATH``
    Writes a machine-readable JSON snapshot of the parsed roadmap to
    ``PATH`` (relative paths resolve against the repo root). The
    schema is pinned at version ``"1.0"`` and is intended as the input
    contract for a downstream ``gh project`` sync action — see the
    "Project board sync" section of ``docs/migration-status.md`` for
    the maintainer runbook.

Stdlib-only per ADR-0004; uses ``re``, ``json``, ``pathlib``,
``argparse``, ``subprocess`` and ``datetime`` only.

Exit codes
----------

* ``0`` — every required section is present, every repo-relative link
  resolves, and (under ``--check``) version drift is at most a warning
  or (under ``--strict-version``) the version triple agrees.
* ``1`` — a structural section is missing, a link is broken, the
  ``Deprecated / declined ideas`` section is empty, or
  ``--strict-version`` was passed and the version triple disagrees.
* ``2`` — usage / I/O error (missing ROADMAP.md, missing VERSION,
  malformed CHANGELOG header).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ``parents[3]`` resolves: roadmap_consistency.py -> audits/ ->
# splunk_uc/ -> src/ -> repo root. The previous home (scripts/) was
# only one level deep so this is the only path adjustment needed.
REPO_ROOT = Path(__file__).resolve().parents[3]
ROADMAP_MD = REPO_ROOT / "ROADMAP.md"
CHANGELOG_MD = REPO_ROOT / "CHANGELOG.md"
VERSION_FILE = REPO_ROOT / "VERSION"

SCHEMA_VERSION = "1.0"

# The six top-level sections that every release of ROADMAP.md must carry.
# Patterns are matched after the leading ``## ``; we use regex because
# the H2 titles for ``Next up`` and the backlog encode the next release
# version inline (e.g. ``Next up: v7.2 — Gold Standard…``).
_REQUIRED_SECTIONS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("current_release", re.compile(r"^Current release$")),
    ("previous_releases", re.compile(r"^Previous releases$")),
    ("next_up", re.compile(r"^Next up:\s*v\d+\.\d+(?:\.\d+)?\s+—.+$")),
    ("backlog", re.compile(r"^v\d+\.\d+\+?\s+backlog\b.*$")),
    ("deprecated", re.compile(r"^Deprecated\s*/\s*declined ideas$")),
    ("how_to_influence", re.compile(r"^How to influence the roadmap$")),
)

# Inline-version patterns. The "Current release" body says
# ``**v7.1 — Non-Technical Everywhere** *(shipped 2026-04-20)*``; we
# pull the version out for the version-triple consistency check.
_INLINE_RELEASE_HEADER = re.compile(
    r"\*\*v(?P<version>\d+\.\d+(?:\.\d+)?)\s+—\s+(?P<name>[^*]+?)\*\*\s*"
    r"\*\((?P<status>shipped|in progress|cancelled)(?:\s+(?P<date>\d{4}-\d{2}-\d{2}))?\)\*",
    re.IGNORECASE,
)

# Match in-doc relative links. We deliberately exclude protocol-prefixed
# (``http://``, ``https://``, ``mailto:``) and pure-anchor (``#section``)
# links since those don't have an on-disk target.
_LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<href>[^)\s]+)\)")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class _ReleaseEntry:
    """One release card under ``## Current release`` / ``## Previous releases``."""

    version: str
    name: str
    status: str  # "shipped" / "in progress" / "cancelled"
    date: str | None  # ISO-8601 (YYYY-MM-DD) or None if not declared


@dataclass
class _Issue:
    """A single audit finding."""

    severity: str  # "error" or "warning"
    message: str

    def format(self) -> str:
        prefix = "ERROR" if self.severity == "error" else "WARN "
        return f"{prefix}: {self.message}"


@dataclass
class _Snapshot:
    """The parsed ROADMAP.md, ready for export or downstream sync."""

    schema_version: str = SCHEMA_VERSION
    captured_at: str = ""
    git_head: str = ""
    current_release: dict[str, Any] = field(default_factory=dict)
    previous_releases: list[dict[str, Any]] = field(default_factory=list)
    next_up: dict[str, Any] = field(default_factory=dict)
    backlog: list[dict[str, Any]] = field(default_factory=list)
    deprecated_ideas: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git_head() -> str:
    """Best-effort current-commit lookup; empty string in a non-git tree.

    We tolerate the no-git case (e.g. an extracted sdist) instead of
    crashing — the JSON snapshot still has structural value without the
    commit identity.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def _read_version_triple() -> tuple[str | None, str | None]:
    """Return (VERSION file content, top CHANGELOG version) — None on miss.

    Both lookups are tolerant: a missing file or unparseable CHANGELOG
    becomes ``None`` rather than an exception, which lets ``--check``
    print a precise issue rather than a stack trace.
    """
    version_text: str | None = None
    if VERSION_FILE.is_file():
        version_text = VERSION_FILE.read_text(encoding="utf-8").strip() or None

    changelog_top: str | None = None
    if CHANGELOG_MD.is_file():
        for line in CHANGELOG_MD.read_text(encoding="utf-8").splitlines():
            # Skip the "[Unreleased]" entry; we want the most recent
            # *released* version. The convention is "## [X.Y.Z] - DATE".
            m = re.match(r"^##\s+\[(?P<v>\d+\.\d+\.\d+)\]\s*-\s*\d{4}-\d{2}-\d{2}\s*$", line)
            if m:
                changelog_top = m.group("v")
                break
    return version_text, changelog_top


def _split_sections(text: str) -> dict[str, list[str]]:
    """Split ROADMAP.md into ``{section_key: [body_lines]}``.

    The keys are the symbolic ones declared in ``_REQUIRED_SECTIONS``;
    a section that doesn't match any required pattern lands under
    ``__unknown__`` (preserved for diagnostics, not re-exported).

    The horizontal-rule markers (``---``) that separate sections are
    stripped from the body. The H2 line itself is *not* included in
    the body; downstream parsers should re-derive the title from the
    section key when needed.
    """
    sections: dict[str, list[str]] = {key: [] for key, _ in _REQUIRED_SECTIONS}
    sections["__unknown__"] = []
    current_key: str | None = None
    for raw_line in text.splitlines():
        if raw_line.startswith("## "):
            heading = raw_line[3:].strip()
            current_key = None
            for key, pattern in _REQUIRED_SECTIONS:
                if pattern.match(heading):
                    current_key = key
                    break
            if current_key is None:
                current_key = "__unknown__"
                sections.setdefault("__unknown__", []).append(f"<<H2>> {heading}")
            continue
        if current_key is None:
            continue
        if raw_line.strip() == "---":
            continue
        sections[current_key].append(raw_line)
    return sections


def _extract_release_entries(body_lines: list[str]) -> list[_ReleaseEntry]:
    """Pull every ``**vX.Y — Name** *(status date)*`` line from a body."""
    entries: list[_ReleaseEntry] = []
    for line in body_lines:
        m = _INLINE_RELEASE_HEADER.search(line)
        if not m:
            continue
        entries.append(
            _ReleaseEntry(
                version=m.group("version"),
                name=m.group("name").strip(),
                status=m.group("status").lower(),
                date=m.group("date"),
            )
        )
    return entries


def _extract_next_up_version(heading: str) -> str | None:
    """Pull ``vX.Y(.Z)`` from a ``Next up: vX.Y …`` heading."""
    m = re.search(r"v(?P<v>\d+\.\d+(?:\.\d+)?)", heading)
    return m.group("v") if m else None


def _next_up_heading(text: str) -> str | None:
    """Return the raw H2 title of the ``Next up`` section, or None."""
    for line in text.splitlines():
        if line.startswith("## ") and re.match(r"^Next up:", line[3:].strip()):
            return line[3:].strip()
    return None


def _join_multiline_bullets(body_lines: list[str]) -> list[str]:
    """Merge wrapped Markdown bullets into single logical lines.

    ROADMAP.md authors wrap long bullets visually::

        - **Industry-specific bundles** — Standalone content packs for
          Finance, OT, Healthcare, …

    A naive line-by-line walker drops the continuation, which makes
    the Project-board sync silently truncate. We detect a bullet
    continuation as any non-empty line that begins with ≥1 spaces and
    *no* bullet marker, and concatenate it onto the previous bullet
    with a single space separator (mirroring how Markdown renders).
    Blank lines reset the "previous bullet" state so two adjacent
    paragraphs don't get mashed together.
    """
    joined: list[str] = []
    for raw in body_lines:
        if raw.lstrip().startswith("- "):
            joined.append(raw.rstrip())
            continue
        if raw.strip() == "":
            joined.append("")
            continue
        if joined and joined[-1].lstrip().startswith("- ") and raw.startswith(" "):
            joined[-1] = joined[-1] + " " + raw.strip()
            continue
        joined.append(raw.rstrip())
    return joined


def _backlog_subsections(body_lines: list[str]) -> list[dict[str, Any]]:
    """Group the backlog body into ``{name, items}`` per H3.

    The backlog body is formatted as::

        ### Content
        - **Industry-specific bundles** — Standalone content packs for
          Finance, OT, Healthcare, …
        - …

        ### Tooling
        - …

    We preserve the bullet-list items verbatim (Markdown intact, with
    multiline wraps re-joined) so downstream Project-board sync can
    render rich body text.
    """
    out: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in _join_multiline_bullets(body_lines):
        if line.startswith("### "):
            if current is not None:
                out.append(current)
            current = {"name": line[4:].strip(), "items": []}
            continue
        if current is None:
            continue
        if line.lstrip().startswith("- "):
            current["items"].append(line.strip()[2:].strip())
    if current is not None:
        out.append(current)
    return out


def _deprecated_items(body_lines: list[str]) -> list[str]:
    """Pull every top-level bullet from the Deprecated / declined section.

    The Markdown convention is::

        - **Hosted SaaS** — The project stays static-site-first…

    We keep the bullet text verbatim (with the bold lead-in and any
    wrapped continuation lines re-joined) so the Project-board sync
    can preserve formatting.
    """
    out: list[str] = []
    for line in _join_multiline_bullets(body_lines):
        if line.lstrip().startswith("- "):
            out.append(line.strip()[2:].strip())
    return out


def _check_links(text: str) -> list[_Issue]:
    """Walk every ``[text](href)`` link; report repo-relative misses.

    External (``http(s)://``, ``mailto:``) and pure-anchor (``#``)
    links are skipped — they're handled by the project's link-check
    workflow and are out of scope for this audit.
    """
    issues: list[_Issue] = []
    seen: set[str] = set()
    for m in _LINK_RE.finditer(text):
        href = m.group("href")
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_str = href.split("#", 1)[0]
        if not target_str:
            continue
        if target_str in seen:
            continue
        seen.add(target_str)
        target = (REPO_ROOT / target_str).resolve()
        try:
            target.relative_to(REPO_ROOT)
        except ValueError:
            issues.append(
                _Issue(
                    "error",
                    f"link target escapes repo root: {href!r} (resolved to {target})",
                )
            )
            continue
        if not target.exists():
            issues.append(_Issue("error", f"broken repo-relative link: {href!r}"))
    return issues


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------


def parse_roadmap(text: str) -> tuple[_Snapshot, list[_Issue]]:
    """Parse ROADMAP.md into a snapshot + structural issues."""
    snap = _Snapshot()
    snap.captured_at = _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")
    snap.git_head = _git_head()

    issues: list[_Issue] = []

    sections = _split_sections(text)

    # 1. Required-section presence
    for key, _pattern in _REQUIRED_SECTIONS:
        body = sections.get(key) or []
        if not any(line.strip() for line in body):
            issues.append(
                _Issue(
                    "error",
                    f"required ROADMAP.md section {key!r} is missing or empty",
                )
            )

    # 2. Current release
    cur_entries = _extract_release_entries(sections.get("current_release", []))
    if not cur_entries:
        issues.append(
            _Issue(
                "error",
                "## Current release does not declare a release "
                "(expected '**vX.Y — Name** *(shipped DATE)*')",
            )
        )
    else:
        cur = cur_entries[0]
        snap.current_release = {
            "version": cur.version,
            "name": cur.name,
            "status": cur.status,
            "date": cur.date,
        }

    # 3. Previous releases
    prev_entries = _extract_release_entries(sections.get("previous_releases", []))
    if not prev_entries:
        issues.append(
            _Issue(
                "warning",
                "## Previous releases section has no parseable release "
                "entries — this is acceptable on a brand-new project but "
                "unusual mid-life",
            )
        )
    snap.previous_releases = [
        {
            "version": e.version,
            "name": e.name,
            "status": e.status,
            "date": e.date,
        }
        for e in prev_entries
    ]

    # 4. Next up
    nxt_heading = _next_up_heading(text)
    if nxt_heading is not None:
        snap.next_up = {
            "version": _extract_next_up_version(nxt_heading) or "",
            "title": nxt_heading,
        }

    # 5. Backlog
    snap.backlog = _backlog_subsections(sections.get("backlog", []))
    if not snap.backlog:
        issues.append(
            _Issue(
                "warning",
                "## vX.Y+ backlog has no H3 subsections — Project-board "
                "sync expects at least one {Content, Tooling, Community}",
            )
        )

    # 6. Deprecated
    snap.deprecated_ideas = _deprecated_items(sections.get("deprecated", []))
    if not snap.deprecated_ideas:
        issues.append(
            _Issue(
                "error",
                "## Deprecated / declined ideas is empty — every release "
                "should at least preserve the historical 'no SaaS' / "
                "'no commercial edition' commitments",
            )
        )

    # 7. Links
    issues.extend(_check_links(text))

    return snap, issues


# ---------------------------------------------------------------------------
# Version-triple consistency
# ---------------------------------------------------------------------------


def check_version_triple(
    snap: _Snapshot,
    *,
    strict: bool,
) -> list[_Issue]:
    """Compare ROADMAP current release ↔ VERSION ↔ CHANGELOG top entry."""
    issues: list[_Issue] = []
    version_file, changelog_top = _read_version_triple()
    roadmap_v = (snap.current_release or {}).get("version")

    severity = "error" if strict else "warning"

    if version_file is None:
        issues.append(_Issue("error", f"VERSION file missing at {VERSION_FILE}"))
    if changelog_top is None:
        issues.append(
            _Issue(
                "error",
                "CHANGELOG.md has no '## [X.Y.Z] - YYYY-MM-DD' entry",
            )
        )

    if roadmap_v and version_file and not _versions_compatible(roadmap_v, version_file):
        issues.append(
            _Issue(
                severity,
                f"ROADMAP.md '## Current release' is v{roadmap_v} but VERSION is "
                f"{version_file}; bump the roadmap heading or release notes "
                "to match the latest release",
            )
        )
    if roadmap_v and changelog_top and not _versions_compatible(roadmap_v, changelog_top):
        issues.append(
            _Issue(
                severity,
                f"ROADMAP.md '## Current release' is v{roadmap_v} but the "
                f"top CHANGELOG.md entry is {changelog_top}; the two must "
                "describe the same release",
            )
        )
    return issues


def _versions_compatible(a: str, b: str) -> bool:
    """Return True if ``a`` and ``b`` describe the same X.Y release line.

    Roadmap headings are conventionally ``vX.Y`` (no patch); VERSION
    and the CHANGELOG carry the full ``X.Y.Z``. We strip the trailing
    patch when comparing so a roadmap entry of ``v9.2`` matches a
    VERSION of ``9.2.0``. Strict equality is opt-in via the caller's
    own logic (e.g. release-day verification).
    """

    def _normalise(v: str) -> tuple[int, int]:
        parts = v.lstrip("v").split(".")
        try:
            return int(parts[0]), int(parts[1])
        except (IndexError, ValueError):
            return -1, -1

    return _normalise(a) == _normalise(b)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit_roadmap_consistency",
        description="Lint ROADMAP.md and emit a Project-board JSON snapshot.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Run structural / link / version-drift checks (default).",
    )
    p.add_argument(
        "--strict-version",
        action="store_true",
        help="Promote VERSION-triple drift from a warning to an error.",
    )
    p.add_argument(
        "--export",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Write a structured JSON snapshot of the parsed roadmap to "
            "PATH (relative paths resolve against the repo root). The "
            "schema is the input contract for downstream Project sync."
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)

    if not ROADMAP_MD.is_file():
        print(f"ERROR: ROADMAP.md missing at {ROADMAP_MD}", file=sys.stderr)
        return 2

    text = ROADMAP_MD.read_text(encoding="utf-8")
    snap, issues = parse_roadmap(text)
    issues.extend(check_version_triple(snap, strict=args.strict_version))

    # Print every finding to stderr so JSON export on stdout (when
    # added later) stays parseable in shell pipelines.
    error_count = 0
    for issue in issues:
        print(issue.format(), file=sys.stderr)
        if issue.severity == "error":
            error_count += 1

    if args.export is not None:
        export_path = args.export
        if not export_path.is_absolute():
            export_path = REPO_ROOT / export_path
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(
            json.dumps(_snapshot_to_dict(snap), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote roadmap snapshot to {export_path}", file=sys.stderr)

    if error_count > 0:
        return 1

    return 0


def _snapshot_to_dict(snap: _Snapshot) -> dict[str, Any]:
    """Stable, JSON-serializable view of the snapshot."""
    return {
        "schema_version": snap.schema_version,
        "captured_at": snap.captured_at,
        "git_head": snap.git_head,
        "current_release": snap.current_release,
        "previous_releases": snap.previous_releases,
        "next_up": snap.next_up,
        "backlog": snap.backlog,
        "deprecated_ideas": snap.deprecated_ideas,
    }


if __name__ == "__main__":
    raise SystemExit(main())
