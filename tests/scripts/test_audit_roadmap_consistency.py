"""Unit tests for ``scripts/audit_roadmap_consistency.py``.

Repo-overhaul plan §P11 (2026-05-09): ``ROADMAP.md`` is the public
front door for "where is this project going?". A regression here is
silent — there's no Splunk job that fails, no external integration
that pages. The audit script + these tests are the only guard. We
exercise:

* The pure parsers (section-split, release-line extractor, multiline
  bullet joiner, link checker, version comparator) with synthetic
  fixtures so the assertions don't drift when the live ROADMAP.md
  evolves.
* End-to-end ``main()`` against the live ROADMAP.md to catch any
  *new* structural / link / version-drift issues the moment they
  land.
* The ``--export`` JSON snapshot contract so a downstream
  ``gh project item-add`` sync action can rely on a stable shape.

The tests deliberately avoid relying on any specific *content* of
the live ROADMAP.md (other than that it parses) so an authoring
change to the marketing copy doesn't cascade into red CI; the
content-coupled assertions all run against synthetic fixtures.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_roadmap_consistency.py"
LIVE_ROADMAP = REPO_ROOT / "ROADMAP.md"
SRC_DIR = REPO_ROOT / "src"


def _load_audit_module() -> ModuleType:
    """Import the audit implementation module directly.

    P6 (scripts taxonomy, 2026-05-09) relocated the implementation to
    ``src/splunk_uc/audits/roadmap_consistency.py``; the original
    ``scripts/audit_roadmap_consistency.py`` is now a thin shim.

    Tests that monkeypatch module-level constants (``VERSION_FILE``,
    ``CHANGELOG_MD``) MUST go through the implementation module rather
    than the shim — patching the shim only mutates its local
    re-export and does not propagate into the implementation's
    function closures. We therefore import the implementation module
    directly via the package, which both honours that contract and
    keeps the test resilient to future shim deletions in v9.

    The legacy ``importlib.util.spec_from_file_location`` path is
    preserved as a deliberate fallback for the (unlikely) case where
    the package can't be imported (e.g. an unpacked sdist that lost
    the ``src/`` tree); it loads the shim, which still re-exports
    the same names.
    """
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    try:
        import splunk_uc.audits.roadmap_consistency as impl

        return impl
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "audit_roadmap_consistency", SCRIPT_PATH
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["audit_roadmap_consistency"] = module
        spec.loader.exec_module(module)
        return module


@pytest.fixture(scope="module")
def audit() -> ModuleType:
    return _load_audit_module()


# ---------------------------------------------------------------------------
# 1. Pure helpers
# ---------------------------------------------------------------------------


def test_versions_compatible_strips_patch(audit: ModuleType) -> None:
    """X.Y is treated equal to X.Y.Z for the same minor line."""
    assert audit._versions_compatible("v9.2", "9.2.0")
    assert audit._versions_compatible("v9.2.1", "9.2.0")
    assert not audit._versions_compatible("v9.1", "9.2.0")
    assert not audit._versions_compatible("v8.0", "9.0.0")


def test_versions_compatible_handles_garbage(audit: ModuleType) -> None:
    """Unparseable input falls into ``(-1, -1)`` and only matches itself."""
    assert audit._versions_compatible("garbage", "garbage")
    assert not audit._versions_compatible("garbage", "9.2.0")


def test_extract_next_up_version(audit: ModuleType) -> None:
    """Version is pulled from ``Next up: vX.Y — Title`` headings."""
    assert audit._extract_next_up_version(
        "Next up: v7.2 — Gold Standard Content Uplift *(in progress)*"
    ) == "7.2"
    assert audit._extract_next_up_version(
        "Next up: v10.0.5 — A Minor Patch"
    ) == "10.0.5"
    assert audit._extract_next_up_version("No version here") is None


def test_extract_release_entries_parses_status_line(audit: ModuleType) -> None:
    """``**vX.Y — Name** *(shipped DATE)*`` is captured into a record."""
    body = [
        "",
        "**v7.1 — Non-Technical Everywhere** *(shipped 2026-04-20)*",
        "",
        "Theme: ...",
    ]
    entries = audit._extract_release_entries(body)
    assert len(entries) == 1
    assert entries[0].version == "7.1"
    assert entries[0].name == "Non-Technical Everywhere"
    assert entries[0].status == "shipped"
    assert entries[0].date == "2026-04-20"


def test_extract_release_entries_handles_in_progress(audit: ModuleType) -> None:
    """Status field captures ``in progress`` (no date is acceptable)."""
    body = [
        "**v8.0 — Future Release** *(in progress)*",
    ]
    entries = audit._extract_release_entries(body)
    assert len(entries) == 1
    assert entries[0].status == "in progress"
    assert entries[0].date is None


def test_extract_release_entries_picks_up_multiple(audit: ModuleType) -> None:
    """Previous-releases body collects all release headers in order."""
    body = [
        "**v7.0 — Per-UC Content Architecture** *(shipped 2026-04-19)*",
        "Theme: ...",
        "**v6.1 — Verifiable Compliance Coverage** *(shipped 2026-04-16)*",
        "**v6.0 — Verifiable Quality** *(shipped 2026-04-16)*",
    ]
    entries = audit._extract_release_entries(body)
    assert [e.version for e in entries] == ["7.0", "6.1", "6.0"]


def test_join_multiline_bullets_merges_continuations(audit: ModuleType) -> None:
    """Wrapped bullets re-join into a single logical line."""
    src = [
        "- **Industry-specific bundles** — Standalone content packs for",
        "  Finance, OT, Healthcare.",
        "- **CLI** — pip install foo.",
    ]
    out = audit._join_multiline_bullets(src)
    assert out == [
        "- **Industry-specific bundles** — Standalone content packs for Finance, OT, Healthcare.",
        "- **CLI** — pip install foo.",
    ]


def test_join_multiline_bullets_blank_line_resets(audit: ModuleType) -> None:
    """A blank line breaks the continuation chain so paragraphs stay separate."""
    src = [
        "- one",
        "  continuation of one",
        "",
        "  this should NOT join because of the blank above",
        "- two",
    ]
    out = audit._join_multiline_bullets(src)
    assert out[0] == "- one continuation of one"
    assert "" in out
    assert out[-1] == "- two"


def test_split_sections_keys_required_sections(audit: ModuleType) -> None:
    """The required-section table populates with body lines only."""
    text = (
        "# Roadmap\n"
        "## Current release\n"
        "**v1.0 — First** *(shipped 2024-01-01)*\n"
        "## Previous releases\n"
        "## Next up: v1.1 — Next thing *(in progress)*\n"
        "## v1.2+ backlog *(no fixed date)*\n"
        "## Deprecated / declined ideas\n"
        "- **No SaaS** — explained.\n"
        "## How to influence the roadmap\n"
        "Open an issue.\n"
    )
    sections = audit._split_sections(text)
    assert "current_release" in sections
    assert any(
        "First" in line for line in sections["current_release"]
    ), f"expected the release header inside current_release, got {sections['current_release']!r}"
    assert "deprecated" in sections
    assert any("No SaaS" in line for line in sections["deprecated"])


def test_split_sections_horizontal_rules_dropped(audit: ModuleType) -> None:
    """``---`` separators don't pollute the body lines."""
    text = (
        "## Current release\n"
        "before\n"
        "---\n"
        "after\n"
    )
    sections = audit._split_sections(text)
    assert "before" in sections["current_release"]
    assert "after" in sections["current_release"]
    assert "---" not in sections["current_release"]


def test_check_links_flags_missing_targets(audit: ModuleType, tmp_path: Path) -> None:
    """Repo-relative links to non-existent files report an error."""
    text = (
        "[good](CHANGELOG.md)\n"
        "[bad](docs/this-does-not-exist.md)\n"
        "[external](https://example.com/page)\n"
        "[anchor](#section)\n"
    )
    issues = audit._check_links(text)
    messages = [i.message for i in issues]
    assert any("does-not-exist" in m for m in messages)
    assert not any("CHANGELOG.md" in m for m in messages), (
        "live CHANGELOG.md exists; should not be flagged"
    )
    assert not any("example.com" in m for m in messages), (
        "external links should be skipped"
    )
    assert not any("#section" in m for m in messages), (
        "pure anchor links should be skipped"
    )


def test_deprecated_items_extracts_top_level_bullets(audit: ModuleType) -> None:
    """Top-level ``- **Title** — body`` bullets become items."""
    body = [
        "Some text.",
        "- **Hosted SaaS** — The project stays static-site-first.",
        "  continuation that should join.",
        "- **Commercial edition** — No paid tier.",
    ]
    items = audit._deprecated_items(body)
    assert len(items) == 2
    assert items[0].startswith("**Hosted SaaS**")
    assert "continuation that should join" in items[0]
    assert items[1].startswith("**Commercial edition**")


def test_backlog_subsections_groups_by_h3(audit: ModuleType) -> None:
    """The backlog body splits into ``{name, items}`` per H3."""
    body = [
        "Pre-amble text.",
        "### Content",
        "- **Industry bundles** — story.",
        "- **Cloud deep dives** — story.",
        "### Tooling",
        "- **CLI** — story.",
        "### Community & process",
        "- **Translations** — story.",
    ]
    out = audit._backlog_subsections(body)
    names = [s["name"] for s in out]
    assert names == ["Content", "Tooling", "Community & process"]
    assert len(out[0]["items"]) == 2
    assert out[2]["items"][0].startswith("**Translations**")


# ---------------------------------------------------------------------------
# 2. Top-level parser
# ---------------------------------------------------------------------------


_HAPPY_FIXTURE = """\
# Roadmap

> Source of truth: CHANGELOG.md.

## Current release

**v9.2 — Foo** *(shipped 2026-05-09)*

Theme: lorem.

---

## Previous releases

**v9.1 — Bar** *(shipped 2026-05-08)*

**v9.0 — Baz** *(shipped 2026-05-08)*

---

## Next up: v9.3 — Quux *(in progress)*

Body.

---

## v10.0+ backlog *(no fixed date)*

### Content
- **Item A** — body.
- **Item B** — body.

### Tooling
- **Item C** — body.

### Community & process
- **Item D** — body.

---

## Deprecated / declined ideas

- **No SaaS** — explained.

---

## How to influence the roadmap

Open an issue.
"""


def test_parse_roadmap_happy_path_emits_no_errors(audit: ModuleType) -> None:
    """A well-formed synthetic ROADMAP.md emits zero error issues."""
    snap, issues = audit.parse_roadmap(_HAPPY_FIXTURE)
    errors = [i for i in issues if i.severity == "error"]
    assert errors == [], f"unexpected errors: {[i.format() for i in errors]}"
    assert snap.current_release == {
        "version": "9.2",
        "name": "Foo",
        "status": "shipped",
        "date": "2026-05-09",
    }
    assert [r["version"] for r in snap.previous_releases] == ["9.1", "9.0"]
    assert snap.next_up == {
        "version": "9.3",
        "title": "Next up: v9.3 — Quux *(in progress)*",
    }
    assert [s["name"] for s in snap.backlog] == [
        "Content",
        "Tooling",
        "Community & process",
    ]
    assert snap.deprecated_ideas[0].startswith("**No SaaS**")


def test_parse_roadmap_missing_section_reports_error(audit: ModuleType) -> None:
    """Removing a required section surfaces a clear error."""
    fixture = _HAPPY_FIXTURE.replace(
        "## Deprecated / declined ideas\n\n- **No SaaS** — explained.\n\n---\n\n",
        "",
    )
    _snap, issues = audit.parse_roadmap(fixture)
    errors = [i for i in issues if i.severity == "error"]
    assert any("deprecated" in i.message for i in errors), (
        "expected a 'deprecated section missing' error; got "
        f"{[i.format() for i in errors]}"
    )


def test_parse_roadmap_empty_deprecated_reports_error(audit: ModuleType) -> None:
    """An empty ``Deprecated / declined ideas`` section is rejected.

    The historical "no SaaS" / "no commercial edition" commitments are
    a public promise that must persist across releases — losing them
    silently would be a project-direction regression.
    """
    fixture = _HAPPY_FIXTURE.replace(
        "- **No SaaS** — explained.\n",
        "",
    )
    _snap, issues = audit.parse_roadmap(fixture)
    error_msgs = [i.message for i in issues if i.severity == "error"]
    assert any(
        "deprecated" in m.lower() for m in error_msgs
    ), f"expected an empty-deprecated error; got {error_msgs}"


def test_parse_roadmap_missing_current_release_reports_error(
    audit: ModuleType,
) -> None:
    """``## Current release`` must declare a release line."""
    fixture = _HAPPY_FIXTURE.replace(
        "**v9.2 — Foo** *(shipped 2026-05-09)*",
        "Coming soon.",
    )
    _snap, issues = audit.parse_roadmap(fixture)
    error_msgs = [i.message for i in issues if i.severity == "error"]
    assert any("Current release" in m for m in error_msgs), (
        f"expected a missing-release error; got {error_msgs}"
    )


# ---------------------------------------------------------------------------
# 3. Version-triple consistency
# ---------------------------------------------------------------------------


def test_check_version_triple_passes_when_aligned(
    audit: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Aligned VERSION + CHANGELOG-top + ROADMAP current pass cleanly."""
    version = tmp_path / "VERSION"
    version.write_text("9.2.0\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [9.2.0] - 2026-05-09\n", encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", version)
    monkeypatch.setattr(audit, "CHANGELOG_MD", changelog)

    snap = audit._Snapshot(
        current_release={"version": "9.2", "name": "Foo", "status": "shipped"}
    )
    issues = audit.check_version_triple(snap, strict=True)
    assert issues == [], f"unexpected version drift: {[i.format() for i in issues]}"


def test_check_version_triple_warns_under_check_mode(
    audit: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Under ``--check`` (strict=False) a drift surfaces as a warning."""
    version = tmp_path / "VERSION"
    version.write_text("9.2.0\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [9.2.0] - 2026-05-09\n", encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", version)
    monkeypatch.setattr(audit, "CHANGELOG_MD", changelog)

    snap = audit._Snapshot(current_release={"version": "7.1", "status": "shipped"})
    issues = audit.check_version_triple(snap, strict=False)
    severities = {i.severity for i in issues}
    assert severities == {"warning"}, (
        f"expected only warnings under --check; got {severities}"
    )
    assert len(issues) == 2, "expected one warning per upstream source (VERSION + CHANGELOG)"


def test_check_version_triple_errors_under_strict(
    audit: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``--strict-version`` promotes drift to an error."""
    version = tmp_path / "VERSION"
    version.write_text("9.2.0\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [9.2.0] - 2026-05-09\n", encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", version)
    monkeypatch.setattr(audit, "CHANGELOG_MD", changelog)

    snap = audit._Snapshot(current_release={"version": "7.1", "status": "shipped"})
    issues = audit.check_version_triple(snap, strict=True)
    severities = {i.severity for i in issues}
    assert severities == {"error"}


def test_check_version_triple_handles_missing_files(
    audit: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing VERSION / CHANGELOG produce structural errors, not crashes."""
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "missing-VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "missing-CHANGELOG.md")
    snap = audit._Snapshot(current_release={"version": "9.2"})
    issues = audit.check_version_triple(snap, strict=False)
    msgs = [i.message for i in issues]
    assert any("VERSION file missing" in m for m in msgs)
    assert any("CHANGELOG.md has no" in m for m in msgs)


# ---------------------------------------------------------------------------
# 4. End-to-end main()
# ---------------------------------------------------------------------------


def test_main_check_passes_against_live_roadmap(audit: ModuleType) -> None:
    """``--check`` against the real ROADMAP.md exits 0 (warnings allowed).

    Today the live ROADMAP.md is structurally clean and link-clean
    but the version triple drifts from VERSION (v7.1 vs 9.2.0); this
    test pins that the soft-fail mode lets the gate land without a
    same-PR roadmap rewrite.
    """
    rc = audit.main(["--check"])
    assert rc == 0, "live ROADMAP.md must pass --check (structural + link)"


def test_main_export_writes_snapshot_with_stable_keys(
    audit: ModuleType, tmp_path: Path
) -> None:
    """``--export`` writes a JSON snapshot with the contract-pinned keys."""
    target = tmp_path / "roadmap.json"
    rc = audit.main(["--export", str(target)])
    # Soft warnings are OK; export-only path doesn't fail on drift.
    assert rc == 0
    assert target.is_file()
    payload = json.loads(target.read_text(encoding="utf-8"))
    expected_keys = {
        "schema_version",
        "captured_at",
        "git_head",
        "current_release",
        "previous_releases",
        "next_up",
        "backlog",
        "deprecated_ideas",
    }
    assert set(payload.keys()) == expected_keys, (
        f"export schema drifted; got keys={set(payload.keys())}, "
        f"expected={expected_keys}"
    )
    assert payload["schema_version"] == "1.0", (
        "schema_version is the input contract for downstream Project sync; "
        "bumps require a coordinated update on the consumer side"
    )


def test_main_strict_version_fails_on_drift(audit: ModuleType) -> None:
    """``--strict-version`` flips the live drift to a hard failure.

    Sanity-check that strict mode is wired correctly: today's
    ROADMAP.md ships v7.1 against a VERSION of 9.2.0, so strict mode
    must exit 1.
    """
    rc = audit.main(["--strict-version"])
    assert rc == 1, (
        "expected --strict-version to fail today; if this passes, the "
        "ROADMAP refresh shipped — promote validate.yml to use --strict-version"
    )


# ---------------------------------------------------------------------------
# 5. Live link-resolution smoke
# ---------------------------------------------------------------------------


def test_live_roadmap_links_all_resolve(audit: ModuleType) -> None:
    """Every repo-relative link in the live ROADMAP.md resolves on disk.

    Independent of ``main()``: this test calls the link checker
    directly so the failure message points at the broken href, not at
    the synthesised ``error_count``.
    """
    text = LIVE_ROADMAP.read_text(encoding="utf-8")
    issues = audit._check_links(text)
    bad = [i for i in issues if i.severity == "error"]
    assert not bad, (
        "live ROADMAP.md has broken repo-relative links: "
        + "; ".join(i.message for i in bad)
    )
