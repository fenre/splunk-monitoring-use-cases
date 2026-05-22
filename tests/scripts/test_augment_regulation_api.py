"""Hermetic coverage for ``scripts/augment_regulation_api.py``.

The script is the Phase 2b post-processor that injects
``clauseCoverageMatrix[]``, ``clausesReferencedByCatalogue[]``,
``useCasesTaggingThisVersion[]``, and per-version
``coverageSummary`` into every regulation file emitted by
``python3 -m splunk_uc generate-api-surface``. It also re-roots the
catalogue rollup on ``regulations/index.json``.

CI exercises this module only via the full ``generate-api-surface``
chain (which fans out into a large temp tree), so the script's unit
seams were previously untested — 57.1 % line coverage on a 254-stmt
file. This suite drives every helper, the file-by-file augmentation
functions, the orchestrator, the drift checker, and the CLI through
hermetic fixtures rooted at ``tmp_path``. No network, no real
``api/v1`` tree, no shared state.

Most tests load the module dynamically via ``importlib.util`` so we
never pollute ``sys.modules`` with the script's top-level constants
that point at the real repo paths.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


# --------------------------------------------------------------------------- #
# Module import — load the script as a normal Python module so we can call
# its functions directly AND coverage can track it under the canonical
# ``augment_regulation_api`` name.
# --------------------------------------------------------------------------- #


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "augment_regulation_api.py"

_spec = importlib.util.spec_from_file_location(
    "augment_regulation_api", _SCRIPT_PATH
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("augment_regulation_api", _mod)
_spec.loader.exec_module(_mod)


@pytest.fixture(scope="module")
def ara() -> Any:
    return _mod


# --------------------------------------------------------------------------- #
# Fixture builders.
# --------------------------------------------------------------------------- #


def _clause_index(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a minimal valid ``api/v1/compliance/clauses/index.json``
    payload. Default ``rows`` cover one regulation × one version with a
    mix of full/partial/contributing/uncovered states."""
    return {
        "clauses": rows
        if rows is not None
        else [
            {
                "regulationId": "demo-reg",
                "version": "2024",
                "clause": "1.1",
                "topic": "Logging",
                "priorityWeight": 10.0,
                "coveringUcs": ["UC-1.1.1", "UC-1.1.2"],
                "assuranceBreakdown": {"full": 2, "partial": 0, "contributing": 0},
                "coverageState": "covered-full",
                "topAssurance": "full",
            },
            {
                "regulationId": "demo-reg",
                "version": "2024",
                "clause": "1.2",
                "topic": "Access",
                "priorityWeight": 5.0,
                "coveringUcs": ["UC-1.1.3"],
                "assuranceBreakdown": {"full": 0, "partial": 1, "contributing": 0},
                "coverageState": "covered-partial",
                "topAssurance": "partial",
            },
            {
                "regulationId": "demo-reg",
                "version": "2024",
                "clause": "1.3",  # off-common-list (not in commonClauses)
                "topic": "Backups",
                "priorityWeight": 1.0,
                "coveringUcs": ["UC-2.1.1"],
                "assuranceBreakdown": {"full": 0, "partial": 0, "contributing": 1},
                "coverageState": "contributing-only",
                "topAssurance": "contributing",
            },
        ]
    }


def _reg_payload(
    *,
    common_clauses: list[dict[str, Any]] | None = None,
    extra_versions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal regulation payload with one version and the
    canonical ``commonClauses`` shape used in the live data."""
    versions = [
        {
            "version": "2024",
            "commonClauses": common_clauses
            if common_clauses is not None
            else [
                {
                    "clause": "1.1",
                    "topic": "Logging",
                    "priorityWeight": 10.0,
                    "obligationText": "Must keep audit logs.",
                    "obligationSource": "demo-reg §1.1",
                },
                {
                    "clause": "1.2",
                    "topic": "Access",
                    "priorityWeight": 5.0,
                    "obligationText": "Must restrict access.",
                    "obligationSource": "demo-reg §1.2",
                },
                {
                    "clause": "1.4",
                    "topic": "Encryption",
                    "priorityWeight": 7.0,
                    "obligationText": "Must encrypt PII.",
                    "obligationSource": "demo-reg §1.4",
                },
            ],
        }
    ]
    if extra_versions:
        versions.extend(extra_versions)
    return {"id": "demo-reg", "versions": versions}


def _slice_payload(
    *,
    version: str = "2024",
    common_clauses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": "demo-reg",
        "version": {
            "version": version,
            "commonClauses": common_clauses
            if common_clauses is not None
            else [
                {
                    "clause": "1.1",
                    "topic": "Logging",
                    "priorityWeight": 10.0,
                    "obligationText": "Must keep audit logs.",
                    "obligationSource": "demo-reg §1.1",
                },
            ],
        },
    }


def _index_payload() -> dict[str, Any]:
    return {
        "frameworks": [
            {"id": "demo-reg", "label": "Demo Regulation"},
            {"id": 12345, "label": "Bad ID (non-string)"},
            "not-a-mapping",
        ]
    }


def _seed_tree(
    tmp_path: Path,
    *,
    clause_rows: list[dict[str, Any]] | None = None,
    include_slice: bool = True,
    include_index: bool = True,
) -> tuple[Path, Path]:
    """Lay out a tmp api/v1/compliance/{clauses,regulations}/ tree and
    return ``(reg_root, clauses_dir)``."""
    api = tmp_path / "api" / "v1" / "compliance"
    clauses = api / "clauses"
    regs = api / "regulations"
    clauses.mkdir(parents=True)
    regs.mkdir(parents=True)
    (clauses / "index.json").write_text(
        json.dumps(_clause_index(clause_rows)), encoding="utf-8"
    )
    (regs / "demo-reg.json").write_text(
        json.dumps(_reg_payload()), encoding="utf-8"
    )
    if include_slice:
        (regs / "demo-reg@2024.json").write_text(
            json.dumps(_slice_payload()), encoding="utf-8"
        )
    if include_index:
        (regs / "index.json").write_text(
            json.dumps(_index_payload()), encoding="utf-8"
        )
    return regs, clauses


# --------------------------------------------------------------------------- #
# IO helpers.
# --------------------------------------------------------------------------- #


class TestIOHelpers:
    def test_load_json_round_trip(self, ara: Any, tmp_path: Path) -> None:
        path = tmp_path / "data.json"
        path.write_text(json.dumps({"k": "v"}), encoding="utf-8")
        assert ara._load_json(path) == {"k": "v"}

    def test_write_json_creates_parent_and_trailing_newline(
        self, ara: Any, tmp_path: Path
    ) -> None:
        path = tmp_path / "new" / "nested" / "out.json"
        ara._write_json(path, {"x": 1, "y": 2})
        text = path.read_text(encoding="utf-8")
        # Sort-keys + indent=2 + trailing newline.
        assert text.endswith("\n")
        assert text.splitlines()[0] == "{"
        assert json.loads(text) == {"x": 1, "y": 2}

    def test_write_json_is_deterministic(self, ara: Any, tmp_path: Path) -> None:
        """Two writes of the same payload produce byte-identical files."""
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        payload = {"b": [1, 2, 3], "a": "x"}
        ara._write_json(a, payload)
        ara._write_json(b, payload)
        assert a.read_bytes() == b.read_bytes()


# --------------------------------------------------------------------------- #
# load_clause_index / group_clauses_by_regulation_version.
# --------------------------------------------------------------------------- #


class TestLoadClauseIndex:
    def test_returns_rows(self, ara: Any, tmp_path: Path) -> None:
        (tmp_path / "index.json").write_text(
            json.dumps(_clause_index()), encoding="utf-8"
        )
        rows = ara.load_clause_index(tmp_path)
        assert len(rows) == 3
        assert rows[0]["clause"] == "1.1"

    def test_raises_system_exit_when_index_missing(
        self, ara: Any, tmp_path: Path
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            ara.load_clause_index(tmp_path)
        assert "missing" in str(exc.value)

    def test_raises_system_exit_when_clauses_not_a_list(
        self, ara: Any, tmp_path: Path
    ) -> None:
        (tmp_path / "index.json").write_text(
            json.dumps({"clauses": "not-a-list"}), encoding="utf-8"
        )
        with pytest.raises(SystemExit) as exc:
            ara.load_clause_index(tmp_path)
        assert "no 'clauses' array" in str(exc.value)

    def test_missing_clauses_key_treated_as_empty(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """When ``clauses`` is missing entirely, ``rows or []`` makes
        the function return an empty list rather than crash."""
        (tmp_path / "index.json").write_text(
            json.dumps({"unrelated": "field"}), encoding="utf-8"
        )
        rows = ara.load_clause_index(tmp_path)
        assert rows == []


class TestGroupClausesByRegulationVersion:
    def test_groups_by_reg_and_version(self, ara: Any) -> None:
        rows = [
            {"regulationId": "a", "version": "v1", "clause": "1"},
            {"regulationId": "a", "version": "v1", "clause": "2"},
            {"regulationId": "a", "version": "v2", "clause": "3"},
            {"regulationId": "b", "version": "v1", "clause": "4"},
        ]
        out = ara.group_clauses_by_regulation_version(rows)
        assert len(out[("a", "v1")]) == 2
        assert len(out[("a", "v2")]) == 1
        assert len(out[("b", "v1")]) == 1

    def test_skips_rows_without_string_reg_id(self, ara: Any) -> None:
        rows = [
            {"regulationId": None, "version": "v1", "clause": "x"},
            {"regulationId": 42, "version": "v1", "clause": "x"},
            {"regulationId": "ok", "version": "v1", "clause": "x"},
        ]
        out = ara.group_clauses_by_regulation_version(rows)
        assert list(out.keys()) == [("ok", "v1")]

    def test_skips_rows_without_string_version(self, ara: Any) -> None:
        rows = [
            {"regulationId": "ok", "version": None, "clause": "x"},
            {"regulationId": "ok", "version": "v1", "clause": "x"},
        ]
        out = ara.group_clauses_by_regulation_version(rows)
        assert list(out.keys()) == [("ok", "v1")]


# --------------------------------------------------------------------------- #
# _coverage_state_from_assurance / _better_assurance / _stronger_coverage_state.
# --------------------------------------------------------------------------- #


class TestCoverageStateFromAssurance:
    @pytest.mark.parametrize(
        ("top", "expected"),
        [
            ("full", "covered-full"),
            ("partial", "covered-partial"),
            ("contributing", "contributing-only"),
            (None, "uncovered"),
            ("bogus", "uncovered"),
            ("", "uncovered"),
        ],
    )
    def test_mapping(self, ara: Any, top: str | None, expected: str) -> None:
        assert ara._coverage_state_from_assurance(top) == expected


class TestBetterAssurance:
    def test_prefers_higher_rank(self, ara: Any) -> None:
        assert ara._better_assurance("partial", "full") == "full"
        assert ara._better_assurance("full", "partial") == "full"
        assert ara._better_assurance("contributing", "partial") == "partial"

    def test_returns_other_when_first_falsy(self, ara: Any) -> None:
        assert ara._better_assurance(None, "partial") == "partial"
        assert ara._better_assurance("", "partial") == "partial"

    def test_returns_first_when_second_falsy(self, ara: Any) -> None:
        assert ara._better_assurance("partial", None) == "partial"
        assert ara._better_assurance("partial", "") == "partial"

    def test_equal_rank_keeps_first(self, ara: Any) -> None:
        assert ara._better_assurance("full", "full") == "full"


class TestStrongerCoverageState:
    def test_picks_higher_rank(self, ara: Any) -> None:
        assert ara._stronger_coverage_state("uncovered", "covered-full") == "covered-full"
        assert ara._stronger_coverage_state("covered-full", "uncovered") == "covered-full"
        assert (
            ara._stronger_coverage_state("contributing-only", "covered-partial")
            == "covered-partial"
        )

    def test_treats_none_as_uncovered(self, ara: Any) -> None:
        assert ara._stronger_coverage_state(None, "covered-full") == "covered-full"
        assert ara._stronger_coverage_state("covered-partial", None) == "covered-partial"


# --------------------------------------------------------------------------- #
# build_clause_coverage_matrix.
# --------------------------------------------------------------------------- #


class TestBuildClauseCoverageMatrix:
    def test_common_clauses_seed_the_matrix(self, ara: Any) -> None:
        ver = {
            "commonClauses": [
                {
                    "clause": "1.1",
                    "topic": "T",
                    "priorityWeight": 5.0,
                    "obligationText": "txt",
                    "obligationSource": "src",
                },
            ]
        }
        out = ara.build_clause_coverage_matrix(ver, [])
        assert len(out) == 1
        row = out[0]
        assert row["clause"] == "1.1"
        assert row["onCommonList"] is True
        assert row["coveringUcs"] == []
        assert row["coverageState"] == "uncovered"

    def test_off_common_list_clauses_appended(self, ara: Any) -> None:
        ver = {"commonClauses": [{"clause": "1.1", "priorityWeight": 5}]}
        reg_rows = [
            {
                "clause": "2.1",
                "topic": "Off list",
                "priorityWeight": 2.0,
                "coveringUcs": ["UC-X"],
                "assuranceBreakdown": {"full": 1, "partial": 0, "contributing": 0},
                "coverageState": "covered-full",
                "topAssurance": "full",
            }
        ]
        out = ara.build_clause_coverage_matrix(ver, reg_rows)
        # 2 rows: 1.1 (common) and 2.1 (off-list), sorted on/off then clause
        assert len(out) == 2
        assert out[0]["clause"] == "1.1"
        assert out[0]["onCommonList"] is True
        assert out[1]["clause"] == "2.1"
        assert out[1]["onCommonList"] is False
        assert out[1]["topAssurance"] == "full"
        assert out[1]["coverageState"] == "covered-full"

    def test_matching_common_clause_updates_in_place(self, ara: Any) -> None:
        ver = {
            "commonClauses": [
                {
                    "clause": "1.1",
                    "topic": "Logging",
                    "priorityWeight": 10.0,
                    "obligationText": "T",
                    "obligationSource": "S",
                },
            ]
        }
        reg_rows = [
            {
                "clause": "1.1",
                "coveringUcs": ["UC-1.1.1"],
                "assuranceBreakdown": {"full": 1, "partial": 0, "contributing": 0},
                "coverageState": "covered-full",
                "topAssurance": "full",
            }
        ]
        out = ara.build_clause_coverage_matrix(ver, reg_rows)
        assert out[0]["coveringUcs"] == ["UC-1.1.1"]
        assert out[0]["coverageState"] == "covered-full"
        assert out[0]["topAssurance"] == "full"
        assert out[0]["assuranceBreakdown"] == {"full": 1, "partial": 0, "contributing": 0}

    def test_skips_rows_without_string_clause(self, ara: Any) -> None:
        ver = {"commonClauses": [{"clause": None}, {"clause": "1.1", "priorityWeight": 5}]}
        reg_rows = [{"clause": None, "coveringUcs": ["X"]}]
        out = ara.build_clause_coverage_matrix(ver, reg_rows)
        # Only the valid 1.1 entry survives.
        assert [r["clause"] for r in out] == ["1.1"]

    def test_no_covering_ucs_forces_uncovered(self, ara: Any) -> None:
        """A common-list clause with empty ``coveringUcs`` must be
        normalised to ``uncovered`` even if the seed row carried a
        ``topAssurance`` value somehow."""
        ver = {"commonClauses": [{"clause": "1.1", "priorityWeight": 1}]}
        reg_rows = [
            {
                "clause": "1.1",
                "coveringUcs": [],
                "topAssurance": "full",
                "coverageState": "covered-full",
            }
        ]
        out = ara.build_clause_coverage_matrix(ver, reg_rows)
        assert out[0]["coveringUcs"] == []
        assert out[0]["coverageState"] == "uncovered"
        assert out[0]["topAssurance"] is None

    def test_top_assurance_recovers_when_state_is_only_uncovered(
        self, ara: Any
    ) -> None:
        """An off-list clause whose seed coverageState is missing/uncovered
        but whose topAssurance is known should get the derived state."""
        ver = {"commonClauses": []}
        reg_rows = [
            {
                "clause": "2.1",
                "coveringUcs": ["UC-X"],
                "topAssurance": "partial",
                # No coverageState set, so the empty-string-or-None
                # rebound runs.
            }
        ]
        out = ara.build_clause_coverage_matrix(ver, reg_rows)
        assert out[0]["coverageState"] == "covered-partial"


# --------------------------------------------------------------------------- #
# build_coverage_summary.
# --------------------------------------------------------------------------- #


class TestBuildCoverageSummary:
    def test_basic_rollup(self, ara: Any) -> None:
        matrix = [
            {
                "clause": "1.1",
                "onCommonList": True,
                "priorityWeight": 10.0,
                "topAssurance": "full",
                "coverageState": "covered-full",
                "coveringUcs": ["UC-X"],
            },
            {
                "clause": "1.2",
                "onCommonList": True,
                "priorityWeight": 5.0,
                "topAssurance": "partial",
                "coverageState": "covered-partial",
                "coveringUcs": ["UC-Y"],
            },
            {
                "clause": "1.3",
                "onCommonList": True,
                "priorityWeight": 2.0,
                "topAssurance": "contributing",
                "coverageState": "contributing-only",
                "coveringUcs": ["UC-Z"],
            },
            {
                "clause": "1.4",
                "onCommonList": True,
                "priorityWeight": 1.0,
                "topAssurance": None,
                "coverageState": "uncovered",
                "coveringUcs": [],
            },
            # Off-common-list rows count for offCommonListClauseCount only.
            {
                "clause": "2.1",
                "onCommonList": False,
                "priorityWeight": 1.0,
                "topAssurance": "full",
                "coverageState": "covered-full",
                "coveringUcs": ["UC-OFF"],
            },
        ]
        out = ara.build_coverage_summary(matrix)
        assert out["commonClauseCount"] == 4
        assert out["coveredClauseCount"] == 3  # everything but the uncovered 1.4
        assert out["stateCounts"] == {
            "covered-full": 1,
            "covered-partial": 1,
            "contributing-only": 1,
            "uncovered": 1,
        }
        # 10 + 5 + 2 + 1 = 18 priority weight; covered = 10*1.0 + 5*0.5 + 2*0.25 = 13
        assert out["clauseCoveragePercent"] == pytest.approx(75.0)
        # priority-weighted = 100 * 13 / 18 = 72.22…
        assert out["priorityWeightedCoveragePercent"] == pytest.approx(72.22)
        assert out["offCommonListClauseCount"] == 1

    def test_handles_empty_matrix(self, ara: Any) -> None:
        out = ara.build_coverage_summary([])
        assert out["commonClauseCount"] == 0
        assert out["coveredClauseCount"] == 0
        assert out["clauseCoveragePercent"] == 0.0
        assert out["priorityWeightedCoveragePercent"] == 0.0
        assert out["offCommonListClauseCount"] == 0
        assert out["stateCounts"] == {
            "covered-full": 0,
            "covered-partial": 0,
            "contributing-only": 0,
            "uncovered": 0,
        }

    def test_zero_priority_weight_does_not_divide_by_zero(self, ara: Any) -> None:
        matrix = [
            {
                "clause": "1.1",
                "onCommonList": True,
                "priorityWeight": 0,
                "topAssurance": "full",
                "coverageState": "covered-full",
                "coveringUcs": ["UC-X"],
            }
        ]
        out = ara.build_coverage_summary(matrix)
        assert out["priorityWeightedCoveragePercent"] == 0.0

    def test_unknown_state_label_is_routed_into_state_counts(self, ara: Any) -> None:
        """A row whose coverageState is not in the canonical four is
        still counted because ``state_counts.get(state, 0) + 1`` is
        used to update."""
        matrix = [
            {
                "clause": "1.1",
                "onCommonList": True,
                "priorityWeight": 1.0,
                "topAssurance": "full",
                "coverageState": "weird-state",
                "coveringUcs": ["UC-X"],
            }
        ]
        out = ara.build_coverage_summary(matrix)
        # Falls through to setdefault-style add — surfaces under the
        # custom key.
        assert out["stateCounts"]["weird-state"] == 1
        # The "weird-state" is also non-"uncovered", so coveredClauseCount fires.
        assert out["coveredClauseCount"] == 1


# --------------------------------------------------------------------------- #
# version_slug.
# --------------------------------------------------------------------------- #


class TestVersionSlug:
    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("2024", "2024"),
            ("v1.0", "v1.0"),
            ("ISO/IEC", "ISO-IEC"),
            ("UK GDPR", "UK-GDPR"),
            ("rev A.1", "rev-A.1"),
            ("foo bar/baz", "foo-bar-baz"),
            ("(2024-rev)", "(2024-rev)"),
        ],
    )
    def test_slug_for_various_versions(
        self, ara: Any, version: str, expected: str
    ) -> None:
        assert ara.version_slug(version) == expected

    def test_url_escapes_unsafe_chars(self, ara: Any) -> None:
        # ``%`` is unsafe and gets encoded.
        slug = ara.version_slug("100%")
        assert slug == "100%25"


# --------------------------------------------------------------------------- #
# augment_regulation_file.
# --------------------------------------------------------------------------- #


class TestAugmentRegulationFile:
    def test_writes_matrix_and_coverage_fields(
        self, ara: Any, tmp_path: Path
    ) -> None:
        reg_path = tmp_path / "demo-reg.json"
        reg_path.write_text(json.dumps(_reg_payload()), encoding="utf-8")
        rows_by_rv = ara.group_clauses_by_regulation_version(
            _clause_index()["clauses"]
        )
        matrices = ara.augment_regulation_file(reg_path, rows_by_rv)
        assert "2024" in matrices
        payload = json.loads(reg_path.read_text(encoding="utf-8"))
        v = payload["versions"][0]
        assert "clauseCoverageMatrix" in v
        assert "clausesReferencedByCatalogue" in v
        assert "useCasesTaggingThisVersion" in v
        assert "coverageSummary" in v
        # The clauses referenced are sorted and de-duplicated.
        assert v["clausesReferencedByCatalogue"] == sorted(
            v["clausesReferencedByCatalogue"]
        )
        assert v["useCasesTaggingThisVersion"] == sorted(
            v["useCasesTaggingThisVersion"]
        )

    def test_skips_when_id_missing_or_non_string(
        self, ara: Any, tmp_path: Path
    ) -> None:
        path = tmp_path / "noid.json"
        path.write_text(json.dumps({"id": 42, "versions": []}), encoding="utf-8")
        assert ara.augment_regulation_file(path, {}) == {}

    def test_skips_when_versions_not_a_list(
        self, ara: Any, tmp_path: Path
    ) -> None:
        path = tmp_path / "demo.json"
        path.write_text(
            json.dumps({"id": "demo", "versions": "not-a-list"}),
            encoding="utf-8",
        )
        assert ara.augment_regulation_file(path, {}) == {}

    def test_skips_non_mapping_version_entries(
        self, ara: Any, tmp_path: Path
    ) -> None:
        payload = {"id": "demo", "versions": ["not-a-dict", {"version": 999}]}
        path = tmp_path / "demo.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        out = ara.augment_regulation_file(path, {})
        # Both entries get skipped — non-dict, non-string version.
        assert out == {}


# --------------------------------------------------------------------------- #
# augment_single_version_file.
# --------------------------------------------------------------------------- #


class TestAugmentSingleVersionFile:
    def test_writes_matrix_into_slice(self, ara: Any, tmp_path: Path) -> None:
        path = tmp_path / "demo-reg@2024.json"
        path.write_text(json.dumps(_slice_payload()), encoding="utf-8")
        matrices = {
            "2024": [
                {
                    "clause": "1.1",
                    "topic": "Logging",
                    "priorityWeight": 10.0,
                    "onCommonList": True,
                    "topAssurance": "full",
                    "coverageState": "covered-full",
                    "coveringUcs": ["UC-1.1.1"],
                }
            ]
        }
        ara.augment_single_version_file(path, "demo-reg", matrices, "2024")
        v = json.loads(path.read_text(encoding="utf-8"))["version"]
        assert v["clauseCoverageMatrix"][0]["clause"] == "1.1"
        assert v["clausesReferencedByCatalogue"] == ["1.1"]
        assert v["useCasesTaggingThisVersion"] == ["UC-1.1.1"]
        assert "coverageSummary" in v

    def test_noops_when_slice_missing(self, ara: Any, tmp_path: Path) -> None:
        # Function returns None — and must not crash on missing file.
        ara.augment_single_version_file(
            tmp_path / "missing.json", "demo-reg", {}, "2024"
        )

    def test_noops_when_version_not_a_mapping(self, ara: Any, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text(
            json.dumps({"id": "demo-reg", "version": "string-not-dict"}),
            encoding="utf-8",
        )
        ara.augment_single_version_file(path, "demo-reg", {}, "2024")
        # File unchanged.
        assert json.loads(path.read_text(encoding="utf-8"))["version"] == "string-not-dict"


# --------------------------------------------------------------------------- #
# augment_regulations_index.
# --------------------------------------------------------------------------- #


class TestAugmentRegulationsIndex:
    def test_writes_catalogue_coverage_summary(
        self, ara: Any, tmp_path: Path
    ) -> None:
        reg_root, _ = _seed_tree(tmp_path)
        # Pre-augment the per-reg file so the index reads its summaries.
        rows_by_rv = ara.group_clauses_by_regulation_version(
            _clause_index()["clauses"]
        )
        ara.augment_regulation_file(reg_root / "demo-reg.json", rows_by_rv)
        ara.augment_regulations_index(reg_root, rows_by_rv)
        idx = json.loads((reg_root / "index.json").read_text(encoding="utf-8"))
        assert "catalogueCoverageSummary" in idx
        assert "demo-reg" in idx["catalogueCoverageSummary"]
        rollup = idx["catalogueCoverageSummary"]["demo-reg"]
        assert {"commonClauseCount", "coveredClauseCount", "uncoveredClauseCount",
                "priorityWeightedCoverageMean"} <= rollup.keys()

    def test_noops_when_index_missing(self, ara: Any, tmp_path: Path) -> None:
        reg_root = tmp_path / "regs"
        reg_root.mkdir()
        # No index.json present.
        ara.augment_regulations_index(reg_root, {})
        assert not (reg_root / "index.json").exists()

    def test_skips_non_mapping_frameworks_and_non_string_ids(
        self, ara: Any, tmp_path: Path
    ) -> None:
        reg_root, _ = _seed_tree(tmp_path)
        # Pre-augment so demo-reg has a coverageSummary.
        rows_by_rv = ara.group_clauses_by_regulation_version(
            _clause_index()["clauses"]
        )
        ara.augment_regulation_file(reg_root / "demo-reg.json", rows_by_rv)
        # Index already contains a non-string id and a non-mapping
        # entry from ``_index_payload`` — neither should error.
        ara.augment_regulations_index(reg_root, rows_by_rv)
        idx = json.loads((reg_root / "index.json").read_text(encoding="utf-8"))
        # The valid demo-reg framework is the only one with a rollup.
        assert list(idx["catalogueCoverageSummary"].keys()) == ["demo-reg"]

    def test_priority_weighted_coverage_mean_stays_zero_when_no_pw_values(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """Covers the ``False`` arm of ``if pw_vals:`` (391->393).

        Hand-crafts a per-regulation file whose ``coverageSummary``
        omits ``priorityWeightedCoveragePercent`` so the appender on
        line 390 never fires and the mean stays at its initial 0.0.
        """
        api = tmp_path / "api" / "v1" / "compliance"
        regs = api / "regulations"
        regs.mkdir(parents=True)
        # Index points at the single demo-reg framework.
        (regs / "index.json").write_text(
            json.dumps({"frameworks": [{"id": "demo-reg", "label": "Demo"}]}),
            encoding="utf-8",
        )
        # Hand-rolled per-reg file with a coverageSummary that lacks
        # priorityWeightedCoveragePercent. Other counters are present.
        (regs / "demo-reg.json").write_text(
            json.dumps(
                {
                    "id": "demo-reg",
                    "versions": [
                        {
                            "version": "2024",
                            "coverageSummary": {
                                "commonClauseCount": 5,
                                "coveredClauseCount": 2,
                                # priorityWeightedCoveragePercent omitted.
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        ara.augment_regulations_index(regs, {})
        idx = json.loads((regs / "index.json").read_text(encoding="utf-8"))
        rollup = idx["catalogueCoverageSummary"]["demo-reg"]
        assert rollup["priorityWeightedCoverageMean"] == 0.0
        assert rollup["commonClauseCount"] == 5
        assert rollup["coveredClauseCount"] == 2
        assert rollup["uncoveredClauseCount"] == 3

    def test_priority_weighted_value_with_non_numeric_pw_is_ignored(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """A non-numeric ``priorityWeightedCoveragePercent`` (string)
        is skipped by the ``isinstance(pw, (int, float))`` filter and
        the mean stays zero — same end state as the missing-key case
        but through the False arm of the isinstance guard."""
        regs = tmp_path / "regs"
        regs.mkdir()
        (regs / "index.json").write_text(
            json.dumps({"frameworks": [{"id": "demo-reg", "label": "Demo"}]}),
            encoding="utf-8",
        )
        (regs / "demo-reg.json").write_text(
            json.dumps(
                {
                    "id": "demo-reg",
                    "versions": [
                        {
                            "version": "2024",
                            "coverageSummary": {
                                "commonClauseCount": 3,
                                "coveredClauseCount": 1,
                                "priorityWeightedCoveragePercent": "not-a-number",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        ara.augment_regulations_index(regs, {})
        rollup = json.loads((regs / "index.json").read_text())[
            "catalogueCoverageSummary"
        ]["demo-reg"]
        assert rollup["priorityWeightedCoverageMean"] == 0.0


# --------------------------------------------------------------------------- #
# augment_all + main + _check_drift.
# --------------------------------------------------------------------------- #


class TestAugmentAll:
    def test_happy_path_writes_all_three_artefacts(
        self, ara: Any, tmp_path: Path
    ) -> None:
        reg_root, clauses = _seed_tree(tmp_path)
        ara.augment_all(reg_root, clauses_dir=clauses)
        # The reg file now has the matrix.
        v = json.loads((reg_root / "demo-reg.json").read_text())["versions"][0]
        assert "clauseCoverageMatrix" in v
        # The slice file too.
        s = json.loads((reg_root / "demo-reg@2024.json").read_text())["version"]
        assert "clauseCoverageMatrix" in s
        # The index file too.
        idx = json.loads((reg_root / "index.json").read_text())
        assert "catalogueCoverageSummary" in idx

    def test_missing_reg_root_raises_system_exit_with_relative_path(
        self, ara: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When reg_root sits under the configured REPO_ROOT the error
        message uses the relative form. We monkeypatch REPO_ROOT so
        ``tmp_path`` looks like it's under the repo for this test."""
        monkeypatch.setattr(ara, "REPO_ROOT", tmp_path)
        missing = tmp_path / "missing-regs"
        with pytest.raises(SystemExit) as exc:
            ara.augment_all(missing)
        # Relative form contains just the leaf, not the absolute path.
        assert "missing-regs" in str(exc.value)

    def test_missing_reg_root_falls_back_to_absolute_when_outside_repo(
        self, ara: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Covers the ``except ValueError`` arm of relative_to() —
        when reg_root cannot be expressed relative to REPO_ROOT."""
        monkeypatch.setattr(ara, "REPO_ROOT", tmp_path / "elsewhere")
        missing = tmp_path / "missing-regs"
        with pytest.raises(SystemExit) as exc:
            ara.augment_all(missing)
        assert "missing-regs" in str(exc.value)

    def test_skips_slice_files_and_index_during_walk(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """Slice files (``demo@v.json``) and ``index.json`` must not
        be treated as standalone regulation payloads."""
        reg_root, clauses = _seed_tree(tmp_path)
        # If the slice were misinterpreted, augment_regulation_file
        # would crash on its non-canonical 'version' field shape.
        ara.augment_all(reg_root, clauses_dir=clauses)
        # And the per-reg path now carries the matrix.
        v = json.loads((reg_root / "demo-reg.json").read_text())["versions"][0]
        assert "clauseCoverageMatrix" in v

    def test_skips_reg_payloads_with_non_string_id(
        self, ara: Any, tmp_path: Path
    ) -> None:
        reg_root, clauses = _seed_tree(tmp_path)
        # Drop a stray reg file with a non-string id.
        (reg_root / "noid.json").write_text(
            json.dumps({"id": None, "versions": []}), encoding="utf-8"
        )
        ara.augment_all(reg_root, clauses_dir=clauses)
        # File unchanged.
        loaded = json.loads((reg_root / "noid.json").read_text())
        assert "versions" in loaded
        # No matrix was injected because the loop skipped the payload.
        assert "clauseCoverageMatrix" not in loaded

    def test_skips_version_entries_with_non_string_version(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """The orchestrator's second pass (slice augmentation) also
        guards against non-string version entries."""
        reg_root, clauses = _seed_tree(tmp_path)
        # Splice in an extra version with a non-string label.
        path = reg_root / "demo-reg.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["versions"].append({"version": 42})
        path.write_text(json.dumps(payload), encoding="utf-8")
        # Should not crash.
        ara.augment_all(reg_root, clauses_dir=clauses)

    def test_clauses_dir_auto_resolved_from_reg_root(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """When ``clauses_dir`` is None and reg_root is not the default,
        the script looks for a sibling ``clauses/`` directory."""
        reg_root, _ = _seed_tree(tmp_path)
        # Pass no clauses_dir — function should find sibling `clauses/`.
        ara.augment_all(reg_root)
        v = json.loads((reg_root / "demo-reg.json").read_text())["versions"][0]
        assert "clauseCoverageMatrix" in v


# --------------------------------------------------------------------------- #
# _hash_tree.
# --------------------------------------------------------------------------- #


class TestHashTree:
    def test_returns_constant_for_missing_root(
        self, ara: Any, tmp_path: Path
    ) -> None:
        # Empty SHA-256 of nothing is a known constant.
        out = ara._hash_tree(tmp_path / "missing")
        assert isinstance(out, str)
        assert len(out) == 64

    def test_identical_trees_hash_same(self, ara: Any, tmp_path: Path) -> None:
        for sub in ("a", "b"):
            d = tmp_path / sub
            d.mkdir()
            (d / "file.txt").write_text("content", encoding="utf-8")
        assert ara._hash_tree(tmp_path / "a") == ara._hash_tree(tmp_path / "b")

    def test_different_content_changes_hash(
        self, ara: Any, tmp_path: Path
    ) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "f.txt").write_text("x", encoding="utf-8")
        (b / "f.txt").write_text("y", encoding="utf-8")
        assert ara._hash_tree(a) != ara._hash_tree(b)

    def test_different_paths_change_hash(self, ara: Any, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "f.txt").write_text("x", encoding="utf-8")
        (b / "g.txt").write_text("x", encoding="utf-8")
        assert ara._hash_tree(a) != ara._hash_tree(b)

    def test_directory_entries_are_skipped(
        self, ara: Any, tmp_path: Path
    ) -> None:
        """Covers the False arm of ``if p.is_file()`` (450->449): when
        ``rglob('*')`` yields a directory, the loop must move on
        without folding it into the hash.

        We assert this by comparing a tree that contains one file +
        one empty subdirectory against the same tree without the
        subdirectory — hashes must match if directories are ignored.
        """
        a = tmp_path / "with-dir"
        b = tmp_path / "without-dir"
        a.mkdir()
        b.mkdir()
        (a / "f.txt").write_text("content", encoding="utf-8")
        (a / "emptydir").mkdir()
        (b / "f.txt").write_text("content", encoding="utf-8")
        assert ara._hash_tree(a) == ara._hash_tree(b)


# --------------------------------------------------------------------------- #
# _check_drift + main.
# --------------------------------------------------------------------------- #


class TestCheckDrift:
    def _wire(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Path:
        reg_root, clauses = _seed_tree(tmp_path)
        # Pre-augment so the committed tree matches the regenerated one.
        ara.augment_all(reg_root, clauses_dir=clauses)
        # Point the script's globals at our tmp tree.
        monkeypatch.setattr(ara, "REGS_DIR", reg_root)
        monkeypatch.setattr(ara, "CLAUSES_DIR", clauses)
        return reg_root

    def test_no_drift_returns_zero(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._wire(ara, tmp_path, monkeypatch)
        rc = ara._check_drift()
        assert rc == 0
        err = capsys.readouterr().err
        assert "up to date" in err

    def test_drift_returns_one(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        reg_root = self._wire(ara, tmp_path, monkeypatch)
        # Corrupt one of the augmented files so the temp regen diverges.
        bad = reg_root / "demo-reg.json"
        payload = json.loads(bad.read_text(encoding="utf-8"))
        payload["versions"][0]["clauseCoverageMatrix"] = "STALE"
        bad.write_text(json.dumps(payload), encoding="utf-8")
        rc = ara._check_drift()
        assert rc == 1
        err = capsys.readouterr().err
        assert "out of date" in err


class TestMainCli:
    def _wire(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Path:
        reg_root, clauses = _seed_tree(tmp_path)
        monkeypatch.setattr(ara, "REGS_DIR", reg_root)
        monkeypatch.setattr(ara, "CLAUSES_DIR", clauses)
        return reg_root

    def test_default_run_returns_zero(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._wire(ara, tmp_path, monkeypatch)
        rc = ara.main([])
        assert rc == 0
        err = capsys.readouterr().err
        assert "Augmented" in err

    def test_check_mode_passes_when_in_sync(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        reg_root = self._wire(ara, tmp_path, monkeypatch)
        # Pre-augment.
        ara.augment_all(reg_root, clauses_dir=reg_root.parent / "clauses")
        rc = ara.main(["--check"])
        assert rc == 0

    def test_unexpected_exception_returns_2(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Force ``augment_all`` to raise a non-SystemExit exception
        so the catch-all path runs."""

        def boom(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("synthetic")

        monkeypatch.setattr(ara, "augment_all", boom)
        rc = ara.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "UNEXPECTED ERROR" in err

    def test_system_exit_from_augment_all_propagates(
        self,
        ara: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A SystemExit raised by augment_all (e.g., missing reg_root)
        should propagate, not be caught by the ``except Exception``."""

        def boom(*_args: Any, **_kwargs: Any) -> None:
            raise SystemExit("planned exit")

        monkeypatch.setattr(ara, "augment_all", boom)
        with pytest.raises(SystemExit):
            ara.main([])
