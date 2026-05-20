"""Unit tests for ``splunk_uc.audits.peer_review_signoffs``.

P16 wave EE: lifts ``src/splunk_uc/audits/peer_review_signoffs.py``
from ~12% to 100% combined coverage. Pins every documented contract
of the Phase 4.5a peer-review gate audit:

(a) ``data/provenance/peer-review-signoffs.json`` validates against
    the JSON Schema 2020-12 schema in ``schemas/`` (schema invariant).
(b) Every semantic invariant fires under tailored fixtures
    (author != reviewer, secondReviewer != either, notes required on
    failed checks or on derivatives=n/a, commit SHA uniqueness, and
    baseline commit SHA validity).
"""

from __future__ import annotations

import json
import pathlib
import shutil
from collections.abc import Callable
from typing import Any

import pytest

from splunk_uc.audits import peer_review_signoffs as prs

MakeSignoffFile = Callable[[dict[str, Any]], pathlib.Path]


_VALID_BASELINE = "c6463a1d461b6b5813b9c58d4492818ee6805dd8"
_VALID_COMMIT_A = "abcdef1234567890abcdef1234567890abcdef12"
_VALID_COMMIT_B = "1234567890abcdef1234567890abcdef12345678"


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with schemas/ + data/provenance/ skeleton."""
    (tmp_path / "schemas").mkdir()
    (tmp_path / "data" / "provenance").mkdir(parents=True)

    # Copy the real schema so jsonschema validation matches CI.
    real_schema = (
        pathlib.Path(__file__).resolve().parents[3] / "schemas" / "peer-review-signoff.schema.json"
    )
    shutil.copy(real_schema, tmp_path / "schemas" / "peer-review-signoff.schema.json")

    monkeypatch.setattr(prs, "REPO", tmp_path)
    monkeypatch.setattr(
        prs, "SCHEMA_PATH", tmp_path / "schemas" / "peer-review-signoff.schema.json"
    )
    monkeypatch.setattr(
        prs, "DATA_PATH", tmp_path / "data" / "provenance" / "peer-review-signoffs.json"
    )
    return tmp_path


@pytest.fixture
def make_signoff_file(fake_repo: pathlib.Path) -> MakeSignoffFile:
    def _make(data: dict[str, Any]) -> pathlib.Path:
        path: pathlib.Path = prs.DATA_PATH
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    return _make


def _checks_all_pass() -> dict[str, str]:
    """Build a schema-valid `checks` payload where every check passes."""
    return {
        "clausePrecision": "pass",
        "assuranceHonesty": "pass",
        "mitreOscalCrossRefs": "pass",
        "provenance": "pass",
        "derivatives": "pass",
        "buildHygiene": "pass",
    }


def _basic_signoff(**overrides: Any) -> dict[str, Any]:
    """Build a schema-valid signoff record."""
    base: dict[str, Any] = {
        "pr": "#1234",
        "date": "2026-04-18",
        "commit": _VALID_COMMIT_A,
        "author": "alice",
        "reviewer": "bob",
        "scope": ["1.1.1"],
        "checks": _checks_all_pass(),
    }
    base.update(overrides)
    return base


def _signoff_file(**overrides: Any) -> dict[str, Any]:
    """Build a schema-valid top-level signoff payload."""
    base: dict[str, Any] = {
        "generated_at": "2026-04-18T12:00:00Z",
        "baseline_commit": _VALID_BASELINE,
        "signoffs": [],
    }
    base.update(overrides)
    return base


# ----------------------------------------------------------------------
# Module constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    """Pins the immutable surface of the module."""

    def test_repo_resolves_to_real_repo(self) -> None:
        """``REPO`` resolves to a directory containing ``schemas/``."""
        # The fixture monkey-patches REPO; this test deliberately
        # consults the import-time value (a real repo path) instead.
        from splunk_uc.audits import peer_review_signoffs as fresh

        assert (fresh.REPO / "schemas").is_dir()

    def test_sha_re_accepts_short_lowercase(self) -> None:
        assert prs._SHA_RE.match("abc1234") is not None

    def test_sha_re_accepts_full_lowercase(self) -> None:
        assert prs._SHA_RE.match("a" * 40) is not None

    def test_sha_re_rejects_too_short(self) -> None:
        assert prs._SHA_RE.match("abc123") is None

    def test_sha_re_rejects_too_long(self) -> None:
        assert prs._SHA_RE.match("a" * 41) is None

    def test_sha_re_rejects_uppercase(self) -> None:
        assert prs._SHA_RE.match("ABCDEF1234567") is None

    def test_sha_re_rejects_non_hex(self) -> None:
        assert prs._SHA_RE.match("ghijklm") is None


# ----------------------------------------------------------------------
# _load_json
# ----------------------------------------------------------------------


class TestLoadJson:
    """Exit-on-failure I/O helper."""

    def test_missing_file_exits_with_one(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing = fake_repo / "does-not-exist.json"
        with pytest.raises(SystemExit) as excinfo:
            prs._load_json(missing, "test file")
        err = capsys.readouterr().err
        assert excinfo.value.code == 1
        assert "test file not found" in err

    def test_invalid_json_exits_with_one(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bad = fake_repo / "bad.json"
        bad.write_text("{not json,,,}", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            prs._load_json(bad, "test file")
        err = capsys.readouterr().err
        assert excinfo.value.code == 1
        assert "test file is not valid JSON" in err

    def test_happy_path_returns_payload(self, fake_repo: pathlib.Path) -> None:
        good = fake_repo / "good.json"
        good.write_text('{"hello": "world"}', encoding="utf-8")
        result = prs._load_json(good, "test file")
        assert result == {"hello": "world"}


# ----------------------------------------------------------------------
# _normalise_handle
# ----------------------------------------------------------------------


class TestNormaliseHandle:
    """Case-insensitive handle comparison with optional @ stripping."""

    def test_strips_leading_at(self) -> None:
        assert prs._normalise_handle("@Alice") == "alice"

    def test_lowercases(self) -> None:
        assert prs._normalise_handle("BOB") == "bob"

    def test_strips_whitespace(self) -> None:
        assert prs._normalise_handle("  alice  ") == "alice"

    def test_no_leading_at(self) -> None:
        assert prs._normalise_handle("alice") == "alice"

    def test_combined(self) -> None:
        """The function applies ``lstrip("@")`` BEFORE ``strip()``, so a
        leading-whitespace ``@``-prefix is preserved in the trim.
        Pins the (slightly surprising) production order."""
        assert prs._normalise_handle("  @Alice  ") == "@alice"

    def test_at_only_after_strip(self) -> None:
        """``strip()`` removes whitespace; ``lower()`` lowercases."""
        assert prs._normalise_handle("@Alice  ") == "alice"

    def test_empty_string(self) -> None:
        assert prs._normalise_handle("") == ""


# ----------------------------------------------------------------------
# _validate_schema
# ----------------------------------------------------------------------


class TestValidateSchema:
    """JSON Schema validation against the live schema file."""

    def test_clean_data_returns_no_issues(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file()
        assert prs._validate_schema(data) == []

    def test_missing_top_required_field_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file()
        del data["signoffs"]
        issues = prs._validate_schema(data)
        assert issues
        assert any("<root>" in i for i in issues)

    def test_invalid_baseline_pattern_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(baseline_commit="NOT-HEX")
        issues = prs._validate_schema(data)
        assert any("baseline_commit" in i for i in issues)

    def test_unknown_top_level_field_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(stray_field="oops")
        issues = prs._validate_schema(data)
        assert any("schema:" in i for i in issues)

    def test_signoff_missing_required_field_flagged(self, fake_repo: pathlib.Path) -> None:
        partial = _basic_signoff()
        del partial["reviewer"]
        data = _signoff_file(signoffs=[partial])
        issues = prs._validate_schema(data)
        assert issues
        # Path should include the index into signoffs.
        assert any("signoffs/0" in i for i in issues)


# ----------------------------------------------------------------------
# _validate_semantics
# ----------------------------------------------------------------------


class TestValidateSemanticsAuthorReviewer:
    """Self-review prohibition (author != reviewer)."""

    def test_distinct_handles_pass(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer="bob")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("must differ" in i for i in issues)

    def test_self_review_flagged(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer="alice")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("author and reviewer must differ" in i and "Self-review" in i for i in issues)

    def test_at_prefix_treated_same_handle(self, fake_repo: pathlib.Path) -> None:
        """``@Alice`` and ``alice`` collapse to the same handle."""
        record = _basic_signoff(author="@Alice", reviewer="alice")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("author and reviewer must differ" in i for i in issues)

    def test_case_insensitive_collision(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="ALICE", reviewer="alice")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("author and reviewer must differ" in i for i in issues)

    def test_non_string_author_skips_check(self, fake_repo: pathlib.Path) -> None:
        """Schema stage handles type errors; semantic stage skips."""
        record = _basic_signoff(author=42, reviewer="bob")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("author and reviewer must differ" in i for i in issues)

    def test_non_string_reviewer_skips_check(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer=42)
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("author and reviewer must differ" in i for i in issues)


class TestValidateSemanticsSecondReviewer:
    """``secondReviewer`` must differ from both author and reviewer."""

    def test_distinct_second_reviewer_passes(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer="bob", secondReviewer="carol")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("secondReviewer must differ" in i for i in issues)

    def test_second_reviewer_equals_author_flagged(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer="bob", secondReviewer="@Alice")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("secondReviewer must differ from author" in i for i in issues)

    def test_second_reviewer_equals_reviewer_flagged(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer="bob", secondReviewer="bob")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("secondReviewer must differ from primary reviewer" in i for i in issues)

    def test_second_reviewer_empty_string_skips(self, fake_repo: pathlib.Path) -> None:
        """Empty ``secondReviewer`` is treated as absent."""
        record = _basic_signoff(author="alice", reviewer="bob", secondReviewer="")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("secondReviewer must differ" in i for i in issues)

    def test_second_reviewer_non_string_skips(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(author="alice", reviewer="bob", secondReviewer=42)
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("secondReviewer must differ" in i for i in issues)

    def test_second_reviewer_equals_non_string_author_skips(self, fake_repo: pathlib.Path) -> None:
        """When author is non-string, the secondReviewer-vs-author check
        skips even if a secondReviewer is supplied — branch covers the
        ``isinstance(author, str)`` guard in the secondReviewer block."""
        record = _basic_signoff(author=42, reviewer="bob", secondReviewer="carol")
        # Author isn't a string, so the author-vs-secondReviewer arm
        # of the secondReviewer block cannot fire — but the
        # reviewer arm CAN.
        record["secondReviewer"] = "bob"
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("secondReviewer must differ from primary reviewer" in i for i in issues)

    def test_second_reviewer_equals_non_string_reviewer_skips(
        self, fake_repo: pathlib.Path
    ) -> None:
        """When reviewer is non-string, the secondReviewer-vs-reviewer
        arm skips — branch covers the ``isinstance(reviewer, str)``
        guard."""
        record = _basic_signoff(author="alice", reviewer=42, secondReviewer="alice")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        # secondReviewer collides with author, so the author arm fires;
        # the reviewer arm cannot fire because reviewer is not a str.
        assert any("secondReviewer must differ from author" in i for i in issues)
        assert not any("secondReviewer must differ from primary reviewer" in i for i in issues)


class TestValidateSemanticsNotesRequired:
    """``notes`` is required on failed checks or derivatives=n/a."""

    def test_passing_checks_no_notes_passes(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff()  # all-pass, no notes needed
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("notes" in i for i in issues)

    def test_failed_check_without_notes_flagged(self, fake_repo: pathlib.Path) -> None:
        checks = _checks_all_pass()
        checks["clausePrecision"] = "fail"
        record = _basic_signoff(checks=checks)  # no notes
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("one or more checks failed" in i for i in issues)

    def test_multiple_failed_checks_listed_sorted(self, fake_repo: pathlib.Path) -> None:
        checks = _checks_all_pass()
        checks["clausePrecision"] = "fail"
        checks["provenance"] = "fail"
        record = _basic_signoff(checks=checks)
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        # Failed names are sorted in the error message.
        matched = [i for i in issues if "one or more checks failed" in i]
        assert matched
        assert "clausePrecision" in matched[0]
        assert "provenance" in matched[0]
        # Order: sorted alphabetically.
        assert matched[0].index("clausePrecision") < matched[0].index("provenance")

    def test_failed_check_with_notes_passes(self, fake_repo: pathlib.Path) -> None:
        checks = _checks_all_pass()
        checks["clausePrecision"] = "fail"
        record = _basic_signoff(checks=checks, notes="Fixed by tightening regex.")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("one or more checks failed" in i for i in issues)

    def test_failed_check_with_whitespace_notes_flagged(self, fake_repo: pathlib.Path) -> None:
        """Whitespace-only notes do not count as present."""
        checks = _checks_all_pass()
        checks["clausePrecision"] = "fail"
        record = _basic_signoff(checks=checks, notes="   \t  ")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("one or more checks failed" in i for i in issues)

    def test_failed_check_with_non_string_notes_flagged(self, fake_repo: pathlib.Path) -> None:
        """Non-string notes do not count as present."""
        checks = _checks_all_pass()
        checks["clausePrecision"] = "fail"
        record = _basic_signoff(checks=checks, notes=42)
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("one or more checks failed" in i for i in issues)

    def test_derivatives_na_without_notes_flagged(self, fake_repo: pathlib.Path) -> None:
        checks = _checks_all_pass()
        checks["derivatives"] = "n/a"
        record = _basic_signoff(checks=checks)  # no notes
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("checks.derivatives is 'n/a'" in i for i in issues)

    def test_derivatives_na_with_notes_passes(self, fake_repo: pathlib.Path) -> None:
        checks = _checks_all_pass()
        checks["derivatives"] = "n/a"
        record = _basic_signoff(checks=checks, notes="UC is authored from scratch.")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("checks.derivatives is 'n/a'" in i for i in issues)

    def test_derivatives_pass_no_notes_required(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff()  # derivatives = pass, all-pass, no notes
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("derivatives" in i for i in issues)

    def test_missing_checks_field_no_crash(self, fake_repo: pathlib.Path) -> None:
        """``checks`` missing entirely: semantic stage doesn't crash."""
        record = _basic_signoff()
        del record["checks"]
        # Schema stage already flags this; semantic stage must survive.
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        # No "checks failed" or "derivatives is n/a" issues fire.
        assert not any("one or more checks failed" in i for i in issues)
        assert not any("checks.derivatives" in i for i in issues)


class TestValidateSemanticsCommitUniqueness:
    """Commit-level SHA validation + uniqueness across signoffs."""

    def test_unique_commits_pass(self, fake_repo: pathlib.Path) -> None:
        a = _basic_signoff(commit=_VALID_COMMIT_A)
        b = _basic_signoff(commit=_VALID_COMMIT_B, pr="#5678")
        issues = prs._validate_semantics(_signoff_file(signoffs=[a, b]))
        assert not any("already signed off" in i for i in issues)

    def test_invalid_commit_sha_flagged(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(commit="NOT-HEX")
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert any("not a valid short/long hex SHA" in i for i in issues)

    def test_duplicate_commit_flagged(self, fake_repo: pathlib.Path) -> None:
        a = _basic_signoff(commit=_VALID_COMMIT_A)
        b = _basic_signoff(commit=_VALID_COMMIT_A, pr="#5678")
        issues = prs._validate_semantics(_signoff_file(signoffs=[a, b]))
        msg = [i for i in issues if "already signed off" in i]
        assert msg
        assert "signoffs[0]" in msg[0]

    def test_non_string_commit_skips_validation(self, fake_repo: pathlib.Path) -> None:
        record = _basic_signoff(commit=42)
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("not a valid short/long hex SHA" in i for i in issues)
        assert not any("already signed off" in i for i in issues)

    def test_missing_commit_skips_validation(self, fake_repo: pathlib.Path) -> None:
        """Missing ``commit`` is handled silently by the semantic stage
        (schema stage already flags it)."""
        record = _basic_signoff()
        del record["commit"]
        issues = prs._validate_semantics(_signoff_file(signoffs=[record]))
        assert not any("not a valid short/long hex SHA" in i for i in issues)


class TestValidateSemanticsBaseline:
    """``baseline_commit`` SHA validation."""

    def test_valid_baseline_passes(self, fake_repo: pathlib.Path) -> None:
        issues = prs._validate_semantics(_signoff_file(baseline_commit=_VALID_BASELINE))
        assert not any("baseline_commit" in i for i in issues)

    def test_invalid_baseline_flagged(self, fake_repo: pathlib.Path) -> None:
        issues = prs._validate_semantics(_signoff_file(baseline_commit="NOT-HEX"))
        assert any("baseline_commit" in i and "is not a valid" in i for i in issues)

    def test_non_string_baseline_skips(self, fake_repo: pathlib.Path) -> None:
        """Schema stage flags non-string baseline; semantic stage skips
        the SHA-pattern check."""
        issues = prs._validate_semantics(_signoff_file(baseline_commit=42))
        assert not any("baseline_commit" in i for i in issues)


class TestValidateSemanticsEdgeCases:
    """Robustness against malformed inputs."""

    def test_signoffs_not_a_list_returns_empty(self, fake_repo: pathlib.Path) -> None:
        """Schema stage will have flagged this; semantic stage bails."""
        issues = prs._validate_semantics({"signoffs": "not a list"})
        assert issues == []

    def test_signoffs_missing_returns_empty(self, fake_repo: pathlib.Path) -> None:
        issues = prs._validate_semantics({})
        assert issues == []

    def test_non_dict_record_skipped(self, fake_repo: pathlib.Path) -> None:
        """Non-dict records are silently skipped by the semantic stage."""
        issues = prs._validate_semantics(_signoff_file(signoffs=["not a dict", _basic_signoff()]))
        # Non-dict produces no errors; the dict record passes cleanly.
        assert issues == []


# ----------------------------------------------------------------------
# _print_summary
# ----------------------------------------------------------------------


class TestPrintSummary:
    def test_empty_signoffs_prints_green(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        prs._print_summary(_signoff_file(), [])
        out = capsys.readouterr().out
        assert "Peer-review signoff audit" in out
        assert "Signoffs total  : 0" in out
        assert "GREEN" in out

    def test_lists_recent_entries(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        records = [_basic_signoff(pr=f"#{i}", commit=f"{i:040x}") for i in range(7)]
        prs._print_summary(_signoff_file(signoffs=records), [])
        out = capsys.readouterr().out
        # Only the last 5 should appear.
        assert "Recent entries" in out
        assert "#2" in out
        assert "#6" in out
        # First two should be omitted (only 5 most recent).
        assert "#0" not in out
        assert "#1" not in out

    def test_issues_block_when_errors_exist(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        prs._print_summary(_signoff_file(), ["bogus error 1", "bogus error 2"])
        out = capsys.readouterr().out
        assert "=== ISSUES (2) ===" in out
        assert "bogus error 1" in out
        assert "bogus error 2" in out

    def test_missing_baseline_shows_placeholder(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        data: dict[str, Any] = {"signoffs": []}
        prs._print_summary(data, [])
        out = capsys.readouterr().out
        assert "Baseline commit : <missing>" in out

    def test_signoffs_field_missing_shows_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        prs._print_summary({"baseline_commit": _VALID_BASELINE}, [])
        out = capsys.readouterr().out
        assert "Signoffs total  : 0" in out

    def test_scope_array_rendered(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        record = _basic_signoff(scope=["1.1.1", "schema"])
        prs._print_summary(_signoff_file(signoffs=[record]), [])
        out = capsys.readouterr().out
        assert "scope=[1.1.1, schema]" in out


# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------


class TestMain:
    def test_clean_data_returns_zero(
        self,
        make_signoff_file: MakeSignoffFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_signoff_file(_signoff_file())
        rc = prs.main(None)
        out = capsys.readouterr().out
        assert rc == 0
        assert "GREEN" in out

    def test_schema_failure_returns_one(
        self,
        make_signoff_file: MakeSignoffFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bad = _signoff_file()
        del bad["signoffs"]
        make_signoff_file(bad)
        rc = prs.main(None)
        out = capsys.readouterr().out
        assert rc == 1
        assert "ISSUES" in out

    def test_semantic_failure_returns_one(
        self,
        make_signoff_file: MakeSignoffFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        record = _basic_signoff(author="alice", reviewer="alice")
        make_signoff_file(_signoff_file(signoffs=[record]))
        rc = prs.main(None)
        out = capsys.readouterr().out
        assert rc == 1
        assert "must differ" in out

    def test_missing_data_file_exits_one(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # No signoff file created — DATA_PATH points to a non-existent path.
        with pytest.raises(SystemExit) as excinfo:
            prs.main(None)
        err = capsys.readouterr().err
        assert excinfo.value.code == 1
        assert "peer-review signoff file not found" in err

    def test_argv_is_ignored(
        self,
        make_signoff_file: MakeSignoffFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``argv`` is intentionally ignored via ``del argv``."""
        make_signoff_file(_signoff_file())
        rc = prs.main(["unused", "--flag"])
        assert rc == 0
        # No exception, output is the normal GREEN summary.
        assert "GREEN" in capsys.readouterr().out
