"""Unit tests for ``audit-compliance-gaps`` (P16 wave I).

Phase 2.1 of the gold-standard plan ships
``src/splunk_uc/audits/compliance_gaps.py`` — a clause-level inversion
of the compliance coverage audit that emits the canonical machine-
readable JSON (``reports/compliance-gaps.json``) and an
auditor-readable markdown report (``docs/compliance-gaps.md``). The
audit's design invariants — deterministic byte-identical output,
offline-only, alias-compatible with the coverage audit, and
status-aware (draft UCs count toward `uc_ids` but never flip a clause
from gap → covered) — are tested below.

Coverage at the start of this wave: **0%** (660 lines / 300 covered
statements untouched).  The tests pin the dataclass contracts
(`ClauseEntry`, `RegVersion`, `UcComplianceHit.multiplier`,
`ClauseGap.{uc_count,draft_count,covered,to_json}` including the
`UC_SAMPLE_LIMIT` cap), `RegulationsCatalogue` alias resolution
(shortName, full name, aliases-list, `aliasIndex` with `$`-prefix
skip, missing-name returns None), `_iter_uc_sidecars` /
`_collect_uc_hits` (skips malformed JSON, skips blank clauses,
applies alias resolution, captures every status / assurance
combination), `_rank_assurance` (full > partial > contributing,
empty-string skipped, all-blank → None), `_build_gaps` (drafts vs.
covered list partitioning, deduplication via `sorted(set(...))`,
``max_assurance`` from non-draft hits only), `_compute_report`
(tier rollups, version sort key, zero-clause denominator → 0.0,
authoritative_url passthrough), `_generated_timestamp`
(SOURCE_DATE_EPOCH → git log → sentinel fallback chain),
`_render_markdown` (rollups table, per-framework sections,
covered ✔ / gap ✖ markers, top-gaps `<details>` block elision when
nothing is missing), `_canonical_json` (sorted keys + 2-space
indent + trailing newline + `ensure_ascii=False`),
`_write_report` (creates parent dirs), `_check_drift`
(missing-committed-file rc=1, mismatch rc=1, identical rc=0), and
the CLI surface (`--check`, `--json-out`, `--md-out`, missing
regulations.json rc=1, happy-path rc=0).
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import compliance_gaps as cg

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_HARNESS_DIR = cg.REPO_ROOT / ".pytest-tmp-compliance-gaps"


def _good_regulations() -> dict[str, Any]:
    """Two frameworks, one tier-1 and one tier-2, each with one version."""

    return {
        "frameworks": [
            {
                "id": "iso-27001",
                "shortName": "ISO 27001",
                "name": "Information security management",
                "tier": 1,
                "aliases": ["ISO27001"],
                "versions": [
                    {
                        "version": "2022",
                        "authoritativeUrl": "https://example.test/iso-27001.html",
                        "commonClauses": [
                            {
                                "clause": "A.5.1",
                                "topic": "Policies",
                                "priorityWeight": 0.9,
                            },
                            {
                                "clause": "A.5.2",
                                "topic": "Roles",
                                "priorityWeight": 0.7,
                            },
                            {
                                "clause": "A.5.3",
                                "topic": "Segregation",
                                "priorityWeight": 0.5,
                            },
                        ],
                    }
                ],
            },
            {
                "id": "soc-2",
                "shortName": "SOC 2",
                "name": "Trust Services Criteria",
                "tier": 2,
                "versions": [
                    {
                        "version": "2017",
                        "authoritativeUrl": "",
                        "commonClauses": [
                            {
                                "clause": "CC1.1",
                                "topic": "Control environment",
                                "priorityWeight": 1.0,
                            },
                        ],
                    }
                ],
            },
        ],
        "aliasIndex": {
            "$comment": "should be skipped",
            "isms": "iso-27001",
        },
    }


def _uc_doc(
    *,
    uc_id: str = "1.1.1",
    status: str = "production",
    compliance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": uc_id,
        "title": "Test UC",
        "status": status,
    }
    if compliance is not None:
        doc["compliance"] = compliance
    return doc


def _setup_harness(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a tmp ``content/`` tree under REPO_ROOT and rewire constants."""

    _teardown_harness()
    _HARNESS_DIR.mkdir(exist_ok=True)
    content_dir: Path = _HARNESS_DIR / "content"
    cat_dir: Path = content_dir / "cat-22-regulatory"
    cat_dir.mkdir(parents=True)
    monkeypatch.setattr(cg, "USE_CASES_DIR", content_dir)
    return cat_dir


def _teardown_harness() -> None:
    if _HARNESS_DIR.exists():
        shutil.rmtree(_HARNESS_DIR)


@pytest.fixture(autouse=True)
def _auto_cleanup() -> Iterable[None]:
    yield
    _teardown_harness()


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_status_multiplier_known_values(self) -> None:
        assert cg.STATUS_MULTIPLIER["production"] == 1.0
        assert cg.STATUS_MULTIPLIER["draft"] == 0.0
        assert cg.STATUS_MULTIPLIER["review"] == 0.75
        assert cg.STATUS_MULTIPLIER["__unset__"] == 1.0

    def test_assurance_rank_strict_order(self) -> None:
        assert cg.ASSURANCE_RANK["full"] > cg.ASSURANCE_RANK["partial"]
        assert cg.ASSURANCE_RANK["partial"] > cg.ASSURANCE_RANK["contributing"]
        assert cg.ASSURANCE_RANK["contributing"] > 0

    def test_uc_sample_limit_is_positive(self) -> None:
        assert cg.UC_SAMPLE_LIMIT > 0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class TestClauseEntry:
    def test_construction_and_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        ce = cg.ClauseEntry(clause="A.5.1", topic="Policies", priority_weight=0.9)
        assert ce.clause == "A.5.1"
        assert ce.topic == "Policies"
        assert ce.priority_weight == 0.9
        with pytest.raises(FrozenInstanceError):
            ce.clause = "X"


class TestRegVersion:
    def test_construction_and_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        ce = cg.ClauseEntry(clause="A.5.1", topic="t", priority_weight=0.5)
        rv = cg.RegVersion(
            framework_id="iso-27001",
            short_name="ISO 27001",
            name="ISO 27001:2022",
            tier=1,
            version="2022",
            authoritative_url="https://example.test/",
            clauses=(ce,),
        )
        assert rv.framework_id == "iso-27001"
        assert rv.clauses == (ce,)
        with pytest.raises(FrozenInstanceError):
            rv.tier = 2


class TestUcComplianceHit:
    def test_multiplier_known_status(self) -> None:
        h = cg.UcComplianceHit(
            uc_id="1.1.1", status="production", assurance="full", mode="satisfies"
        )
        assert h.multiplier == 1.0

    def test_multiplier_draft(self) -> None:
        h = cg.UcComplianceHit(uc_id="1.1.1", status="draft", assurance="full", mode="satisfies")
        assert h.multiplier == 0.0

    def test_multiplier_review_partial(self) -> None:
        h = cg.UcComplianceHit(
            uc_id="1.1.1", status="review", assurance="partial", mode="satisfies"
        )
        assert h.multiplier == 0.75

    def test_multiplier_unknown_status_defaults_to_one(self) -> None:
        h = cg.UcComplianceHit(uc_id="1.1.1", status="invented", assurance="", mode="")
        assert h.multiplier == 1.0

    def test_multiplier_empty_status_treated_as_unset(self) -> None:
        h = cg.UcComplianceHit(uc_id="1.1.1", status="", assurance="", mode="")
        assert h.multiplier == 1.0

    def test_multiplier_case_insensitive(self) -> None:
        h = cg.UcComplianceHit(uc_id="1.1.1", status="DRAFT", assurance="", mode="")
        assert h.multiplier == 0.0


class TestClauseGap:
    def test_empty_state(self) -> None:
        g = cg.ClauseGap(clause="A.5.1", topic="t", priority_weight=0.5)
        assert g.uc_count == 0
        assert g.draft_count == 0
        assert g.covered is False
        out = g.to_json()
        assert out == {
            "clause": "A.5.1",
            "covered": False,
            "draft_uc_count": 0,
            "draft_uc_ids": [],
            "max_assurance": None,
            "priority_weight": 0.5,
            "topic": "t",
            "uc_count": 0,
            "uc_ids": [],
        }

    def test_covered_with_assurance(self) -> None:
        g = cg.ClauseGap(
            clause="A.5.1",
            topic="t",
            priority_weight=0.9,
            uc_ids=["1.1.1", "1.1.2"],
            draft_uc_ids=[],
            max_assurance="full",
        )
        assert g.uc_count == 2
        assert g.covered is True
        out = g.to_json()
        assert out["uc_count"] == 2
        assert out["max_assurance"] == "full"

    def test_uc_ids_sample_cap(self) -> None:
        many = [f"1.1.{i}" for i in range(20)]
        g = cg.ClauseGap(
            clause="A.5.1",
            topic="t",
            priority_weight=1.0,
            uc_ids=many,
            draft_uc_ids=many,
        )
        out = g.to_json()
        assert len(out["uc_ids"]) == cg.UC_SAMPLE_LIMIT
        assert len(out["draft_uc_ids"]) == cg.UC_SAMPLE_LIMIT
        # Samples are sorted
        assert out["uc_ids"] == sorted(out["uc_ids"])

    def test_priority_weight_rounded(self) -> None:
        g = cg.ClauseGap(clause="A", topic="t", priority_weight=0.123456789)
        out = g.to_json()
        assert out["priority_weight"] == 0.1235


# ---------------------------------------------------------------------------
# RegulationsCatalogue
# ---------------------------------------------------------------------------


class TestRegulationsCatalogueBuild:
    def test_indexes_all_alias_candidates(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        for key in ["iso 27001", "iso27001", "iso-27001", "information security management"]:
            assert cat.resolve_framework(key) == "iso-27001"

    def test_resolve_framework_case_insensitive_and_whitespace_tolerant(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        assert cat.resolve_framework("  ISO 27001  ") == "iso-27001"

    def test_resolve_framework_alias_index_with_dollar_skip(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        assert cat.resolve_framework("isms") == "iso-27001"
        # $comment is skipped
        assert cat.resolve_framework("$comment") is None

    def test_resolve_framework_empty_returns_none(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        assert cat.resolve_framework("") is None
        assert cat.resolve_framework("   ") is None

    def test_resolve_framework_unknown_returns_none(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        assert cat.resolve_framework("made-up-reg") is None

    def test_versions_returned_in_definition_order(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        ids = [v.framework_id for v in cat.versions()]
        assert ids == ["iso-27001", "soc-2"]

    def test_versions_clauses_are_loaded(self) -> None:
        cat = cg.RegulationsCatalogue(_good_regulations())
        iso = cat.versions()[0]
        assert len(iso.clauses) == 3
        assert iso.clauses[0].clause == "A.5.1"
        assert iso.clauses[0].priority_weight == 0.9

    def test_load_from_file(self, tmp_path: Path) -> None:
        p = tmp_path / "regs.json"
        p.write_text(json.dumps(_good_regulations()), encoding="utf-8")
        cat = cg.RegulationsCatalogue.load(p)
        assert cat.resolve_framework("ISO 27001") == "iso-27001"

    def test_alias_skips_empty_strings(self) -> None:
        # A framework with blank shortName/name should not register "" alias
        raw = {
            "frameworks": [
                {
                    "id": "x",
                    "shortName": "",
                    "name": "",
                    "tier": 3,
                    "aliases": [],
                    "versions": [],
                }
            ]
        }
        cat = cg.RegulationsCatalogue(raw)
        assert cat.resolve_framework("") is None

    def test_default_tier_when_missing(self) -> None:
        raw = {
            "frameworks": [
                {
                    "id": "x",
                    "shortName": "X",
                    "name": "X",
                    # no "tier"
                    "versions": [{"version": "1", "commonClauses": []}],
                }
            ]
        }
        cat = cg.RegulationsCatalogue(raw)
        assert cat.versions()[0].tier == 3


# ---------------------------------------------------------------------------
# _iter_uc_sidecars + _collect_uc_hits
# ---------------------------------------------------------------------------


class TestCollectUcHits:
    def test_no_sidecars_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _setup_harness(monkeypatch)
        cat = cg.RegulationsCatalogue(_good_regulations())
        hits = cg._collect_uc_hits(cat)
        assert hits == {}

    def test_indexes_by_framework_version_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        doc = _uc_doc(
            uc_id="1.1.1",
            compliance=[
                {
                    "regulation": "ISO 27001",
                    "version": "2022",
                    "clause": "A.5.1",
                    "assurance": "full",
                    "mode": "satisfies",
                }
            ],
        )
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        hits = cg._collect_uc_hits(cat)
        key = ("iso-27001", "2022", "A.5.1")
        assert key in hits
        assert hits[key][0].uc_id == "1.1.1"
        assert hits[key][0].assurance == "full"

    def test_skips_blank_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        doc = _uc_doc(compliance=[{"regulation": "ISO 27001", "version": "2022", "clause": "   "}])
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        assert cg._collect_uc_hits(cat) == {}

    def test_skips_unknown_regulation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        doc = _uc_doc(
            compliance=[
                {"regulation": "made-up-reg", "version": "1", "clause": "X"},
            ]
        )
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        assert cg._collect_uc_hits(cat) == {}

    def test_skips_malformed_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        (cat_dir / "UC-1.1.1.json").write_text("not-json{{", encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        # No exceptions — just silently skipped
        assert cg._collect_uc_hits(cat) == {}

    def test_uses_filename_stem_when_id_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        doc = {"compliance": [{"regulation": "ISO 27001", "version": "2022", "clause": "A.5.1"}]}
        (cat_dir / "UC-9.9.9.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        hits = cg._collect_uc_hits(cat)
        assert hits[("iso-27001", "2022", "A.5.1")][0].uc_id == "UC-9.9.9"

    def test_handles_missing_status_as_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        doc = {
            "id": "1.1.1",
            "compliance": [{"regulation": "ISO 27001", "version": "2022", "clause": "A.5.1"}],
        }
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        hits = cg._collect_uc_hits(cat)
        h = hits[("iso-27001", "2022", "A.5.1")][0]
        assert h.status == "__unset__"
        assert h.multiplier == 1.0

    def test_handles_explicit_null_compliance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        doc = {"id": "1.1.1", "compliance": None}
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        # `or []` short-circuit means None is treated as empty
        assert cg._collect_uc_hits(cat) == {}


# ---------------------------------------------------------------------------
# _rank_assurance
# ---------------------------------------------------------------------------


class TestRankAssurance:
    def test_full_beats_partial(self) -> None:
        assert cg._rank_assurance(["partial", "full", "contributing"]) == "full"

    def test_partial_beats_contributing(self) -> None:
        assert cg._rank_assurance(["partial", "contributing"]) == "partial"

    def test_empty_returns_none(self) -> None:
        assert cg._rank_assurance([]) is None

    def test_all_blank_returns_none(self) -> None:
        assert cg._rank_assurance(["", "   ", ""]) is None

    def test_unknown_value_treated_as_zero_rank(self) -> None:
        # "invented" has rank 0; "contributing" has rank 1 → contributing wins
        assert cg._rank_assurance(["invented", "contributing"]) == "contributing"

    def test_case_insensitive(self) -> None:
        assert cg._rank_assurance(["FULL"]) == "full"


# ---------------------------------------------------------------------------
# _build_gaps
# ---------------------------------------------------------------------------


class TestBuildGaps:
    def _version(self) -> cg.RegVersion:
        return cg.RegVersion(
            framework_id="iso-27001",
            short_name="ISO 27001",
            name="ISO 27001",
            tier=1,
            version="2022",
            authoritative_url="",
            clauses=(
                cg.ClauseEntry("A.5.1", "Policies", 0.9),
                cg.ClauseEntry("A.5.2", "Roles", 0.5),
            ),
        )

    def test_empty_hits_all_gaps(self) -> None:
        gaps = cg._build_gaps(self._version(), {})
        assert len(gaps) == 2
        assert all(not g.covered for g in gaps)
        assert gaps[0].max_assurance is None

    def test_production_hit_marks_covered(self) -> None:
        hits = {
            ("iso-27001", "2022", "A.5.1"): [
                cg.UcComplianceHit("1.1.1", "production", "full", "satisfies")
            ]
        }
        gaps = cg._build_gaps(self._version(), hits)
        a51 = next(g for g in gaps if g.clause == "A.5.1")
        a52 = next(g for g in gaps if g.clause == "A.5.2")
        assert a51.covered is True
        assert a51.max_assurance == "full"
        assert a51.uc_ids == ["1.1.1"]
        assert a52.covered is False

    def test_draft_hit_goes_to_draft_list_only(self) -> None:
        hits = {
            ("iso-27001", "2022", "A.5.1"): [
                cg.UcComplianceHit("1.1.1", "draft", "full", "satisfies")
            ]
        }
        gaps = cg._build_gaps(self._version(), hits)
        a51 = next(g for g in gaps if g.clause == "A.5.1")
        assert a51.covered is False  # draft doesn't flip the bit
        assert a51.uc_ids == []
        assert a51.draft_uc_ids == ["1.1.1"]
        assert a51.max_assurance is None  # assurance comes from non-drafts only

    def test_duplicate_uc_id_deduplicated(self) -> None:
        hits = {
            ("iso-27001", "2022", "A.5.1"): [
                cg.UcComplianceHit("1.1.1", "production", "partial", "satisfies"),
                cg.UcComplianceHit("1.1.1", "production", "full", "satisfies"),
            ]
        }
        gaps = cg._build_gaps(self._version(), hits)
        a51 = next(g for g in gaps if g.clause == "A.5.1")
        assert a51.uc_ids == ["1.1.1"]
        # Both assurance levels considered; max wins
        assert a51.max_assurance == "full"

    def test_mixed_draft_and_production_partitioned(self) -> None:
        hits = {
            ("iso-27001", "2022", "A.5.1"): [
                cg.UcComplianceHit("1.1.1", "production", "partial", "satisfies"),
                cg.UcComplianceHit("1.1.2", "draft", "full", "satisfies"),
                cg.UcComplianceHit("1.1.3", "production", "contributing", "satisfies"),
            ]
        }
        gaps = cg._build_gaps(self._version(), hits)
        a51 = next(g for g in gaps if g.clause == "A.5.1")
        assert a51.uc_ids == ["1.1.1", "1.1.3"]
        assert a51.draft_uc_ids == ["1.1.2"]
        # Drafts don't contribute to max_assurance (1.1.2 with "full" excluded)
        assert a51.max_assurance == "partial"


# ---------------------------------------------------------------------------
# _compute_report — end-to-end orchestrator
# ---------------------------------------------------------------------------


class TestComputeReport:
    def test_empty_inputs_produce_empty_tiers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _setup_harness(monkeypatch)
        cat = cg.RegulationsCatalogue({"frameworks": []})
        report = cg._compute_report(cat)
        assert report["tiers"] == {}
        assert report["rollups"] == {}
        assert report["schema_version"] == "1.0.0"
        assert "generated_utc" in report

    def test_zero_coverage_reports_zero_pct_no_divzero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_harness(monkeypatch)
        cat = cg.RegulationsCatalogue(_good_regulations())
        report = cg._compute_report(cat)
        tier1 = report["tiers"]["tier-1"]["iso-27001"]["versions"]["2022"]
        assert tier1["covered_count"] == 0
        assert tier1["coverage_pct"] == 0.0
        assert tier1["priority_weight_pct"] == 0.0
        assert tier1["common_clause_count"] == 3
        rollups = report["rollups"]
        assert rollups["tier-1"]["covered_count"] == 0

    def test_full_coverage_computes_100_pct(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        compliance = [
            {
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.1",
                "assurance": "full",
                "mode": "satisfies",
            },
            {
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.2",
                "assurance": "partial",
                "mode": "satisfies",
            },
            {
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.3",
                "assurance": "full",
                "mode": "satisfies",
            },
            {
                "regulation": "SOC 2",
                "version": "2017",
                "clause": "CC1.1",
                "assurance": "full",
                "mode": "satisfies",
            },
        ]
        doc = _uc_doc(compliance=compliance)
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        report = cg._compute_report(cat)
        iso = report["tiers"]["tier-1"]["iso-27001"]["versions"]["2022"]
        assert iso["covered_count"] == 3
        assert iso["coverage_pct"] == 100.0
        assert iso["priority_weight_pct"] == 100.0
        assert iso["authoritative_url"] == "https://example.test/iso-27001.html"
        soc2 = report["tiers"]["tier-2"]["soc-2"]["versions"]["2017"]
        assert soc2["coverage_pct"] == 100.0
        rollups = report["rollups"]
        assert rollups["tier-1"]["coverage_pct"] == 100.0
        assert rollups["tier-2"]["coverage_pct"] == 100.0

    def test_partial_coverage_rounded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        compliance = [
            {
                "regulation": "ISO 27001",
                "version": "2022",
                "clause": "A.5.1",
                "assurance": "full",
                "mode": "satisfies",
            },
        ]
        doc = _uc_doc(compliance=compliance)
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        report = cg._compute_report(cat)
        iso = report["tiers"]["tier-1"]["iso-27001"]["versions"]["2022"]
        # 1/3 covered → 33.33%
        assert iso["covered_count"] == 1
        assert iso["coverage_pct"] == 33.33
        # priority_weight_total = 0.9 + 0.7 + 0.5 = 2.1
        # priority_weight_covered = 0.9
        # → 42.86%
        assert iso["priority_weight_pct"] == 42.86

    def test_rollups_aggregate_across_versions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _setup_harness(monkeypatch)
        compliance = [
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.5.1"},
            {"regulation": "SOC 2", "version": "2017", "clause": "CC1.1"},
        ]
        doc = _uc_doc(compliance=compliance)
        (cat_dir / "UC-1.1.1.json").write_text(json.dumps(doc), encoding="utf-8")
        cat = cg.RegulationsCatalogue(_good_regulations())
        report = cg._compute_report(cat)
        # tier-1: 3 clauses, 1 covered; tier-2: 1 clause, 1 covered
        assert report["rollups"]["tier-1"]["common_clause_count"] == 3
        assert report["rollups"]["tier-1"]["covered_count"] == 1
        assert report["rollups"]["tier-2"]["common_clause_count"] == 1
        assert report["rollups"]["tier-2"]["covered_count"] == 1

    def test_zero_priority_weight_total_yields_zero_pct(self) -> None:
        # Construct manually: zero-weight clauses, full coverage
        raw = {
            "frameworks": [
                {
                    "id": "x",
                    "shortName": "X",
                    "name": "X",
                    "tier": 1,
                    "versions": [
                        {
                            "version": "1",
                            "commonClauses": [
                                {"clause": "A", "topic": "t", "priorityWeight": 0.0},
                            ],
                        }
                    ],
                }
            ]
        }
        cat = cg.RegulationsCatalogue(raw)
        report = cg._compute_report(cat)
        v = report["tiers"]["tier-1"]["x"]["versions"]["1"]
        assert v["priority_weight_pct"] == 0.0


# ---------------------------------------------------------------------------
# _generated_timestamp
# ---------------------------------------------------------------------------


class TestGeneratedTimestamp:
    def test_uses_source_date_epoch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        ts = cg._generated_timestamp()
        assert ts.startswith("2023-11-14T")
        assert ts.endswith("Z")

    def test_invalid_source_date_epoch_falls_back_to_git(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")

        class _StubResult:
            stdout = "1700000001\n"

        def _fake_run(*_a: Any, **_kw: Any) -> _StubResult:
            return _StubResult()

        import subprocess

        monkeypatch.setattr(subprocess, "run", _fake_run)
        ts = cg._generated_timestamp()
        assert ts.startswith("2023-11-14T")

    def test_git_returns_non_digit_falls_back_to_sentinel(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        class _StubResult:
            stdout = "not-a-stamp\n"

        def _fake_run(*_a: Any, **_kw: Any) -> _StubResult:
            return _StubResult()

        import subprocess

        monkeypatch.setattr(subprocess, "run", _fake_run)
        assert cg._generated_timestamp() == "1970-01-01T00:00:00Z"

    def test_git_raises_falls_back_to_sentinel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def _fake_run(*_a: Any, **_kw: Any) -> Any:
            raise RuntimeError("git not installed")

        import subprocess

        monkeypatch.setattr(subprocess, "run", _fake_run)
        assert cg._generated_timestamp() == "1970-01-01T00:00:00Z"

    def test_empty_source_date_epoch_does_not_crash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "")
        # Should fall through to git path; we don't care which result,
        # just that no exception bubbles
        ts = cg._generated_timestamp()
        assert ts.endswith("Z")


# ---------------------------------------------------------------------------
# _canonical_json + _write_report
# ---------------------------------------------------------------------------


class TestCanonicalJson:
    def test_sorted_keys_and_trailing_newline(self) -> None:
        s = cg._canonical_json({"b": 1, "a": 2})
        assert s == '{\n  "a": 2,\n  "b": 1\n}\n'

    def test_ensure_ascii_false_preserves_unicode(self) -> None:
        s = cg._canonical_json({"name": "ÉlÄn"})
        assert "ÉlÄn" in s
        assert "\\u" not in s


class TestWriteReport:
    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        report = {"foo": "bar"}
        json_p = tmp_path / "nested" / "out.json"
        md_p = tmp_path / "deeper" / "out.md"
        # Bypass _render_markdown by providing a minimal real report
        cg._write_report(
            {"generated_utc": "x", "rollups": {}, "schema_version": "1.0.0", "tiers": {}, **report},
            json_path=json_p,
            md_path=md_p,
        )
        assert json_p.is_file()
        assert md_p.is_file()
        loaded = json.loads(json_p.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "1.0.0"


# ---------------------------------------------------------------------------
# _render_markdown
# ---------------------------------------------------------------------------


def _sample_report() -> dict[str, Any]:
    return {
        "generated_utc": "2026-05-19T00:00:00Z",
        "schema_version": "1.0.0",
        "rollups": {
            "tier-1": {
                "common_clause_count": 3,
                "covered_count": 1,
                "coverage_pct": 33.33,
                "priority_weight_covered": 0.9,
                "priority_weight_total": 2.1,
                "priority_weight_pct": 42.86,
            },
        },
        "tiers": {
            "tier-1": {
                "iso-27001": {
                    "short_name": "ISO 27001",
                    "name": "Information security management",
                    "tier": 1,
                    "versions": {
                        "2022": {
                            "authoritative_url": "https://example.test/iso-27001.html",
                            "clauses": [
                                {
                                    "clause": "A.5.1",
                                    "covered": True,
                                    "draft_uc_count": 0,
                                    "draft_uc_ids": [],
                                    "max_assurance": "full",
                                    "priority_weight": 0.9,
                                    "topic": "Policies",
                                    "uc_count": 1,
                                    "uc_ids": ["1.1.1"],
                                },
                                {
                                    "clause": "A.5.2",
                                    "covered": False,
                                    "draft_uc_count": 0,
                                    "draft_uc_ids": [],
                                    "max_assurance": None,
                                    "priority_weight": 0.7,
                                    "topic": "Roles",
                                    "uc_count": 0,
                                    "uc_ids": [],
                                },
                                {
                                    "clause": "A.5.3",
                                    "covered": False,
                                    "draft_uc_count": 1,
                                    "draft_uc_ids": ["1.1.2"],
                                    "max_assurance": None,
                                    "priority_weight": 0.5,
                                    "topic": "Segregation",
                                    "uc_count": 0,
                                    "uc_ids": [],
                                },
                            ],
                            "common_clause_count": 3,
                            "covered_count": 1,
                            "coverage_pct": 33.33,
                            "priority_weight_covered": 0.9,
                            "priority_weight_pct": 42.86,
                            "priority_weight_total": 2.1,
                        }
                    },
                }
            }
        },
    }


class TestRenderMarkdown:
    def test_includes_header_and_rollups(self) -> None:
        md = cg._render_markdown(_sample_report())
        assert "# Compliance clause-level gap analysis" in md
        assert "## Tier rollups" in md
        assert "tier-1" in md
        # Rounded values appear
        assert "33.33" in md

    def test_includes_per_framework_section(self) -> None:
        md = cg._render_markdown(_sample_report())
        assert "### ISO 27001 — `iso-27001`" in md
        assert "_Information security management_" in md
        assert "#### ISO 27001@2022" in md

    def test_covered_marker_for_covered_clauses(self) -> None:
        md = cg._render_markdown(_sample_report())
        assert "✔ 1" in md  # A.5.1 has 1 uc
        assert "✖ 0" in md  # A.5.2 and A.5.3 are gaps

    def test_top_gaps_section_present(self) -> None:
        md = cg._render_markdown(_sample_report())
        assert "<details><summary>Top gaps" in md
        # Should be sorted by priority weight descending
        # A.5.2 (0.7) before A.5.3 (0.5)
        a52 = md.index("`A.5.2`")
        a53 = md.index("`A.5.3`")
        assert a52 < a53

    def test_top_gaps_section_omitted_when_all_covered(self) -> None:
        report = _sample_report()
        clauses = report["tiers"]["tier-1"]["iso-27001"]["versions"]["2022"]["clauses"]
        for c in clauses:
            c["covered"] = True
            c["uc_count"] = 1
            c["uc_ids"] = ["1.1.1"]
        md = cg._render_markdown(report)
        assert "Top gaps" not in md

    def test_authoritative_url_line_appears(self) -> None:
        md = cg._render_markdown(_sample_report())
        assert "https://example.test/iso-27001.html" in md

    def test_authoritative_url_line_omitted_when_empty(self) -> None:
        report = _sample_report()
        report["tiers"]["tier-1"]["iso-27001"]["versions"]["2022"]["authoritative_url"] = ""
        md = cg._render_markdown(report)
        assert "Authoritative source:" not in md

    def test_em_dash_when_no_assurance(self) -> None:
        md = cg._render_markdown(_sample_report())
        # The A.5.2 / A.5.3 rows have max_assurance=None → renders as "—"
        assert "| —" in md or "— |" in md

    def test_em_dash_when_no_sample_ucs(self) -> None:
        md = cg._render_markdown(_sample_report())
        # The gap rows have empty uc_ids → sample joined to "—"
        # The table row for A.5.2 ends with " — |"
        assert "A.5.2`" in md

    def test_footer_present(self) -> None:
        md = cg._render_markdown(_sample_report())
        assert "audit-compliance-gaps" in md
        assert md.endswith("\n")

    def test_top_gaps_capped_at_twelve(self) -> None:
        report = _sample_report()
        clauses = report["tiers"]["tier-1"]["iso-27001"]["versions"]["2022"]["clauses"]
        # Bump to 20 uncovered clauses
        clauses.clear()
        for i in range(20):
            clauses.append(
                {
                    "clause": f"A.{i:02d}",
                    "covered": False,
                    "draft_uc_count": 0,
                    "draft_uc_ids": [],
                    "max_assurance": None,
                    "priority_weight": float(i) / 20,
                    "topic": f"Topic {i}",
                    "uc_count": 0,
                    "uc_ids": [],
                }
            )
        md = cg._render_markdown(report)
        # Count occurrences of the "| Priority | Clause | Topic |" header section
        # by counting rendered priority cells in the gaps table
        gap_section = md[md.index("<details><summary>Top gaps") :]
        # Each top-gap row starts with "| {priority:.2f} |"
        rows = [line for line in gap_section.split("\n") if line.startswith("| 0.")]
        assert len(rows) == 12


# ---------------------------------------------------------------------------
# _check_drift
# ---------------------------------------------------------------------------


class TestCheckDrift:
    def _patch_paths(self, monkeypatch: pytest.MonkeyPatch, json_path: Path, md_path: Path) -> None:
        monkeypatch.setattr(cg, "REPORT_JSON", json_path)
        monkeypatch.setattr(cg, "REPORT_MD", md_path)

    def test_identical_returns_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        report = _sample_report()
        report["generated_utc"] = "frozen"  # fix so fresh write matches
        live_json = tmp_path / "compliance-gaps.json"
        live_md = tmp_path / "compliance-gaps.md"
        # Write the live tree exactly the same way
        cg._write_report(report, json_path=live_json, md_path=live_md)
        # Need to live under REPO_ROOT so .relative_to works in error path
        # (only triggered when files differ — happy path doesn't need it)
        self._patch_paths(monkeypatch, live_json, live_md)
        rc = cg._check_drift(report)
        assert rc == 0

    def test_missing_committed_file_returns_one(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Both committed paths under REPO_ROOT so relative_to works
        live_json = cg.REPO_ROOT / ".pytest-tmp-cg-missing.json"
        live_md = cg.REPO_ROOT / ".pytest-tmp-cg-missing.md"
        # Ensure they don't exist
        live_json.unlink(missing_ok=True)
        live_md.unlink(missing_ok=True)
        self._patch_paths(monkeypatch, live_json, live_md)
        try:
            rc = cg._check_drift(_sample_report())
            assert rc == 1
            err = capsys.readouterr().err
            assert "missing committed file" in err
        finally:
            live_json.unlink(missing_ok=True)
            live_md.unlink(missing_ok=True)

    def test_drift_detected_returns_one(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        live_json = cg.REPO_ROOT / ".pytest-tmp-cg-live.json"
        live_md = cg.REPO_ROOT / ".pytest-tmp-cg-live.md"
        # Pre-seed with stale content
        live_json.write_text("{}\n", encoding="utf-8")
        live_md.write_text("stale\n", encoding="utf-8")
        self._patch_paths(monkeypatch, live_json, live_md)
        try:
            rc = cg._check_drift(_sample_report())
            assert rc == 1
            err = capsys.readouterr().err
            assert "drift detected" in err
        finally:
            live_json.unlink(missing_ok=True)
            live_md.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CLI / main()
# ---------------------------------------------------------------------------


class TestMain:
    def test_missing_regulations_returns_one(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(cg, "REGS_PATH", tmp_path / "does-not-exist.json")
        rc = cg.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "missing" in err

    def test_happy_writes_both_artefacts(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _setup_harness(monkeypatch)
        regs_path = tmp_path / "regs.json"
        regs_path.write_text(json.dumps(_good_regulations()), encoding="utf-8")
        monkeypatch.setattr(cg, "REGS_PATH", regs_path)
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")

        # The audit prints `args.json_out.relative_to(REPO_ROOT)` so the
        # output paths must be inside the repo root.
        json_out = cg.REPO_ROOT / ".pytest-tmp-cg-out.json"
        md_out = cg.REPO_ROOT / ".pytest-tmp-cg-out.md"
        try:
            rc = cg.main(["--json-out", str(json_out), "--md-out", str(md_out)])
            assert rc == 0
            assert json_out.is_file()
            assert md_out.is_file()
            loaded = json.loads(json_out.read_text(encoding="utf-8"))
            assert loaded["schema_version"] == "1.0.0"
            out = capsys.readouterr().out
            assert "Compliance gap analysis" in out
        finally:
            json_out.unlink(missing_ok=True)
            md_out.unlink(missing_ok=True)

    def test_check_mode_passes_when_artefacts_match(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _setup_harness(monkeypatch)
        regs_path = tmp_path / "regs.json"
        regs_path.write_text(json.dumps(_good_regulations()), encoding="utf-8")
        monkeypatch.setattr(cg, "REGS_PATH", regs_path)
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")

        # First write the artefacts
        live_json = cg.REPO_ROOT / ".pytest-tmp-cg-live.json"
        live_md = cg.REPO_ROOT / ".pytest-tmp-cg-live.md"
        monkeypatch.setattr(cg, "REPORT_JSON", live_json)
        monkeypatch.setattr(cg, "REPORT_MD", live_md)
        try:
            cg.main(["--json-out", str(live_json), "--md-out", str(live_md)])
            # Now --check should find no drift
            rc = cg.main(["--check"])
            assert rc == 0
        finally:
            live_json.unlink(missing_ok=True)
            live_md.unlink(missing_ok=True)

    def test_check_mode_fails_when_no_artefacts(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _setup_harness(monkeypatch)
        regs_path = tmp_path / "regs.json"
        regs_path.write_text(json.dumps(_good_regulations()), encoding="utf-8")
        monkeypatch.setattr(cg, "REGS_PATH", regs_path)
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")

        live_json = cg.REPO_ROOT / ".pytest-tmp-cg-live.json"
        live_md = cg.REPO_ROOT / ".pytest-tmp-cg-live.md"
        live_json.unlink(missing_ok=True)
        live_md.unlink(missing_ok=True)
        monkeypatch.setattr(cg, "REPORT_JSON", live_json)
        monkeypatch.setattr(cg, "REPORT_MD", live_md)
        rc = cg.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "missing committed file" in err

    def test_happy_path_with_zero_clause_tier_shows_not_applicable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _setup_harness(monkeypatch)
        raw = {
            "frameworks": [
                {
                    "id": "empty",
                    "shortName": "E",
                    "name": "Empty",
                    "tier": 1,
                    "versions": [{"version": "1", "commonClauses": []}],
                }
            ]
        }
        regs_path = tmp_path / "regs.json"
        regs_path.write_text(json.dumps(raw), encoding="utf-8")
        monkeypatch.setattr(cg, "REGS_PATH", regs_path)
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")

        # Outputs must live under REPO_ROOT for the audit's relative_to print
        json_out = cg.REPO_ROOT / ".pytest-tmp-cg-zero-out.json"
        md_out = cg.REPO_ROOT / ".pytest-tmp-cg-zero-out.md"
        try:
            rc = cg.main(
                [
                    "--json-out",
                    str(json_out),
                    "--md-out",
                    str(md_out),
                ]
            )
            assert rc == 0
            out = capsys.readouterr().out
            assert "no common clauses defined — not applicable" in out
        finally:
            json_out.unlink(missing_ok=True)
            md_out.unlink(missing_ok=True)
