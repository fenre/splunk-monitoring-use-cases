"""Unit tests for ``splunk_uc.audits.legal_review_signoffs``.

P16 wave DD: lifts ``src/splunk_uc/audits/legal_review_signoffs.py``
from ~10% to ~100% combined coverage. Pins every documented
contract of the Phase 4.5b legal-review gate audit.
"""

from __future__ import annotations

import json
import pathlib
import shutil
from collections.abc import Callable
from typing import Any

import pytest

from splunk_uc.audits import legal_review_signoffs as lrs

MakeSignoffFile = Callable[[dict[str, Any]], pathlib.Path]
MakeUC = Callable[[int, str, dict[str, Any]], pathlib.Path]
MakeDoc = Callable[[str, str], pathlib.Path]


_VALID_BASELINE = "c6463a1d461b6b5813b9c58d4492818ee6805dd8"
_VALID_COMMIT = "abcdef1234567890abcdef1234567890abcdef12"
_VALID_COMMIT_2 = "1234567890abcdef1234567890abcdef12345678"


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with content/ + schemas/ + data/provenance/."""
    (tmp_path / "content").mkdir()
    (tmp_path / "schemas").mkdir()
    (tmp_path / "data" / "provenance").mkdir(parents=True)

    real_schema = (
        pathlib.Path(__file__).resolve().parents[3] / "schemas" / "legal-review-signoff.schema.json"
    )
    shutil.copy(real_schema, tmp_path / "schemas" / "legal-review-signoff.schema.json")

    monkeypatch.setattr(lrs, "REPO", tmp_path)
    monkeypatch.setattr(
        lrs, "SCHEMA_PATH", tmp_path / "schemas" / "legal-review-signoff.schema.json"
    )
    monkeypatch.setattr(
        lrs, "DATA_PATH", tmp_path / "data" / "provenance" / "legal-review-signoffs.json"
    )
    monkeypatch.setattr(lrs, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def make_signoff_file(fake_repo: pathlib.Path) -> MakeSignoffFile:
    def _make(data: dict[str, Any]) -> pathlib.Path:
        path: pathlib.Path = lrs.DATA_PATH
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    return _make


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    def _make(category: int, uc_id: str, payload: dict[str, Any]) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-test-cat"
        cat_dir.mkdir(parents=True, exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **payload}
        sidecar.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        return sidecar

    return _make


@pytest.fixture
def make_doc(fake_repo: pathlib.Path) -> MakeDoc:
    def _make(rel: str, content: str) -> pathlib.Path:
        path = fake_repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return _make


def _basic_signoff(**overrides: Any) -> dict[str, Any]:
    """Build a schema-valid legal signoff record."""
    base: dict[str, Any] = {
        "pr": "#1234",
        "date": "2026-04-18",
        "commit": _VALID_COMMIT,
        "reviewer": "Alice Counsel (LLP)",
        "reviewerRole": "internal-counsel",
        "scope": {"regulations": ["GDPR"]},
        "outcome": "approved",
    }
    base.update(overrides)
    return base


def _signoff_file(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "generated_at": "2026-04-18T14:22:52Z",
        "baseline_commit": _VALID_BASELINE,
        "documentation": "docs/legal-review-guide.md",
        "signoffs": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_sha_regex_lowercase_only(self) -> None:
        assert lrs._SHA_RE.match("c6463a1")
        assert lrs._SHA_RE.match("C6463A1") is None

    def test_sha_regex_min_length_7(self) -> None:
        assert lrs._SHA_RE.match("123456") is None
        assert lrs._SHA_RE.match("1234567") is not None

    def test_sha_regex_max_length_40(self) -> None:
        assert lrs._SHA_RE.match("a" * 40) is not None
        assert lrs._SHA_RE.match("a" * 41) is None

    def test_uc_id_regex_basic(self) -> None:
        m = lrs._UC_ID_RE.match("22.3.41")
        assert m is not None
        assert m.group("cat") == "22"

    def test_uc_id_regex_rejects_leading_zero(self) -> None:
        assert lrs._UC_ID_RE.match("01.2.3") is None

    def test_uc_id_regex_allows_zero_cat(self) -> None:
        assert lrs._UC_ID_RE.match("0.1.1") is not None

    def test_repo_resolves(self) -> None:
        import importlib

        fresh = importlib.reload(lrs)
        assert (fresh.REPO / "schemas").is_dir() or (fresh.REPO / "content").is_dir()


# ---------------------------------------------------------------------------
# _load_json
# ---------------------------------------------------------------------------


class TestLoadJson:
    def test_missing_file_exits(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            lrs._load_json(fake_repo / "missing.json", "missing test")
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "missing test not found" in err

    def test_invalid_json_exits(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = fake_repo / "bad.json"
        path.write_text("not json", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            lrs._load_json(path, "bad json")
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "is not valid JSON" in err

    def test_happy_path(self, fake_repo: pathlib.Path) -> None:
        path = fake_repo / "ok.json"
        path.write_text(json.dumps({"k": "v"}), encoding="utf-8")
        assert lrs._load_json(path, "ok") == {"k": "v"}


# ---------------------------------------------------------------------------
# _validate_schema
# ---------------------------------------------------------------------------


class TestValidateSchema:
    def test_clean_data_no_issues(self, fake_repo: pathlib.Path) -> None:
        assert lrs._validate_schema(_signoff_file()) == []

    def test_missing_required_field_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file()
        del data["generated_at"]
        issues = lrs._validate_schema(data)
        assert any("generated_at" in i for i in issues)

    def test_root_path_emitted_for_top_level_error(self, fake_repo: pathlib.Path) -> None:
        issues = lrs._validate_schema({"signoffs": []})
        assert any("<root>" in i for i in issues)


# ---------------------------------------------------------------------------
# _uc_sidecar_path
# ---------------------------------------------------------------------------


class TestUcSidecarPath:
    def test_invalid_id_returns_none(self, fake_repo: pathlib.Path) -> None:
        assert lrs._uc_sidecar_path("not-uc") is None

    def test_partial_id_returns_none(self, fake_repo: pathlib.Path) -> None:
        assert lrs._uc_sidecar_path("1.2") is None

    def test_existing_uc_returns_real_path(self, make_uc: MakeUC) -> None:
        make_uc(7, "7.1.40", {})
        path = lrs._uc_sidecar_path("7.1.40")
        assert path is not None
        assert path.is_file()
        assert path.name == "UC-7.1.40.json"

    def test_missing_uc_returns_synthetic_path(self, fake_repo: pathlib.Path) -> None:
        path = lrs._uc_sidecar_path("7.1.40")
        assert path is not None
        assert not path.is_file()
        assert "?" in str(path)


# ---------------------------------------------------------------------------
# _collect_uc_legal_caveats
# ---------------------------------------------------------------------------


class TestCollectUcLegalCaveats:
    def test_empty_list(self, fake_repo: pathlib.Path) -> None:
        assert lrs._collect_uc_legal_caveats([]) == set()

    def test_invalid_id_skipped(self, fake_repo: pathlib.Path) -> None:
        assert lrs._collect_uc_legal_caveats(["bogus"]) == set()

    def test_missing_sidecar_skipped(self, fake_repo: pathlib.Path) -> None:
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == set()

    def test_happy_path(self, make_uc: MakeUC) -> None:
        make_uc(
            1,
            "1.1.1",
            {"compliance": [{"legalCaveat": "Caveat A"}, {"legalCaveat": "Caveat B"}]},
        )
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == {"Caveat A", "Caveat B"}

    def test_whitespace_stripped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": [{"legalCaveat": "  Trimmed  "}]})
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == {"Trimmed"}

    def test_empty_string_skipped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": [{"legalCaveat": ""}]})
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == set()

    def test_non_string_skipped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": [{"legalCaveat": 42}]})
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == set()

    def test_non_dict_entry_skipped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": ["not a dict", {"legalCaveat": "real"}]})
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == {"real"}

    def test_missing_compliance(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {})
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == set()

    def test_unparseable_sidecar_skipped(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(1, "1.1.1", {})
        sidecar = fake_repo / "content" / "cat-01-test-cat" / "UC-1.1.1.json"
        sidecar.write_text("not json", encoding="utf-8")
        assert lrs._collect_uc_legal_caveats(["1.1.1"]) == set()


# ---------------------------------------------------------------------------
# _validate_semantics — outcome-driven invariants
# ---------------------------------------------------------------------------


class TestSemanticsOutcomes:
    def test_approved_with_revisions_requires_array(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[_basic_signoff(outcome="approved-with-revisions", revisionsRequested=[])]
        )
        issues = lrs._validate_semantics(data)
        assert any("approved-with-revisions" in i for i in issues)

    def test_approved_with_revisions_satisfied(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[
                _basic_signoff(
                    outcome="approved-with-revisions",
                    revisionsRequested=["Long enough revision text"],
                )
            ]
        )
        issues = lrs._validate_semantics(data)
        assert not any("approved-with-revisions" in i for i in issues)

    def test_conditional_requires_caveats(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=[_basic_signoff(outcome="conditional")])
        issues = lrs._validate_semantics(data)
        assert any("conditional" in i for i in issues)

    def test_conditional_with_caveats_passes_outcome_check(self, fake_repo: pathlib.Path) -> None:
        # The outcome check passes; caveat-mirror check is separate.
        data = _signoff_file(
            signoffs=[_basic_signoff(outcome="conditional", caveats=["Caveat is here"])]
        )
        issues = lrs._validate_semantics(data)
        # Filter: there should be no "'caveats' array" rationale.
        assert not any(
            "outcome='conditional' requires a non-empty 'caveats' array" in i for i in issues
        )


# ---------------------------------------------------------------------------
# Commit uniqueness
# ---------------------------------------------------------------------------


class TestCommitUniqueness:
    def test_duplicate_commit_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=[_basic_signoff(), _basic_signoff(reviewer="Bob")])
        issues = lrs._validate_semantics(data)
        assert any("already signed off" in i for i in issues)

    def test_different_commits_pass(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[
                _basic_signoff(),
                _basic_signoff(commit=_VALID_COMMIT_2, reviewer="Bob"),
            ]
        )
        issues = lrs._validate_semantics(data)
        assert not any("already signed off" in i for i in issues)

    def test_invalid_commit_sha_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=[_basic_signoff(commit="NOTHEX")])
        issues = lrs._validate_semantics(data)
        assert any("not a valid short/long hex SHA" in i for i in issues)

    def test_non_string_commit_skipped(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=[_basic_signoff(commit=42)])
        issues = lrs._validate_semantics(data)
        assert not any("hex SHA" in i for i in issues)

    def test_baseline_commit_invalid_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(baseline_commit="NOT_HEX")
        issues = lrs._validate_semantics(data)
        assert any("baseline_commit" in i for i in issues)


# ---------------------------------------------------------------------------
# Paralegal scope restriction
# ---------------------------------------------------------------------------


class TestParalegalScope:
    def test_paralegal_with_only_ucs_passes(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff(reviewerRole="paralegal")
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("paralegal" in i for i in issues)

    def test_paralegal_with_documents_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(reviewerRole="paralegal")
        signoff["scope"]["ucs"] = ["1.1.1"]
        signoff["scope"]["documents"] = ["docs/regulatory-primer.md"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert any("paralegal" in i and "clause-number" in i for i in issues)

    def test_paralegal_with_empty_ucs_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(reviewerRole="paralegal")
        signoff["scope"]["ucs"] = []
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert any("paralegal" in i for i in issues)


# ---------------------------------------------------------------------------
# Scope existence checks
# ---------------------------------------------------------------------------


class TestScopeExistence:
    def test_invalid_uc_id_in_scope_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["bogus"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert any("not a valid UC id" in i for i in issues)

    def test_missing_uc_sidecar_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert any("no sidecar on disk" in i for i in issues)

    def test_existing_uc_passes(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("no sidecar on disk" in i for i in issues)

    def test_non_string_uc_id_skipped(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = [42]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("scope.ucs entry" in i for i in issues)

    def test_missing_document_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["documents"] = ["docs/missing.md"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert any("does not resolve to a file" in i for i in issues)

    def test_existing_document_passes(self, make_doc: MakeDoc) -> None:
        make_doc("docs/regulatory-primer.md", "# Primer")
        signoff = _basic_signoff()
        signoff["scope"]["documents"] = ["docs/regulatory-primer.md"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("does not resolve" in i for i in issues)

    def test_document_with_anchor_stripped(self, make_doc: MakeDoc) -> None:
        make_doc("docs/regulatory-primer.md", "# Primer")
        signoff = _basic_signoff()
        signoff["scope"]["documents"] = ["docs/regulatory-primer.md#article-5"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("does not resolve" in i for i in issues)

    def test_non_string_document_skipped(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["documents"] = [42]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("scope.documents" in i for i in issues)


# ---------------------------------------------------------------------------
# Caveat mirror
# ---------------------------------------------------------------------------


class TestCaveatMirror:
    def test_missing_caveat_on_sidecar_flagged(
        self, make_uc: MakeUC, fake_repo: pathlib.Path
    ) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff(outcome="conditional", caveats=["Specific caveat"])
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert any("not present as a 'legalCaveat'" in i for i in issues)

    def test_caveat_present_on_sidecar_passes(self, make_uc: MakeUC) -> None:
        make_uc(
            1,
            "1.1.1",
            {"compliance": [{"legalCaveat": "Specific caveat"}]},
        )
        signoff = _basic_signoff(outcome="conditional", caveats=["Specific caveat"])
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("not present as a 'legalCaveat'" in i for i in issues)

    def test_no_caveats_no_check(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        assert not any("not present as a 'legalCaveat'" in i for i in issues)

    def test_non_string_caveat_skipped(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff(outcome="conditional", caveats=[42, "real caveat"])
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        issues = lrs._validate_semantics(data)
        # 42 skipped; "real caveat" still flagged.
        assert any("not present as a 'legalCaveat'" in i for i in issues)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_signoffs_not_list_returns_empty(self, fake_repo: pathlib.Path) -> None:
        assert lrs._validate_semantics({"signoffs": "not a list"}) == []

    def test_missing_signoffs_key_returns_empty(self, fake_repo: pathlib.Path) -> None:
        assert lrs._validate_semantics({}) == []

    def test_non_dict_record_skipped(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=["not a dict", _basic_signoff()])
        issues = lrs._validate_semantics(data)
        # Should not crash.
        assert isinstance(issues, list)


# ---------------------------------------------------------------------------
# _print_summary
# ---------------------------------------------------------------------------


class TestPrintSummary:
    def test_clean_run_prints_green(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lrs._print_summary(_signoff_file(), [])
        out = capsys.readouterr().out
        assert "Legal-review signoff audit" in out
        assert "GREEN" in out

    def test_lists_recent_entries(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        signoffs = [_basic_signoff(pr=f"#{i}") for i in range(10)]
        data = _signoff_file(signoffs=signoffs)
        lrs._print_summary(data, [])
        out = capsys.readouterr().out
        assert "#9" in out
        assert "#5" in out
        assert "#0" not in out  # Outside last-5 window.

    def test_prints_issues_block(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lrs._print_summary(_signoff_file(), ["bad thing"])
        out = capsys.readouterr().out
        assert "ISSUES (1)" in out
        assert "bad thing" in out

    def test_missing_signoffs_field_shows_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lrs._print_summary({"baseline_commit": "abc1234"}, [])
        out = capsys.readouterr().out
        assert "Signoffs total  : 0" in out

    def test_missing_baseline_shows_placeholder(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lrs._print_summary({}, [])
        out = capsys.readouterr().out
        assert "<missing>" in out


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


class TestMain:
    def test_clean_returns_zero(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_signoff_file(_signoff_file())
        rc = lrs.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "GREEN" in out

    def test_schema_failure_returns_one(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        data = _signoff_file()
        del data["generated_at"]
        make_signoff_file(data)
        rc = lrs.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "ISSUES" in out

    def test_semantic_failure_returns_one(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
    ) -> None:
        make_signoff_file(_signoff_file(signoffs=[_basic_signoff(outcome="conditional")]))
        rc = lrs.main([])
        assert rc == 1

    def test_missing_data_file_exits(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            lrs.main([])
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "signoff file not found" in err

    def test_argv_ignored(
        self,
        make_signoff_file: MakeSignoffFile,
    ) -> None:
        make_signoff_file(_signoff_file())
        rc = lrs.main(["--anything", "--at-all"])
        assert rc == 0
