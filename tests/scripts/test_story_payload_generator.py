"""Hermetic coverage suite for ``splunk_uc.generators.story_payload``.

Mission: lift the per-regulation story payload generator from 0% to
100% combined coverage. Mirrors the contracts used by the rest of the
``api/v1/compliance`` family (deterministic timestamps, canonical JSON,
``--check`` drift detection) so a regression to any of the buyer /
auditor / implementer / deep-coverage blocks blocks CI rather than
shipping silently to ``compliance-story.html``.

All tests are hermetic: every external surface (REPO_ROOT, file paths,
subprocess, time.gmtime) is monkeypatched onto a ``tmp_path``-rooted
fake repository so the suite is parallel-safe and contains no real-FS
writes outside ``tmp_path``.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any

import pytest

from splunk_uc.generators import story_payload as sp

# ---------------------------------------------------------------------------
# Fake-repo plumbing
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    """Build a minimal fake repo, then re-point every module-level Path
    constant at it so individual tests can populate exactly the files
    they need."""
    repo = tmp_path
    (repo / "data" / "per-regulation").mkdir(parents=True)
    (repo / "data").mkdir(exist_ok=True)
    (repo / "api" / "v1" / "compliance" / "regulations").mkdir(parents=True)
    (repo / "api" / "v1" / "compliance" / "clauses").mkdir(parents=True)
    (repo / "api" / "v1" / "compliance" / "story").mkdir(parents=True)
    (repo / "docs" / "evidence-packs").mkdir(parents=True)

    monkeypatch.setattr(sp, "REPO_ROOT", repo)
    monkeypatch.setattr(sp, "REGULATIONS_PATH", repo / "data" / "regulations.json")
    monkeypatch.setattr(sp, "REGS_DIR", repo / "api" / "v1" / "compliance" / "regulations")
    monkeypatch.setattr(sp, "CLAUSES_DIR", repo / "api" / "v1" / "compliance" / "clauses")
    monkeypatch.setattr(sp, "OUT_DIR", repo / "api" / "v1" / "compliance" / "story")
    monkeypatch.setattr(sp, "VERSION_FILE", repo / "VERSION")
    monkeypatch.setattr(sp, "EVIDENCE_PACK_DIR", repo / "docs" / "evidence-packs")
    monkeypatch.setattr(sp, "PRIMER_PATH", repo / "docs" / "regulatory-primer.md")
    monkeypatch.setattr(
        sp,
        "NIS2_MATRIX_PATH",
        repo / "data" / "per-regulation" / "nis2-coverage-expansion.json",
    )
    monkeypatch.setattr(
        sp, "NIS2_SOURCE_MAP_PATH", repo / "data" / "nis2-source-map.json"
    )
    return repo


# ---------------------------------------------------------------------------
# IO + timestamp helpers
# ---------------------------------------------------------------------------


class TestDeterministicTimestamp:
    def test_uses_source_date_epoch_when_present(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        assert sp._deterministic_timestamp() == "2023-11-14T22:13:20Z"

    def test_ignores_non_digit_source_date_epoch_and_falls_through(
        self, monkeypatch: pytest.MonkeyPatch, fake_repo: pathlib.Path
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")

        def fake_run(*args: Any, **kw: Any):
            raise FileNotFoundError("git")

        monkeypatch.setattr(sp.subprocess, "run", fake_run)
        ts = sp._deterministic_timestamp()
        assert ts.endswith("Z") and "T" in ts

    def test_uses_git_committer_timestamp(
        self, monkeypatch: pytest.MonkeyPatch, fake_repo: pathlib.Path
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def fake_run(*args: Any, **kw: Any):
            return subprocess.CompletedProcess(
                args=args[0], returncode=0, stdout="1700000000\n", stderr=""
            )

        monkeypatch.setattr(sp.subprocess, "run", fake_run)
        assert sp._deterministic_timestamp() == "2023-11-14T22:13:20Z"

    def test_git_timeout_then_wall_clock_fallback(
        self, monkeypatch: pytest.MonkeyPatch, fake_repo: pathlib.Path
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def fake_run(*args: Any, **kw: Any):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=3)

        monkeypatch.setattr(sp.subprocess, "run", fake_run)
        ts = sp._deterministic_timestamp()
        assert ts.endswith("Z")

    def test_git_non_digit_stdout_falls_through(
        self, monkeypatch: pytest.MonkeyPatch, fake_repo: pathlib.Path
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def fake_run(*args: Any, **kw: Any):
            return subprocess.CompletedProcess(
                args=args[0], returncode=0, stdout="not-a-stamp\n", stderr=""
            )

        monkeypatch.setattr(sp.subprocess, "run", fake_run)
        ts = sp._deterministic_timestamp()
        assert ts.endswith("Z")


class TestJsonIo:
    def test_load_json_roundtrip(self, tmp_path: pathlib.Path) -> None:
        target = tmp_path / "x.json"
        target.write_text('{"a": 1}', encoding="utf-8")
        assert sp._load_json(target) == {"a": 1}

    def test_write_json_creates_parents_and_sorts(self, tmp_path: pathlib.Path) -> None:
        target = tmp_path / "deep" / "child" / "out.json"
        sp._write_json(target, {"z": 1, "a": 2})
        text = target.read_text(encoding="utf-8")
        assert text.startswith('{\n  "a": 2,')
        assert text.endswith("\n")


class TestReadVersion:
    def test_present_file_returns_stripped(self, fake_repo: pathlib.Path) -> None:
        (fake_repo / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        assert sp._read_version() == "9.9.9"

    def test_missing_file_returns_zero(self, fake_repo: pathlib.Path) -> None:
        assert sp._read_version() == "0.0.0"


# ---------------------------------------------------------------------------
# UC index loader
# ---------------------------------------------------------------------------


class TestLoadUcIndex:
    def _write_uc(self, repo: pathlib.Path, uc_id: str, extra: dict[str, Any]) -> None:
        cat = repo / "content" / "cat-01-foo"
        cat.mkdir(parents=True, exist_ok=True)
        payload = {"id": uc_id, **extra}
        (cat / f"UC-{uc_id}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def test_skips_malformed_and_missing_id(self, fake_repo: pathlib.Path) -> None:
        self._write_uc(fake_repo, "1.1.1", {"title": "T1", "criticality": "high"})
        cat = fake_repo / "content" / "cat-01-foo"
        # malformed JSON
        (cat / "UC-1.1.2.json").write_text("not json", encoding="utf-8")
        # missing id
        (cat / "UC-1.1.3.json").write_text('{"title": "no-id"}', encoding="utf-8")
        # id wrong type
        (cat / "UC-1.1.4.json").write_text('{"id": 99}', encoding="utf-8")
        idx = sp.load_uc_index()
        assert set(idx) == {"1.1.1"}
        assert idx["1.1.1"]["title"] == "T1"


# ---------------------------------------------------------------------------
# Sort keys
# ---------------------------------------------------------------------------


class TestUcSortKey:
    def test_returns_int_triple_for_valid_id(self) -> None:
        assert sp._uc_sort_key_from_id("1.2.3") == (1, 2, 3)

    def test_returns_sentinel_for_invalid_id(self) -> None:
        assert sp._uc_sort_key_from_id("garbage") == (1_000_000, 1_000_000, 1_000_000)


# ---------------------------------------------------------------------------
# Narrative loader
# ---------------------------------------------------------------------------


class TestLoadCat22Areas:
    def test_returns_empty_when_source_missing(self, fake_repo: pathlib.Path) -> None:
        assert sp.load_cat22_areas() == {}

    def test_parses_areas_with_optional_fields(self, fake_repo: pathlib.Path) -> None:
        src = fake_repo / "non-technical-view.js"
        src.write_text(
            'var NON_TECHNICAL = {\n'
            '  "22": {\n'
            '    areas: [\n'
            '      { name: "GDPR compliance", whatItIs: "EU privacy law", '
            'whoItAffects: "Any org processing EU data", '
            'splunkValue: "Detection + evidence", '
            'primer: "docs/regulatory-primer.md#gdpr", '
            'evidencePack: "docs/evidence-packs/gdpr.md" },\n'
            '      { name: "Quick name only" },\n'
            '    ],\n'
            '  },\n'
            '  "23": { areas: [] }\n'
            '};\n',
            encoding="utf-8",
        )
        areas = sp.load_cat22_areas()
        assert "gdpr compliance" in areas
        gdpr = areas["gdpr compliance"]
        assert gdpr["whatItIs"] == "EU privacy law"
        assert gdpr["primer"] == "docs/regulatory-primer.md#gdpr"
        # Optional fields default to None on the bare entry.
        assert areas["quick name only"]["whatItIs"] is None

    def test_falls_back_to_window_open_ended_when_no_closing_marker(
        self, fake_repo: pathlib.Path
    ) -> None:
        src = fake_repo / "non-technical-view.js"
        src.write_text(
            'var NON_TECHNICAL = {\n'
            '  "22": {\n'
            '    areas: [\n'
            '      { name: "Only-One" }\n'
            '    ]\n'
            '  }\n'
            '};\n',
            encoding="utf-8",
        )
        areas = sp.load_cat22_areas()
        assert "only-one" in areas

    def test_returns_empty_when_cat22_marker_missing(
        self, fake_repo: pathlib.Path
    ) -> None:
        src = fake_repo / "non-technical-view.js"
        src.write_text(
            'var NON_TECHNICAL = { "21": {}, "23": {} };', encoding="utf-8"
        )
        assert sp.load_cat22_areas() == {}

    def test_skips_lines_without_name_marker(self, fake_repo: pathlib.Path) -> None:
        src = fake_repo / "non-technical-view.js"
        src.write_text(
            'var NON_TECHNICAL = {\n'
            '  "22": {\n'
            '    areas: [\n'
            '      "ignored-line",\n'
            # A line that contains "name:" but no quoted value — the
            # inner regex must fail and the parser bails out.
            '      // todo: rename: this area later\n'
            '      { name: "Real" },\n'
            '    ]\n'
            '  },\n'
            '  "23": {}\n'
            '};\n',
            encoding="utf-8",
        )
        areas = sp.load_cat22_areas()
        assert "real" in areas


class TestNarrativeForRegulation:
    def test_manual_map_hit(self) -> None:
        areas = {"gdpr compliance": {"name": "GDPR compliance"}}
        rec = sp.narrative_for_regulation("gdpr", "GDPR", areas)
        assert rec == {"name": "GDPR compliance", "matchedBy": "manual-map"}

    def test_manual_map_miss_falls_to_fuzzy(self) -> None:
        areas = {"general data protection": {"name": "General Data Protection"}}
        rec = sp.narrative_for_regulation("zzz", "data", areas)
        assert rec is not None
        assert rec["matchedBy"] == "fuzzy-shortname"

    def test_returns_none_when_nothing_matches(self) -> None:
        areas = {"hipaa": {"name": "HIPAA"}}
        assert sp.narrative_for_regulation("zzz", "totally-unrelated", areas) is None

    def test_manual_map_with_missing_area_falls_to_fuzzy(self) -> None:
        # "gdpr" is mapped to "GDPR compliance" but only "GDPR something"
        # is in areas — manual-map miss → fuzzy on the short name.
        areas = {"gdpr something": {"name": "GDPR something"}}
        rec = sp.narrative_for_regulation("gdpr", "gdpr", areas)
        assert rec is not None
        assert rec["matchedBy"] == "fuzzy-shortname"


class TestNarrativeSlug:
    def test_lowercases_and_collapses_nonalnum(self) -> None:
        assert sp._narrative_slug("GDPR Compliance!") == "gdpr-compliance"

    def test_empty_when_only_punctuation(self) -> None:
        assert sp._narrative_slug("---!!!") == ""


# ---------------------------------------------------------------------------
# Pure ranking helpers
# ---------------------------------------------------------------------------


class TestCriticalityScore:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("critical", 4),
            ("High", 3),
            ("MEDIUM", 2),
            ("low", 1),
            ("unknown", 0),
            (None, 0),
            (5, 0),
        ],
    )
    def test_scores(self, value: Any, expected: int) -> None:
        assert sp._criticality_score(value) == expected


class TestUcPlaybookRank:
    def test_assurance_and_criticality_both_lowercased(self) -> None:
        uc_index = {"1.1.1": {"criticality": "critical"}}
        row = {"ucId": "1.1.1", "assurance": "FULL"}
        key = sp._uc_playbook_rank(row, uc_index)
        # -ASSURANCE_RANK[full]=-3, -CRITICALITY[critical]=-4, sort=(1,1,1)
        assert key == (-3, -4, (1, 1, 1))

    def test_fallbacks_from_uc_index(self) -> None:
        uc_index = {"2.2.2": {"assurance": "partial", "criticality": "high"}}
        row = {"ucId": "2.2.2"}
        assert sp._uc_playbook_rank(row, uc_index) == (-2, -3, (2, 2, 2))


# ---------------------------------------------------------------------------
# Build blocks: auditor / implementer / buyer
# ---------------------------------------------------------------------------


class TestBuildAuditorBlock:
    def test_skips_versions_without_string_version(self) -> None:
        reg = {
            "versions": [
                {"version": 12, "clauseCoverageMatrix": [{"clause": "X"}]},
                {"version": "v1", "clauseCoverageMatrix": [{"clause": "A"}]},
                {"version": "v1", "clauseCoverageMatrix": [{"clause": "B"}]},
            ]
        }
        out = sp.build_auditor_block(reg)
        assert [r["clause"] for r in out] == ["A", "B"]
        for row in out:
            assert row["version"] == "v1"

    def test_handles_empty_versions(self) -> None:
        assert sp.build_auditor_block({}) == []


class TestLoadDetailedClause:
    def test_returns_none_when_file_missing(self, fake_repo: pathlib.Path) -> None:
        assert sp._load_detailed_clause("gdpr", "2016/679", "Art.32") is None

    def test_returns_payload_when_file_present(self, fake_repo: pathlib.Path) -> None:
        # urllib.quote("2016/679", safe="-._") → "2016%2F679", then
        # .replace("/", "_") leaves the %2F percent-escape untouched.
        target = sp.CLAUSES_DIR / "gdpr__2016%2F679__Art.32.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"clause": "Art.32"}), encoding="utf-8")
        out = sp._load_detailed_clause("gdpr", "2016/679", "Art.32")
        assert out == {"clause": "Art.32"}

    def test_returns_none_when_payload_not_dict(self, fake_repo: pathlib.Path) -> None:
        target = sp.CLAUSES_DIR / "gdpr__v1__Art.10.json"
        target.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        assert sp._load_detailed_clause("gdpr", "v1", "Art.10") is None


class TestBuildImplementerBlock:
    def test_empty_when_no_versions(self) -> None:
        assert sp.build_implementer_block({}, {}) == []

    def test_skips_non_string_versions(self) -> None:
        reg = {"versions": [{"version": 99, "clauseCoverageMatrix": [{"clause": "A", "coveringUcs": ["1.1.1"]}]}]}
        assert sp.build_implementer_block(reg, {}) == []

    def test_skips_clauses_without_covering(self) -> None:
        reg = {
            "id": "gdpr",
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {"clause": "A", "coveringUcs": [], "priorityWeight": 0.5}
                    ],
                }
            ],
        }
        assert sp.build_implementer_block(reg, {}) == []

    def test_uses_uc_index_fallback_when_no_detail_file(
        self, fake_repo: pathlib.Path
    ) -> None:
        reg = {
            "id": "gdpr",
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {
                            "clause": "A",
                            "coveringUcs": ["1.1.1", "1.1.2"],
                            "topic": "TopicA",
                            "priorityWeight": 0.9,
                            "coverageState": "covered-full",
                        }
                    ],
                }
            ],
        }
        uc_index = {
            "1.1.1": {"title": "First", "criticality": "high"},
            "1.1.2": {"title": "Second", "criticality": "low"},
        }
        out = sp.build_implementer_block(reg, uc_index)
        assert len(out) == 1
        playbook = out[0]
        assert playbook["clause"] == "A"
        # No detail → scored from uc_index, no assurance, ranked by criticality.
        # "1.1.1" has higher criticality (high>low), so it ranks first.
        assert [u["ucId"] for u in playbook["quickStartUcs"]] == ["1.1.1", "1.1.2"]
        assert playbook["quickStartUcs"][0]["assurance"] is None

    def test_detail_file_overrides_uc_index(self, fake_repo: pathlib.Path) -> None:
        # Write a per-clause detail file under clauses/.
        # filename = "gdpr__v1__A.json"
        (sp.CLAUSES_DIR / "gdpr__v1__A.json").write_text(
            json.dumps(
                {
                    "coveringUcs": [
                        {
                            "ucId": "1.1.2",
                            "ucTitle": "Detail title",
                            "assurance": "full",
                            "mode": "control",
                            "controlObjective": "obj",
                            "evidenceArtifact": "ev",
                            "criticality": "critical",
                        },
                        {
                            "ucId": "1.1.1",
                            "ucTitle": "",
                            "assurance": "partial",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        reg = {
            "id": "gdpr",
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {
                            "clause": "A",
                            "coveringUcs": ["1.1.1", "1.1.2"],
                            "priorityWeight": 1.0,
                        }
                    ],
                }
            ],
        }
        uc_index = {"1.1.1": {"criticality": "low"}, "1.1.2": {"criticality": "low"}}
        out = sp.build_implementer_block(reg, uc_index, max_ucs_per_clause=2)
        # 1.1.2 has assurance=full → ranks first.
        assert [u["ucId"] for u in out[0]["quickStartUcs"]] == ["1.1.2", "1.1.1"]
        # And criticality from the detail wins over the (low) uc_index hint.
        assert out[0]["quickStartUcs"][0]["criticality"] == "critical"

    def test_max_ucs_truncates(self) -> None:
        reg = {
            "id": "gdpr",
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {
                            "clause": "A",
                            "coveringUcs": ["1.1.1", "1.1.2", "1.1.3"],
                            "priorityWeight": 1.0,
                        }
                    ],
                }
            ],
        }
        out = sp.build_implementer_block(reg, {}, max_ucs_per_clause=2)
        assert len(out[0]["quickStartUcs"]) == 2

    def test_playbook_sorted_by_priority_then_version_then_clause(self) -> None:
        reg = {
            "id": "gdpr",
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {"clause": "B", "coveringUcs": ["1.1.1"], "priorityWeight": 0.5},
                        {"clause": "A", "coveringUcs": ["1.1.2"], "priorityWeight": 0.9},
                    ],
                }
            ],
        }
        out = sp.build_implementer_block(reg, {})
        assert [p["clause"] for p in out] == ["A", "B"]


class TestHeadlinePhrase:
    def test_default_when_no_total(self) -> None:
        assert "No common clauses" in sp._headline_phrase({})

    def test_normal_phrasing(self) -> None:
        msg = sp._headline_phrase(
            {
                "commonClauseCount": 10,
                "coveredClauseCount": 5,
                "priorityWeightedCoveragePercent": 50.0,
            }
        )
        assert "5 of 10" in msg
        assert "50.0%" in msg


class TestBuildBuyerBlock:
    def test_full_flow_with_highlights_and_gaps(self) -> None:
        reg = {
            "versions": [
                {
                    "version": "v1",
                    "coverageSummary": {
                        "commonClauseCount": 3,
                        "coveredClauseCount": 1,
                        "priorityWeightedCoveragePercent": 33.3,
                        "stateCounts": {
                            "covered-full": 1,
                            "covered-partial": 0,
                            "contributing-only": 0,
                            "uncovered": 2,
                        },
                    },
                    "clauseCoverageMatrix": [
                        {
                            "clause": "A",
                            "topic": "TopicA",
                            "priorityWeight": 0.9,
                            "topAssurance": "full",
                            "coveringUcs": ["1.1.1"],
                            "onCommonList": True,
                        },
                        {
                            "clause": "B",
                            "topic": "TopicB",
                            "priorityWeight": 0.4,
                            "coveringUcs": [],
                            "onCommonList": True,
                            "obligationText": "must do",
                        },
                        {
                            "clause": "C",
                            "topic": None,
                            "priorityWeight": 0.2,
                            "coveringUcs": [],
                            "onCommonList": True,
                            "obligationText": "must also",
                        },
                    ],
                }
            ]
        }
        uc_index = {"1.1.1": {"title": "Killer-UC"}}
        block = sp.build_buyer_block(reg, uc_index)
        assert block["coverageHeadline"].startswith("1 of 3")
        assert block["topFiveHighlights"][0]["clause"] == "A"
        assert block["topFiveHighlights"][0]["killerUcTitle"] == "Killer-UC"
        assert [g["clause"] for g in block["topThreeGaps"]] == ["B", "C"]
        assert block["summary"]["priorityWeightedCoveragePercent"] == 33.3

    def test_skips_non_string_versions(self) -> None:
        reg = {
            "versions": [
                {
                    "version": 99,
                    "clauseCoverageMatrix": [
                        {"clause": "X", "coveringUcs": ["1.1.1"]}
                    ],
                }
            ]
        }
        block = sp.build_buyer_block(reg, {})
        assert block["topFiveHighlights"] == []
        assert block["topThreeGaps"] == []
        assert block["summary"]["commonClauseCount"] == 0

    def test_no_uc_index_match_returns_blank_title(self) -> None:
        reg = {
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {
                            "clause": "X",
                            "coveringUcs": ["9.9.9"],
                            "topic": "T",
                            "priorityWeight": 0.5,
                            "topAssurance": "partial",
                        }
                    ],
                }
            ]
        }
        block = sp.build_buyer_block(reg, {})
        assert block["topFiveHighlights"][0]["killerUcTitle"] == ""

    def test_killer_uc_id_none_when_coveringUcs_empty_first_slot(self) -> None:
        # Edge case: coveringUcs has [None] (the default sentinel branch).
        reg = {
            "versions": [
                {
                    "version": "v1",
                    "clauseCoverageMatrix": [
                        {
                            "clause": "X",
                            "coveringUcs": [None],
                            "topic": None,
                            "priorityWeight": 0.5,
                            "topAssurance": None,
                        }
                    ],
                }
            ]
        }
        block = sp.build_buyer_block(reg, {})
        # coveringUcs is [None], which is truthy → enters `covered`.
        assert block["topFiveHighlights"][0]["killerUcId"] is None

    def test_handles_missing_pw_in_summary(self) -> None:
        reg = {
            "versions": [
                {
                    "version": "v1",
                    "coverageSummary": {
                        "commonClauseCount": 1,
                        "coveredClauseCount": 0,
                        "stateCounts": {},
                    },
                    "clauseCoverageMatrix": [],
                }
            ]
        }
        block = sp.build_buyer_block(reg, {})
        assert block["summary"]["priorityWeightedCoveragePercent"] == 0.0


# ---------------------------------------------------------------------------
# Related-endpoint discovery
# ---------------------------------------------------------------------------


class TestDiscoverEvidencePack:
    def test_returns_path_when_present(self, fake_repo: pathlib.Path) -> None:
        (sp.EVIDENCE_PACK_DIR / "gdpr.md").write_text("# pack", encoding="utf-8")
        assert sp.discover_evidence_pack("gdpr") == "docs/evidence-packs/gdpr.md"

    def test_returns_none_when_missing(self, fake_repo: pathlib.Path) -> None:
        assert sp.discover_evidence_pack("nope") is None


class TestDiscoverPrimerAnchor:
    def test_returns_none_when_primer_missing(self, fake_repo: pathlib.Path) -> None:
        assert sp.discover_primer_anchor("gdpr") is None

    def test_returns_none_when_slug_empty(self, fake_repo: pathlib.Path) -> None:
        sp.PRIMER_PATH.write_text("### 1.1 Heading\n", encoding="utf-8")
        assert sp.discover_primer_anchor("---") is None

    def test_starts_match_wins(self, fake_repo: pathlib.Path) -> None:
        sp.PRIMER_PATH.write_text(
            "### 4.1 GDPR — General Data Protection Regulation\n"
            "### 4.2 GDPR Extended Notes\n",
            encoding="utf-8",
        )
        result = sp.discover_primer_anchor("GDPR")
        assert result is not None
        assert result.startswith("docs/regulatory-primer.md#")
        # Shorter heading wins (the second one is shorter once slugged).
        assert "extended" in result or "general" in result

    def test_token_match_when_no_starts(self, fake_repo: pathlib.Path) -> None:
        sp.PRIMER_PATH.write_text(
            "### 4.1 EU GDPR Article 32 — encryption rules\n", encoding="utf-8"
        )
        result = sp.discover_primer_anchor("gdpr")
        # Heading slug = "eu-gdpr-article-32-encryption-rules"; "gdpr" appears
        # bordered by hyphens → token match.
        assert result is not None

    def test_contains_match_when_no_starts_or_token(
        self, fake_repo: pathlib.Path
    ) -> None:
        sp.PRIMER_PATH.write_text(
            "### 4.1 zgdprx merged tokenless heading\n",
            encoding="utf-8",
        )
        result = sp.discover_primer_anchor("gdpr")
        # "gdpr" is a substring of the heading slug but not bordered.
        assert result is not None
        assert result.startswith("docs/regulatory-primer.md#")

    def test_returns_none_when_no_heading_matches(
        self, fake_repo: pathlib.Path
    ) -> None:
        sp.PRIMER_PATH.write_text(
            "### 4.1 nothing here\n### 4.2 still nothing\n", encoding="utf-8"
        )
        assert sp.discover_primer_anchor("gdpr") is None

    def test_skips_blank_heading_slug(self, fake_repo: pathlib.Path) -> None:
        # Heading with only punctuation → slug is empty → skipped by the
        # `if not heading_slug: continue` branch.
        sp.PRIMER_PATH.write_text(
            "### 4.1 ---\n### 4.2 GDPR rules\n", encoding="utf-8"
        )
        result = sp.discover_primer_anchor("gdpr")
        assert result is not None and "gdpr" in result

    def test_longer_starts_match_does_not_overwrite_shorter(
        self, fake_repo: pathlib.Path
    ) -> None:
        # Two starts-matches: the shorter one ("gdpr") wins; the longer
        # one ("gdpr-extended-notes-on-art-32-encryption") must NOT
        # overwrite it. Hits the `if score < starts_match[0]` False
        # branch.
        sp.PRIMER_PATH.write_text(
            "### 4.1 GDPR\n"
            "### 4.2 GDPR Extended Notes On Art 32 Encryption\n",
            encoding="utf-8",
        )
        result = sp.discover_primer_anchor("gdpr")
        assert result is not None
        # Slug 'gdpr' is shortest → 'gdpr' (or trailing variant) wins.
        # Compare on the trailing anchor token.
        anchor = result.rsplit("#", 1)[1]
        assert "extended" not in anchor

    def test_longer_token_match_does_not_overwrite_shorter(
        self, fake_repo: pathlib.Path
    ) -> None:
        # Two token-matches (slug surrounded by non-alphanumerics): the
        # shorter one wins. Hits the `if token_match is None or score
        # < token_match[0]` False branch.
        sp.PRIMER_PATH.write_text(
            "### 4.1 EU GDPR something\n"
            "### 4.2 EU GDPR something more extensive plus extras\n",
            encoding="utf-8",
        )
        result = sp.discover_primer_anchor("gdpr")
        assert result is not None
        anchor = result.rsplit("#", 1)[1]
        # Shorter heading is "41-eu-gdpr-something"; longer is "42-eu-gdpr-something-more-extensive-plus-extras"
        assert "extensive" not in anchor

    def test_longer_contains_match_does_not_overwrite_shorter(
        self, fake_repo: pathlib.Path
    ) -> None:
        # Two contains-matches (slug appears as substring but NOT
        # bordered). Shorter heading wins. Hits the
        # `if contains_match is None or score < contains_match[0]`
        # False branch.
        sp.PRIMER_PATH.write_text(
            "### 4.1 zzgdprzz one\n"
            "### 4.2 zzgdprzz two added even more extra text here\n",
            encoding="utf-8",
        )
        result = sp.discover_primer_anchor("gdpr")
        assert result is not None
        anchor = result.rsplit("#", 1)[1]
        # The shorter heading ("zzgdprzz one") wins.
        assert "added" not in anchor


class TestGithubHeadingAnchor:
    def test_strips_hashes_and_normalises(self) -> None:
        # The period after "4" and the em-dash both fall outside
        # ``[\w\s-]`` so they're stripped before whitespace collapses
        # into single hyphens.
        assert (
            sp._github_heading_anchor("### 4.1 GDPR — Data Protection")
            == "41-gdpr-data-protection"
        )

    def test_unicode_pass_through(self) -> None:
        # The "\w" character class with UNICODE flag keeps letters in
        # other scripts.
        anchor = sp._github_heading_anchor("### Schöne Welt")
        assert "schöne" in anchor


# ---------------------------------------------------------------------------
# Deep coverage (NIS2)
# ---------------------------------------------------------------------------


class TestCountNis2Ucs:
    def test_counts_only_nis2_entries(self) -> None:
        uc_index = {
            "1.1.1": {"compliance": [{"regulation": "GDPR"}]},
            "1.1.2": {"compliance": [{"regulation": "nis2"}]},
            "1.1.3": {"compliance": [{"regulation": "NIS2"}, {"regulation": "NIS2"}]},
            "1.1.4": {"compliance": []},
            "1.1.5": {"compliance": "not-a-list"},
            "1.1.6": {"compliance": [None, "junk", {"regulation": 5}]},
            "1.1.7": {},
        }
        assert sp._count_nis2_ucs(uc_index) == 2  # 1.1.2 and 1.1.3


class TestBucketCounts:
    def test_returns_dict_with_all_buckets_initialised_to_zero(self) -> None:
        rows = [{"x": "a"}, {"x": "b"}, {"x": "a"}, {"x": "c"}, {"x": 123}]
        out = sp._bucket_counts(rows, "x", ["a", "b"])
        assert out == {"a": 2, "b": 1}


class TestBuildNis2DeepCoverage:
    def test_returns_none_when_not_nis2(self, fake_repo: pathlib.Path) -> None:
        assert sp.build_nis2_deep_coverage("gdpr", {}) is None

    def test_returns_none_when_matrix_missing(self, fake_repo: pathlib.Path) -> None:
        assert sp.build_nis2_deep_coverage("nis2", {}) is None

    def test_returns_none_when_no_rows(self, fake_repo: pathlib.Path) -> None:
        sp.NIS2_MATRIX_PATH.write_text(
            json.dumps({"coverageRows": []}), encoding="utf-8"
        )
        assert sp.build_nis2_deep_coverage("nis2", {}) is None

    def test_full_payload_with_source_map(self, fake_repo: pathlib.Path) -> None:
        sp.NIS2_MATRIX_PATH.write_text(
            json.dumps(
                {
                    "coverageRows": [
                        {
                            "splunkCoverageType": "full",
                            "assuranceTarget": "full",
                            "reviewConfidence": "high",
                            "sourceType": "directive",
                            "controlFamily": "logging",
                        },
                        {
                            "splunkCoverageType": "not-monitorable",
                            "assuranceTarget": "partial",
                            "reviewConfidence": "requires-legal-review",
                            "sourceType": "implementing-regulation",
                            "controlFamily": None,  # → "unspecified"
                        },
                        # Row with unknown coverage value → falls into
                        # the domain "unspecified" bucket.
                        {
                            "splunkCoverageType": "what-is-this",
                            "assuranceTarget": "contributing",
                            "controlFamily": "logging",
                        },
                        # Truthy-but-non-str ``controlFamily`` exercises
                        # the ``if not isinstance(family, str)`` branch
                        # (line 724-725) — the value is coerced back to
                        # "unspecified" before the per-family bucket is
                        # incremented.
                        {
                            "splunkCoverageType": "full",
                            "assuranceTarget": "full",
                            "controlFamily": ["nested-list"],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        sp.NIS2_SOURCE_MAP_PATH.write_text(
            json.dumps({"sourceAuthorityRanking": ["EUR-Lex"]}), encoding="utf-8"
        )
        deep = sp.build_nis2_deep_coverage("nis2", {})
        assert deep is not None
        assert deep["matrixRows"] == 4
        # Row 2 is "not-monitorable" → monitorableRows == 3
        # (rows 1, 3, 4 are monitorable).
        assert deep["monitorableRows"] == 3
        # Row 2 is both not-monitorable AND requires-legal-review →
        # contributes once to legalBoundaryRowCount.
        assert deep["legalBoundaryRowCount"] == 1
        assert deep["sourceAuthorityRanking"] == ["EUR-Lex"]
        # "logging" family appears twice — one full, one unspecified.
        logging_fam = next(
            d for d in deep["domainOverview"] if d["controlFamily"] == "logging"
        )
        assert logging_fam["rowCount"] == 2
        assert logging_fam["coverageByType"]["full"] == 1
        assert logging_fam["coverageByType"]["unspecified"] == 1
        # The non-str controlFamily row was coerced into the
        # "unspecified" bucket alongside the None row.
        unspec_fam = next(
            d for d in deep["domainOverview"] if d["controlFamily"] == "unspecified"
        )
        assert unspec_fam["rowCount"] == 2


# ---------------------------------------------------------------------------
# Build one story
# ---------------------------------------------------------------------------


class TestBuildStory:
    def _bare_reg(self, reg_id: str = "gdpr") -> dict[str, Any]:
        return {
            "id": reg_id,
            "shortName": "GDPR",
            "name": "GDPR full name",
            "tier": "tier-1",
            "jurisdiction": "EU",
            "versions": [
                {
                    "version": "2016/679",
                    "coverageSummary": {
                        "commonClauseCount": 1,
                        "coveredClauseCount": 1,
                        "priorityWeightedCoveragePercent": 100.0,
                        "stateCounts": {
                            "covered-full": 1,
                            "covered-partial": 0,
                            "contributing-only": 0,
                            "uncovered": 0,
                        },
                    },
                    "clauseCoverageMatrix": [
                        {
                            "clause": "Art.32",
                            "topic": "Security",
                            "priorityWeight": 0.9,
                            "topAssurance": "full",
                            "coveringUcs": ["1.1.1"],
                            "onCommonList": True,
                        }
                    ],
                }
            ],
        }

    def test_story_has_all_blocks(self, fake_repo: pathlib.Path) -> None:
        story = sp.build_story(
            self._bare_reg(),
            areas={},
            uc_index={"1.1.1": {"title": "Encryption UC", "criticality": "high"}},
            generated_at="2026-01-01T00:00:00Z",
            api_version="v1",
            catalogue_version="9.9.9",
        )
        assert story["regulationId"] == "gdpr"
        assert story["narrative"] is None
        assert story["narrativeRef"] is None
        assert story["buyer"]["coverageHeadline"]
        assert len(story["auditor"]) == 1
        assert story["implementer"]["quickStartPlaybook"]
        assert story["relatedEndpoints"]["regulation"].endswith("/gdpr.json")

    def test_narrative_ref_uses_slug(self, fake_repo: pathlib.Path) -> None:
        areas = {"gdpr compliance": {"name": "GDPR Compliance!"}}
        story = sp.build_story(
            self._bare_reg(),
            areas=areas,
            uc_index={},
            generated_at="2026-01-01T00:00:00Z",
            api_version="v1",
            catalogue_version="9.9.9",
        )
        assert story["narrative"] is not None
        assert story["narrativeRef"] == "non-technical-view.js#cat-22/area/gdpr-compliance"

    def test_nis2_attaches_deep_coverage(self, fake_repo: pathlib.Path) -> None:
        sp.NIS2_MATRIX_PATH.write_text(
            json.dumps(
                {
                    "coverageRows": [
                        {"splunkCoverageType": "full", "assuranceTarget": "full"}
                    ]
                }
            ),
            encoding="utf-8",
        )
        reg = self._bare_reg("nis2")
        story = sp.build_story(
            reg,
            areas={},
            uc_index={},
            generated_at="2026-01-01T00:00:00Z",
            api_version="v1",
            catalogue_version="9.9.9",
        )
        assert "deepCoverage" in story


# ---------------------------------------------------------------------------
# generate() orchestration
# ---------------------------------------------------------------------------


def _seed_regulations(repo: pathlib.Path) -> None:
    (repo / "VERSION").write_text("3.0.0\n", encoding="utf-8")
    (repo / "api" / "v1" / "compliance" / "regulations" / "gdpr.json").write_text(
        json.dumps(
            {
                "id": "gdpr",
                "shortName": "GDPR",
                "name": "GDPR full name",
                "tier": "tier-1",
                "versions": [
                    {
                        "version": "v1",
                        "coverageSummary": {
                            "commonClauseCount": 1,
                            "coveredClauseCount": 1,
                            "priorityWeightedCoveragePercent": 100.0,
                            "stateCounts": {
                                "covered-full": 1,
                                "covered-partial": 0,
                                "contributing-only": 0,
                                "uncovered": 0,
                            },
                        },
                        "clauseCoverageMatrix": [
                            {
                                "clause": "Art.1",
                                "priorityWeight": 1.0,
                                "topAssurance": "full",
                                "coveringUcs": ["1.1.1"],
                                "onCommonList": True,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    # Index file in the same dir is skipped on purpose.
    (repo / "api" / "v1" / "compliance" / "regulations" / "index.json").write_text(
        "{}", encoding="utf-8"
    )
    # Versioned shadow files (containing "@") are also skipped.
    (
        repo / "api" / "v1" / "compliance" / "regulations" / "gdpr@v1.json"
    ).write_text("{}", encoding="utf-8")
    # A regulation file whose id field is missing is silently skipped.
    (
        repo / "api" / "v1" / "compliance" / "regulations" / "no-id.json"
    ).write_text(json.dumps({"shortName": "X"}), encoding="utf-8")
    (
        repo / "api" / "v1" / "compliance" / "regulations" / "wrong-id-type.json"
    ).write_text(json.dumps({"id": 9}), encoding="utf-8")


class TestGenerate:
    def test_raises_when_regs_dir_missing(self, fake_repo: pathlib.Path) -> None:
        sp.REGS_DIR.rmdir()
        with pytest.raises(SystemExit) as excinfo:
            sp.generate()
        assert "missing" in str(excinfo.value)

    def test_writes_index_and_per_regulation_files(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_regulations(fake_repo)
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        idx = sp.generate()
        assert idx["totalRegulations"] == 1
        out_root = sp.OUT_DIR
        assert (out_root / "gdpr.json").exists()
        assert (out_root / "index.json").exists()
        idx_payload = json.loads((out_root / "index.json").read_text(encoding="utf-8"))
        assert idx_payload["regulations"][0]["regulationId"] == "gdpr"

    def test_accepts_explicit_output_root_and_regs_dir(
        self,
        fake_repo: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        regs_src = tmp_path / "alt-regs"
        regs_src.mkdir()
        (regs_src / "gdpr.json").write_text(
            json.dumps(
                {
                    "id": "gdpr",
                    "shortName": "G",
                    "name": "G",
                    "tier": "tier-1",
                    "versions": [
                        {
                            "version": "v1",
                            "coverageSummary": {
                                "commonClauseCount": 0,
                                "coveredClauseCount": 0,
                            },
                            "clauseCoverageMatrix": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (fake_repo / "VERSION").write_text("3.0.0", encoding="utf-8")
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        out_root = tmp_path / "out"
        idx = sp.generate(output_root=out_root, regs_dir=regs_src)
        assert idx["totalRegulations"] == 1
        assert (out_root / "gdpr.json").exists()
        assert (out_root / "index.json").exists()

    def test_rebuilds_when_output_root_already_exists(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Pre-populate the output dir with a stale file that should be wiped.
        stale = sp.OUT_DIR / "stale.json"
        stale.write_text("delete-me", encoding="utf-8")
        _seed_regulations(fake_repo)
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        sp.generate()
        assert not stale.exists()


# ---------------------------------------------------------------------------
# _hash_tree / _check_drift / main
# ---------------------------------------------------------------------------


class TestHashTree:
    def test_returns_empty_digest_for_missing_root(self, tmp_path: pathlib.Path) -> None:
        nope = tmp_path / "nope"
        h = sp._hash_tree(nope)
        assert h == sp.hashlib.sha256().hexdigest()

    def test_hash_changes_when_content_changes(self, tmp_path: pathlib.Path) -> None:
        root = tmp_path / "r"
        root.mkdir()
        (root / "a.json").write_text("{}", encoding="utf-8")
        h1 = sp._hash_tree(root)
        (root / "a.json").write_text('{"x":1}', encoding="utf-8")
        h2 = sp._hash_tree(root)
        assert h1 != h2

    def test_skips_directories_during_hash(self, tmp_path: pathlib.Path) -> None:
        root = tmp_path / "r"
        sub = root / "sub"
        sub.mkdir(parents=True)
        (sub / "a.json").write_text("{}", encoding="utf-8")
        # The function should walk past `sub/` (directory) without
        # raising on read_bytes() of a directory.
        h = sp._hash_tree(root)
        assert h


class TestCheckDrift:
    def test_returns_zero_when_tree_matches(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_regulations(fake_repo)
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        sp.generate()  # populate OUT_DIR with current expected tree
        rc = sp._check_drift()
        assert rc == 0

    def test_returns_one_when_tree_diverges(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_regulations(fake_repo)
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        sp.generate()
        # Mutate the on-disk file so _check_drift detects drift.
        (sp.OUT_DIR / "gdpr.json").write_text('{"drift": true}', encoding="utf-8")
        rc = sp._check_drift()
        assert rc == 1
        err = capsys.readouterr().err
        assert "out of date" in err


class TestMain:
    def test_main_write_mode_prints_summary(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_regulations(fake_repo)
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        rc = sp.main([])
        assert rc == 0
        err = capsys.readouterr().err
        assert "Wrote 1 story payloads" in err

    def test_main_check_returns_zero_when_clean(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_regulations(fake_repo)
        monkeypatch.setattr(sp, "_deterministic_timestamp", lambda: "2026-01-01T00:00:00Z")
        sp.generate()
        rc = sp.main(["--check"])
        assert rc == 0

    def test_main_propagates_systemexit(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(*a: Any, **kw: Any):
            raise SystemExit("fatal")

        monkeypatch.setattr(sp, "generate", boom)
        with pytest.raises(SystemExit):
            sp.main([])

    def test_main_returns_two_on_unexpected_exception(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        def boom(*a: Any, **kw: Any):
            raise RuntimeError("not an exit")

        monkeypatch.setattr(sp, "generate", boom)
        rc = sp.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "UNEXPECTED ERROR" in err


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
