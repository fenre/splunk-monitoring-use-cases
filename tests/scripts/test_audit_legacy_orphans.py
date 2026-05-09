"""Tests for ``scripts/audit_legacy_orphans.py``.

The auditor is the burndown-phase gate for retiring the legacy
``use-cases/`` markdown tree (P1 step 7). It compares UC IDs in
legacy markdown against UC IDs in JSON SSOT and reports orphans
(legacy-only UCs that would be lost by deletion).

These tests run hermetically in tmp_path — no test reads or
writes the real ``use-cases/`` or ``content/`` trees.

Coverage:

* ``collect_legacy_ids`` and ``collect_ssot_ids`` correctly
  inventory their respective trees.
* ``collect_orphan_titles`` parses the markdown headings.
* ``--report`` always exits 0.
* ``--check`` exits 1 when orphans exist, 0 when none do.
* ``--baseline N`` exits 0 if ``count <= N``, 1 if greater.
* The committed inventory snapshot in
  ``docs/use-cases-burndown.md`` matches the auditor's count
  (the ``EXPECTED_ORPHAN_COUNT_AT_BASELINE`` constant is the
  source of truth and the doc echoes it).

The committed live-state assertion (``20 orphans, all in cat-5``)
runs against the real repository so a future PR that migrates an
orphan to JSON SSOT correctly fails this test until the test +
doc + ``EXPECTED_ORPHAN_COUNT_AT_BASELINE`` constant are updated
together.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# P6 (scripts taxonomy, 2026-05-09): the audit body now lives at
# src/splunk_uc/audits/legacy_orphans.py with a thin shim at the
# original scripts/ path. Tests that monkeypatch module-level
# constants (LEGACY_ROOT, SSOT_ROOT) MUST reach the implementation
# module so the patches propagate into the function closures —
# patching the shim only mutates its local re-export. The
# legacy spec-loader path is preserved as a deliberate fallback.
try:
    import splunk_uc.audits.legacy_orphans as audit
except ImportError:
    _spec = importlib.util.spec_from_file_location(
        "audit_legacy_orphans",
        REPO_ROOT / "scripts" / "audit_legacy_orphans.py",
    )
    assert _spec is not None and _spec.loader is not None
    audit = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(audit)


# ---------------------------------------------------------------------------
# Inventory functions (live repo)
# ---------------------------------------------------------------------------


def test_collect_legacy_ids_finds_real_inventory() -> None:
    """The auditor must agree with the doc-locked inventory.

    Lower bound only — adding more orphan IDs to the legacy
    markdown is in-scope until Phase B; this test catches an
    accidental *deletion* of legacy markdown that would silently
    shrink the inventory.
    """
    legacy = audit.collect_legacy_ids()
    assert len(legacy) >= 6_500, (
        f"legacy inventory shrank to {len(legacy)} UCs; expected at least 6,500. "
        "Did someone delete a use-cases/cat-*.md file?"
    )


def test_collect_ssot_ids_finds_real_inventory() -> None:
    """Same lower-bound check for the JSON SSOT — catches mass-deletion."""
    ssot = audit.collect_ssot_ids()
    assert len(ssot) >= 7_500, (
        f"SSOT inventory shrank to {len(ssot)} UCs; expected at least 7,500. "
        "Did someone delete content/cat-*/UC-*.json files?"
    )


def test_orphans_match_committed_baseline() -> None:
    """The 20 orphans documented in docs/use-cases-burndown.md must
    still be the live answer.

    A new orphan is ALLOWED but signals the doc + baseline are stale —
    a single failing test is enough to catch the drift. A *removed*
    orphan signals successful migration (also requires updating the
    doc + the EXPECTED_ORPHAN_COUNT_AT_BASELINE constant).
    """
    legacy = audit.collect_legacy_ids()
    ssot = audit.collect_ssot_ids()
    orphans = legacy - ssot
    assert len(orphans) == audit.EXPECTED_ORPHAN_COUNT_AT_BASELINE, (
        f"orphan count drifted: live={len(orphans)}, "
        f"locked={audit.EXPECTED_ORPHAN_COUNT_AT_BASELINE}. "
        "If you migrated orphans, decrement EXPECTED_ORPHAN_COUNT_AT_BASELINE "
        "in scripts/audit_legacy_orphans.py and update the inventory table in "
        "docs/use-cases-burndown.md."
    )


def test_all_orphans_live_in_cat_5() -> None:
    """Pin the cat-5-only invariant from the burndown plan.

    If a new orphan appears in another category, the burndown plan needs
    a new subcategory section and a fresh per-PR migration plan.
    """
    legacy = audit.collect_legacy_ids()
    ssot = audit.collect_ssot_ids()
    orphans = legacy - ssot
    non_cat5 = [uc for uc in orphans if not uc.startswith("5.")]
    assert not non_cat5, (
        f"orphans found outside cat-5: {sorted(non_cat5)}. "
        "Update docs/use-cases-burndown.md with a new subcategory section "
        "before migrating these."
    )


# ---------------------------------------------------------------------------
# Hermetic tests for the CLI modes (tmp_path-driven)
# ---------------------------------------------------------------------------


def _make_legacy_dir(root: Path, uc_lines: list[str]) -> None:
    legacy = root / "use-cases"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "cat-99-fake.md").write_text(
        "\n".join(uc_lines) + "\n", encoding="utf-8"
    )


def _make_ssot_dir(root: Path, uc_ids: list[str]) -> None:
    ssot = root / "content"
    cat_dir = ssot / "cat-99-fake"
    cat_dir.mkdir(parents=True, exist_ok=True)
    for uc in uc_ids:
        (cat_dir / f"UC-{uc}.json").write_text("{}", encoding="utf-8")


def test_check_mode_passes_when_no_orphans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(audit, "LEGACY_ROOT", tmp_path / "use-cases")
    monkeypatch.setattr(audit, "SSOT_ROOT", tmp_path / "content")
    _make_legacy_dir(tmp_path, ["### UC-99.1.1 — Foo"])
    _make_ssot_dir(tmp_path, ["99.1.1"])

    rc = audit.main(["--check"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "zero orphans" in out


def test_check_mode_fails_when_orphans_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(audit, "LEGACY_ROOT", tmp_path / "use-cases")
    monkeypatch.setattr(audit, "SSOT_ROOT", tmp_path / "content")
    _make_legacy_dir(
        tmp_path,
        ["### UC-99.1.1 — Has SSOT", "### UC-99.1.2 — Orphan!"],
    )
    _make_ssot_dir(tmp_path, ["99.1.1"])

    rc = audit.main(["--check"])
    assert rc == 1


def test_baseline_mode_passes_at_or_below_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(audit, "LEGACY_ROOT", tmp_path / "use-cases")
    monkeypatch.setattr(audit, "SSOT_ROOT", tmp_path / "content")
    _make_legacy_dir(
        tmp_path,
        [f"### UC-99.1.{i} — Foo" for i in range(1, 4)],  # 3 orphans
    )
    _make_ssot_dir(tmp_path, [])

    assert audit.main(["--baseline", "5"]) == 0  # 3 ≤ 5
    assert audit.main(["--baseline", "3"]) == 0  # 3 ≤ 3
    assert audit.main(["--baseline", "2"]) == 1  # 3 > 2


def test_report_mode_always_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(audit, "LEGACY_ROOT", tmp_path / "use-cases")
    monkeypatch.setattr(audit, "SSOT_ROOT", tmp_path / "content")
    _make_legacy_dir(tmp_path, ["### UC-99.1.1 — Orphan"])
    _make_ssot_dir(tmp_path, [])

    assert audit.main(["--report"]) == 0
    assert audit.main([]) == 0  # default mode = report


def test_collect_orphan_titles_parses_supported_separators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The auditor supports the three separators that appear in the real
    ``use-cases/cat-*.md`` files: middle-dot (·), bullet (•), and hyphen (-).

    Em-dash (—, U+2014) is intentionally NOT supported because the
    legacy authoring style guide standardised on middle-dot — adding
    em-dash support here would invite drift in newly-authored markdown.
    """
    monkeypatch.setattr(audit, "LEGACY_ROOT", tmp_path / "use-cases")
    _make_legacy_dir(
        tmp_path,
        [
            "### UC-99.1.1 · Middle-dot separator",
            "### UC-99.1.2 • Bullet separator",
            "### UC-99.1.3 - Hyphen separator",
        ],
    )
    titles = audit.collect_orphan_titles()
    assert titles["99.1.1"] == "Middle-dot separator"
    assert titles["99.1.2"] == "Bullet separator"
    assert titles["99.1.3"] == "Hyphen separator"


def test_collect_legacy_ids_handles_missing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase C end-state: ``use-cases/`` is gone. Auditor must not crash."""
    monkeypatch.setattr(audit, "LEGACY_ROOT", tmp_path / "no_such_dir")
    monkeypatch.setattr(audit, "SSOT_ROOT", tmp_path / "no_other_dir")
    legacy = audit.collect_legacy_ids()
    ssot = audit.collect_ssot_ids()
    assert legacy == set()
    assert ssot == set()


# ---------------------------------------------------------------------------
# Doc <-> code sync
# ---------------------------------------------------------------------------


def test_burndown_doc_states_orphan_count() -> None:
    """The committed inventory in docs/use-cases-burndown.md must reference
    the same orphan count as the audit constant. Drift here means the doc
    is lying to readers.

    Looser match than ``**N UCs**`` because the doc lays out the count in
    several places (TL;DR, table, prose); we just want any of them to use
    the same number the auditor's constant claims.
    """
    doc_path = REPO_ROOT / "docs" / "use-cases-burndown.md"
    assert doc_path.is_file(), f"burndown doc missing at {doc_path}"
    text = doc_path.read_text(encoding="utf-8")
    n = audit.EXPECTED_ORPHAN_COUNT_AT_BASELINE
    # At least one of "N UCs", "N orphans", or "N legacy-only" must appear.
    candidates = [f"{n} UCs", f"{n} orphans", f"{n} legacy-only"]
    assert any(c in text for c in candidates), (
        f"burndown doc should mention the locked baseline N={n} in one of "
        f"{candidates!r}; either update the doc or the constant."
    )


def test_burndown_doc_has_all_three_phases() -> None:
    """The doc must enumerate Phase A, Phase B, and Phase C — anyone reading
    it should immediately see the three-phase sequence."""
    doc = (REPO_ROOT / "docs" / "use-cases-burndown.md").read_text(encoding="utf-8")
    assert "Phase A —" in doc
    assert "Phase B —" in doc
    assert "Phase C —" in doc


def test_burndown_doc_cross_links_dependencies() -> None:
    """The doc must reference the operational pair (rollback playbook,
    external-consumer-matrix) so a reader can follow the safety story."""
    doc = (REPO_ROOT / "docs" / "use-cases-burndown.md").read_text(encoding="utf-8")
    assert "external-consumer-matrix.md" in doc
    assert "rollback-playbook.md" in doc
    assert "uc.schema.json" in doc
