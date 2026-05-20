"""Unit tests for ``audit-compliance-mappings`` (P16 wave G).

The audit is the tier-1 compliance gate (Phase 1.5c of the Gold-Standard
plan): it validates UC sidecars against ``schemas/uc.schema.json``,
reconciles every ``compliance[]`` entry against ``data/regulations.json``,
runs the golden-tuple gate, computes the four-scope coverage metrics
(global / per-tier / per-family / per-version), and writes the JSON +
markdown reports that ``docs/coverage-methodology.md`` defines.

Before this wave the module had **16.60% line coverage** despite owning
several hundred lines of business logic that block every PR. The tests
in this file pin:

* the deterministic-timestamp resolver (``SOURCE_DATE_EPOCH`` /
  ``git log`` / wall-clock fallback);
* every dataclass invariant (``Finding.fingerprint``, ``Finding.to_dict``,
  ``ComplianceEntry.raw_multiplier``/``capped_multiplier``,
  ``ResolvedRef.key``);
* the ``RegulationsCatalogue`` index (alias resolution, version
  lookups, framework metadata, derivesFrom graph walks);
* every finding code emitted by ``_reconcile_compliance``
  (``unknown-regulation``, ``unknown-version``, ``clause-grammar``,
  ``assurance-invalid``, ``assurance-rationale-missing``,
  ``missing-control-objective``, ``missing-evidence-artifact``,
  ``mode-invalid``) plus the happy path;
* the metrics aggregator (``_metrics_for``,
  ``_build_coverage_by_version``, ``_compute_coverage``) on a handful
  of input shapes;
* the baseline mechanism (``_load_baseline``, ``_apply_baseline``,
  ``_write_baseline``) including the BASELINEABLE_CODES carve-out;
* the markdown rendering (``_markdown_for``) on payloads with and
  without baselined / blocking findings;
* the report writers (``_write_json_report``, ``_write_markdown_report``)
  in a tmp-path sandbox;
* the golden-tuple gate (``_run_golden_tests``) for the three
  observable outcomes (file missing, empty tuples, real run).

The fixtures are deliberately minimal so a change to the audit's
business logic produces a single, obvious test failure rather than
a cascade of brittle setup errors.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import compliance_mappings as cm
from splunk_uc.audits.compliance_mappings import (
    ASSURANCE_MULTIPLIER,
    ASSURANCE_RANK,
    BASELINEABLE_CODES,
    STATUS_CAP,
    AuditState,
    ComplianceEntry,
    Finding,
    Metrics,
    RegulationsCatalogue,
    RegVersion,
    ResolvedRef,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _good_regs() -> dict[str, Any]:
    """Stub regulations catalogue: two frameworks, one derivative chain."""

    return copy.deepcopy(
        {
            "frameworks": [
                {
                    "id": "iso-27001",
                    "name": "ISO/IEC 27001:2022",
                    "shortName": "ISO 27001",
                    "tier": 1,
                    "jurisdiction": ["global"],
                    "tags": ["isms"],
                    "aliases": ["ISO27001", "ISO/IEC 27001"],
                    "versions": [
                        {
                            "version": "2022",
                            "clauseGrammar": r"^A\.\d+\.\d+$",
                            "authoritativeUrl": "https://example.test/iso27001",
                            "commonClauses": [
                                {"clause": "A.5.1", "priorityWeight": 2.0},
                                {"clause": "A.8.1", "priorityWeight": 1.0},
                            ],
                        },
                        {
                            "version": "2013",
                            "clauseGrammar": r"^A\.\d+\.\d+$",
                            "commonClauses": [],
                        },
                    ],
                },
                {
                    "id": "soc-2",
                    "name": "AICPA SOC 2",
                    "shortName": "SOC 2",
                    "tier": 2,
                    "aliases": [],
                    "versions": [
                        {
                            "version": "2017",
                            "clauseGrammar": r"^CC\d+\.\d+$",
                            "commonClauses": [
                                {"clause": "CC1.1", "priorityWeight": 1.5},
                            ],
                        }
                    ],
                },
                {
                    "id": "iso-27002",
                    "name": "ISO/IEC 27002",
                    "shortName": "ISO 27002",
                    "tier": 3,
                    "versions": [
                        {
                            "version": "2022",
                            "clauseGrammar": r"^A\.\d+\.\d+$",
                            "commonClauses": [],
                        }
                    ],
                },
            ],
            "aliasIndex": {
                "iso 27001:2022": "iso-27001",
                "$comment": "should be skipped",
            },
            "derivesFrom": {
                "iso-27002": {"parent": "iso-27001"},
                "self-loop": {"parent": "self-loop"},
            },
        }
    )


def _good_catalogue() -> RegulationsCatalogue:
    return RegulationsCatalogue(_good_regs())


def _good_uc() -> dict[str, Any]:
    """Minimum-viable UC sidecar with one happy-path compliance entry."""

    return {
        "id": "1.1.1",
        "status": "verified",
        "compliance": [
            {
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.1",
                "mode": "satisfies",
                "assurance": "full",
                "assurance_rationale": "Implements ISMS leadership review.",
                "controlObjective": "Maintain documented information security policies.",
                "evidenceArtifact": "saved-search:policies/review",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Module-level constants — must remain stable contracts
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_assurance_multiplier_keys(self) -> None:
        assert ASSURANCE_MULTIPLIER == {"full": 1.0, "partial": 0.5, "contributing": 0.25}

    def test_assurance_rank_orders_levels(self) -> None:
        assert ASSURANCE_RANK == {"contributing": 0, "partial": 1, "full": 2}

    def test_status_cap_keys(self) -> None:
        assert set(STATUS_CAP) == {"verified", "community", "__unset__", "draft"}
        assert STATUS_CAP["draft"] == 0.0
        assert STATUS_CAP["verified"] == 1.0

    def test_baselineable_codes(self) -> None:
        assert {
            "equipment-orphan",
            "missing-control-objective",
            "missing-evidence-artifact",
            "unknown-version",
        } == BASELINEABLE_CODES

    def test_repo_root_is_three_levels_above_module(self) -> None:
        assert cm.REPO_ROOT.is_dir()
        assert (cm.REPO_ROOT / "schemas" / "uc.schema.json").is_file()


# ---------------------------------------------------------------------------
# _deterministic_timestamp
# ---------------------------------------------------------------------------


class TestDeterministicTimestamp:
    def test_uses_source_date_epoch_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
        assert cm._deterministic_timestamp() == "1970-01-01T00:00:00Z"

    def test_uses_source_date_epoch_with_spaces(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "  1700000000  ")
        ts = cm._deterministic_timestamp()
        assert ts.startswith("2023-")
        assert ts.endswith("Z")

    def test_falls_back_to_git_when_sde_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        ts = cm._deterministic_timestamp()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts) is not None

    def test_falls_back_to_wall_clock_when_git_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        import subprocess

        def _boom(*_: Any, **__: Any) -> None:
            raise FileNotFoundError("no git here")

        monkeypatch.setattr(subprocess, "run", _boom)
        ts = cm._deterministic_timestamp()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts) is not None

    def test_falls_back_to_wall_clock_on_git_called_process_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        import subprocess

        def _boom(*_: Any, **__: Any) -> None:
            raise subprocess.CalledProcessError(returncode=128, cmd=["git"])

        monkeypatch.setattr(subprocess, "run", _boom)
        ts = cm._deterministic_timestamp()
        assert ts.endswith("Z")

    def test_falls_back_to_wall_clock_on_git_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        import subprocess

        def _boom(*_: Any, **__: Any) -> None:
            raise subprocess.TimeoutExpired(cmd=["git"], timeout=3)

        monkeypatch.setattr(subprocess, "run", _boom)
        ts = cm._deterministic_timestamp()
        assert ts.endswith("Z")

    def test_falls_back_to_wall_clock_when_git_returns_non_digit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        import subprocess

        class _Fake:
            stdout = "not-a-timestamp\n"

        def _ok(*_: Any, **__: Any) -> _Fake:
            return _Fake()

        monkeypatch.setattr(subprocess, "run", _ok)
        ts = cm._deterministic_timestamp()
        assert ts.endswith("Z")

    def test_ignores_non_digit_source_date_epoch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "garbage")
        ts = cm._deterministic_timestamp()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts) is not None


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class TestDataClasses:
    def test_finding_to_dict(self) -> None:
        f = Finding(level="error", uc_id="1.1.1", code="x", message="m", path="p")
        assert f.to_dict() == {
            "level": "error",
            "uc": "1.1.1",
            "code": "x",
            "path": "p",
            "message": "m",
        }

    def test_finding_fingerprint_excludes_level(self) -> None:
        a = Finding(level="error", uc_id="1.1.1", code="x", message="m", path="p")
        b = Finding(level="baselined", uc_id="1.1.1", code="x", message="m", path="p")
        assert a.fingerprint() == b.fingerprint()

    def test_finding_fingerprint_includes_other_fields(self) -> None:
        a = Finding(level="error", uc_id="1.1.1", code="x", message="m", path="p")
        b = Finding(level="error", uc_id="1.1.2", code="x", message="m", path="p")
        c = Finding(level="error", uc_id="1.1.1", code="y", message="m", path="p")
        d = Finding(level="error", uc_id="1.1.1", code="x", message="z", path="p")
        e = Finding(level="error", uc_id="1.1.1", code="x", message="m", path="q")
        seen = {a.fingerprint(), b.fingerprint(), c.fingerprint(), d.fingerprint(), e.fingerprint()}
        assert len(seen) == 5

    def test_resolved_ref_key(self) -> None:
        r = ResolvedRef(framework_id="iso-27001", short_name="ISO 27001", tier=1, version="2022")
        assert r.key() == ("iso-27001", "2022")

    def test_compliance_entry_raw_multiplier_known(self) -> None:
        e = ComplianceEntry(
            uc_id="1",
            uc_status="verified",
            regulation="ISO 27001",
            version="2022",
            framework_id="iso-27001",
            tier=1,
            clause="A.5.1",
            mode="satisfies",
            assurance="full",
            rationale="r",
        )
        assert e.raw_multiplier == 1.0
        assert e.capped_multiplier == 1.0

    def test_compliance_entry_partial_at_community_keeps_partial(self) -> None:
        e = ComplianceEntry(
            uc_id="1",
            uc_status="community",
            regulation="ISO 27001",
            version="2022",
            framework_id="iso-27001",
            tier=1,
            clause="A.5.1",
            mode="satisfies",
            assurance="partial",
            rationale="r",
        )
        # min(0.5, 0.5) = 0.5
        assert e.capped_multiplier == 0.5

    def test_compliance_entry_full_at_community_caps_at_half(self) -> None:
        e = ComplianceEntry(
            uc_id="1",
            uc_status="community",
            regulation="ISO 27001",
            version="2022",
            framework_id="iso-27001",
            tier=1,
            clause="A.5.1",
            mode="satisfies",
            assurance="full",
            rationale="r",
        )
        # min(1.0, 0.5) = 0.5
        assert e.capped_multiplier == 0.5

    def test_compliance_entry_draft_status_zeros_out(self) -> None:
        e = ComplianceEntry(
            uc_id="1",
            uc_status="draft",
            regulation="ISO 27001",
            version="2022",
            framework_id="iso-27001",
            tier=1,
            clause="A.5.1",
            mode="satisfies",
            assurance="full",
            rationale="r",
        )
        assert e.capped_multiplier == 0.0

    def test_compliance_entry_unknown_status_zeros_out(self) -> None:
        e = ComplianceEntry(
            uc_id="1",
            uc_status="weird",
            regulation="ISO 27001",
            version="2022",
            framework_id="iso-27001",
            tier=1,
            clause="A.5.1",
            mode="satisfies",
            assurance="full",
            rationale="r",
        )
        # STATUS_CAP.get("weird", 0.0) == 0.0
        assert e.capped_multiplier == 0.0

    def test_compliance_entry_unknown_assurance_raw_is_zero(self) -> None:
        e = ComplianceEntry(
            uc_id="1",
            uc_status="verified",
            regulation="ISO 27001",
            version="2022",
            framework_id="iso-27001",
            tier=1,
            clause="A.5.1",
            mode="satisfies",
            assurance="??",
            rationale="r",
        )
        assert e.raw_multiplier == 0.0
        assert e.capped_multiplier == 0.0

    def test_audit_state_add_finding(self) -> None:
        st = AuditState()
        assert st.findings == []
        st.add(Finding(level="error", uc_id="1", code="x", message="m"))
        assert len(st.findings) == 1


# ---------------------------------------------------------------------------
# RegulationsCatalogue
# ---------------------------------------------------------------------------


class TestRegulationsCatalogue:
    def test_load_from_tmp_file(self, tmp_path: Path) -> None:
        path = tmp_path / "regs.json"
        path.write_text(json.dumps(_good_regs()), encoding="utf-8")
        cat = RegulationsCatalogue.load(path)
        assert "iso-27001" in cat.all_framework_ids()

    def test_resolve_framework_by_alias(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("ISO27001") == "iso-27001"
        assert cat.resolve_framework("iso/iec 27001") == "iso-27001"
        assert cat.resolve_framework("ISO 27001:2022") == "iso-27001"

    def test_resolve_framework_by_short_name(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("ISO 27001") == "iso-27001"
        assert cat.resolve_framework("soc 2") == "soc-2"

    def test_resolve_framework_by_full_name(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("AICPA SOC 2") == "soc-2"

    def test_resolve_framework_by_id(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("iso-27001") == "iso-27001"

    def test_resolve_framework_handles_whitespace(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("  ISO 27001  ") == "iso-27001"

    def test_resolve_framework_empty_input(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("") is None
        assert cat.resolve_framework("   ") is None

    def test_resolve_framework_unknown(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("nonexistent") is None

    def test_alias_index_skips_underscore_comment(self) -> None:
        cat = _good_catalogue()
        assert cat.resolve_framework("$comment") is None

    def test_get_version_known(self) -> None:
        cat = _good_catalogue()
        rv = cat.get_version("iso-27001", "2022")
        assert rv is not None
        assert rv.framework_id == "iso-27001"
        assert rv.short_name == "ISO 27001"
        assert rv.tier == 1
        assert rv.version == "2022"
        assert rv.clause_grammar.pattern == r"^A\.\d+\.\d+$"
        assert rv.authoritative_url == "https://example.test/iso27001"
        assert ("A.5.1", 2.0) in rv.common_clauses

    def test_get_version_unknown(self) -> None:
        cat = _good_catalogue()
        assert cat.get_version("iso-27001", "1999") is None
        assert cat.get_version("nope", "any") is None

    def test_framework_meta(self) -> None:
        cat = _good_catalogue()
        meta = cat.framework_meta("iso-27001")
        assert meta["name"] == "ISO/IEC 27001:2022"
        assert meta["tier"] == 1
        assert meta["shortName"] == "ISO 27001"
        assert "ISO27001" in meta["aliases"]

    def test_framework_meta_unknown(self) -> None:
        cat = _good_catalogue()
        assert cat.framework_meta("nope") == {}

    def test_versions_for_framework(self) -> None:
        cat = _good_catalogue()
        versions = cat.versions_for_framework("iso-27001")
        assert set(versions.keys()) == {"2022", "2013"}

    def test_versions_for_framework_unknown(self) -> None:
        cat = _good_catalogue()
        assert cat.versions_for_framework("nope") == {}

    def test_all_framework_ids_sorted(self) -> None:
        cat = _good_catalogue()
        ids = cat.all_framework_ids()
        assert ids == sorted(ids)
        assert ids == ["iso-27001", "iso-27002", "soc-2"]

    def test_derives_from_exposes_raw(self) -> None:
        cat = _good_catalogue()
        df = cat.derives_from()
        assert df["iso-27002"]["parent"] == "iso-27001"

    def test_family_for_root_is_self(self) -> None:
        cat = _good_catalogue()
        assert cat.family_for("iso-27001") == "iso-27001"
        assert cat.family_for("soc-2") == "soc-2"

    def test_family_for_derivative(self) -> None:
        cat = _good_catalogue()
        # iso-27002 -> iso-27001 (root)
        assert cat.family_for("iso-27002") == "iso-27001"

    def test_family_for_self_loop_terminates(self) -> None:
        cat = _good_catalogue()
        # The self-loop derives-from entry must not cause infinite recursion.
        assert cat.family_for("self-loop") == "self-loop"

    def test_build_handles_missing_short_name(self) -> None:
        # Framework with no shortName / name / aliases — alias index just
        # gets the id.
        regs = {
            "frameworks": [
                {
                    "id": "bare",
                    "tier": 3,
                    "versions": [
                        {
                            "version": "1",
                            "clauseGrammar": r"^x$",
                            "commonClauses": [],
                        }
                    ],
                }
            ]
        }
        cat = RegulationsCatalogue(regs)
        assert cat.resolve_framework("bare") == "bare"
        assert cat.framework_meta("bare")["tier"] == 3
        assert cat.framework_meta("bare")["shortName"] == ""

    def test_build_indexes_by_short_name_and_framework_id(self) -> None:
        cat = _good_catalogue()
        # internal mapping invariants
        assert "2022" in cat._by_short_name["ISO 27001"]
        assert "2022" in cat._by_framework_id["iso-27001"]


# ---------------------------------------------------------------------------
# _uc_status
# ---------------------------------------------------------------------------


class TestUcStatus:
    def test_returns_status_when_present(self) -> None:
        assert cm._uc_status({"status": "verified"}) == "verified"
        assert cm._uc_status({"status": "draft"}) == "draft"

    def test_returns_unset_sentinel_when_missing(self) -> None:
        assert cm._uc_status({}) == "__unset__"

    def test_returns_unset_sentinel_when_empty(self) -> None:
        # Empty string is falsy → sentinel
        assert cm._uc_status({"status": ""}) == "__unset__"


# ---------------------------------------------------------------------------
# _reconcile_compliance — one finding code per test
# ---------------------------------------------------------------------------


class TestReconcileCompliance:
    def _run(self, uc: dict[str, Any]) -> tuple[AuditState, list[str]]:
        state = AuditState()
        regs = _good_catalogue()
        cm._reconcile_compliance(uc, regs, state)
        return state, [f.code for f in state.findings]

    def test_happy_path_records_entry(self) -> None:
        state, codes = self._run(_good_uc())
        assert codes == []
        assert len(state.entries) == 1
        entry = state.entries[0]
        assert entry.uc_id == "1.1.1"
        assert entry.regulation == "ISO 27001"
        assert entry.framework_id == "iso-27001"
        assert entry.tier == 1
        assert entry.assurance == "full"
        assert entry.rationale == "Implements ISMS leadership review."

    def test_no_compliance_field_is_noop(self) -> None:
        state, codes = self._run({"id": "1.1.1"})
        assert codes == []
        assert state.entries == []

    def test_compliance_explicit_null_is_noop(self) -> None:
        _state, codes = self._run({"id": "1.1.1", "compliance": None})
        assert codes == []

    def test_unknown_regulation(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["regulation"] = "made-up regulation"
        state, codes = self._run(uc)
        assert codes == ["unknown-regulation"]
        # unknown_regulations counter incremented
        assert state.unknown_regulations["made-up regulation"] == 1

    def test_unknown_regulation_increments_counter(self) -> None:
        state = AuditState()
        regs = _good_catalogue()
        for _ in range(3):
            uc = _good_uc()
            uc["compliance"][0]["regulation"] = "ghost"
            cm._reconcile_compliance(uc, regs, state)
        assert state.unknown_regulations["ghost"] == 3

    def test_unknown_version(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["version"] = "1999"
        _state, codes = self._run(uc)
        assert codes == ["unknown-version"]

    def test_clause_grammar_violation(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["clause"] = "ZZ.99"
        _state, codes = self._run(uc)
        assert codes == ["clause-grammar"]

    def test_clause_grammar_violation_empty_clause(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["clause"] = ""
        _state, codes = self._run(uc)
        assert codes == ["clause-grammar"]

    def test_assurance_invalid(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["assurance"] = "ultra"
        _state, codes = self._run(uc)
        assert codes == ["assurance-invalid"]

    def test_assurance_rationale_missing(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["assurance_rationale"] = ""
        _state, codes = self._run(uc)
        assert codes == ["assurance-rationale-missing"]

    def test_assurance_rationale_too_short(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["assurance_rationale"] = "short"  # 5 chars
        _state, codes = self._run(uc)
        assert codes == ["assurance-rationale-missing"]

    def test_missing_control_objective(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["controlObjective"] = ""
        state, codes = self._run(uc)
        # Note: missing-control-objective does NOT continue; mode check
        # still runs. So we expect the missing-control-objective finding
        # and the entry should still be recorded.
        assert "missing-control-objective" in codes
        assert len(state.entries) == 1

    def test_missing_control_objective_when_field_absent(self) -> None:
        uc = _good_uc()
        del uc["compliance"][0]["controlObjective"]
        _state, codes = self._run(uc)
        assert "missing-control-objective" in codes

    def test_missing_evidence_artifact(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["evidenceArtifact"] = ""
        state, codes = self._run(uc)
        assert "missing-evidence-artifact" in codes
        assert len(state.entries) == 1

    def test_missing_both_story_layer_fields(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["controlObjective"] = ""
        uc["compliance"][0]["evidenceArtifact"] = ""
        _state, codes = self._run(uc)
        assert set(codes) == {"missing-control-objective", "missing-evidence-artifact"}

    def test_mode_invalid(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["mode"] = "implies"
        _state, codes = self._run(uc)
        assert "mode-invalid" in codes

    def test_mode_detects_violation_of_is_valid(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["mode"] = "detects-violation-of"
        state, codes = self._run(uc)
        assert codes == []
        assert state.entries[0].mode == "detects-violation-of"

    def test_unknown_uc_status_uses_unset(self) -> None:
        uc = _good_uc()
        del uc["status"]
        state, codes = self._run(uc)
        assert codes == []
        assert state.entries[0].uc_status == "__unset__"

    def test_rationale_strips_whitespace_on_recorded_entry(self) -> None:
        uc = _good_uc()
        uc["compliance"][0]["assurance_rationale"] = "   well documented review.  "
        state, codes = self._run(uc)
        assert codes == []
        assert state.entries[0].rationale == "well documented review."

    def test_finding_path_includes_index(self) -> None:
        uc = _good_uc()
        uc["compliance"] = [
            {
                "regulation": "ghost",
                "version": "2022",
                "clause": "A.5.1",
                "mode": "satisfies",
                "assurance": "full",
                "assurance_rationale": "ok ok ok ok ok",
                "controlObjective": "x",
                "evidenceArtifact": "y",
            },
            _good_uc()["compliance"][0],
        ]
        state, codes = self._run(uc)
        assert codes == ["unknown-regulation"]
        assert state.findings[0].path == "compliance[0]"


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetricsFor:
    def test_zero_denominator_short_circuits(self) -> None:
        m = cm._metrics_for([], {})
        assert m == Metrics(0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0)

    def test_full_coverage(self) -> None:
        common = [("A", 1.0), ("B", 2.0)]
        m = cm._metrics_for(common, {"A": 1.0, "B": 1.0})
        assert m.clauses_covered == 2
        assert m.clause_pct == 100.0
        assert m.priority_pct == 100.0
        assert m.assurance_pct == 100.0

    def test_partial_coverage(self) -> None:
        common = [("A", 1.0), ("B", 3.0)]
        m = cm._metrics_for(common, {"A": 0.5})
        assert m.clauses_covered == 1
        assert m.clause_pct == 50.0
        # weight 1 / weight 4 = 25%
        assert m.priority_pct == 25.0
        # 1 * 0.5 / 4.0 = 12.5%
        assert m.assurance_pct == 12.5

    def test_zero_weight_clauses_still_count(self) -> None:
        common = [("A", 0.0), ("B", 0.0)]
        m = cm._metrics_for(common, {"A": 1.0})
        assert m.clauses_covered == 1
        assert m.clause_pct == 50.0
        # weighted denom is zero → percentages clamp to 0
        assert m.priority_pct == 0.0
        assert m.assurance_pct == 0.0


class TestBuildCoverageByVersion:
    def test_skips_zero_capped_entries(self) -> None:
        entries = [
            ComplianceEntry(
                uc_id="1",
                uc_status="draft",  # cap 0.0
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="full",
                rationale="r",
            )
        ]
        cov = cm._build_coverage_by_version(entries)
        assert cov == {}

    def test_takes_max_when_multiple_entries_for_same_clause(self) -> None:
        entries = [
            ComplianceEntry(
                uc_id="1",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="partial",  # 0.5
                rationale="r",
            ),
            ComplianceEntry(
                uc_id="2",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="full",  # 1.0 — should win
                rationale="r",
            ),
            ComplianceEntry(
                uc_id="3",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="contributing",  # 0.25 — should NOT overwrite full
                rationale="r",
            ),
        ]
        cov = cm._build_coverage_by_version(entries)
        assert cov[("iso-27001", "2022")] == {"A.5.1": 1.0}


class TestComputeCoverage:
    def test_empty_entries_returns_zeros(self) -> None:
        cat = _good_catalogue()
        out = cm._compute_coverage([], cat)
        assert out["global"]["denominator_count"] == 3  # 2 + 1 + 0
        # No coverage anywhere
        assert out["global"]["clause_pct"] == 0.0
        # Per-version always emitted (one row per (framework, version))
        assert "ISO 27001@2022" in out["perVersion"]
        assert "ISO 27001@2013" in out["perVersion"]
        assert "SOC 2@2017" in out["perVersion"]
        # Per-tier rows exist
        assert "tier-1" in out["perTier"]
        assert "tier-2" in out["perTier"]
        assert "tier-3" in out["perTier"]
        # Per-family includes iso-27002 rolled into iso-27001
        assert "iso-27001" in out["perFamily"]

    def test_full_coverage_through_pipeline(self) -> None:
        cat = _good_catalogue()
        entries = [
            ComplianceEntry(
                uc_id="1",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="full",
                rationale="r",
            ),
            ComplianceEntry(
                uc_id="2",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.8.1",
                mode="satisfies",
                assurance="full",
                rationale="r",
            ),
            ComplianceEntry(
                uc_id="3",
                uc_status="verified",
                regulation="SOC 2",
                version="2017",
                framework_id="soc-2",
                tier=2,
                clause="CC1.1",
                mode="satisfies",
                assurance="full",
                rationale="r",
            ),
        ]
        out = cm._compute_coverage(entries, cat)
        # Global must hit 100% across all common clauses
        assert out["global"]["clauses_covered"] == 3
        assert out["global"]["clause_pct"] == 100.0
        assert out["perVersion"]["ISO 27001@2022"]["clause_pct"] == 100.0
        assert out["perVersion"]["SOC 2@2017"]["clause_pct"] == 100.0

    def test_per_tier_aggregates_correctly(self) -> None:
        cat = _good_catalogue()
        entries = [
            ComplianceEntry(
                uc_id="1",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="full",
                rationale="r",
            )
        ]
        out = cm._compute_coverage(entries, cat)
        tier1 = out["perTier"]["tier-1"]
        # Tier 1 has 2 common clauses (A.5.1, A.8.1) — we covered 1.
        assert tier1["denominator_count"] == 2
        assert tier1["clauses_covered"] == 1
        assert tier1["clause_pct"] == 50.0


# ---------------------------------------------------------------------------
# Baseline mechanism
# ---------------------------------------------------------------------------


class TestBaseline:
    def test_load_baseline_missing_returns_empty_skeleton(self, tmp_path: Path) -> None:
        result = cm._load_baseline(tmp_path / "no-such.json")
        assert result == {"version": 1, "generatedAt": "", "fingerprints": []}

    def test_load_baseline_valid_file(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        path.write_text(
            json.dumps({"version": 1, "fingerprints": ["a\tb\tc\td"]}), encoding="utf-8"
        )
        result = cm._load_baseline(path)
        assert "a\tb\tc\td" in result["fingerprints"]

    def test_load_baseline_invalid_json_raises_systemexit(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        path.write_text("{not-json", encoding="utf-8")
        # Path must be inside REPO_ROOT for relative_to() in the error
        # message to succeed; route through a real tmp path nested under
        # REPO_ROOT to avoid that branch.
        repo_path = cm.REPO_ROOT / ".pytest-tmp-baseline-invalid-json.json"
        try:
            repo_path.write_text("{not-json", encoding="utf-8")
            with pytest.raises(SystemExit, match="not valid JSON"):
                cm._load_baseline(repo_path)
        finally:
            if repo_path.exists():
                repo_path.unlink()

    def test_load_baseline_malformed_shape_raises_systemexit(self) -> None:
        repo_path = cm.REPO_ROOT / ".pytest-tmp-baseline-shape.json"
        try:
            repo_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            with pytest.raises(SystemExit, match="malformed"):
                cm._load_baseline(repo_path)
        finally:
            if repo_path.exists():
                repo_path.unlink()

    def test_load_baseline_missing_fingerprints_key_raises(self) -> None:
        repo_path = cm.REPO_ROOT / ".pytest-tmp-baseline-no-fps.json"
        try:
            repo_path.write_text(json.dumps({"version": 1}), encoding="utf-8")
            with pytest.raises(SystemExit, match="malformed"):
                cm._load_baseline(repo_path)
        finally:
            if repo_path.exists():
                repo_path.unlink()

    def test_apply_baseline_downgrades_eligible_codes(self) -> None:
        findings = [
            Finding(
                level="error", uc_id="1", code="equipment-orphan", message="x", path="equipment"
            ),
        ]
        fp = findings[0].fingerprint()
        blocking, baselined, new_errors = cm._apply_baseline(findings, {fp})
        assert blocking == 0
        assert baselined == 1
        assert new_errors == 0
        assert findings[0].level == "baselined"

    def test_apply_baseline_does_not_downgrade_non_baselineable_codes(self) -> None:
        findings = [
            Finding(level="error", uc_id="1", code="clause-grammar", message="x", path="p"),
        ]
        fp = findings[0].fingerprint()
        blocking, baselined, new_errors = cm._apply_baseline(findings, {fp})
        assert blocking == 1
        assert baselined == 0
        assert new_errors == 0
        assert findings[0].level == "error"

    def test_apply_baseline_treats_unmatched_baselineable_as_new(self) -> None:
        findings = [
            Finding(
                level="error", uc_id="1", code="equipment-orphan", message="x", path="equipment"
            ),
        ]
        blocking, baselined, new_errors = cm._apply_baseline(findings, set())
        assert blocking == 1
        assert baselined == 0
        assert new_errors == 1

    def test_apply_baseline_skips_non_error_levels(self) -> None:
        findings = [
            Finding(level="warn", uc_id="1", code="equipment-orphan", message="x"),
        ]
        blocking, baselined, new_errors = cm._apply_baseline(findings, set())
        assert blocking == 0
        assert baselined == 0
        assert new_errors == 0

    def test_write_baseline_writes_sorted_fingerprints(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        path = tmp_path / "baseline.json"
        findings = [
            Finding(
                level="error", uc_id="2", code="equipment-orphan", message="b", path="equipment"
            ),
            Finding(
                level="error", uc_id="1", code="equipment-orphan", message="a", path="equipment"
            ),
            Finding(level="error", uc_id="3", code="clause-grammar", message="c", path="p"),
            # baselineable but not error/baselined → excluded
            Finding(level="warn", uc_id="4", code="equipment-orphan", message="d"),
        ]
        count = cm._write_baseline(path, findings)
        # Only the two equipment-orphan errors are baselineable
        assert count == 2
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["version"] == 1
        assert payload["count"] == 2
        assert payload["fingerprints"] == sorted(payload["fingerprints"])

    def test_write_baseline_includes_baselined_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        path = tmp_path / "baseline.json"
        findings = [
            Finding(
                level="baselined",
                uc_id="1",
                code="equipment-orphan",
                message="x",
                path="equipment",
            )
        ]
        count = cm._write_baseline(path, findings)
        assert count == 1

    def test_write_baseline_deduplicates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        path = tmp_path / "baseline.json"
        findings = [
            Finding(
                level="error",
                uc_id="1",
                code="equipment-orphan",
                message="dup",
                path="equipment",
            ),
            Finding(
                level="error",
                uc_id="1",
                code="equipment-orphan",
                message="dup",
                path="equipment",
            ),
        ]
        count = cm._write_baseline(path, findings)
        assert count == 1


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _stub_payload(
    *,
    blocking: int = 0,
    baselined: int = 0,
    baseline_enabled: bool = False,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for i in range(blocking):
        findings.append(
            {
                "level": "error",
                "uc": f"1.1.{i}",
                "code": "clause-grammar",
                "path": f"compliance[{i}]",
                "message": f"bad clause {i}",
            }
        )
    for i in range(baselined):
        findings.append(
            {
                "level": "baselined",
                "uc": f"2.2.{i}",
                "code": "equipment-orphan",
                "path": "equipment",
                "message": f"pre-existing orphan {i}",
            }
        )
    payload: dict[str, Any] = {
        "generatedAt": "2026-01-01T00:00:00Z",
        "status": "passed" if blocking == 0 else "failed",
        "counts": {
            "ucFilesChecked": 10,
            "ucFilesValid": 10,
            "complianceEntries": 15,
            "findings": len(findings),
            "errors": blocking,
            "baselined": baselined,
        },
        "coverage": {
            "global": {
                "clause_pct": 25.0,
                "priority_pct": 30.0,
                "assurance_pct": 22.5,
                "denominator_count": 4,
                "denominator_weighted": 6.0,
                "clauses_covered": 1,
                "weighted_covered": 1.5,
                "assurance_numerator": 1.35,
            },
            "perTier": {
                "tier-1": {
                    "clause_pct": 50.0,
                    "priority_pct": 60.0,
                    "assurance_pct": 45.0,
                    "denominator_count": 2,
                },
                "tier-2": {
                    "clause_pct": 0.0,
                    "priority_pct": 0.0,
                    "assurance_pct": 0.0,
                    "denominator_count": 0,
                },
            },
            "perFamily": {
                "iso-27001": {
                    "clause_pct": 50.0,
                    "priority_pct": 60.0,
                    "assurance_pct": 45.0,
                }
            },
            "perVersion": {
                "ISO 27001@2022": {
                    "tier": 1,
                    "clause_pct": 50.0,
                    "priority_pct": 60.0,
                    "assurance_pct": 45.0,
                }
            },
        },
        "golden": {"total": 5, "passed": 5, "failed": 0},
        "findings": findings,
    }
    if baseline_enabled:
        payload["baseline"] = {
            "enabled": True,
            "path": "tests/golden/audit-baseline.json",
            "total": baselined + 1,
            "matched": baselined,
            "newErrors": 0,
            "unused": ["uc-x:code-y"],
        }
    return payload


class TestMarkdownFor:
    def test_no_findings_renders_clean(self) -> None:
        md = cm._markdown_for(_stub_payload())
        assert "# Compliance coverage report" in md
        assert "Status: **passed**" in md
        assert "## Per tier" in md
        assert "## Per family (derivesFrom roots)" in md
        assert "## Per regulation-version" in md
        assert "## Golden tuples" in md
        assert "## Blocking findings" not in md
        assert "## Baselined" not in md

    def test_tier_with_zero_denominator_renders_na(self) -> None:
        md = cm._markdown_for(_stub_payload())
        assert "tier-2 | n/a (no common clauses defined)" in md

    def test_blocking_findings_table_renders_first_50(self) -> None:
        payload = _stub_payload(blocking=3)
        md = cm._markdown_for(payload)
        assert "## Blocking findings" in md
        assert "1.1.0" in md
        assert "1.1.2" in md
        assert "_… and" not in md

    def test_blocking_findings_truncates_at_50(self) -> None:
        payload = _stub_payload(blocking=75)
        md = cm._markdown_for(payload)
        assert "_… and 25 more blocking findings." in md

    def test_baselined_section_renders_when_present(self) -> None:
        md = cm._markdown_for(_stub_payload(baselined=3))
        assert "## Baselined" in md
        assert "2.2.0" in md

    def test_baselined_section_truncates_at_20(self) -> None:
        md = cm._markdown_for(_stub_payload(baselined=30))
        assert "_… and 10 more baselined findings" in md

    def test_baseline_summary_line_when_baseline_enabled(self) -> None:
        md = cm._markdown_for(_stub_payload(baselined=1, baseline_enabled=True))
        assert "Baseline (`tests/golden/audit-baseline.json`)" in md
        assert "unused fingerprints **1**" in md

    def test_pipe_characters_in_messages_are_escaped(self) -> None:
        payload = _stub_payload(blocking=1)
        payload["findings"][0]["message"] = "this|has|pipes"
        md = cm._markdown_for(payload)
        assert "this\\|has\\|pipes" in md


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


class TestReportWriters:
    def test_write_json_report_creates_parent_dirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "subdir" / "compliance-coverage.json"
        monkeypatch.setattr(cm, "REPORT_JSON", target)
        payload = {"hello": "world", "list": [3, 2, 1]}
        cm._write_json_report(payload)
        assert target.is_file()
        # sort_keys=True and indent=2
        text = target.read_text(encoding="utf-8")
        assert text.endswith("\n")
        assert '"hello": "world"' in text

    def test_write_markdown_report_writes_markdown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "subdir" / "compliance-coverage.md"
        monkeypatch.setattr(cm, "REPORT_MD", target)
        cm._write_markdown_report(_stub_payload())
        assert target.is_file()
        text = target.read_text(encoding="utf-8")
        assert text.startswith("# Compliance coverage report")


# ---------------------------------------------------------------------------
# Schema validation + iter_uc_files
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_load_schema_returns_dict_with_expected_top_level(self) -> None:
        schema = cm._load_schema()
        assert isinstance(schema, dict)
        # uc.schema.json uses draft 2020-12
        assert "$schema" in schema

    def test_iter_uc_files_yields_files_only(self) -> None:
        # Sanity check: the real catalogue produces a non-empty iterator
        # of files that all exist.
        files = list(cm._iter_uc_files())
        assert len(files) > 0
        for p in files[:5]:
            assert p.is_file()
            assert p.name.startswith("UC-")

    def test_reimport_when_scripts_dir_already_in_sys_path_is_a_noop(
        self,
    ) -> None:
        """Pins the False branch of the module-level ``if str(_SCRIPTS_DIR)
        not in sys.path:`` (line 95): once the module has been imported
        during the test session, ``_SCRIPTS_DIR`` is already in
        ``sys.path``, so reloading the module must skip the
        ``sys.path.insert`` and fall through to the lazy
        ``equipment_lib`` import. The existing test suite only ever
        observed the True branch (initial import-time path injection)."""
        import importlib
        import sys

        scripts_dir = str(cm.REPO_ROOT / "scripts")
        assert scripts_dir in sys.path, (
            "preconditioned to pin the False branch: the module's "
            "initial import already populated sys.path"
        )
        path_before = list(sys.path)
        reloaded = importlib.reload(cm)
        assert sys.path.count(scripts_dir) == path_before.count(scripts_dir), (
            "reload must not append a duplicate scripts_dir entry"
        )
        assert reloaded._EQUIPMENT_LIB_OK is True

    def test_reimport_when_scripts_dir_missing_re_inserts(self) -> None:
        """Pins the True branch of the module-level ``if str(_SCRIPTS_DIR)
        not in sys.path:`` (line 95 → line 96): when ``_SCRIPTS_DIR`` is
        absent from ``sys.path`` at import time, the module must invoke
        ``sys.path.insert(0, str(_SCRIPTS_DIR))`` so that the lazy
        ``equipment_lib`` import can resolve.

        The live runtime executes this branch on cold-start (no test
        fixture has yet polluted ``sys.path``), but every subsequent test
        observation runs in a hot interpreter where the entry is already
        present. To pin the True arm hermetically we remove the entry,
        reload the module, and re-assert insertion happened. The
        ``try/finally`` block restores the pre-test ``sys.path`` so this
        test is order-independent. Mirrors the equivalent test for
        ``equipment_tags`` (Wave OOO) and ``repo_consistency``."""
        import importlib
        import sys

        scripts_dir = str(cm.REPO_ROOT / "scripts")
        original = list(sys.path)
        try:
            while scripts_dir in sys.path:
                sys.path.remove(scripts_dir)
            assert scripts_dir not in sys.path
            reloaded = importlib.reload(cm)
            assert scripts_dir in sys.path, (
                "module-level guard must re-insert _SCRIPTS_DIR when it "
                "is absent from sys.path at import time"
            )
            assert reloaded._EQUIPMENT_LIB_OK is True
        finally:
            sys.path[:] = original

    def test_iter_uc_files_skips_directories_matching_glob(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pins the False branch of ``if p.is_file():`` (line 304 in
        ``_iter_uc_files``): a directory whose name matches the
        ``UC-*.json`` glob is silently skipped, not yielded. The real
        catalogue never contains a directory shaped like this, so the
        False branch is otherwise unreachable."""
        fake_content = tmp_path / "content" / "cat-99-fake"
        fake_content.mkdir(parents=True)
        (fake_content / "UC-99.1.1.json").write_text("{}", encoding="utf-8")
        (fake_content / "UC-99.1.2.json").mkdir()
        monkeypatch.setattr(cm, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cm, "UC_GLOB", "content/cat-*/UC-*.json")
        files = list(cm._iter_uc_files())
        names = {p.name for p in files}
        assert names == {"UC-99.1.1.json"}
        for p in files:
            assert p.is_file()

    def test_validate_uc_schema_parse_error(self, tmp_path: Path) -> None:
        from jsonschema import Draft202012Validator

        bad = tmp_path / "UC-broken.json"
        bad.write_text("{not-json", encoding="utf-8")
        # Move under repo root for relative_to() to succeed
        repo_path = cm.REPO_ROOT / ".pytest-tmp-uc-broken.json"
        try:
            repo_path.write_text("{not-json", encoding="utf-8")
            schema = cm._load_schema()
            validator = Draft202012Validator(schema)
            state = AuditState()
            result = cm._validate_uc_schema(validator, repo_path, state)
            assert result is None
            assert state.findings[0].code == "uc-json-parse"
        finally:
            if repo_path.exists():
                repo_path.unlink()

    def test_validate_uc_schema_validation_errors(self) -> None:
        from jsonschema import Draft202012Validator

        # Build a UC missing several required fields → schema reports errors.
        repo_path = cm.REPO_ROOT / ".pytest-tmp-uc-incomplete.json"
        try:
            repo_path.write_text(
                json.dumps({"id": "1.1.1"}),  # missing many required fields
                encoding="utf-8",
            )
            schema = cm._load_schema()
            validator = Draft202012Validator(schema)
            state = AuditState()
            result = cm._validate_uc_schema(validator, repo_path, state)
            assert result is None
            # At least one error
            assert any(f.code == "uc-schema-validation" for f in state.findings)
        finally:
            if repo_path.exists():
                repo_path.unlink()


# ---------------------------------------------------------------------------
# _run_golden_tests
# ---------------------------------------------------------------------------


class TestGoldenTests:
    def test_missing_file_emits_finding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Point the audit at a non-existent golden file. The audit calls
        # ``relative_to(REPO_ROOT)`` for the error message, so the bogus
        # path has to live somewhere under the repo root.
        target = cm.REPO_ROOT / ".pytest-tmp-golden-missing.yaml"
        if target.exists():
            target.unlink()
        monkeypatch.setattr(cm, "GOLDEN_PATH", target)
        state = AuditState()
        result = cm._run_golden_tests([], state)
        assert result == {"total": 0, "passed": 0, "failed": 0, "failures": []}
        assert state.findings[0].code == "golden-missing"

    def test_empty_tuples_emits_finding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        golden_path = tmp_path / "golden.yaml"
        golden_path.write_text("tuples: []\n", encoding="utf-8")
        monkeypatch.setattr(cm, "GOLDEN_PATH", golden_path)
        state = AuditState()
        result = cm._run_golden_tests([], state)
        assert result["total"] == 0
        assert any(f.code == "golden-empty" for f in state.findings)

    def test_missing_tuple_emits_finding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        golden_path = tmp_path / "golden.yaml"
        golden_path.write_text(
            (
                "tuples:\n"
                "  - uc: '1.1.1'\n"
                "    regulation: 'ISO 27001'\n"
                "    version: '2022'\n"
                "    clause: 'A.5.1'\n"
                "    mode: 'satisfies'\n"
                "    min_assurance: 'partial'\n"
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cm, "GOLDEN_PATH", golden_path)
        state = AuditState()
        result = cm._run_golden_tests([], state)
        assert result["total"] == 1
        assert result["failed"] == 1
        assert result["failures"][0]["reason"] == "tuple-not-found"
        assert any(f.code == "golden-missing-tuple" for f in state.findings)

    def test_assurance_below_min_emits_finding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        golden_path = tmp_path / "golden.yaml"
        golden_path.write_text(
            (
                "tuples:\n"
                "  - uc: '1.1.1'\n"
                "    regulation: 'ISO 27001'\n"
                "    version: '2022'\n"
                "    clause: 'A.5.1'\n"
                "    mode: 'satisfies'\n"
                "    min_assurance: 'full'\n"
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cm, "GOLDEN_PATH", golden_path)
        entries = [
            ComplianceEntry(
                uc_id="1.1.1",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="contributing",  # below required `full`
                rationale="r",
            )
        ]
        state = AuditState()
        result = cm._run_golden_tests(entries, state)
        assert result["failed"] == 1
        assert result["failures"][0]["reason"] == "assurance-below-min"
        assert any(f.code == "golden-assurance-below-min" for f in state.findings)

    def test_happy_path_no_findings(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        golden_path = tmp_path / "golden.yaml"
        golden_path.write_text(
            (
                "tuples:\n"
                "  - uc: '1.1.1'\n"
                "    regulation: 'ISO 27001'\n"
                "    version: '2022'\n"
                "    clause: 'A.5.1'\n"
                "    mode: 'satisfies'\n"
                "    min_assurance: 'partial'\n"
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cm, "GOLDEN_PATH", golden_path)
        entries = [
            ComplianceEntry(
                uc_id="1.1.1",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="full",
                rationale="r",
            )
        ]
        state = AuditState()
        result = cm._run_golden_tests(entries, state)
        assert result["total"] == 1
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert state.findings == []

    def test_unknown_min_assurance_defaults_to_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        golden_path = tmp_path / "golden.yaml"
        golden_path.write_text(
            (
                "tuples:\n"
                "  - uc: '1.1.1'\n"
                "    regulation: 'ISO 27001'\n"
                "    version: '2022'\n"
                "    clause: 'A.5.1'\n"
                "    mode: 'satisfies'\n"
                "    min_assurance: 'wat'\n"
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cm, "GOLDEN_PATH", golden_path)
        entries = [
            ComplianceEntry(
                uc_id="1.1.1",
                uc_status="verified",
                regulation="ISO 27001",
                version="2022",
                framework_id="iso-27001",
                tier=1,
                clause="A.5.1",
                mode="satisfies",
                assurance="contributing",
                rationale="r",
            )
        ]
        state = AuditState()
        result = cm._run_golden_tests(entries, state)
        # Unknown min_assurance maps to ASSURANCE_RANK.get('wat', 0)=0
        # which 'contributing' (rank 0) satisfies → passes.
        assert result["passed"] == 1


# ---------------------------------------------------------------------------
# RegVersion is frozen and hashable
# ---------------------------------------------------------------------------


class TestRegVersionDataclass:
    def test_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        rv = RegVersion(
            framework_id="iso-27001",
            short_name="ISO 27001",
            tier=1,
            version="2022",
            clause_grammar=re.compile(r"x"),
            common_clauses=(),
        )
        with pytest.raises(FrozenInstanceError):
            rv.version = "2099"

    def test_default_authoritative_url_is_empty(self) -> None:
        rv = RegVersion(
            framework_id="x",
            short_name="X",
            tier=3,
            version="1",
            clause_grammar=re.compile(r"x"),
            common_clauses=(),
        )
        assert rv.authoritative_url == ""


# ---------------------------------------------------------------------------
# _equipment_patterns + _lint_equipment_orphans
# ---------------------------------------------------------------------------


class TestEquipmentLint:
    def test_equipment_patterns_returns_empty_when_lib_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", False)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", None)
        assert cm._equipment_patterns() == []

    def test_equipment_patterns_cached(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sentinel: list[Any] = ["cached!"]
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", sentinel)
        # ``_EQUIPMENT_LIB_OK`` could be True or False; the cache should
        # short-circuit either way.
        assert cm._equipment_patterns() is sentinel

    def test_equipment_patterns_compiles_when_lib_ok(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", None)
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        sentinel = [("any", object())]
        monkeypatch.setattr(cm, "compile_patterns", lambda: sentinel, raising=False)
        result = cm._equipment_patterns()
        assert result == sentinel

    def test_lint_skipped_when_lib_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", False)
        state = AuditState()
        cm._lint_equipment_orphans({"id": "22.1.1", "description": "Palo Alto"}, state)
        assert state.findings == []

    def test_lint_skipped_for_non_cat22(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("paloalto", object())])
        state = AuditState()
        cm._lint_equipment_orphans({"id": "1.1.1", "description": "Palo Alto"}, state)
        assert state.findings == []

    def test_lint_skipped_when_no_patterns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [])
        state = AuditState()
        cm._lint_equipment_orphans({"id": "22.1.1", "description": "Palo Alto"}, state)
        assert state.findings == []

    def test_lint_skipped_when_no_narrative(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("paloalto", object())])
        # No description / spl / implementation / dataSources / app
        state = AuditState()
        cm._lint_equipment_orphans({"id": "22.1.1"}, state)
        assert state.findings == []

    def test_lint_emits_finding_for_orphaned_equipment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("paloalto", object())])

        def fake_match(
            _narrative: str, _patterns: Any, *, min_pattern_len: int = 4
        ) -> tuple[list[str], list[str]]:
            return (["paloalto"], [])

        monkeypatch.setattr(cm, "match_equipment", fake_match, raising=False)
        state = AuditState()
        doc = {
            "id": "22.1.1",
            "description": "Mentions Palo Alto",
            "equipment": ["cisco"],
            "equipmentModels": [],
        }
        cm._lint_equipment_orphans(doc, state)
        assert len(state.findings) == 1
        f = state.findings[0]
        assert f.code == "equipment-orphan"
        assert f.level == "warn"
        assert "paloalto" in f.message
        assert f.path == "equipment"

    def test_lint_emits_finding_for_orphaned_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("anything", object())])

        def fake_match(
            _n: str, _p: Any, *, min_pattern_len: int = 4
        ) -> tuple[list[str], list[str]]:
            return ([], ["panorama-pa-220"])

        monkeypatch.setattr(cm, "match_equipment", fake_match, raising=False)
        state = AuditState()
        doc = {
            "id": "22.1.1",
            "spl": "index=panorama-pa-220 *",
            "equipment": ["paloalto"],
            "equipmentModels": [],
        }
        cm._lint_equipment_orphans(doc, state)
        assert len(state.findings) == 1
        assert "equipmentModels" in state.findings[0].message

    def test_lint_no_finding_when_everything_tagged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("anything", object())])

        def fake_match(
            _n: str, _p: Any, *, min_pattern_len: int = 4
        ) -> tuple[list[str], list[str]]:
            return (["paloalto"], ["pa-220"])

        monkeypatch.setattr(cm, "match_equipment", fake_match, raising=False)
        state = AuditState()
        doc = {
            "id": "22.1.1",
            "description": "uses Palo Alto pa-220",
            "equipment": ["PaloAlto"],
            "equipmentModels": ["PA-220"],
        }
        cm._lint_equipment_orphans(doc, state)
        assert state.findings == []

    def test_lint_narrative_collects_lists_and_strings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Narrative builder must accept str, list[str], and list[int|float]
        for description / implementation / spl / dataSources / app."""
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("anything", object())])
        captured: dict[str, str] = {}

        def fake_match(n: str, _p: Any, *, min_pattern_len: int = 4) -> tuple[list[str], list[str]]:
            captured["narrative"] = n
            return ([], [])

        monkeypatch.setattr(cm, "match_equipment", fake_match, raising=False)
        state = AuditState()
        doc = {
            "id": "22.1.1",
            "description": "string desc",
            "implementation": ["impl-a", "impl-b"],
            "dataSources": [1, 2.5, "real-source"],
            "app": "ESCU",
        }
        cm._lint_equipment_orphans(doc, state)
        assert "string desc" in captured["narrative"]
        assert "impl-a" in captured["narrative"]
        assert "real-source" in captured["narrative"]
        assert "ESCU" in captured["narrative"]

    def test_lint_handles_app_as_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cm, "_EQUIPMENT_LIB_OK", True)
        monkeypatch.setattr(cm, "_EQUIPMENT_PATTERNS_CACHE", [("anything", object())])
        captured: dict[str, str] = {}

        def fake_match(n: str, _p: Any, *, min_pattern_len: int = 4) -> tuple[list[str], list[str]]:
            captured["narrative"] = n
            return ([], [])

        monkeypatch.setattr(cm, "match_equipment", fake_match, raising=False)
        state = AuditState()
        doc = {
            "id": "22.1.1",
            "app": ["app-a", "app-b"],
            "description": "y",
        }
        cm._lint_equipment_orphans(doc, state)
        assert "app-a" in captured["narrative"]
        assert "app-b" in captured["narrative"]


# ---------------------------------------------------------------------------
# _print_pretty
# ---------------------------------------------------------------------------


class TestPrintPretty:
    def test_empty_payload(self, capsys: pytest.CaptureFixture[str]) -> None:
        cm._print_pretty(_stub_payload())
        out = capsys.readouterr().out
        assert "Compliance audit: PASSED" in out
        assert "Global   clause%" in out
        # tier-1 has denom 2, tier-2 has denom 0 → "not applicable"
        assert "tier-1" in out
        assert "tier-2" in out
        assert "not applicable" in out
        # baseline not enabled
        assert "Baseline" not in out
        # No blocking findings header
        assert "Blocking findings" not in out

    def test_with_baseline_meta(self, capsys: pytest.CaptureFixture[str]) -> None:
        cm._print_pretty(_stub_payload(baseline_enabled=True, baselined=1))
        out = capsys.readouterr().out
        assert "Baseline tests/golden/audit-baseline.json" in out
        assert "tolerated=1" in out

    def test_with_blocking_findings_under_20(self, capsys: pytest.CaptureFixture[str]) -> None:
        cm._print_pretty(_stub_payload(blocking=5))
        out = capsys.readouterr().out
        assert "Blocking findings (first 20):" in out
        # No truncation suffix
        assert "and 0 more" not in out
        assert "more. See" not in out

    def test_with_blocking_findings_over_20_emits_truncation(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cm._print_pretty(_stub_payload(blocking=25))
        out = capsys.readouterr().out
        assert "Blocking findings (first 20):" in out
        assert "and 5 more" in out


# ---------------------------------------------------------------------------
# main() — end-to-end smoke tests with monkeypatched IO
# ---------------------------------------------------------------------------


def _stub_uc_payload_doc(uc_id: str = "1.1.1") -> dict[str, Any]:
    """Return a fully-valid UC sidecar that satisfies uc.schema.json.

    Field shapes match uc.schema.json v1.6+ exactly:

    * ``title``    minLength 8
    * ``difficulty``  enum ``beginner|intermediate|advanced|expert``
    * ``monitoringType``  array of enum
    * ``value``    minLength 20
    * ``implementation`` minLength 20
    * ``dataSources``  string (not array)
    * ``grandmaExplanation``  minLength 20
    """

    return {
        "id": uc_id,
        "title": "Test Use Case For Audit Smoke",
        "criticality": "high",
        "difficulty": "beginner",
        "monitoringType": ["Operations"],
        "value": "Detects test conditions for validation purposes.",
        "app": "Splunk Enterprise",
        "dataSources": "test-source",
        "spl": "index=test * | stats count",
        "implementation": "Install the test source and configure the SPL pipeline above.",
        "visualization": "table",
        "cimModels": ["Authentication"],
        "grandmaExplanation": "We look for unusual things on the system and flag them for review.",
        "status": "verified",
        "compliance": [
            {
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.1",
                "mode": "satisfies",
                "assurance": "full",
                "assurance_rationale": "Implements documented review for the clause.",
                "controlObjective": "Documented information security policies.",
                "evidenceArtifact": "saved-search:policies/review",
            }
        ],
    }


_HARNESS_DIR = cm.REPO_ROOT / ".pytest-tmp-compliance-main"


def _setup_main_harness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    uc_docs: list[dict[str, Any]] | None = None,
    regs: dict[str, Any] | None = None,
    golden_tuples: list[dict[str, Any]] | None = None,
    baseline_fingerprints: list[str] | None = None,
) -> dict[str, Path]:
    """Wire ``main()`` to a hermetic fixture rooted under REPO_ROOT.

    The audit's ``_validate_uc_schema`` calls ``uc_path.relative_to(REPO_ROOT)``
    so UC fixtures must live somewhere inside the repo. The harness writes
    them under ``.pytest-tmp-compliance-main/`` and cleans up via
    :func:`_cleanup_harness_dir` in the test's teardown. ``tmp_path`` is
    still used for the bits that don't need to be inside the repo (regs,
    golden, reports).
    """

    _cleanup_harness_dir()
    _HARNESS_DIR.mkdir(exist_ok=True)
    uc_dir = _HARNESS_DIR / "content" / "cat-22-regulatory"
    uc_dir.mkdir(parents=True)

    uc_docs = uc_docs if uc_docs is not None else [_stub_uc_payload_doc()]
    uc_paths = []
    for d in uc_docs:
        p = uc_dir / f"UC-{d['id']}.json"
        p.write_text(json.dumps(d), encoding="utf-8")
        uc_paths.append(p)
    monkeypatch.setattr(cm, "_iter_uc_files", lambda: iter(uc_paths))

    regs_data = regs if regs is not None else _good_regs()
    regs_path = tmp_path / "regulations.json"
    regs_path.write_text(json.dumps(regs_data), encoding="utf-8")
    monkeypatch.setattr(
        cm.RegulationsCatalogue,
        "load",
        classmethod(lambda cls: cls(regs_data)),
    )

    golden_path = tmp_path / "golden.yaml"
    if golden_tuples is None:
        golden_tuples = [
            {
                "uc": "1.1.1",
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.1",
                "mode": "satisfies",
                "min_assurance": "partial",
            }
        ]
    import yaml as _yaml

    golden_path.write_text(_yaml.safe_dump({"tuples": golden_tuples}), encoding="utf-8")
    monkeypatch.setattr(cm, "GOLDEN_PATH", golden_path)

    baseline_path = _HARNESS_DIR / "audit-baseline.json"
    if baseline_fingerprints is not None:
        baseline_path.write_text(
            json.dumps({"version": 1, "fingerprints": baseline_fingerprints}),
            encoding="utf-8",
        )
    else:
        baseline_path.write_text(
            json.dumps({"version": 1, "fingerprints": []}),
            encoding="utf-8",
        )

    report_json = tmp_path / "compliance-coverage.json"
    report_md = tmp_path / "compliance-coverage.md"
    monkeypatch.setattr(cm, "REPORT_JSON", report_json)
    monkeypatch.setattr(cm, "REPORT_MD", report_md)

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")

    return {
        "uc_dir": uc_dir,
        "regs": regs_path,
        "golden": golden_path,
        "baseline": baseline_path,
        "report_json": report_json,
        "report_md": report_md,
    }


def _cleanup_harness_dir() -> None:
    if not _HARNESS_DIR.exists():
        return
    import shutil

    shutil.rmtree(_HARNESS_DIR)


class TestMain:
    def teardown_method(self) -> None:
        _cleanup_harness_dir()

    def test_main_happy_path_returns_zero(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        paths = _setup_main_harness(tmp_path, monkeypatch)
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel])
        assert rc == 0
        # Report files should be written.
        assert paths["report_json"].is_file()
        assert paths["report_md"].is_file()
        # Pretty stdout should contain status banner.
        out = capsys.readouterr().out
        assert "Compliance audit: PASSED" in out

    def test_main_json_only_suppresses_pretty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        paths = _setup_main_harness(tmp_path, monkeypatch)
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel, "--json-only"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Compliance audit:" not in out
        decoded = json.loads(out.strip())
        assert decoded == {"status": "passed", "errors": 0}

    def test_main_no_write_skips_report_files(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _setup_main_harness(tmp_path, monkeypatch)
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel, "--no-write"])
        assert rc == 0
        assert not paths["report_json"].exists()
        assert not paths["report_md"].exists()

    def test_main_fails_when_uc_has_unknown_regulation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bad_uc = _stub_uc_payload_doc()
        bad_uc["compliance"][0]["regulation"] = "made-up"
        paths = _setup_main_harness(tmp_path, monkeypatch, uc_docs=[bad_uc])
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel, "--no-write"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAILED" in out
        assert "unknown-regulation" in out

    def test_main_no_baseline_flag_ignores_baseline_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Even with a baseline that *would* tolerate a finding, --no-baseline
        # should still emit it as a blocking error. Use ``unknown-version``
        # — baselineable and passes the schema gate (the value is still a
        # non-empty string).
        bad_uc = _stub_uc_payload_doc()
        bad_uc["compliance"][0]["version"] = "1999"  # not in stub regs
        paths = _setup_main_harness(tmp_path, monkeypatch, uc_docs=[bad_uc])
        fp_finding = Finding(
            level="error",
            uc_id="1.1.1",
            code="unknown-version",
            message=(
                "regulation 'ISO 27001' (id=iso-27001) has no version "
                "'1999'. Known versions: ['2013', '2022']"
            ),
            path="compliance[0]",
        )
        paths["baseline"].write_text(
            json.dumps({"version": 1, "fingerprints": [fp_finding.fingerprint()]}),
            encoding="utf-8",
        )
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel, "--no-baseline", "--no-write"])
        assert rc == 1

    def test_main_update_baseline_rewrites_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bad_uc = _stub_uc_payload_doc()
        bad_uc["compliance"][0]["version"] = "1999"  # baselineable unknown-version
        paths = _setup_main_harness(tmp_path, monkeypatch, uc_docs=[bad_uc])
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel, "--update-baseline"])
        # --update-baseline always returns 0 (one-shot rewrite)
        assert rc == 0
        stderr = capsys.readouterr().err
        assert "Wrote baseline" in stderr
        payload = json.loads(paths["baseline"].read_text(encoding="utf-8"))
        assert payload["count"] == 1

    def test_main_invalid_uc_skipped_but_counted(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Build a UC missing the required ``title``; schema fails, the UC
        # is *not* counted as valid, but main() still completes.
        bad_uc = _stub_uc_payload_doc()
        del bad_uc["title"]
        paths = _setup_main_harness(tmp_path, monkeypatch, uc_docs=[bad_uc])
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel, "--no-write"])
        assert rc == 1
        # We can't inspect the in-process payload here, but the test
        # exercises the validate→skip branch in main().

    def test_main_writes_payload_with_baseline_meta(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _setup_main_harness(tmp_path, monkeypatch)
        baseline_rel = str(paths["baseline"].relative_to(cm.REPO_ROOT))
        rc = cm.main(["--baseline", baseline_rel])
        assert rc == 0
        payload = json.loads(paths["report_json"].read_text(encoding="utf-8"))
        # The payload should have a baseline meta entry, golden block,
        # coverage block, and findings list.
        assert payload["baseline"]["enabled"] is True
        assert "global" in payload["coverage"]
        assert isinstance(payload["findings"], list)
        # No findings since the happy-path uc + regs are aligned.
        assert payload["counts"]["errors"] == 0
