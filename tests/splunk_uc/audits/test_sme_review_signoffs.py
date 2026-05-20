"""Unit tests for ``splunk_uc.audits.sme_review_signoffs``.

P16 wave CC: lifts ``src/splunk_uc/audits/sme_review_signoffs.py``
from ~8% to ~99% combined coverage. Pins every documented contract
of the Phase 5.2 SME-review gate audit:

(a) `data/provenance/sme-signoffs.json` validates against the
    JSON Schema;
(b) every outcome-driven semantic invariant fires under tailored
    fixtures (approved-with-revisions / conditional / rejected /
    approved-with-failing-checks / reviewer-commit uniqueness /
    fixture replay self-consistency / splunk-engineer warning);
(c) every scope-existence check fires (UC existence + fixture
    existence + evidence-pack existence + caveat mirror).
"""

from __future__ import annotations

import json
import pathlib
import shutil
from collections.abc import Callable
from typing import Any

import pytest

from splunk_uc.audits import sme_review_signoffs as srs

MakeSignoffFile = Callable[[dict[str, Any]], pathlib.Path]
MakeUC = Callable[[int, str, dict[str, Any]], pathlib.Path]
MakeFixture = Callable[[str, str], pathlib.Path]
MakeEvidence = Callable[[str, str], pathlib.Path]


_VALID_BASELINE = "c6463a1d461b6b5813b9c58d4492818ee6805dd8"
_VALID_COMMIT = "abcdef1234567890abcdef1234567890abcdef12"


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with content/ + sample-data/ + docs/evidence-packs/
    + schemas/."""
    (tmp_path / "content").mkdir()
    (tmp_path / "sample-data").mkdir()
    (tmp_path / "docs" / "evidence-packs").mkdir(parents=True)
    (tmp_path / "schemas").mkdir()
    (tmp_path / "data" / "provenance").mkdir(parents=True)

    # Copy the real schema so jsonschema validation works against
    # realistic data.
    real_schema = (
        pathlib.Path(__file__).resolve().parents[3] / "schemas" / "sme-review-signoff.schema.json"
    )
    shutil.copy(real_schema, tmp_path / "schemas" / "sme-review-signoff.schema.json")

    monkeypatch.setattr(srs, "REPO", tmp_path)
    monkeypatch.setattr(srs, "SCHEMA_PATH", tmp_path / "schemas" / "sme-review-signoff.schema.json")
    monkeypatch.setattr(srs, "DATA_PATH", tmp_path / "data" / "provenance" / "sme-signoffs.json")
    monkeypatch.setattr(srs, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(srs, "SAMPLE_DATA", tmp_path / "sample-data")
    monkeypatch.setattr(srs, "EVIDENCE_PACKS", tmp_path / "docs" / "evidence-packs")
    return tmp_path


@pytest.fixture
def make_signoff_file(fake_repo: pathlib.Path) -> MakeSignoffFile:
    def _make(data: dict[str, Any]) -> pathlib.Path:
        path: pathlib.Path = srs.DATA_PATH
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
def make_fixture(fake_repo: pathlib.Path) -> MakeFixture:
    def _make(rel: str, content: str) -> pathlib.Path:
        path = fake_repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return _make


@pytest.fixture
def make_evidence(fake_repo: pathlib.Path) -> MakeEvidence:
    def _make(rel: str, content: str) -> pathlib.Path:
        path = fake_repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return _make


def _basic_signoff(**overrides: Any) -> dict[str, Any]:
    """Build a schema-valid signoff record."""
    base = {
        "pr": "#1234",
        "date": "2026-04-18",
        "commit": _VALID_COMMIT,
        "reviewer": "Alice Engineer",
        "reviewerRole": "splunk-engineer",
        "scope": {"ucs": [], "regulations": []},
        "outcome": "approved",
        "checks": {
            "splCorrectness": "n/a",
            "dataSourceRealism": "pass",
            "splunkCompat": "pass",
            "evidenceCompleteness": "pass",
            "regulationApplicability": "pass",
            "falsePositiveAssessment": "pass",
        },
    }
    base.update(overrides)
    return base


def _signoff_file(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "generated_at": "2026-04-18T14:22:52Z",
        "baseline_commit": _VALID_BASELINE,
        "documentation": "docs/sme-review-guide.md",
        "signoffs": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_sha_regex_matches_short(self) -> None:
        assert srs._SHA_RE.match("c6463a1")

    def test_sha_regex_matches_full(self) -> None:
        assert srs._SHA_RE.match("c6463a1d461b6b5813b9c58d4492818ee6805dd8")

    def test_sha_regex_rejects_short(self) -> None:
        # Must be at least 7 hex chars.
        assert srs._SHA_RE.match("c6463a") is None

    def test_sha_regex_rejects_uppercase(self) -> None:
        assert srs._SHA_RE.match("C6463A1") is None

    def test_sha_regex_rejects_non_hex(self) -> None:
        assert srs._SHA_RE.match("c6463xy") is None

    def test_uc_id_regex_matches_basic(self) -> None:
        m = srs._UC_ID_RE.match("1.2.3")
        assert m is not None
        assert m.group("cat") == "1"

    def test_uc_id_regex_matches_multi_digit(self) -> None:
        m = srs._UC_ID_RE.match("22.11.105")
        assert m is not None
        assert m.group("cat") == "22"

    def test_uc_id_regex_rejects_leading_zero(self) -> None:
        # "01.1.1" must be rejected — cat is `0|[1-9][0-9]*`.
        assert srs._UC_ID_RE.match("01.1.1") is None

    def test_uc_id_regex_allows_zero_cat(self) -> None:
        # cat=0 is permitted (stub categories).
        assert srs._UC_ID_RE.match("0.1.1") is not None

    def test_uc_id_regex_rejects_two_segments(self) -> None:
        assert srs._UC_ID_RE.match("1.2") is None

    def test_repo_constant_resolves(self) -> None:
        import importlib

        fresh = importlib.reload(srs)
        assert (fresh.REPO / "schemas").is_dir() or (fresh.REPO / "content").is_dir()


# ---------------------------------------------------------------------------
# _load_json
# ---------------------------------------------------------------------------


class TestLoadJson:
    def test_missing_file_exits_one(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            srs._load_json(fake_repo / "missing.json", "missing test")
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "missing test not found" in err

    def test_invalid_json_exits_one(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = fake_repo / "bad.json"
        path.write_text("not json", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            srs._load_json(path, "bad json")
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "bad json is not valid JSON" in err

    def test_happy_path(self, fake_repo: pathlib.Path) -> None:
        path = fake_repo / "good.json"
        path.write_text(json.dumps({"k": "v"}), encoding="utf-8")
        assert srs._load_json(path, "ok") == {"k": "v"}


# ---------------------------------------------------------------------------
# _validate_schema
# ---------------------------------------------------------------------------


class TestValidateSchema:
    def test_valid_data_returns_no_issues(self, fake_repo: pathlib.Path) -> None:
        issues = srs._validate_schema(_signoff_file())
        assert issues == []

    def test_missing_required_top_field(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file()
        del data["generated_at"]
        issues = srs._validate_schema(data)
        assert any("schema:" in i for i in issues)
        assert any("generated_at" in i for i in issues)

    def test_invalid_baseline_commit(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(baseline_commit="NOT_A_SHA")
        issues = srs._validate_schema(data)
        assert any("baseline_commit" in i for i in issues)

    def test_returns_path_root_when_missing_top_level(self, fake_repo: pathlib.Path) -> None:
        # An error at the very top has empty path → "<root>".
        issues = srs._validate_schema({"signoffs": []})
        assert any("<root>" in i for i in issues)


# ---------------------------------------------------------------------------
# _uc_sidecar_path
# ---------------------------------------------------------------------------


class TestUcSidecarPath:
    def test_invalid_uc_id_returns_none(self, fake_repo: pathlib.Path) -> None:
        assert srs._uc_sidecar_path("not-a-uc-id") is None

    def test_partial_uc_id_returns_none(self, fake_repo: pathlib.Path) -> None:
        assert srs._uc_sidecar_path("1.2") is None

    def test_existing_uc_returns_real_path(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(7, "7.1.40", {})
        path = srs._uc_sidecar_path("7.1.40")
        assert path is not None
        assert path.is_file()
        assert path.name == "UC-7.1.40.json"

    def test_missing_uc_returns_synthetic_path(self, fake_repo: pathlib.Path) -> None:
        path = srs._uc_sidecar_path("7.1.40")
        assert path is not None
        # Synthetic path — not on disk.
        assert not path.is_file()
        assert path.name == "UC-7.1.40.json"


# ---------------------------------------------------------------------------
# _collect_uc_sme_caveats
# ---------------------------------------------------------------------------


class TestCollectUcSmeCaveats:
    def test_empty_list_returns_empty(self, fake_repo: pathlib.Path) -> None:
        assert srs._collect_uc_sme_caveats([]) == set()

    def test_invalid_uc_id_skipped(self, fake_repo: pathlib.Path) -> None:
        assert srs._collect_uc_sme_caveats(["bogus"]) == set()

    def test_uc_without_sidecar_skipped(self, fake_repo: pathlib.Path) -> None:
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == set()

    def test_collects_caveats_from_sidecar(self, make_uc: MakeUC) -> None:
        make_uc(
            1,
            "1.1.1",
            {
                "compliance": [
                    {"smeCaveat": "Caveat A"},
                    {"smeCaveat": "Caveat B"},
                ]
            },
        )
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == {"Caveat A", "Caveat B"}

    def test_strips_whitespace(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": [{"smeCaveat": "  Trimmed  "}]})
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == {"Trimmed"}

    def test_empty_caveat_string_skipped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": [{"smeCaveat": ""}]})
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == set()

    def test_non_string_caveat_skipped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": [{"smeCaveat": 42}]})
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == set()

    def test_non_dict_compliance_entry_skipped(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {"compliance": ["not a dict", {"smeCaveat": "real"}]})
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == {"real"}

    def test_missing_compliance_field_returns_empty(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {})
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == set()

    def test_unparseable_sidecar_skipped(self, fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {})
        # Corrupt the sidecar by overwriting it with junk.
        sidecar = fake_repo / "content" / "cat-01-test-cat" / "UC-1.1.1.json"
        sidecar.write_text("not json", encoding="utf-8")
        assert srs._collect_uc_sme_caveats(["1.1.1"]) == set()


# ---------------------------------------------------------------------------
# _validate_semantics — outcome-driven invariants
# ---------------------------------------------------------------------------


class TestSemanticsOutcomes:
    def test_approved_with_revisions_requires_array(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[_basic_signoff(outcome="approved-with-revisions", revisionsRequested=[])]
        )
        errs, _warns = srs._validate_semantics(data)
        assert any("approved-with-revisions" in e for e in errs)

    def test_approved_with_revisions_satisfied(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[
                _basic_signoff(
                    outcome="approved-with-revisions",
                    revisionsRequested=["Add KFP guidance"],
                )
            ]
        )
        errs, _warns = srs._validate_semantics(data)
        assert not any("approved-with-revisions" in e for e in errs)

    def test_conditional_requires_caveats(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=[_basic_signoff(outcome="conditional")])
        errs, _warns = srs._validate_semantics(data)
        assert any("conditional" in e for e in errs)

    def test_rejected_requires_long_rejection_reason(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[_basic_signoff(outcome="rejected", rejectionReason="too short")]
        )
        errs, _warns = srs._validate_semantics(data)
        assert any("rejected" in e and "rejectionReason" in e for e in errs)

    def test_rejected_with_long_reason_passes(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(
            signoffs=[
                _basic_signoff(
                    outcome="rejected",
                    rejectionReason="This UC cannot land because the SPL is fundamentally wrong.",
                )
            ]
        )
        errs, _warns = srs._validate_semantics(data)
        assert not any("rejectionReason" in e for e in errs)

    def test_rejected_missing_field_flagged(self, fake_repo: pathlib.Path) -> None:
        # The "rejectionReason" key is absent entirely.
        data = _signoff_file(signoffs=[_basic_signoff(outcome="rejected")])
        errs, _warns = srs._validate_semantics(data)
        assert any("rejectionReason" in e for e in errs)

    def test_approved_with_failing_check_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["checks"]["splCorrectness"] = "fail"
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("inconsistent" in e for e in errs)


# ---------------------------------------------------------------------------
# Reviewer/commit uniqueness + SHA validation
# ---------------------------------------------------------------------------


class TestReviewerCommitUniqueness:
    def test_invalid_commit_sha_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(signoffs=[_basic_signoff(commit="NOT_A_SHA")])
        errs, _warns = srs._validate_semantics(data)
        assert any("not a valid short/long hex SHA" in e for e in errs)

    def test_same_reviewer_same_commit_flagged(self, fake_repo: pathlib.Path) -> None:
        s1 = _basic_signoff(reviewer="Alice")
        s2 = _basic_signoff(reviewer="Alice")
        data = _signoff_file(signoffs=[s1, s2])
        errs, _warns = srs._validate_semantics(data)
        assert any("already signed off" in e for e in errs)

    def test_two_different_reviewers_same_commit_allowed(self, fake_repo: pathlib.Path) -> None:
        s1 = _basic_signoff(reviewer="Alice")
        s2 = _basic_signoff(reviewer="Bob")
        data = _signoff_file(signoffs=[s1, s2])
        errs, _warns = srs._validate_semantics(data)
        assert not any("already signed off" in e for e in errs)

    def test_baseline_commit_invalid_sha_flagged(self, fake_repo: pathlib.Path) -> None:
        data = _signoff_file(baseline_commit="NOT_HEX")
        errs, _warns = srs._validate_semantics(data)
        assert any("baseline_commit" in e for e in errs)

    def test_blank_reviewer_skips_pair_check(self, fake_repo: pathlib.Path) -> None:
        s1 = _basic_signoff(reviewer="")
        s2 = _basic_signoff(reviewer="")
        data = _signoff_file(signoffs=[s1, s2])
        errs, _warns = srs._validate_semantics(data)
        # Neither should fire — but the empty reviewer might be a schema issue.
        assert not any("already signed off" in e for e in errs)

    def test_non_string_commit_skipped(self, fake_repo: pathlib.Path) -> None:
        # When ``commit`` is not a string, the entire reviewer/commit
        # uniqueness block is skipped — no SHA validation, no pair
        # tracking. Pins the branch `218->234`.
        signoff = _basic_signoff(commit=42)
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        # No SHA error fires.
        assert not any("not a valid short/long hex SHA" in e for e in errs)


# ---------------------------------------------------------------------------
# Fixture replay self-consistency
# ---------------------------------------------------------------------------


class TestFixtureReplaySelfConsistency:
    def test_replayed_false_with_pass_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(
            outcome="approved-with-revisions",
            revisionsRequested=["x"],
            fixtureReplayResult={"replayed": False},
        )
        signoff["checks"]["splCorrectness"] = "pass"
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("replayed=false" in e for e in errs)

    def test_replayed_true_with_mismatch_and_pass_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(
            outcome="approved-with-revisions",
            revisionsRequested=["x"],
            fixtureReplayResult={
                "replayed": True,
                "positiveDetected": False,
                "negativeSilent": True,
            },
        )
        signoff["checks"]["splCorrectness"] = "pass"
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("replay mismatch" in e for e in errs)

    def test_clean_replay_with_fail_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(
            outcome="approved-with-revisions",
            revisionsRequested=["x"],
            fixtureReplayResult={
                "replayed": True,
                "positiveDetected": True,
                "negativeSilent": True,
            },
        )
        signoff["checks"]["splCorrectness"] = "fail"
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("contradicts the replay" in e for e in errs)

    def test_self_consistent_replay_passes(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(
            fixtureReplayResult={
                "replayed": True,
                "positiveDetected": True,
                "negativeSilent": True,
            }
        )
        signoff["checks"]["splCorrectness"] = "pass"
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        # Filter out warnings; we only care that no replay-consistency
        # error fires.
        assert not any(
            "replay mismatch" in e or "replayed=false" in e or "contradicts" in e for e in errs
        )

    def test_empty_replay_dict_skipped(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(fixtureReplayResult={})
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        # No replay-specific errors should fire on empty dict.
        assert not any("replayed=" in e for e in errs)


# ---------------------------------------------------------------------------
# splunk-engineer warning (soft check)
# ---------------------------------------------------------------------------


class TestSplunkEngineerWarning:
    def test_warning_fires_without_replay(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(reviewerRole="splunk-engineer")
        signoff["checks"]["splCorrectness"] = "pass"
        data = _signoff_file(signoffs=[signoff])
        _errs, warns = srs._validate_semantics(data)
        assert any("splunk-engineer" in w for w in warns)

    def test_warning_suppressed_with_replay(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(
            reviewerRole="splunk-engineer",
            fixtureReplayResult={
                "replayed": True,
                "positiveDetected": True,
                "negativeSilent": True,
            },
        )
        signoff["checks"]["splCorrectness"] = "pass"
        data = _signoff_file(signoffs=[signoff])
        _errs, warns = srs._validate_semantics(data)
        assert not any("splunk-engineer" in w for w in warns)

    def test_other_roles_dont_trigger_warning(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff(reviewerRole="external-sme")
        signoff["checks"]["splCorrectness"] = "pass"
        data = _signoff_file(signoffs=[signoff])
        _errs, warns = srs._validate_semantics(data)
        assert not any("splunk-engineer" in w for w in warns)


# ---------------------------------------------------------------------------
# Scope existence checks (ucs, fixtures, evidence packs)
# ---------------------------------------------------------------------------


class TestScopeExistenceChecks:
    def test_invalid_uc_id_in_scope_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["bogus"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("not a valid UC id" in e for e in errs)

    def test_missing_uc_sidecar_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("no sidecar on disk" in e for e in errs)

    def test_existing_uc_passes(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("no sidecar on disk" in e for e in errs)

    def test_non_string_uc_id_skipped(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = [42]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("not a valid UC id" in e for e in errs)

    def test_fixture_outside_sample_data_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["fixtures"] = ["docs/somewhere.json"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("must live under" in e and "sample-data/" in e for e in errs)

    def test_missing_fixture_file_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["fixtures"] = ["sample-data/missing.json"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("does not resolve to a file" in e for e in errs)

    def test_existing_fixture_passes(
        self, make_fixture: MakeFixture, fake_repo: pathlib.Path
    ) -> None:
        make_fixture("sample-data/UC-1.1.1/positive.json", "{}")
        signoff = _basic_signoff()
        signoff["scope"]["fixtures"] = ["sample-data/UC-1.1.1/positive.json"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("does not resolve to a file" in e for e in errs)
        assert not any("must live under" in e for e in errs)

    def test_non_string_fixture_skipped(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["fixtures"] = [42]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("scope.fixtures" in e for e in errs)

    def test_evidence_pack_outside_dir_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["evidencePacks"] = ["docs/not-evidence.md"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("must live under" in e and "docs/evidence-packs/" in e for e in errs)

    def test_missing_evidence_pack_flagged(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["evidencePacks"] = ["docs/evidence-packs/missing.md"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("does not" in e and "resolve to a file" in e for e in errs)

    def test_evidence_pack_with_anchor_stripped(
        self, make_evidence: MakeEvidence, fake_repo: pathlib.Path
    ) -> None:
        make_evidence("docs/evidence-packs/GDPR.md", "# GDPR")
        signoff = _basic_signoff()
        signoff["scope"]["evidencePacks"] = ["docs/evidence-packs/GDPR.md#article-5"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        # No path-resolution error because the # anchor is stripped.
        assert not any("does not" in e and "resolve to a file" in e for e in errs)

    def test_non_string_evidence_pack_skipped(self, fake_repo: pathlib.Path) -> None:
        signoff = _basic_signoff()
        signoff["scope"]["evidencePacks"] = [42]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("scope.evidencePacks" in e for e in errs)


# ---------------------------------------------------------------------------
# Caveat mirror
# ---------------------------------------------------------------------------


class TestCaveatMirror:
    def test_caveat_missing_from_sidecar_flagged(
        self, make_uc: MakeUC, fake_repo: pathlib.Path
    ) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff(outcome="conditional", caveats=["Watch for jitter"])
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert any("not present as an 'smeCaveat'" in e for e in errs)

    def test_caveat_present_on_sidecar_passes(
        self, make_uc: MakeUC, fake_repo: pathlib.Path
    ) -> None:
        make_uc(
            1,
            "1.1.1",
            {"compliance": [{"smeCaveat": "Watch for jitter"}]},
        )
        signoff = _basic_signoff(outcome="conditional", caveats=["Watch for jitter"])
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("not present as an 'smeCaveat'" in e for e in errs)

    def test_no_caveats_no_check(self, fake_repo: pathlib.Path) -> None:
        # No caveats array → caveat mirror loop doesn't fire.
        signoff = _basic_signoff()
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        assert not any("not present as an 'smeCaveat'" in e for e in errs)

    def test_non_string_caveat_skipped(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(1, "1.1.1", {})
        signoff = _basic_signoff(outcome="conditional", caveats=[42, "real"])
        signoff["scope"]["ucs"] = ["1.1.1"]
        data = _signoff_file(signoffs=[signoff])
        errs, _warns = srs._validate_semantics(data)
        # 42 is not a string → skipped. "real" still triggers.
        assert any("not present as an 'smeCaveat'" in e for e in errs)


# ---------------------------------------------------------------------------
# Non-dict / non-list edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_signoffs_not_a_list_returns_empty(self, fake_repo: pathlib.Path) -> None:
        errs, warns = srs._validate_semantics({"signoffs": "not a list"})
        assert errs == []
        assert warns == []

    def test_missing_signoffs_key_returns_empty(self, fake_repo: pathlib.Path) -> None:
        errs, warns = srs._validate_semantics({})
        assert errs == []
        assert warns == []

    def test_non_dict_signoff_record_skipped(self, fake_repo: pathlib.Path) -> None:
        # A list with a non-dict element shouldn't crash.
        data = _signoff_file(signoffs=["not a dict", _basic_signoff()])
        errs, _warns = srs._validate_semantics(data)
        # No crash; only the dict signoff contributes findings (if any).
        assert isinstance(errs, list)


# ---------------------------------------------------------------------------
# _print_summary
# ---------------------------------------------------------------------------


class TestPrintSummary:
    def test_empty_signoffs(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        data = _signoff_file()
        srs._print_summary(data, [], [])
        out = capsys.readouterr().out
        assert "SME-review signoff audit" in out
        assert "No errors. SME-review gate is GREEN." in out

    def test_lists_recent_signoffs(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        signoffs = [_basic_signoff(pr=f"#{i}") for i in range(10)]
        data = _signoff_file(signoffs=signoffs)
        srs._print_summary(data, [], [])
        out = capsys.readouterr().out
        # Should show last 5 entries (#5 through #9).
        assert "#9" in out
        assert "#5" in out
        assert "#0" not in out  # Beyond the last-5 window.

    def test_prints_warnings_block(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        srs._print_summary(_signoff_file(), [], ["some warning"])
        out = capsys.readouterr().out
        assert "WARNINGS (1)" in out
        assert "some warning" in out

    def test_prints_errors_block(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        srs._print_summary(_signoff_file(), ["bad thing"], [])
        out = capsys.readouterr().out
        assert "ERRORS (1)" in out
        assert "bad thing" in out

    def test_missing_signoffs_field_shows_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        srs._print_summary({"baseline_commit": "abc1234"}, [], [])
        out = capsys.readouterr().out
        assert "Signoffs total  : 0" in out


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


class TestMain:
    def test_returns_zero_on_clean_data(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_signoff_file(_signoff_file())
        rc = srs.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "No errors" in out

    def test_returns_one_on_schema_failure(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Schema-invalid: missing required field.
        data = _signoff_file()
        del data["baseline_commit"]
        make_signoff_file(data)
        rc = srs.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "ERRORS" in out

    def test_returns_one_on_semantic_failure(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        signoff = _basic_signoff(outcome="rejected", rejectionReason="too short")
        make_signoff_file(_signoff_file(signoffs=[signoff]))
        rc = srs.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "rejectionReason" in out

    def test_missing_data_file_exits_one(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            srs.main([])
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "signoff file not found" in err

    def test_argv_ignored(
        self,
        make_signoff_file: MakeSignoffFile,
        fake_repo: pathlib.Path,
    ) -> None:
        # main() declares `del argv`, so passing arbitrary garbage is fine.
        make_signoff_file(_signoff_file())
        rc = srs.main(["--unknown", "flag", "extra"])
        assert rc == 0
