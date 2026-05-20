"""Hermetic unit tests for helper functions in
``src/splunk_uc/generators/evidence_packs.py``.

These tests cover the pure helpers that the larger
``_generate_all`` / ``_render_markdown_pack`` / ``_render_json_twin``
pipelines compose. They run against fixtures only — no real
filesystem walk, no subprocess, no network — and they monkeypatch
``ROOT``-derived paths in the few cases (``_chain_doc_references``,
``_check_drift``, ``_prune_orphans``) where the helper reads the
repo directly.

The goal is to lift the module's branch coverage from ~9 % toward
the ~80 % budget the rest of the audit / generator surface enforces,
without growing the slower integration suite.

Test groups in this file (in render order):

* deterministic serialisers — ``_dump_json_bytes`` /
  ``_stable_markdown_bytes``
* version reader — ``_get_version``
* compliance index — ``_build_compliance_index``
* assurance — ``_best_assurance``
* clause sort key — ``_clause_sort_key``
* gap-report lookup — ``_load_gap_report`` / ``_gap_report_lookup``
* coverage computation — ``_compute_coverage_from_index`` /
  ``_extract_coverage``
* per-UC detail — ``_build_uc_details``
* small formatters — ``_clause_url`` / ``_assurance_badge`` /
  ``_fmt_pct``
* markdown / JSON / README renderers smoke tests
* inputs sha — ``_inputs_sha256``
* drift / prune helpers — ``_check_drift`` / ``_prune_orphans``
* chained citations — ``_chain_doc_references``
* CLI surface — ``main``
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import splunk_uc.generators.evidence_packs as ep  # noqa: E402

# ---------------------------------------------------------------------------
# Deterministic serialisers
# ---------------------------------------------------------------------------


def test_dump_json_bytes_is_deterministic_and_unicode_safe():
    payload = {"b": 2, "a": 1, "ü": "日本"}
    out1 = ep._dump_json_bytes(payload)
    out2 = ep._dump_json_bytes(payload)
    assert out1 == out2
    # 2-space indent, sorted keys, trailing newline, non-ASCII preserved.
    assert out1.endswith(b"\n")
    text = out1.decode("utf-8")
    assert text.startswith("{\n  \"a\": 1")
    assert "\"日本\"" in text


def test_stable_markdown_bytes_strips_trailing_ws_and_normalises_newline():
    text = "line one  \nline two\t\n\n\n  \n"
    out = ep._stable_markdown_bytes(text)
    # Trailing whitespace per line stripped, trailing blank lines popped,
    # exactly one trailing newline preserved.
    assert out == b"line one\nline two\n"


def test_stable_markdown_bytes_handles_empty_input():
    # Pure-whitespace input collapses to a single trailing newline.
    assert ep._stable_markdown_bytes("\n   \n  \n") == b"\n"
    assert ep._stable_markdown_bytes("") == b"\n"


# ---------------------------------------------------------------------------
# _get_version
# ---------------------------------------------------------------------------


def test_get_version_reads_version_file(monkeypatch, tmp_path: Path):
    vp = tmp_path / "VERSION"
    vp.write_text("9.99.42\n", encoding="utf-8")
    monkeypatch.setattr(ep, "VERSION_PATH", vp)
    assert ep._get_version() == "9.99.42"


def test_get_version_returns_unknown_when_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(ep, "VERSION_PATH", tmp_path / "no-such-file")
    assert ep._get_version() == "unknown"


# ---------------------------------------------------------------------------
# _iter_uc_sidecars / _load_all_ucs
# ---------------------------------------------------------------------------


def test_iter_uc_sidecars_returns_sorted_paths(monkeypatch, tmp_path: Path):
    (tmp_path / "content" / "cat-22-compliance").mkdir(parents=True)
    p1 = tmp_path / "content" / "cat-22-compliance" / "UC-22.2.2.json"
    p2 = tmp_path / "content" / "cat-22-compliance" / "UC-22.1.1.json"
    p1.write_text("{}", encoding="utf-8")
    p2.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(ep, "ROOT", tmp_path)
    out = ep._iter_uc_sidecars()
    assert out == [p2, p1]


def test_load_all_ucs_annotates_source_path(monkeypatch, tmp_path: Path):
    (tmp_path / "content" / "cat-1-x").mkdir(parents=True)
    p = tmp_path / "content" / "cat-1-x" / "UC-1.1.1.json"
    p.write_text(json.dumps({"id": "1.1.1", "title": "test"}), encoding="utf-8")
    monkeypatch.setattr(ep, "ROOT", tmp_path)
    out = ep._load_all_ucs()
    assert len(out) == 1
    assert out[0]["id"] == "1.1.1"
    assert out[0]["_source_path"] == "content/cat-1-x/UC-1.1.1.json"


def test_load_all_ucs_raises_on_malformed_json(monkeypatch, tmp_path: Path):
    (tmp_path / "content" / "cat-1-x").mkdir(parents=True)
    bad = tmp_path / "content" / "cat-1-x" / "UC-1.1.1.json"
    bad.write_text("{not json}", encoding="utf-8")
    monkeypatch.setattr(ep, "ROOT", tmp_path)
    with pytest.raises(json.JSONDecodeError):
        ep._load_all_ucs()


# ---------------------------------------------------------------------------
# _build_compliance_index
# ---------------------------------------------------------------------------


def _uc(uc_id: str, compliance: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {
        "id": uc_id,
        "title": extra.pop("title", f"UC {uc_id}"),
        "compliance": compliance,
        "_source_path": extra.pop("_source_path", f"content/cat-22/UC-{uc_id}.json"),
        **extra,
    }


def test_build_compliance_index_resolves_aliases_case_insensitively():
    ucs = [
        _uc("22.1.1", [{"regulation": "GDPR", "clause": "Art.5", "assurance": "full"}]),
        _uc("22.1.2", [{"regulation": "gdpr", "clause": "Art.5", "assurance": "partial"}]),
    ]
    alias = {"GDPR": "gdpr", "$schemaNote": "ignored"}
    idx = ep._build_compliance_index(ucs, alias)
    key = ("gdpr", "")
    assert key in idx
    assert len(idx[key]) == 2
    # First entry retains its assurance
    assert idx[key][0]["assurance"] == "full"


def test_build_compliance_index_skips_missing_uc_or_clause_or_regulation():
    ucs = [
        # Missing id — skipped entirely
        {"compliance": [{"regulation": "GDPR", "clause": "Art.5"}]},
        # Missing regulation — skipped at entry-level
        _uc("22.1.1", [{"clause": "Art.5"}]),
        # Missing clause — skipped at entry-level
        _uc("22.1.2", [{"regulation": "GDPR"}]),
        # Valid entry
        _uc("22.1.3", [{"regulation": "GDPR", "clause": "Art.5", "version": "2018"}]),
    ]
    idx = ep._build_compliance_index(ucs, {"GDPR": "gdpr"})
    assert list(idx.keys()) == [("gdpr", "2018")]
    assert len(idx[("gdpr", "2018")]) == 1
    assert idx[("gdpr", "2018")][0]["uc_id"] == "22.1.3"


def test_build_compliance_index_defaults_assurance_provenance_and_rationale():
    ucs = [_uc("22.1.1", [{"regulation": "GDPR", "clause": "Art.5"}])]
    idx = ep._build_compliance_index(ucs, {"GDPR": "gdpr"})
    entry = idx[("gdpr", "")][0]
    assert entry["assurance"] == "contributing"
    assert entry["provenance"] == "native"
    assert entry["rationale"] == ""
    assert entry["derivationSource"] is None


# ---------------------------------------------------------------------------
# _best_assurance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entries, expected",
    [
        ([{"assurance": "contributing"}, {"assurance": "partial"}, {"assurance": "full"}], "full"),
        ([{"assurance": "partial"}, {"assurance": "contributing"}], "partial"),
        ([{"assurance": "contributing"}], "contributing"),
        ([], "contributing"),
        ([{"assurance": None}, {"assurance": "bogus"}], "contributing"),
        ([{"assurance": 123}], "contributing"),  # non-string ignored
    ],
)
def test_best_assurance(entries, expected):
    assert ep._best_assurance(entries) == expected


# ---------------------------------------------------------------------------
# _clause_sort_key
# ---------------------------------------------------------------------------


def test_clause_sort_key_orders_numerically_within_prefix():
    clauses = ["Art.10", "Art.2", "Art.5(1)(e)", "Art.5"]
    out = sorted(clauses, key=ep._clause_sort_key)
    # Art.2 < Art.5 < Art.5(1)(e) < Art.10
    assert out == ["Art.2", "Art.5", "Art.5(1)(e)", "Art.10"]


def test_clause_sort_key_handles_non_numeric_tokens():
    clauses = ["A.1.1", "AB.1.1", "A.10.1"]
    out = sorted(clauses, key=ep._clause_sort_key)
    # Tokens with no digits return empty numeric tuple → fall through
    # to lexicographic tie-breaker on the original string.
    assert out == ["A.1.1", "A.10.1", "AB.1.1"]


# ---------------------------------------------------------------------------
# _load_gap_report / _gap_report_lookup
# ---------------------------------------------------------------------------


def test_load_gap_report_returns_empty_when_file_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(ep, "GAPS_REPORT_PATH", tmp_path / "missing.json")
    assert ep._load_gap_report() == {}


def test_load_gap_report_returns_parsed_json(monkeypatch, tmp_path: Path):
    fp = tmp_path / "gaps.json"
    fp.write_text(json.dumps({"tiers": {"tier-1": {"gdpr": {}}}}), encoding="utf-8")
    monkeypatch.setattr(ep, "GAPS_REPORT_PATH", fp)
    out = ep._load_gap_report()
    assert "tiers" in out


def test_gap_report_lookup_returns_version_block_from_tier_1():
    report = {
        "tiers": {
            "tier-1": {"gdpr": {"versions": {"2018": {"coverage_pct": 90.0}}}},
            "tier-2": {},
        }
    }
    out = ep._gap_report_lookup(report, "gdpr", "2018")
    assert out == {"coverage_pct": 90.0}


def test_gap_report_lookup_falls_through_to_tier_3():
    report = {
        "tiers": {
            "tier-1": {},
            "tier-2": {},
            "tier-3": {"obscure-reg": {"versions": {"v1": {"coverage_pct": 12.5}}}},
        }
    }
    out = ep._gap_report_lookup(report, "obscure-reg", "v1")
    assert out == {"coverage_pct": 12.5}


def test_gap_report_lookup_returns_none_when_version_missing():
    report = {"tiers": {"tier-1": {"gdpr": {"versions": {"2018": {}}}}}}
    assert ep._gap_report_lookup(report, "gdpr", "1995") is None
    assert ep._gap_report_lookup(report, "unknown", "2018") is None


def test_gap_report_lookup_handles_missing_tiers_block():
    assert ep._gap_report_lookup({}, "gdpr", "2018") is None
    assert ep._gap_report_lookup({"tiers": {}}, "gdpr", "2018") is None


# ---------------------------------------------------------------------------
# _compute_coverage_from_index / _extract_coverage
# ---------------------------------------------------------------------------


def _common_clauses() -> list[dict[str, Any]]:
    return [
        {"clause": "Art.5", "topic": "Principles", "priorityWeight": 1.0},
        {"clause": "Art.6", "topic": "Lawfulness", "priorityWeight": 0.8},
        {"clause": "Art.30", "topic": "Records", "priorityWeight": 0.5},
    ]


def test_compute_coverage_from_index_full_coverage():
    common = _common_clauses()
    idx = {
        ("gdpr", "2018"): [
            {"uc_id": "22.1.1", "clause": "Art.5", "assurance": "full"},
            {"uc_id": "22.1.2", "clause": "Art.5", "assurance": "partial"},
            {"uc_id": "22.1.3", "clause": "Art.6", "assurance": "contributing"},
            {"uc_id": "22.1.4", "clause": "Art.30", "assurance": "full"},
        ]
    }
    out = ep._compute_coverage_from_index("gdpr", "2018", common, idx)
    assert out["common_clause_count"] == 3
    assert out["covered_count"] == 3
    assert out["coverage_pct"] == pytest.approx(100.0)
    assert out["priority_weight_total"] == pytest.approx(2.3)
    assert out["priority_weight_covered"] == pytest.approx(2.3)
    # Per-clause: clause 1 has uc_ids 22.1.1 + 22.1.2 sorted unique.
    clauses = {c["clause"]: c for c in out["clauses"]}
    assert clauses["Art.5"]["uc_ids"] == ["22.1.1", "22.1.2"]
    assert clauses["Art.5"]["max_assurance"] == "full"
    assert clauses["Art.5"]["uc_count"] == 2


def test_compute_coverage_from_index_partial_coverage():
    common = _common_clauses()
    idx = {
        ("gdpr", "2018"): [
            {"uc_id": "22.1.1", "clause": "Art.5", "assurance": "partial"},
        ]
    }
    out = ep._compute_coverage_from_index("gdpr", "2018", common, idx)
    assert out["covered_count"] == 1
    # Coverage on count: 1/3 ≈ 33.33; on priority weight: 1.0 / 2.3 ≈ 43.5
    assert out["coverage_pct"] == pytest.approx(33.333333333333, abs=1e-6)
    assert out["priority_weight_covered"] == pytest.approx(1.0)
    assert out["priority_weight_pct"] == pytest.approx(43.4782608695, abs=1e-6)
    # Uncovered clauses report None / empty
    by_id = {c["clause"]: c for c in out["clauses"]}
    assert by_id["Art.6"]["covered"] is False
    assert by_id["Art.6"]["max_assurance"] is None
    assert by_id["Art.6"]["uc_ids"] == []


def test_compute_coverage_from_index_handles_zero_clauses():
    out = ep._compute_coverage_from_index("gdpr", "2018", [], {})
    assert out["common_clause_count"] == 0
    assert out["coverage_pct"] == 0.0
    assert out["priority_weight_pct"] == 0.0


def test_extract_coverage_prefers_gap_block_when_present():
    gap = {
        "clauses": [
            {
                "clause": "Art.5",
                "topic": "Principles",
                "priority_weight": 1.0,
                "covered": True,
                "max_assurance": "full",
                "uc_count": 2,
                "uc_ids": ["22.1.2", "22.1.1"],  # Should be re-sorted ascending
            }
        ],
        "common_clause_count": 1,
        "covered_count": 1,
        "coverage_pct": 100.0,
        "priority_weight_total": 1.0,
        "priority_weight_covered": 1.0,
        "priority_weight_pct": 100.0,
    }
    out = ep._extract_coverage(gap, "2018", "gdpr", _common_clauses(), {})
    # Gap-block path: uc_ids sorted ascending
    assert out["clauses"][0]["uc_ids"] == ["22.1.1", "22.1.2"]
    assert out["coverage_pct"] == 100.0


def test_extract_coverage_falls_back_to_live_index_when_gap_missing():
    common = _common_clauses()
    idx = {("gdpr", "2018"): [{"uc_id": "22.1.1", "clause": "Art.5", "assurance": "full"}]}
    out = ep._extract_coverage(None, "2018", "gdpr", common, idx)
    # Live path: covered_count derived from the index, not the gap_block.
    assert out["covered_count"] == 1
    assert out["common_clause_count"] == 3


def test_extract_coverage_falls_back_when_gap_clauses_missing():
    # Even if gap_block is provided, missing ``clauses`` triggers the
    # live-index fallback.
    common = _common_clauses()
    idx = {("gdpr", "2018"): [{"uc_id": "22.1.1", "clause": "Art.5", "assurance": "full"}]}
    out = ep._extract_coverage({"coverage_pct": 99.0}, "2018", "gdpr", common, idx)
    assert out["covered_count"] == 1


# ---------------------------------------------------------------------------
# _build_uc_details
# ---------------------------------------------------------------------------


def test_build_uc_details_counts_evidence_list_entries():
    idx = {
        ("gdpr", "2018"): [
            {
                "uc_id": "22.1.1",
                "uc_title": "Records of processing",
                "source_path": "content/cat-22/UC-22.1.1.json",
            },
        ]
    }
    docs = {
        "22.1.1": {
            "id": "22.1.1",
            "title": "Records of processing",
            "evidence": ["a", "b", "c"],
            "controlFamily": "Records",
            "owner": "DPO",
        }
    }
    out = ep._build_uc_details(idx, "gdpr", "2018", docs)
    assert out["22.1.1"]["evidence_count"] == 3
    assert out["22.1.1"]["controlFamily"] == "Records"
    assert out["22.1.1"]["owner"] == "DPO"


def test_build_uc_details_flattens_legacy_evidence_dict():
    idx = {
        ("gdpr", "2018"): [
            {"uc_id": "22.1.1", "uc_title": "x", "source_path": "p"},
        ]
    }
    docs = {
        "22.1.1": {
            "evidence": {
                "field_a": ["a", "b"],
                "field_b": "single-string",
            }
        }
    }
    out = ep._build_uc_details(idx, "gdpr", "2018", docs)
    # Two list entries + one flattened field-mapping → 3 evidence entries.
    assert out["22.1.1"]["evidence_count"] == 3


def test_build_uc_details_handles_string_evidence():
    idx = {
        ("gdpr", "2018"): [
            {"uc_id": "22.1.1", "uc_title": "x", "source_path": "p"},
            {"uc_id": "22.1.2", "uc_title": "y", "source_path": "p"},
        ]
    }
    docs = {
        "22.1.1": {"evidence": "single string"},
        "22.1.2": {"evidence": "   "},  # blank treated as zero
    }
    out = ep._build_uc_details(idx, "gdpr", "2018", docs)
    assert out["22.1.1"]["evidence_count"] == 1
    assert out["22.1.2"]["evidence_count"] == 0


def test_build_uc_details_deduplicates_repeated_uc_ids():
    idx = {
        ("gdpr", "2018"): [
            {"uc_id": "22.1.1", "uc_title": "x", "source_path": "p1"},
            {"uc_id": "22.1.1", "uc_title": "x dup", "source_path": "p2"},
        ]
    }
    out = ep._build_uc_details(idx, "gdpr", "2018", {})
    assert list(out.keys()) == ["22.1.1"]
    # First-occurrence wins on source_path
    assert out["22.1.1"]["source_path"] == "p1"


# ---------------------------------------------------------------------------
# Small formatters
# ---------------------------------------------------------------------------


def test_clause_url_returns_none_when_template_empty():
    assert ep._clause_url(None, "Art.5") is None
    assert ep._clause_url("", "Art.5") is None
    assert ep._clause_url("https://x/{clause}", "") is None


def test_clause_url_substitutes_clause_placeholder():
    assert (
        ep._clause_url("https://example.org/gdpr/{clause}", "Art.5")
        == "https://example.org/gdpr/Art.5"
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        ("full", "full"),
        ("partial", "partial"),
        ("contributing", "contributing"),
        (None, "—"),
        ("nonsense", "—"),
    ],
)
def test_assurance_badge(value, expected):
    assert ep._assurance_badge(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "—"),
        (0.0, "0.0%"),
        (33.3333, "33.3%"),
        (100.0, "100.0%"),
    ],
)
def test_fmt_pct(value, expected):
    assert ep._fmt_pct(value) == expected


# ---------------------------------------------------------------------------
# _inputs_sha256
# ---------------------------------------------------------------------------


def test_inputs_sha256_changes_when_any_input_changes(monkeypatch, tmp_path: Path):
    reg = tmp_path / "regulations.json"
    extras = tmp_path / "extras.json"
    schema = tmp_path / "schema.json"
    for p in (reg, extras, schema):
        p.write_text(p.name, encoding="utf-8")
    monkeypatch.setattr(ep, "REGULATIONS_PATH", reg)
    monkeypatch.setattr(ep, "EXTRAS_PATH", extras)
    monkeypatch.setattr(ep, "EXTRAS_SCHEMA_PATH", schema)

    h1 = ep._inputs_sha256()
    assert len(h1) == 64
    extras.write_text("changed", encoding="utf-8")
    h2 = ep._inputs_sha256()
    assert h2 != h1


def test_inputs_sha256_is_concat_in_fixed_order(monkeypatch, tmp_path: Path):
    reg = tmp_path / "a"
    extras = tmp_path / "b"
    schema = tmp_path / "c"
    reg.write_text("R", encoding="utf-8")
    extras.write_text("E", encoding="utf-8")
    schema.write_text("S", encoding="utf-8")
    monkeypatch.setattr(ep, "REGULATIONS_PATH", reg)
    monkeypatch.setattr(ep, "EXTRAS_PATH", extras)
    monkeypatch.setattr(ep, "EXTRAS_SCHEMA_PATH", schema)
    expected = hashlib.sha256(b"RES").hexdigest()
    assert ep._inputs_sha256() == expected


# ---------------------------------------------------------------------------
# JSON / README / Markdown renderers
# ---------------------------------------------------------------------------


def _framework() -> dict[str, Any]:
    return {
        "id": "gdpr",
        "shortName": "GDPR",
        "name": "General Data Protection Regulation",
        "tier": 1,
        "jurisdiction": ["EU", "UK"],
    }


def _version() -> dict[str, Any]:
    return {
        "version": "2018",
        "authoritativeUrl": "https://example.org",
        "clauseUrlTemplate": "https://example.org/{clause}",
        "effectiveFrom": "2018-05-25",
        "sunsetOn": None,
        "commonClauses": _common_clauses(),
    }


def _extras() -> dict[str, Any]:
    return {
        "version": "2018",
        "summary": "Purpose summary.",
        "scope": "Who it applies to.",
        "territorialScope": "EU + UK + third-country processors.",
        "commonEvidenceSources": ["records-of-processing"],
        "retentionGuidance": [
            {"artifact": "DPIA", "retention": "5y", "source": "Art.35"}
        ],
        "testingApproach": "Sample of representative DPIAs.",
        "reportingCadence": "Annual.",
        "roles": [{"title": "DPO", "responsibility": "Owns evidence pack."}],
        "authoritativeGuidance": [
            {"title": "ICO Guide", "organisation": "ICO", "url": "https://ico.org.uk"}
        ],
        "commonDeficiencies": ["No incident drill log."],
        "auditorQuestions": ["Where are your processing records?"],
        "penaltyStructure": "Up to 4% of global turnover.",
    }


def _coverage_full() -> dict[str, Any]:
    return {
        "clauses": [
            {
                "clause": "Art.5",
                "topic": "Principles",
                "priority_weight": 1.0,
                "covered": True,
                "max_assurance": "full",
                "uc_count": 1,
                "uc_ids": ["22.1.1"],
            },
            {
                "clause": "Art.6",
                "topic": "Lawfulness",
                "priority_weight": 0.8,
                "covered": True,
                "max_assurance": "partial",
                "uc_count": 1,
                "uc_ids": ["22.1.2"],
            },
            {
                "clause": "Art.30",
                "topic": "Records",
                "priority_weight": 0.5,
                "covered": True,
                "max_assurance": "full",
                "uc_count": 1,
                "uc_ids": ["22.1.3"],
            },
        ],
        "common_clause_count": 3,
        "covered_count": 3,
        "coverage_pct": 100.0,
        "priority_weight_total": 2.3,
        "priority_weight_covered": 2.3,
        "priority_weight_pct": 100.0,
    }


def _coverage_partial() -> dict[str, Any]:
    cov = _coverage_full()
    cov["clauses"][1]["covered"] = False
    cov["clauses"][1]["max_assurance"] = None
    cov["clauses"][1]["uc_count"] = 0
    cov["clauses"][1]["uc_ids"] = []
    cov["covered_count"] = 2
    cov["coverage_pct"] = 66.67
    cov["priority_weight_covered"] = 1.5
    cov["priority_weight_pct"] = 65.22
    return cov


def _uc_details() -> dict[str, dict[str, Any]]:
    return {
        "22.1.1": {
            "title": "ROPA",
            "controlFamily": "Records",
            "owner": "DPO",
            "evidence_count": 4,
            "source_path": "content/cat-22/UC-22.1.1.json",
        },
        "22.1.2": {
            "title": "Lawfulness checks",
            "controlFamily": "Privacy",
            "owner": "DPO",
            "evidence_count": 2,
            "source_path": "content/cat-22/UC-22.1.2.json",
        },
        "22.1.3": {
            "title": "Records retention",
            "controlFamily": "Records",
            "owner": "DPO",
            "evidence_count": 5,
            "source_path": "content/cat-22/UC-22.1.3.json",
        },
    }


def _gen_meta() -> dict[str, Any]:
    return {
        "catalogue_version": "9.0.0",
        "generator_script": "scripts/generate_evidence_packs.py",
        "inputs_sha256": "a" * 64,
    }


def test_render_json_twin_includes_metadata_and_contributing_ucs():
    out = ep._render_json_twin(
        _framework(), _version(), _extras(), _coverage_full(),
        _uc_details(), None, _gen_meta(),
    )
    assert out["id"] == "gdpr"
    assert out["coverage"]["coveragePct"] == 100.0
    assert out["coverage"]["contributingUcCount"] == 3
    assert {u["id"] for u in out["contributingUcs"]} == {"22.1.1", "22.1.2", "22.1.3"}
    assert out["generationMetadata"]["catalogue_version"] == "9.0.0"


def test_render_json_twin_handles_uncovered_clauses():
    out = ep._render_json_twin(
        _framework(), _version(), _extras(), _coverage_partial(),
        _uc_details(), None, _gen_meta(),
    )
    # Only the covered uc_ids count as contributing.
    assert out["coverage"]["contributingUcCount"] == 2


def test_render_json_twin_includes_derivation_info():
    derivation = {
        "parent": "gdpr",
        "parentVersion": "2018",
        "inheritanceMode": "identity",
        "divergences": [],
        "clauseMapping": {},
    }
    out = ep._render_json_twin(
        _framework(), _version(), _extras(), _coverage_full(),
        _uc_details(), derivation, _gen_meta(),
    )
    assert out["derivedFrom"] == derivation


def test_render_readme_has_one_row_per_pack():
    packs = [
        {
            "id": "gdpr",
            "shortName": "GDPR",
            "name": "General Data Protection Regulation",
            "tier": 1,
            "jurisdiction": ["EU"],
            "version": "2018",
            "coverage": {"coveragePct": 100.0, "priorityWeightPct": 100.0},
        },
        {
            "id": "hipaa-security",
            "shortName": "HIPAA",
            "name": "HIPAA Security Rule",
            "tier": 1,
            "jurisdiction": ["US"],
            "version": "2013",
            "coverage": {"coveragePct": None, "priorityWeightPct": None},
        },
    ]
    out = ep._render_readme(packs, _gen_meta())
    assert "# Evidence Packs" in out
    assert "**GDPR**" in out
    assert "**HIPAA**" in out
    # Em-dash fallback used when coveragePct is None.
    assert "—" in out


def test_render_markdown_pack_full_coverage_includes_all_sections():
    md = ep._render_markdown_pack(
        _framework(), _version(), _extras(), _coverage_full(),
        _uc_details(), None, _gen_meta(),
    )
    for heading in (
        "# Evidence Pack — GDPR",
        "## 1. Purpose of this evidence pack",
        "## 3. Catalogue coverage at a glance",
        "## 4. Clause-by-clause coverage",
        "## 11. Pack gaps and remediation backlog",
        "## 14. Provenance and regeneration",
    ):
        assert heading in md
    # Full-coverage branch: no gap table — text-only callout
    assert "100 % common-clause coverage" in md
    # Clause table renders with assurance badge
    assert "`full`" in md
    # Per-UC anchor section present
    assert "<a id='uc-22-1-1'></a>" in md


def test_render_markdown_pack_partial_coverage_lists_gaps():
    md = ep._render_markdown_pack(
        _framework(), _version(), _extras(), _coverage_partial(),
        _uc_details(), None, _gen_meta(),
    )
    # Partial coverage triggers the gap table
    assert "| Clause | Topic | Priority |" in md
    assert "`Art.6`" in md
    # Uncovered clause cell uses italic placeholder
    assert "_not yet covered_" in md


def test_render_markdown_pack_identity_derivation_renders_inheritance_note():
    derivation = {
        "parent": "gdpr",
        "parentVersion": "2018",
        "inheritanceMode": "identity",
        "divergences": [],
        "clauseMapping": {},
    }
    md = ep._render_markdown_pack(
        _framework(), _version(), _extras(), _coverage_full(),
        _uc_details(), derivation, _gen_meta(),
    )
    assert "Identity-mode derivatives inherit" in md
    assert "Because this regulation derives from" in md


def test_render_markdown_pack_non_identity_derivation_renders_short_note():
    derivation = {
        "parent": "gdpr",
        "parentVersion": "2018",
        "inheritanceMode": "informative",
        "divergences": [],
        "clauseMapping": {},
    }
    md = ep._render_markdown_pack(
        _framework(), _version(), _extras(), _coverage_full(),
        _uc_details(), derivation, _gen_meta(),
    )
    assert "informative" in md
    # The identity-only callout must NOT appear.
    assert "Identity-mode derivatives inherit" not in md


def test_render_markdown_pack_renders_sunset_on_when_present():
    version = _version()
    version["sunsetOn"] = "2025-12-31"
    md = ep._render_markdown_pack(
        _framework(), version, _extras(), _coverage_full(),
        _uc_details(), None, _gen_meta(),
    )
    assert "Sunset" in md
    assert "2025-12-31" in md


def test_render_markdown_pack_omits_optional_metadata_when_blank():
    version = _version()
    version["authoritativeUrl"] = None
    version["effectiveFrom"] = None
    md = ep._render_markdown_pack(
        _framework(), version, _extras(), _coverage_full(),
        _uc_details(), None, _gen_meta(),
    )
    # Optional callouts disappear when the fields are not populated.
    assert "Authoritative source" not in md
    assert "Effective from" not in md


def test_render_markdown_pack_skips_per_uc_detail_when_no_contributors():
    cov = _coverage_full()
    for clause in cov["clauses"]:
        clause["uc_ids"] = []
        clause["covered"] = False
        clause["uc_count"] = 0
        clause["max_assurance"] = None
    md = ep._render_markdown_pack(
        _framework(), _version(), _extras(), cov,
        _uc_details(), None, _gen_meta(),
    )
    # `### 4.1 Contributing UC detail` only renders when uc_ids_all is non-empty.
    assert "### 4.1 Contributing UC detail" not in md


def test_render_markdown_pack_handles_more_than_six_ucs_per_clause():
    cov = _coverage_full()
    cov["clauses"][0]["uc_ids"] = [f"22.1.{i}" for i in range(1, 9)]
    cov["clauses"][0]["uc_count"] = 8
    md = ep._render_markdown_pack(
        _framework(), _version(), _extras(), cov,
        _uc_details(), None, _gen_meta(),
    )
    # The clause table truncates the visible list at 6 and adds an "(+2 more)" suffix.
    assert "(+2 more)" in md


# ---------------------------------------------------------------------------
# _check_drift / _prune_orphans
# ---------------------------------------------------------------------------


def _patch_output_dirs(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    docs_dir = tmp_path / "docs" / "evidence-packs"
    api_dir = tmp_path / "api" / "v1" / "evidence-packs"
    docs_dir.mkdir(parents=True)
    api_dir.mkdir(parents=True)
    monkeypatch.setattr(ep, "ROOT", tmp_path)
    monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs_dir)
    monkeypatch.setattr(ep, "API_OUT_DIR", api_dir)
    return docs_dir, api_dir


def test_check_drift_reports_missing_md_but_skips_missing_api(monkeypatch, tmp_path: Path):
    docs_dir, api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    planned = {
        docs_dir / "gdpr.md": b"# pack\n",
        api_dir / "gdpr.json": b"{}\n",
    }
    drift = ep._check_drift(planned)
    # Missing .md → drift; missing .json under api dir → silently skipped.
    assert any(d.startswith("missing: docs/evidence-packs/gdpr.md") for d in drift)
    assert all("api/v1/evidence-packs/gdpr.json" not in d for d in drift)


def test_check_drift_reports_changed_md(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    on_disk = docs_dir / "gdpr.md"
    on_disk.write_text("on-disk body\n", encoding="utf-8")
    planned = {on_disk: b"planned body\n"}
    drift = ep._check_drift(planned)
    assert any(d == "changed: docs/evidence-packs/gdpr.md" for d in drift)
    # Diff body appears (first few unified-diff lines).
    assert any("planned body" in d for d in drift)


def test_check_drift_strips_citation_markers_before_compare(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    on_disk = docs_dir / "gdpr.md"
    on_disk.write_text(
        "body\n<sup class=\"ref\">[<a href=\"#ref-1\">1</a>]</sup>\n",
        encoding="utf-8",
    )
    planned = {on_disk: b"body\n\n"}
    drift = ep._check_drift(planned)
    # After citation stripping the contents match → no drift entry.
    assert drift == []


def test_check_drift_reports_orphans_outside_exempt_list(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / "orphan.md").write_text("x\n", encoding="utf-8")
    drift = ep._check_drift({})
    assert any("orphan: docs/evidence-packs/orphan.md" in d for d in drift)


def test_check_drift_skips_exempt_orphan_stems(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    # `cert-in` is in EXEMPT_ORPHANS — must not be reported.
    (docs_dir / "cert-in.md").write_text("x\n", encoding="utf-8")
    drift = ep._check_drift({})
    assert drift == []


def test_prune_orphans_deletes_extra_files(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / "gdpr.md").write_text("planned\n", encoding="utf-8")
    (docs_dir / "obsolete.md").write_text("delete me\n", encoding="utf-8")
    planned = {docs_dir / "gdpr.md": b"planned\n"}
    ep._prune_orphans(planned)
    assert (docs_dir / "gdpr.md").exists()
    assert not (docs_dir / "obsolete.md").exists()


def test_prune_orphans_preserves_exempt_packs(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / "cert-in.md").write_text("hand-authored\n", encoding="utf-8")
    ep._prune_orphans({})
    assert (docs_dir / "cert-in.md").exists()


def test_prune_orphans_ignores_dotfiles(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / ".DS_Store").write_bytes(b"junk")
    ep._prune_orphans({})
    assert (docs_dir / ".DS_Store").exists()


def test_prune_orphans_skips_missing_output_dirs(monkeypatch, tmp_path: Path):
    # Replace one of the dirs with a path that does not exist on disk.
    monkeypatch.setattr(ep, "ROOT", tmp_path)
    monkeypatch.setattr(ep, "DOCS_OUT_DIR", tmp_path / "missing_docs")
    monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "missing_api")
    # Should be a no-op (no AttributeError on iterdir).
    ep._prune_orphans({})


def test_prune_orphans_skips_subdirectories(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / "subdir").mkdir()  # not a file — must be skipped
    ep._prune_orphans({})
    assert (docs_dir / "subdir").is_dir()


def test_check_drift_skips_missing_output_dirs(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(ep, "ROOT", tmp_path)
    monkeypatch.setattr(ep, "DOCS_OUT_DIR", tmp_path / "no_docs")
    monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "no_api")
    # Both dirs missing → orphan loop hits the continue branch silently.
    assert ep._check_drift({}) == []


def test_check_drift_skips_dotfile_orphans(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / ".hidden").write_text("x\n", encoding="utf-8")
    assert ep._check_drift({}) == []


def test_check_drift_skips_directory_entries(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    (docs_dir / "subdir").mkdir()
    # Directories aren't files → must not be reported as orphans.
    assert ep._check_drift({}) == []


def test_check_drift_reports_changed_json_without_citation_strip(monkeypatch, tmp_path: Path):
    # JSON twin files bypass the citation-marker strip path
    # (lines 1634-1635) and still emit a unified-diff.
    _docs_dir, api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    on_disk = api_dir / "gdpr.json"
    on_disk.write_text("{\"old\": true}\n", encoding="utf-8")
    planned = {on_disk: b'{"new": true}\n'}
    drift = ep._check_drift(planned)
    assert any(d == "changed: api/v1/evidence-packs/gdpr.json" for d in drift)
    # Diff body printed (under the 30-line cap).
    assert any("new" in d for d in drift)


def test_check_drift_changed_non_md_non_json_emits_changed_without_diff(monkeypatch, tmp_path: Path):
    # Files with extensions outside {.md, .json} still surface as
    # "changed" entries but skip the diff body — exercises the
    # branch from 1638 back to the next iteration of the loop.
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    on_disk = docs_dir / "side.txt"
    on_disk.write_text("v1\n", encoding="utf-8")
    drift = ep._check_drift({on_disk: b"v2\n"})
    assert drift == ["changed: docs/evidence-packs/side.txt"]


def test_check_drift_truncates_large_diff_output(monkeypatch, tmp_path: Path):
    docs_dir, _api_dir = _patch_output_dirs(monkeypatch, tmp_path)
    on_disk = docs_dir / "gdpr.md"
    on_disk.write_text("\n".join(f"old{i}" for i in range(60)) + "\n", encoding="utf-8")
    planned = {on_disk: ("\n".join(f"new{i}" for i in range(60)) + "\n").encode()}
    drift = ep._check_drift(planned)
    # Diff must include the truncation hint when more than 30 diff lines fire.
    assert any("more diff lines" in d for d in drift)


# ---------------------------------------------------------------------------
# _chain_doc_references
# ---------------------------------------------------------------------------


def test_chain_doc_references_warns_when_script_missing(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setattr(ep, "_DOC_REFS_SCRIPT", tmp_path / "no-script.py")
    rc = ep._chain_doc_references()
    captured = capsys.readouterr()
    assert rc == 0
    assert "WARNING:" in captured.err


def test_chain_doc_references_returns_subprocess_exit_code(monkeypatch, tmp_path: Path):
    script = tmp_path / "fake-script.py"
    script.write_text("# noop", encoding="utf-8")
    monkeypatch.setattr(ep, "_DOC_REFS_SCRIPT", script)

    class _Result:
        def __init__(self, code: int) -> None:
            self.returncode = code

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], cwd: str | None = None) -> Any:
        calls.append(cmd)
        return _Result(0)

    monkeypatch.setattr(ep.subprocess, "run", fake_run)
    assert ep._chain_doc_references() == 0
    # Script is invoked with the evidence-pack glob.
    assert any("--only" in c for c in calls)


def test_chain_doc_references_reports_nonzero_subprocess_exit(monkeypatch, tmp_path: Path, capsys):
    script = tmp_path / "fake-script.py"
    script.write_text("# noop", encoding="utf-8")
    monkeypatch.setattr(ep, "_DOC_REFS_SCRIPT", script)

    class _Result:
        returncode = 7

    monkeypatch.setattr(ep.subprocess, "run", lambda cmd, cwd=None: _Result())
    rc = ep._chain_doc_references()
    captured = capsys.readouterr()
    assert rc == 7
    assert "FAIL:" in captured.err


# ---------------------------------------------------------------------------
# _generate_all — end-to-end with synthetic fixtures
# ---------------------------------------------------------------------------


def _wire_generate_all(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    """Monkeypatch every module-level path that ``_generate_all`` reads
    so the function runs hermetically against fixtures under ``tmp_path``.
    Returns ``(docs_dir, api_dir)`` so the caller can inspect output."""
    docs_dir = tmp_path / "docs" / "evidence-packs"
    api_dir = tmp_path / "api" / "v1" / "evidence-packs"
    docs_dir.mkdir(parents=True)
    api_dir.mkdir(parents=True)

    reg_path = tmp_path / "regulations.json"
    extras_path = tmp_path / "evidence-pack-extras.json"
    schema_path = tmp_path / "evidence-pack-extras.schema.json"
    version_path = tmp_path / "VERSION"
    gaps_path = tmp_path / "compliance-gaps.json"

    # Two-framework fixture: gdpr (primary) and uk-gdpr (identity-mode
    # derivative) — covers both the gap-report and live-compute paths
    # AND the parent-clause inheritance branch.
    reg_path.write_text(
        json.dumps(
            {
                "aliasIndex": {"GDPR": "gdpr", "UK GDPR": "uk-gdpr"},
                "frameworks": [
                    {**_framework(), "versions": [_version()]},
                    {
                        "id": "uk-gdpr",
                        "shortName": "UK GDPR",
                        "name": "UK General Data Protection Regulation",
                        "tier": 2,
                        "jurisdiction": ["UK"],
                        "versions": [
                            {
                                "version": "2018",
                                "authoritativeUrl": "https://ico.org.uk",
                                "clauseUrlTemplate": "https://ico.org.uk/{clause}",
                                "effectiveFrom": "2018-05-25",
                                "commonClauses": [],  # inherits from gdpr
                            }
                        ],
                    },
                ],
                "derivesFrom": {
                    "uk-gdpr": {
                        "parent": "gdpr",
                        "parentVersion": "2018",
                        "inheritanceMode": "identity",
                        "divergences": [],
                        "clauseMapping": {},
                    },
                    "$schemaNote": "skipped",
                },
            }
        ),
        encoding="utf-8",
    )
    extras_path.write_text(
        json.dumps({"regulations": {"gdpr": _extras(), "uk-gdpr": _extras()}}),
        encoding="utf-8",
    )
    schema_path.write_text("{}", encoding="utf-8")
    version_path.write_text("9.9.9\n", encoding="utf-8")
    gaps_path.write_text(
        json.dumps(
            {
                "tiers": {
                    "tier-1": {
                        "gdpr": {
                            "versions": {
                                "2018": {
                                    "clauses": _coverage_full()["clauses"],
                                    "common_clause_count": 3,
                                    "covered_count": 3,
                                    "coverage_pct": 100.0,
                                    "priority_weight_total": 2.3,
                                    "priority_weight_covered": 2.3,
                                    "priority_weight_pct": 100.0,
                                }
                            }
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    # UC sidecar with compliance entries for both regulations.
    (tmp_path / "content" / "cat-22").mkdir(parents=True)
    (tmp_path / "content" / "cat-22" / "UC-22.1.1.json").write_text(
        json.dumps(
            {
                "id": "22.1.1",
                "title": "ROPA",
                "evidence": ["a", "b"],
                "controlFamily": "Records",
                "owner": "DPO",
                "compliance": [
                    {"regulation": "GDPR", "version": "2018", "clause": "Art.5", "assurance": "full"},
                    {"regulation": "UK GDPR", "version": "2018", "clause": "Art.5", "assurance": "partial"},
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(ep, "ROOT", tmp_path)
    monkeypatch.setattr(ep, "REGULATIONS_PATH", reg_path)
    monkeypatch.setattr(ep, "EXTRAS_PATH", extras_path)
    monkeypatch.setattr(ep, "EXTRAS_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(ep, "VERSION_PATH", version_path)
    monkeypatch.setattr(ep, "GAPS_REPORT_PATH", gaps_path)
    monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs_dir)
    monkeypatch.setattr(ep, "API_OUT_DIR", api_dir)
    monkeypatch.setattr(ep, "PACK_TARGETS", ["gdpr", "uk-gdpr"])
    return docs_dir, api_dir


def test_generate_all_write_mode_produces_md_and_json(monkeypatch, tmp_path: Path):
    docs_dir, api_dir = _wire_generate_all(monkeypatch, tmp_path)
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 0
    assert (docs_dir / "gdpr.md").exists()
    assert (docs_dir / "uk-gdpr.md").exists()
    assert (docs_dir / "README.md").exists()
    assert (api_dir / "gdpr.json").exists()
    assert (api_dir / "uk-gdpr.json").exists()
    assert (api_dir / "index.json").exists()


def test_generate_all_check_mode_succeeds_when_output_matches(monkeypatch, tmp_path: Path):
    # First write the artifacts, then re-run in --check mode against
    # the freshly written output.
    _wire_generate_all(monkeypatch, tmp_path)
    assert ep._generate_all(check=False, chain_citations=False) == 0
    assert ep._generate_all(check=True, chain_citations=False) == 0


def test_generate_all_check_mode_reports_drift(monkeypatch, tmp_path: Path, capsys):
    docs_dir, _api_dir = _wire_generate_all(monkeypatch, tmp_path)
    assert ep._generate_all(check=False, chain_citations=False) == 0
    # Mutate one of the written markdown packs and re-check.
    md_path = docs_dir / "gdpr.md"
    md_path.write_text("totally different body\n", encoding="utf-8")
    rc = ep._generate_all(check=True, chain_citations=False)
    captured = capsys.readouterr()
    assert rc == 1
    # Drift report goes to stderr.
    assert "DRIFT" in captured.err
    assert "changed: docs/evidence-packs/gdpr.md" in captured.err


def test_generate_all_errors_when_framework_missing_from_regulations(monkeypatch, tmp_path: Path):
    _wire_generate_all(monkeypatch, tmp_path)
    # Add an unknown target.
    monkeypatch.setattr(ep, "PACK_TARGETS", ["gdpr", "no-such-reg"])
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 1


def test_generate_all_errors_when_extras_missing(monkeypatch, tmp_path: Path):
    _docs_dir, _api_dir = _wire_generate_all(monkeypatch, tmp_path)
    # Strip extras for uk-gdpr so the second iteration trips.
    ep_extras = json.loads(ep.EXTRAS_PATH.read_text(encoding="utf-8"))
    ep_extras["regulations"].pop("uk-gdpr", None)
    ep.EXTRAS_PATH.write_text(json.dumps(ep_extras), encoding="utf-8")
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 1


def test_generate_all_chains_citations_when_enabled(monkeypatch, tmp_path: Path):
    _wire_generate_all(monkeypatch, tmp_path)
    chained = {"called": False}

    def fake_chain() -> int:
        chained["called"] = True
        return 0

    monkeypatch.setattr(ep, "_chain_doc_references", fake_chain)
    assert ep._generate_all(check=False, chain_citations=True) == 0
    assert chained["called"] is True


def test_generate_all_propagates_failing_chain_citations_exit_code(monkeypatch, tmp_path: Path):
    _wire_generate_all(monkeypatch, tmp_path)
    monkeypatch.setattr(ep, "_chain_doc_references", lambda: 7)
    rc = ep._generate_all(check=False, chain_citations=True)
    assert rc == 7


def test_generate_all_skips_unchanged_files_on_second_write(monkeypatch, tmp_path: Path, capsys):
    _wire_generate_all(monkeypatch, tmp_path)
    # First run writes 6 files.
    ep._generate_all(check=False, chain_citations=False)
    capsys.readouterr()  # clear
    # Second run finds every file unchanged → writes 0.
    ep._generate_all(check=False, chain_citations=False)
    out = capsys.readouterr().out
    assert "OK: wrote 0 file(s); total planned 6" in out


def test_generate_all_falls_back_to_max_version_when_extras_version_unknown(
    monkeypatch, tmp_path: Path
):
    _wire_generate_all(monkeypatch, tmp_path)
    extras_doc = json.loads(ep.EXTRAS_PATH.read_text(encoding="utf-8"))
    # Force extras version not to match any framework version, so the
    # loop completes without setting chosen_version and we fall through
    # to the max() selection branch.
    extras_doc["regulations"]["gdpr"]["version"] = "2099-unknown"
    ep.EXTRAS_PATH.write_text(json.dumps(extras_doc), encoding="utf-8")
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 0  # still succeeds — picks the only available version


def test_generate_all_errors_when_framework_has_no_versions(monkeypatch, tmp_path: Path, capsys):
    _wire_generate_all(monkeypatch, tmp_path)
    reg_doc = json.loads(ep.REGULATIONS_PATH.read_text(encoding="utf-8"))
    # Strip versions from gdpr → triggers the "no version available" return.
    for fw in reg_doc["frameworks"]:
        if fw["id"] == "gdpr":
            fw["versions"] = []
    ep.REGULATIONS_PATH.write_text(json.dumps(reg_doc), encoding="utf-8")
    rc = ep._generate_all(check=False, chain_citations=False)
    captured = capsys.readouterr()
    assert rc == 1
    assert "no version available for gdpr" in captured.err


def test_generate_all_identity_mode_handles_missing_parent_framework(
    monkeypatch, tmp_path: Path
):
    _wire_generate_all(monkeypatch, tmp_path)
    reg_doc = json.loads(ep.REGULATIONS_PATH.read_text(encoding="utf-8"))
    # Point uk-gdpr at a non-existent parent → identity-mode branches
    # take the "parent_framework not found" path.
    reg_doc["derivesFrom"]["uk-gdpr"]["parent"] = "ghost-reg"
    ep.REGULATIONS_PATH.write_text(json.dumps(reg_doc), encoding="utf-8")
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 0


def test_generate_all_identity_mode_handles_missing_parent_version(
    monkeypatch, tmp_path: Path
):
    _wire_generate_all(monkeypatch, tmp_path)
    reg_doc = json.loads(ep.REGULATIONS_PATH.read_text(encoding="utf-8"))
    # Parent framework exists, but parentVersion does not match any
    # version → parent_common_clauses ends up empty (covers the
    # `if parent_common_clauses:` False branch at line 1380).
    reg_doc["derivesFrom"]["uk-gdpr"]["parentVersion"] = "non-existent"
    ep.REGULATIONS_PATH.write_text(json.dumps(reg_doc), encoding="utf-8")
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 0


def test_generate_all_identity_mode_overlays_derivative_clauses_on_parent(
    monkeypatch, tmp_path: Path
):
    _wire_generate_all(monkeypatch, tmp_path)
    reg_doc = json.loads(ep.REGULATIONS_PATH.read_text(encoding="utf-8"))
    # Give uk-gdpr its own divergent clause so the overlay loop iterates.
    for fw in reg_doc["frameworks"]:
        if fw["id"] == "uk-gdpr":
            fw["versions"][0]["commonClauses"] = [
                {
                    "clause": "Art.5",  # override parent wording
                    "topic": "UK-specific principles",
                    "priorityWeight": 1.0,
                }
            ]
    ep.REGULATIONS_PATH.write_text(json.dumps(reg_doc), encoding="utf-8")
    rc = ep._generate_all(check=False, chain_citations=False)
    assert rc == 0
    pack_md = (ep.DOCS_OUT_DIR / "uk-gdpr.md").read_text(encoding="utf-8")
    assert "UK-specific principles" in pack_md


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def test_main_passes_check_and_no_citation_chain_flags(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_generate_all(check: bool, chain_citations: bool = True) -> int:
        captured["check"] = check
        captured["chain"] = chain_citations
        return 0

    monkeypatch.setattr(ep, "_generate_all", fake_generate_all)
    assert ep.main(["--check", "--no-citation-chain"]) == 0
    assert captured == {"check": True, "chain": False}


def test_main_defaults(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_generate_all(check: bool, chain_citations: bool = True) -> int:
        captured["check"] = check
        captured["chain"] = chain_citations
        return 0

    monkeypatch.setattr(ep, "_generate_all", fake_generate_all)
    assert ep.main([]) == 0
    assert captured == {"check": False, "chain": True}
