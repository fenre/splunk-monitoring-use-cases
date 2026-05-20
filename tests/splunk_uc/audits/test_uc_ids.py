"""Unit tests for ``splunk_uc.audits.uc_ids``.

P16 wave FF: lifts ``src/splunk_uc/audits/uc_ids.py`` from ~10% to
100% combined coverage. Pins every documented contract of the UC-ID
audit:

(a) ``extract_dir_category`` recognises only zero-or-more-digit
    ``cat-NN-`` directories.
(b) ``audit_category`` walks each ``content/cat-NN-*/UC-*.json``
    sidecar, validates id grammar / filename matching / category
    correctness, and reports duplicates / gaps / wrong-Z within
    subcategories.
(c) ``main`` adds the cross-category global UC-ID uniqueness check
    and honours ``--warn-gaps`` (gaps-only → exit 0).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import uc_ids


class MakeCatDir(Protocol):
    def __call__(self, category: int, slug: str = "test-cat") -> pathlib.Path: ...


class MakeUC(Protocol):
    def __call__(
        self,
        cat_dir: pathlib.Path,
        uc_id: str,
        payload: dict[str, Any] | None = None,
    ) -> pathlib.Path: ...


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with an empty ``content/`` directory."""
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(uc_ids, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(uc_ids, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def make_cat_dir(fake_repo: pathlib.Path) -> MakeCatDir:
    def _make(category: int, slug: str = "test-cat") -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-{slug}"
        cat_dir.mkdir(parents=True, exist_ok=True)
        return cat_dir

    return _make


@pytest.fixture
def make_uc() -> MakeUC:
    def _make(
        cat_dir: pathlib.Path, uc_id: str, payload: dict[str, Any] | None = None
    ) -> pathlib.Path:
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **(payload or {})}
        sidecar.write_text(json.dumps(merged), encoding="utf-8")
        return sidecar

    return _make


# ----------------------------------------------------------------------
# Module constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    def test_repo_root_resolves(self) -> None:
        from splunk_uc.audits import uc_ids as fresh

        assert (fresh.REPO_ROOT / "schemas").is_dir()

    def test_filename_cat_matches_simple(self) -> None:
        m = uc_ids.FILENAME_CAT.search("cat-01-foo")
        assert m is not None
        assert m.group(1) == "01"

    def test_filename_cat_matches_multi_digit(self) -> None:
        m = uc_ids.FILENAME_CAT.search("cat-100-zeta")
        assert m is not None
        assert m.group(1) == "100"

    def test_filename_cat_requires_trailing_dash(self) -> None:
        assert uc_ids.FILENAME_CAT.search("cat-99") is None

    def test_filename_cat_rejects_non_digits(self) -> None:
        assert uc_ids.FILENAME_CAT.search("cat-foo-bar") is None

    def test_id_pattern_matches_basic(self) -> None:
        m = uc_ids.ID_PATTERN.match("1.2.3")
        assert m is not None
        assert m.groups() == ("1", "2", "3")

    def test_id_pattern_matches_multi_digit(self) -> None:
        m = uc_ids.ID_PATTERN.match("10.20.30")
        assert m is not None

    def test_id_pattern_rejects_two_segments(self) -> None:
        assert uc_ids.ID_PATTERN.match("1.2") is None

    def test_id_pattern_rejects_four_segments(self) -> None:
        assert uc_ids.ID_PATTERN.match("1.2.3.4") is None

    def test_id_pattern_rejects_non_numeric(self) -> None:
        assert uc_ids.ID_PATTERN.match("a.b.c") is None


# ----------------------------------------------------------------------
# extract_dir_category
# ----------------------------------------------------------------------


class TestExtractDirCategory:
    def test_zero_padded(self) -> None:
        assert uc_ids.extract_dir_category("cat-01-server-compute") == 1

    def test_unpadded(self) -> None:
        # The regex doesn't require zero-padding.
        assert uc_ids.extract_dir_category("cat-9-foo") == 9

    def test_multi_digit(self) -> None:
        assert uc_ids.extract_dir_category("cat-100-foo") == 100

    def test_no_match_returns_none(self) -> None:
        assert uc_ids.extract_dir_category("notacat") is None

    def test_missing_trailing_dash_returns_none(self) -> None:
        assert uc_ids.extract_dir_category("cat-99") is None

    def test_non_numeric_segment_returns_none(self) -> None:
        assert uc_ids.extract_dir_category("cat-foo-bar") is None


# ----------------------------------------------------------------------
# audit_category
# ----------------------------------------------------------------------


class TestAuditCategoryEarlyReturn:
    def test_non_cat_dir_returns_empty(self, fake_repo: pathlib.Path) -> None:
        bogus = fake_repo / "content" / "notacat"
        bogus.mkdir()
        assert uc_ids.audit_category(bogus) == []

    def test_empty_cat_dir_returns_empty(self, make_cat_dir: MakeCatDir) -> None:
        cat = make_cat_dir(1)
        assert uc_ids.audit_category(cat) == []


class TestAuditCategoryHappyPath:
    def test_single_valid_uc(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        assert uc_ids.audit_category(cat) == []

    def test_multiple_consecutive_ucs(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)
        for z in (1, 2, 3):
            make_uc(cat, f"1.1.{z}")
        assert uc_ids.audit_category(cat) == []

    def test_multiple_subcategories(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)
        for y in (1, 2):
            for z in (1, 2):
                make_uc(cat, f"1.{y}.{z}")
        assert uc_ids.audit_category(cat) == []


class TestAuditCategoryJsonParse:
    def test_invalid_json_flagged(self, make_cat_dir: MakeCatDir) -> None:
        cat = make_cat_dir(1)
        bad = cat / "UC-1.1.1.json"
        bad.write_text("{not json,,,}", encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("failed to parse" in i for i in issues)


class TestAuditCategoryIdValidation:
    def test_missing_id_field(self, make_cat_dir: MakeCatDir) -> None:
        cat = make_cat_dir(1)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(json.dumps({"title": "no id"}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("missing or empty `id` field" in i for i in issues)

    def test_empty_id_field(self, make_cat_dir: MakeCatDir) -> None:
        cat = make_cat_dir(1)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(json.dumps({"id": ""}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("missing or empty" in i for i in issues)

    def test_whitespace_only_id_field(self, make_cat_dir: MakeCatDir) -> None:
        """``str(payload.get('id', '')).strip()`` is empty → missing."""
        cat = make_cat_dir(1)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(json.dumps({"id": "   "}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("missing or empty" in i for i in issues)

    def test_invalid_grammar_flagged(self, make_cat_dir: MakeCatDir) -> None:
        cat = make_cat_dir(1)
        sidecar = cat / "UC-bogus.json"
        sidecar.write_text(json.dumps({"id": "bogus"}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("does not match X.Y.Z grammar" in i for i in issues)

    def test_partial_id_flagged(self, make_cat_dir: MakeCatDir) -> None:
        cat = make_cat_dir(1)
        sidecar = cat / "UC-1.1.json"
        sidecar.write_text(json.dumps({"id": "1.1"}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("does not match X.Y.Z grammar" in i for i in issues)


class TestAuditCategoryFilenameMatch:
    def test_filename_mismatch_flagged(self, make_cat_dir: MakeCatDir) -> None:
        """File is UC-1.1.1.json but id says 1.1.2 — flagged."""
        cat = make_cat_dir(1)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(json.dumps({"id": "1.1.2"}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("filename does not match id" in i for i in issues)


class TestAuditCategoryDuplicates:
    def test_duplicate_uc_id_in_folder(self, make_cat_dir: MakeCatDir) -> None:
        """Two sidecars with the same payload id — flagged."""
        cat = make_cat_dir(1)
        a = cat / "UC-1.1.1.json"
        a.write_text(json.dumps({"id": "1.1.1"}), encoding="utf-8")
        # The second file has a different filename but the same id;
        # it'll be flagged for filename mismatch AND for duplication.
        b = cat / "UC-1.1.99.json"
        b.write_text(json.dumps({"id": "1.1.1"}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("Duplicate UC ID inside" in i and "1.1.1" in i for i in issues)


class TestAuditCategoryWrongCategory:
    def test_wrong_category_flagged(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)  # folder for cat 1
        # File named correctly to match its id (no filename-mismatch
        # issue), but the X segment is 9 — wrong-cat-for-folder.
        make_uc(cat, "9.1.1")
        issues = uc_ids.audit_category(cat)
        assert any("Wrong category" in i and "X=9" in i for i in issues)


class TestAuditCategoryGaps:
    def test_simple_gap(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.3")
        issues = uc_ids.audit_category(cat)
        assert any("Gap in Z for UC-1.1.*" in i and "missing [2]" in i for i in issues)

    def test_multi_element_gap(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.5")
        issues = uc_ids.audit_category(cat)
        assert any("missing [2, 3, 4]" in i for i in issues)

    def test_no_gap_in_consecutive(self, make_cat_dir: MakeCatDir, make_uc: MakeUC) -> None:
        cat = make_cat_dir(1)
        for z in (1, 2, 3):
            make_uc(cat, f"1.1.{z}")
        issues = uc_ids.audit_category(cat)
        assert not any("Gap in Z" in i for i in issues)


class TestAuditCategoryDuplicateZ:
    def test_duplicate_z_flagged(self, make_cat_dir: MakeCatDir) -> None:
        """Two files claiming the same Z within a subcat — flagged
        (alongside the duplicate-id check)."""
        cat = make_cat_dir(1)
        a = cat / "UC-1.1.1.json"
        a.write_text(json.dumps({"id": "1.1.1"}), encoding="utf-8")
        b = cat / "UC-1.1.99.json"
        b.write_text(json.dumps({"id": "1.1.1"}), encoding="utf-8")
        issues = uc_ids.audit_category(cat)
        assert any("Duplicate Z in subcategory UC-1.1.*" in i and "Z=1" in i for i in issues)


# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------


class TestMainCleanRuns:
    def test_empty_content_returns_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = uc_ids.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "No issues found." in out

    def test_single_clean_category_returns_zero(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        rc = uc_ids.main([])
        assert rc == 0
        assert "No issues" in capsys.readouterr().out

    def test_argv_none_uses_sys_argv(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        monkeypatch.setattr("sys.argv", ["uc_ids"])
        rc = uc_ids.main(None)
        assert rc == 0


class TestMainCrossCategoryUniqueness:
    def test_global_duplicate_flagged(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_a = make_cat_dir(1, "first")
        cat_b = make_cat_dir(2, "second")
        # Both carry id "1.1.1" — second one is wrong-cat-for-folder
        # AND collides cross-category with the first.
        make_uc(cat_a, "1.1.1")
        make_uc(cat_b, "1.1.1")
        rc = uc_ids.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "__cross_category__" in out
        assert "appears in multiple sidecars" in out

    def test_unparseable_sidecar_skipped_in_cross_walk(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """JSON parse errors in the cross-category walk must NOT crash;
        per-category audit still reports them."""
        cat = make_cat_dir(1)
        bad = cat / "UC-1.1.1.json"
        bad.write_text("{not json,,,}", encoding="utf-8")
        rc = uc_ids.main([])
        out = capsys.readouterr().out
        assert rc == 1
        # Per-category audit catches the parse failure.
        assert "failed to parse" in out

    def test_empty_id_skipped_in_cross_walk(
        self,
        make_cat_dir: MakeCatDir,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Empty UC ids must NOT be inserted into the global id map
        (would otherwise cluster every empty-id sidecar together)."""
        cat = make_cat_dir(1)
        a = cat / "UC-1.1.1.json"
        a.write_text(json.dumps({"id": ""}), encoding="utf-8")
        b = cat / "UC-1.1.2.json"
        b.write_text(json.dumps({"id": ""}), encoding="utf-8")
        rc = uc_ids.main([])
        out = capsys.readouterr().out
        assert rc == 1
        # No spurious cross-category collision on the empty id.
        assert "__cross_category__" not in out


class TestMainPrintFormatting:
    def test_per_category_header_printed(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.3")  # forces a gap
        uc_ids.main([])
        out = capsys.readouterr().out
        assert "## content/cat-01-test-cat" in out
        assert "Total categories with issues:" in out
        assert "Total issue lines:" in out

    def test_issue_lines_bulleted(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.3")
        uc_ids.main([])
        out = capsys.readouterr().out
        assert "  - Gap in Z" in out


class TestMainWarnGaps:
    def test_warn_gaps_off_returns_one_on_gap(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.3")
        rc = uc_ids.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "Gap in Z" in out
        # No warn-gaps footer when the flag isn't set.
        assert "treated as warnings" not in out

    def test_warn_gaps_on_returns_zero_when_gap_only(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.3")
        rc = uc_ids.main(["--warn-gaps"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "gaps treated as warnings" in out

    def test_warn_gaps_on_returns_one_on_mixed_issues(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``--warn-gaps`` does NOT suppress non-gap issues."""
        cat = make_cat_dir(1)
        make_uc(cat, "1.1.1")
        make_uc(cat, "1.1.3")  # gap
        make_uc(cat, "9.1.1")  # wrong category — non-gap
        rc = uc_ids.main(["--warn-gaps"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "Wrong category" in out

    def test_warn_gaps_on_returns_one_when_cross_dup_only(
        self,
        make_cat_dir: MakeCatDir,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Cross-category duplicates are NOT gap-only — flag does not
        suppress them. Pins that ``__cross_category__`` issues count
        toward the gap_only computation."""
        cat_a = make_cat_dir(1, "first")
        cat_b = make_cat_dir(2, "second")
        make_uc(cat_a, "1.1.1")
        make_uc(cat_b, "1.1.1")
        rc = uc_ids.main(["--warn-gaps"])
        assert rc == 1


class TestMainHelp:
    def test_help_exits_with_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            uc_ids.main(["--help"])
        out = capsys.readouterr().out
        assert excinfo.value.code == 0
        assert "--warn-gaps" in out
