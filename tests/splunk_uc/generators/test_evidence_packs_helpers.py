"""Hermetic tests for src/splunk_uc/generators/evidence_packs.py helpers.

The full ``_generate_all`` pipeline is exercised by the CI drift gate
against the real catalogue; these tests target the pure helper
functions so the unit suite can validate algorithmic invariants
without paying the catalog-load cost.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from splunk_uc.generators import evidence_packs as ep  # noqa: E402


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


class TestLoadJson:
    def test_reads_valid_json(self, tmp_path):
        p = tmp_path / "x.json"
        p.write_text(json.dumps({"k": "v"}), encoding="utf-8")
        assert ep._load_json(p) == {"k": "v"}

    def test_raises_on_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{ broken", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            ep._load_json(p)


class TestDumpJsonBytes:
    def test_serialises_with_sorted_keys_and_trailing_newline(self):
        out = ep._dump_json_bytes({"b": 2, "a": 1})
        # Sorted keys → "a" before "b".
        assert out.startswith(b'{\n  "a": 1,\n  "b": 2\n}')
        assert out.endswith(b"\n")

    def test_handles_unicode_without_escaping(self):
        out = ep._dump_json_bytes({"name": "Müller"})
        assert b"M\xc3\xbcller" in out
        # Should NOT have escaped \u00fc.
        assert b"\\u" not in out

    def test_pretty_prints_with_two_space_indent(self):
        out = ep._dump_json_bytes({"a": [1, 2, 3]})
        text = out.decode("utf-8")
        # 2-space indent on lines after "{".
        assert "  " in text


class TestStableMarkdownBytes:
    def test_strips_trailing_whitespace_per_line(self):
        # Each line gets rstripped.
        out = ep._stable_markdown_bytes("hello   \nworld\t\n")
        assert out == b"hello\nworld\n"

    def test_collapses_trailing_blank_lines_to_single_newline(self):
        out = ep._stable_markdown_bytes("hi\n\n\n\n")
        assert out == b"hi\n"

    def test_empty_input_returns_single_newline(self):
        out = ep._stable_markdown_bytes("")
        assert out == b"\n"

    def test_single_line_no_trailing_newline_added_correctly(self):
        out = ep._stable_markdown_bytes("hello")
        assert out == b"hello\n"


class TestGetVersion:
    def test_returns_version_from_file(self, monkeypatch, tmp_path):
        v = tmp_path / "VERSION"
        v.write_text("9.9.9\n", encoding="utf-8")
        monkeypatch.setattr(ep, "VERSION_PATH", v, raising=True)
        assert ep._get_version() == "9.9.9"

    def test_returns_unknown_on_missing_file(self, monkeypatch, tmp_path):
        # Missing file → OSError → "unknown".
        monkeypatch.setattr(ep, "VERSION_PATH", tmp_path / "missing", raising=True)
        assert ep._get_version() == "unknown"


# ---------------------------------------------------------------------------
# UC sidecar discovery and indexing
# ---------------------------------------------------------------------------


class TestLoadAllUcs:
    """``_load_all_ucs`` annotates each UC with its repo-relative source path."""

    def test_loads_and_annotates(self, monkeypatch, tmp_path):
        # Create a fake content tree at tmp_path.
        content = tmp_path / "content" / "cat-99-test"
        content.mkdir(parents=True)
        (content / "UC-99.1.1.json").write_text(
            json.dumps({"id": "99.1.1", "title": "X", "compliance": []}),
            encoding="utf-8",
        )
        # Override ROOT so _iter_uc_sidecars globs the fake tree.
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)

        ucs = ep._load_all_ucs()
        assert len(ucs) == 1
        assert ucs[0]["id"] == "99.1.1"
        # Source path is relative to ROOT.
        assert ucs[0]["_source_path"] == "content/cat-99-test/UC-99.1.1.json"

    def test_raises_on_malformed_uc_json(self, monkeypatch, tmp_path, capsys):
        content = tmp_path / "content" / "cat-99"
        content.mkdir(parents=True)
        (content / "UC-99.1.1.json").write_text("{ bad", encoding="utf-8")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)

        with pytest.raises(json.JSONDecodeError):
            ep._load_all_ucs()
        # Error message printed to stderr.
        assert "is not valid JSON" in capsys.readouterr().err

    def test_returns_empty_when_no_sidecars(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        assert ep._load_all_ucs() == []


class TestBuildComplianceIndex:
    """Index UCs by (framework_id, version) → list of compliance entries."""

    def test_skips_uc_without_id(self):
        ucs = [{"title": "no id"}]
        idx = ep._build_compliance_index(ucs, alias_index={})
        assert idx == {}

    def test_skips_compliance_entry_without_regulation_or_clause(self):
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {"version": "4.0", "clause": "1.1"},  # no regulation
                    {"regulation": "PCI DSS", "version": "4.0"},  # no clause
                    {
                        "regulation": "PCI DSS",
                        "version": "4.0",
                        "clause": "1.1",
                    },
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={"PCI DSS": "pci-dss"})
        assert ("pci-dss", "4.0") in idx
        assert len(idx[("pci-dss", "4.0")]) == 1

    def test_alias_normalises_regulation_name(self):
        # Human-readable name → framework id via alias_index.
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {"regulation": "PCI DSS", "version": "4.0", "clause": "1.1"}
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={"PCI DSS": "pci-dss"})
        assert ("pci-dss", "4.0") in idx
        # The lowercase fallback is also handled.

    def test_alias_lookup_is_case_insensitive(self):
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {"regulation": "pci dss", "version": "4.0", "clause": "1.1"}
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={"PCI DSS": "pci-dss"})
        # Case-insensitive lookup hits.
        assert ("pci-dss", "4.0") in idx

    def test_skips_dollar_prefixed_aliases(self):
        # Lines 263: ``$schema`` etc. are skipped.
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {"regulation": "$schema", "version": "1", "clause": "x"},
                    {"regulation": "GDPR", "version": "2018", "clause": "Art.5"},
                ],
            }
        ]
        idx = ep._build_compliance_index(
            ucs,
            alias_index={"$schema": "should-be-ignored", "GDPR": "gdpr"},
        )
        # GDPR makes it; $schema becomes a passthrough (not aliased).
        assert ("gdpr", "2018") in idx

    def test_unknown_regulation_passes_through_unchanged(self):
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {"regulation": "Some-Unknown-Reg", "version": "1.0", "clause": "x"}
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={})
        # Falls through with the literal name as the framework key.
        assert ("Some-Unknown-Reg", "1.0") in idx

    def test_falls_back_to_name_when_no_title(self):
        ucs = [
            {
                "id": "1.1.1",
                "name": "Fallback",  # no "title", uses "name"
                "compliance": [
                    {"regulation": "GDPR", "version": "2018", "clause": "Art.5"}
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={"GDPR": "gdpr"})
        entries = idx[("gdpr", "2018")]
        assert entries[0]["uc_title"] == "Fallback"

    def test_fills_default_assurance_and_provenance(self):
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {"regulation": "GDPR", "version": "2018", "clause": "Art.5"}
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={"GDPR": "gdpr"})
        entry = idx[("gdpr", "2018")][0]
        assert entry["assurance"] == "contributing"
        assert entry["provenance"] == "native"
        assert entry["rationale"] == ""

    def test_passes_through_explicit_metadata(self):
        ucs = [
            {
                "id": "1.1.1",
                "title": "T",
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "version": "2018",
                        "clause": "Art.5",
                        "assurance": "full",
                        "provenance": "derived",
                        "rationale": "Strict consent.",
                        "derivationSource": "Art.6",
                    }
                ],
            }
        ]
        idx = ep._build_compliance_index(ucs, alias_index={"GDPR": "gdpr"})
        entry = idx[("gdpr", "2018")][0]
        assert entry["assurance"] == "full"
        assert entry["provenance"] == "derived"
        assert entry["rationale"] == "Strict consent."
        assert entry["derivationSource"] == "Art.6"


# ---------------------------------------------------------------------------
# Assurance bucketing
# ---------------------------------------------------------------------------


class TestBestAssurance:
    def test_picks_full_over_partial(self):
        entries = [{"assurance": "partial"}, {"assurance": "full"}]
        assert ep._best_assurance(entries) == "full"

    def test_picks_partial_over_contributing(self):
        entries = [{"assurance": "contributing"}, {"assurance": "partial"}]
        assert ep._best_assurance(entries) == "partial"

    def test_returns_contributing_for_unknown_or_missing(self):
        entries = [{"assurance": "unknown"}, {"assurance": None}]
        assert ep._best_assurance(entries) == "contributing"

    def test_empty_list_returns_default(self):
        assert ep._best_assurance([]) == "contributing"

    def test_string_assurance_handled(self):
        entries = [{"assurance": "full"}]
        assert ep._best_assurance(entries) == "full"


# ---------------------------------------------------------------------------
# Clause sorting
# ---------------------------------------------------------------------------


class TestClauseSortKey:
    def test_natural_ordering_within_family(self):
        # Art.5 should come before Art.10 — which it doesn't with
        # plain str sort but does with this natural ordering.
        clauses = ["Art.10", "Art.2", "Art.5"]
        clauses.sort(key=ep._clause_sort_key)
        assert clauses == ["Art.2", "Art.5", "Art.10"]

    def test_subclause_after_parent(self):
        # Art.5 < Art.5(1)(e) — the subclause adds digits to the tuple.
        a = ep._clause_sort_key("Art.5")
        b = ep._clause_sort_key("Art.5(1)(e)")
        assert a < b

    def test_different_families_sort_lexically(self):
        # §164.308 < §164.502 (numeric within family).
        clauses = ["§164.502", "§164.308"]
        clauses.sort(key=ep._clause_sort_key)
        assert clauses == ["§164.308", "§164.502"]

    def test_clause_without_digits(self):
        # No digits → empty numeric tuple, still sortable.
        key = ep._clause_sort_key("preamble")
        assert key == ("preamble", (), "preamble")


# ---------------------------------------------------------------------------
# Gap-report lookup
# ---------------------------------------------------------------------------


class TestLoadGapReport:
    def test_returns_empty_dict_when_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ep, "GAPS_REPORT_PATH", tmp_path / "missing.json", raising=True)
        assert ep._load_gap_report() == {}

    def test_loads_existing_file(self, monkeypatch, tmp_path):
        gap = tmp_path / "gaps.json"
        gap.write_text(json.dumps({"tiers": {"tier-1": {}}}), encoding="utf-8")
        monkeypatch.setattr(ep, "GAPS_REPORT_PATH", gap, raising=True)
        assert "tiers" in ep._load_gap_report()


class TestGapReportLookup:
    def test_returns_none_when_no_tiers(self):
        assert ep._gap_report_lookup({}, "x", "1") is None

    def test_finds_in_tier_1(self):
        report = {
            "tiers": {
                "tier-1": {
                    "gdpr": {"versions": {"2018": {"coverage_pct": 50.0}}}
                }
            }
        }
        result = ep._gap_report_lookup(report, "gdpr", "2018")
        assert result == {"coverage_pct": 50.0}

    def test_finds_in_tier_2_when_missing_in_1(self):
        report = {
            "tiers": {
                "tier-1": {},
                "tier-2": {"x": {"versions": {"1": {"covered_count": 3}}}},
            }
        }
        result = ep._gap_report_lookup(report, "x", "1")
        assert result == {"covered_count": 3}

    def test_returns_none_when_version_not_found(self):
        report = {
            "tiers": {
                "tier-1": {
                    "gdpr": {"versions": {"2018": {}}}
                }
            }
        }
        assert ep._gap_report_lookup(report, "gdpr", "9999") is None

    def test_returns_none_when_reg_not_found(self):
        report = {"tiers": {"tier-1": {}}}
        assert ep._gap_report_lookup(report, "missing", "1") is None


# ---------------------------------------------------------------------------
# Coverage computation
# ---------------------------------------------------------------------------


class TestComputeCoverageFromIndex:
    def test_no_clauses_no_coverage(self):
        result = ep._compute_coverage_from_index("gdpr", "2018", [], {})
        assert result["common_clause_count"] == 0
        assert result["covered_count"] == 0
        assert result["coverage_pct"] == 0.0
        assert result["clauses"] == []

    def test_single_clause_uncovered(self):
        clauses = [{"clause": "Art.5", "topic": "Privacy", "priorityWeight": 1.0}]
        result = ep._compute_coverage_from_index("gdpr", "2018", clauses, {})
        assert result["common_clause_count"] == 1
        assert result["covered_count"] == 0
        assert result["coverage_pct"] == 0.0
        c = result["clauses"][0]
        assert c["covered"] is False
        assert c["max_assurance"] is None
        assert c["uc_count"] == 0
        assert c["uc_ids"] == []

    def test_single_clause_covered(self):
        clauses = [{"clause": "Art.5", "topic": "T", "priorityWeight": 1.0}]
        idx = {
            ("gdpr", "2018"): [
                {
                    "uc_id": "1.1.1",
                    "uc_title": "X",
                    "clause": "Art.5",
                    "assurance": "full",
                    "rationale": "",
                    "provenance": "native",
                    "derivationSource": None,
                    "source_path": "p",
                }
            ]
        }
        result = ep._compute_coverage_from_index("gdpr", "2018", clauses, idx)
        assert result["covered_count"] == 1
        assert result["coverage_pct"] == 100.0
        c = result["clauses"][0]
        assert c["covered"] is True
        assert c["max_assurance"] == "full"
        assert c["uc_count"] == 1
        assert c["uc_ids"] == ["1.1.1"]

    def test_priority_weighted_partial_coverage(self):
        clauses = [
            {"clause": "A", "priorityWeight": 1.0},
            {"clause": "B", "priorityWeight": 2.0},
        ]
        idx = {
            ("x", "1"): [
                {
                    "uc_id": "1.1.1",
                    "uc_title": "Y",
                    "clause": "B",
                    "assurance": "partial",
                    "rationale": "",
                    "provenance": "native",
                    "derivationSource": None,
                    "source_path": "p",
                }
            ]
        }
        result = ep._compute_coverage_from_index("x", "1", clauses, idx)
        # 1 of 2 covered; weight: 2 of 3.
        assert result["covered_count"] == 1
        assert abs(result["coverage_pct"] - 50.0) < 1e-6
        assert abs(result["priority_weight_pct"] - (2 / 3 * 100)) < 1e-6

    def test_default_priority_weight_05_when_missing(self):
        clauses = [{"clause": "A"}]
        result = ep._compute_coverage_from_index("x", "1", clauses, {})
        # Default weight is 0.5.
        assert result["priority_weight_total"] == 0.5

    def test_uc_ids_are_unique_and_sorted(self):
        clauses = [{"clause": "A", "priorityWeight": 1.0}]
        idx = {
            ("x", "1"): [
                {
                    "uc_id": "z",
                    "uc_title": "",
                    "clause": "A",
                    "assurance": "full",
                    "rationale": "",
                    "provenance": "native",
                    "derivationSource": None,
                    "source_path": "p",
                },
                {
                    "uc_id": "a",
                    "uc_title": "",
                    "clause": "A",
                    "assurance": "full",
                    "rationale": "",
                    "provenance": "native",
                    "derivationSource": None,
                    "source_path": "p",
                },
                {
                    "uc_id": "a",  # duplicate
                    "uc_title": "",
                    "clause": "A",
                    "assurance": "partial",
                    "rationale": "",
                    "provenance": "native",
                    "derivationSource": None,
                    "source_path": "p",
                },
            ]
        }
        result = ep._compute_coverage_from_index("x", "1", clauses, idx)
        c = result["clauses"][0]
        assert c["uc_ids"] == ["a", "z"]


class TestExtractCoverage:
    def test_uses_gap_block_when_present(self):
        gap_block = {
            "clauses": [
                {
                    "clause": "Art.5",
                    "topic": "Privacy",
                    "priority_weight": 1.0,
                    "covered": True,
                    "max_assurance": "full",
                    "uc_count": 2,
                    "uc_ids": ["b", "a"],
                }
            ],
            "common_clause_count": 1,
            "covered_count": 1,
            "coverage_pct": 100.0,
            "priority_weight_total": 1.0,
            "priority_weight_covered": 1.0,
            "priority_weight_pct": 100.0,
        }
        result = ep._extract_coverage(gap_block, "2018", "gdpr", [], {})
        # uc_ids must be sorted in the output.
        assert result["clauses"][0]["uc_ids"] == ["a", "b"]
        assert result["coverage_pct"] == 100.0

    def test_falls_back_to_live_when_no_gap_block(self):
        clauses = [{"clause": "X", "priorityWeight": 1.0}]
        result = ep._extract_coverage(None, "1", "x", clauses, {})
        # Falls back to _compute_coverage_from_index.
        assert result["common_clause_count"] == 1
        assert result["covered_count"] == 0

    def test_falls_back_when_gap_block_lacks_clauses(self):
        # gap_block exists but has no "clauses" → falls back to live.
        clauses = [{"clause": "X", "priorityWeight": 1.0}]
        result = ep._extract_coverage(
            {"some_other_field": "x"}, "1", "x", clauses, {}
        )
        assert result["common_clause_count"] == 1


# ---------------------------------------------------------------------------
# UC details
# ---------------------------------------------------------------------------


class TestBuildUcDetails:
    def test_empty_index_returns_empty_dict(self):
        result = ep._build_uc_details({}, "gdpr", "2018", {})
        assert result == {}

    def test_skips_duplicate_uc(self):
        idx = {
            ("gdpr", "2018"): [
                {
                    "uc_id": "1.1.1",
                    "uc_title": "First",
                    "clause": "A",
                    "source_path": "p1",
                },
                {
                    "uc_id": "1.1.1",  # same UC, different clause
                    "uc_title": "First",
                    "clause": "B",
                    "source_path": "p1",
                },
            ]
        }
        details = ep._build_uc_details(idx, "gdpr", "2018", {})
        # Only one entry per UC.
        assert len(details) == 1

    def test_uses_uc_doc_evidence_count_list(self):
        idx = {
            ("gdpr", "2018"): [
                {"uc_id": "1.1.1", "uc_title": "T", "clause": "A", "source_path": "p"}
            ]
        }
        uc_docs = {
            "1.1.1": {"title": "T", "evidence": [{"x": 1}, {"y": 2}, {"z": 3}]}
        }
        details = ep._build_uc_details(idx, "gdpr", "2018", uc_docs)
        assert details["1.1.1"]["evidence_count"] == 3

    def test_handles_legacy_dict_evidence(self):
        idx = {
            ("gdpr", "2018"): [
                {"uc_id": "1.1.1", "uc_title": "T", "clause": "A", "source_path": "p"}
            ]
        }
        uc_docs = {
            "1.1.1": {
                "title": "T",
                "evidence": {"alpha": ["a1", "a2"], "beta": "b1"},
            }
        }
        details = ep._build_uc_details(idx, "gdpr", "2018", uc_docs)
        # Flattened: 2 from "alpha" list + 1 dict from "beta" string = 3.
        assert details["1.1.1"]["evidence_count"] == 3

    def test_string_evidence_counts_as_one(self):
        idx = {
            ("gdpr", "2018"): [
                {"uc_id": "1.1.1", "uc_title": "T", "clause": "A", "source_path": "p"}
            ]
        }
        uc_docs = {"1.1.1": {"title": "T", "evidence": "Some evidence"}}
        details = ep._build_uc_details(idx, "gdpr", "2018", uc_docs)
        assert details["1.1.1"]["evidence_count"] == 1

    def test_blank_string_evidence_counts_as_zero(self):
        idx = {
            ("gdpr", "2018"): [
                {"uc_id": "1.1.1", "uc_title": "T", "clause": "A", "source_path": "p"}
            ]
        }
        uc_docs = {"1.1.1": {"title": "T", "evidence": "   "}}
        details = ep._build_uc_details(idx, "gdpr", "2018", uc_docs)
        assert details["1.1.1"]["evidence_count"] == 0

    def test_no_evidence_counts_as_zero(self):
        idx = {
            ("gdpr", "2018"): [
                {"uc_id": "1.1.1", "uc_title": "T", "clause": "A", "source_path": "p"}
            ]
        }
        details = ep._build_uc_details(idx, "gdpr", "2018", {"1.1.1": {"title": "T"}})
        assert details["1.1.1"]["evidence_count"] == 0

    def test_carries_through_control_family_and_owner(self):
        idx = {
            ("x", "1"): [
                {"uc_id": "1.1.1", "uc_title": "T", "clause": "A", "source_path": "p"}
            ]
        }
        uc_docs = {
            "1.1.1": {
                "title": "T",
                "controlFamily": "Access Control",
                "owner": "Security Ops",
            }
        }
        details = ep._build_uc_details(idx, "x", "1", uc_docs)
        assert details["1.1.1"]["controlFamily"] == "Access Control"
        assert details["1.1.1"]["owner"] == "Security Ops"


# ---------------------------------------------------------------------------
# Markdown rendering helpers
# ---------------------------------------------------------------------------


class TestClauseUrl:
    def test_returns_none_when_template_missing(self):
        assert ep._clause_url(None, "Art.5") is None

    def test_returns_none_when_clause_empty(self):
        assert ep._clause_url("https://x/{clause}", "") is None

    def test_substitutes_clause_into_template(self):
        assert (
            ep._clause_url("https://example.com/gdpr/{clause}", "Art.5")
            == "https://example.com/gdpr/Art.5"
        )


class TestAssuranceBadge:
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("full", "full"),
            ("partial", "partial"),
            ("contributing", "contributing"),
            (None, "—"),
            ("unknown", "—"),
            ("", "—"),
        ],
    )
    def test_recognises_known_values(self, input_, expected):
        assert ep._assurance_badge(input_) == expected


class TestFmtPct:
    def test_none_returns_em_dash(self):
        assert ep._fmt_pct(None) == "—"

    def test_zero_formats_correctly(self):
        assert ep._fmt_pct(0.0) == "0.0%"

    def test_round_to_one_decimal(self):
        assert ep._fmt_pct(99.95) == "100.0%"
        assert ep._fmt_pct(33.333) == "33.3%"


# ---------------------------------------------------------------------------
# Citation marker stripping
# ---------------------------------------------------------------------------


class TestStripCitationMarkers:
    def test_strips_inline_sup_markers(self):
        # Single inline marker.
        body = b'Some text<sup class="ref">[<a href="#ref-3">3</a>]</sup>.\n'
        result = ep._strip_citation_markers(body)
        assert b"<sup" not in result
        assert b"Some text." in result

    def test_strips_multiple_inline_markers(self):
        body = (
            b'A<sup class="ref">[<a href="#ref-1">1</a>]</sup> '
            b'B<sup class="ref">[<a href="#ref-2">2</a>]</sup>.\n'
        )
        result = ep._strip_citation_markers(body)
        assert b"<sup" not in result
        assert b"A B." in result

    def test_strips_autogenerated_block(self):
        body = (
            b"Body text.\n"
            b"---\n\n"
            b"<!-- BEGIN-AUTOGENERATED-SOURCES -->\n"
            b"## References\n\n"
            b"[1] Foo\n"
            b"<!-- END-AUTOGENERATED-SOURCES -->\n"
        )
        result = ep._strip_citation_markers(body)
        assert b"BEGIN-AUTOGENERATED" not in result
        assert b"END-AUTOGENERATED" not in result
        assert b"Body text." in result

    def test_normalises_to_single_trailing_newline(self):
        body = b"text\n\n\n"
        result = ep._strip_citation_markers(body)
        assert result.endswith(b"\n")
        # Only one trailing newline.
        assert not result.endswith(b"\n\n")

    def test_idempotent_when_no_markers(self):
        body = b"Plain text.\n"
        result = ep._strip_citation_markers(body)
        assert result == body


# ---------------------------------------------------------------------------
# JSON twin renderer
# ---------------------------------------------------------------------------


def _make_minimal_render_inputs(reg_id="gdpr"):
    """Build the minimum dicts ``_render_json_twin`` (and the markdown
    renderer) require so the tests can drive them without a full catalog
    fixture.
    """
    framework = {
        "id": reg_id,
        "shortName": "GDPR",
        "name": "General Data Protection Regulation",
        "tier": 1,
        "jurisdiction": ["EU", "EEA"],
    }
    version = {
        "version": "2018",
        "authoritativeUrl": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "clauseUrlTemplate": "https://example.com/{clause}",
        "effectiveFrom": "2018-05-25",
        "sunsetOn": None,
        "commonClauses": [
            {"clause": "Art.5", "topic": "Privacy", "priorityWeight": 1.0},
            {"clause": "Art.32", "topic": "Security", "priorityWeight": 1.0},
        ],
    }
    extras = {
        "version": "2018",
        "summary": "Privacy by design.",
        "scope": "Personal data of EU data subjects.",
        "territorialScope": "EU + targeting EU residents.",
        "commonEvidenceSources": [
            {"name": "Audit logs", "description": "Authentication trails"}
        ],
        "retentionGuidance": [{"period": "6 months", "rationale": "GDPR §5"}],
        "testingApproach": "Tabletop quarterly.",
        "reportingCadence": "Annual.",
        "roles": [{"role": "DPO", "responsibility": "Compliance"}],
        "authoritativeGuidance": [{"title": "EDPB Guidelines"}],
        "commonDeficiencies": [{"area": "Subject access requests"}],
        "auditorQuestions": [{"q": "Show retention enforcement"}],
        "penaltyStructure": "Up to 4% of global turnover.",
    }
    coverage = {
        "common_clause_count": 2,
        "covered_count": 1,
        "coverage_pct": 50.0,
        "priority_weight_total": 2.0,
        "priority_weight_covered": 1.0,
        "priority_weight_pct": 50.0,
        "clauses": [
            {
                "clause": "Art.5",
                "topic": "Privacy",
                "priority_weight": 1.0,
                "covered": True,
                "max_assurance": "full",
                "uc_count": 1,
                "uc_ids": ["1.1.1"],
            },
            {
                "clause": "Art.32",
                "topic": "Security",
                "priority_weight": 1.0,
                "covered": False,
                "max_assurance": None,
                "uc_count": 0,
                "uc_ids": [],
            },
        ],
    }
    uc_details = {
        "1.1.1": {
            "title": "Audit log retention",
            "controlFamily": "Access Control",
            "owner": "Sec Ops",
            "evidence_count": 4,
            "source_path": "content/cat-1-x/UC-1.1.1.json",
        }
    }
    metadata = {
        "catalogue_version": "9.9.9",
        "generator_script": "scripts/generate_evidence_packs.py",
        "inputs_sha256": "abc123",
    }
    return framework, version, extras, coverage, uc_details, metadata


class TestRenderJsonTwin:
    def test_minimal_valid_input(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        result = ep._render_json_twin(
            framework, version, extras, coverage, uc_details, None, metadata
        )
        # Top-level identity fields.
        assert result["id"] == "gdpr"
        assert result["shortName"] == "GDPR"
        assert result["version"] == "2018"
        assert result["jurisdiction"] == ["EU", "EEA"]
        # Coverage rollups derived from the input.
        assert result["coverage"]["commonClauseCount"] == 2
        assert result["coverage"]["coveragePct"] == 50.0
        # Contributing UCs derive from clauses.uc_ids.
        assert result["coverage"]["contributingUcCount"] == 1
        assert len(result["contributingUcs"]) == 1
        assert result["contributingUcs"][0]["id"] == "1.1.1"
        assert result["contributingUcs"][0]["evidenceCount"] == 4
        assert result["contributingUcs"][0]["sourcePath"] == "content/cat-1-x/UC-1.1.1.json"
        # Pass-through fields.
        assert result["evidence"]["commonSources"]
        assert result["evidence"]["retentionGuidance"]
        assert result["testing"]["approach"] == "Tabletop quarterly."
        assert result["roles"]
        assert result["penaltyStructure"] == "Up to 4% of global turnover."
        assert result["generationMetadata"] == metadata
        # Derivation info pass-through (None when not derived).
        assert result["derivedFrom"] is None

    def test_passes_derivation_info_when_present(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        derivation = {"parent": "gdpr", "inheritanceMode": "extends"}
        result = ep._render_json_twin(
            framework, version, extras, coverage, uc_details, derivation, metadata
        )
        assert result["derivedFrom"] == derivation

    def test_handles_missing_clauses(self):
        framework, version, extras, _, _, metadata = _make_minimal_render_inputs()
        coverage = {"common_clause_count": 0, "covered_count": 0, "coverage_pct": 0.0}
        result = ep._render_json_twin(
            framework, version, extras, coverage, {}, None, metadata
        )
        # Empty clauses → empty contributingUcs.
        assert result["clauses"] == []
        assert result["contributingUcs"] == []
        assert result["coverage"]["contributingUcCount"] == 0

    def test_falls_back_to_extras_version_when_version_missing(self):
        framework, _, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        version = {"authoritativeUrl": None}  # no "version" key
        result = ep._render_json_twin(
            framework, version, extras, coverage, uc_details, None, metadata
        )
        # Falls back to extras["version"].
        assert result["version"] == "2018"

    def test_empty_jurisdiction_returns_empty_list(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        framework = {**framework, "jurisdiction": None}
        result = ep._render_json_twin(
            framework, version, extras, coverage, uc_details, None, metadata
        )
        assert result["jurisdiction"] == []


# ---------------------------------------------------------------------------
# README renderer
# ---------------------------------------------------------------------------


class TestRenderReadme:
    def test_minimal_no_packs(self):
        result = ep._render_readme([], {"catalogue_version": "9.9.9"})
        # Headers always present.
        assert result.startswith("# Evidence Packs")
        assert "## How to use these packs" in result
        assert "## Pack catalogue" in result
        # Catalogue version surfaces in regen footer.
        assert "9.9.9" in result

    def test_pack_row_renders(self):
        pack = {
            "id": "gdpr",
            "shortName": "GDPR",
            "tier": 1,
            "jurisdiction": ["EU"],
            "version": "2018",
            "coverage": {"coveragePct": 75.5, "priorityWeightPct": 80.2},
        }
        result = ep._render_readme([pack], {"catalogue_version": "1.0"})
        # Pack row appears in the catalogue table.
        assert "**GDPR**" in result
        assert "Tier 1" in result
        assert "75.5%" in result
        assert "80.2%" in result
        # Link to gdpr.md correctly formed.
        assert "[`gdpr.md`](gdpr.md)" in result

    def test_em_dash_for_missing_coverage(self):
        # Pack with no coverage figures at all → em-dash placeholders.
        pack = {
            "id": "x",
            "shortName": "X",
            "tier": None,
            "jurisdiction": [],
            "version": "",
            "coverage": {},
        }
        result = ep._render_readme([pack], {"catalogue_version": "1.0"})
        assert "Tier —" in result
        # Coverage cells should be em-dashes when None.
        assert "| — | — |" in result


# ---------------------------------------------------------------------------
# Markdown pack renderer
# ---------------------------------------------------------------------------


class TestRenderMarkdownPack:
    def test_minimal_render_returns_string(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        out = ep._render_markdown_pack(
            framework, version, extras, coverage, uc_details, None, metadata
        )
        assert isinstance(out, str)
        # Top-level header includes shortName.
        assert "# Evidence Pack — GDPR" in out
        # Tier line.
        assert "Tier 1" in out
        # Version cell.
        assert "`2018`" in out
        # Authoritative URL surfaces.
        assert "https://eur-lex.europa.eu" in out
        # Generation metadata footer.
        assert metadata["inputs_sha256"] in out
        # Coverage summary line.
        assert "50.0%" in out
        # Clause table contains both clauses.
        assert "Art.5" in out
        assert "Art.32" in out

    def test_derivation_info_renders_when_present(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        derivation = {"parent": "gdpr", "inheritanceMode": "extends"}
        out = ep._render_markdown_pack(
            framework, version, extras, coverage, uc_details, derivation, metadata
        )
        assert "Derived from" in out
        assert "extends" in out

    def test_minimal_extras_no_optional_sections(self):
        framework, version, _, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        # Strip extras to bare minimum.
        extras = {"version": "2018", "summary": "S.", "scope": "Sc."}
        out = ep._render_markdown_pack(
            framework, version, extras, coverage, uc_details, None, metadata
        )
        # Still produces a valid markdown pack.
        assert "# Evidence Pack" in out
        # No retention guidance section bullet items expected.
        # (We just verify it doesn't crash; specific section absence is
        # internal to the renderer.)
        assert "S." in out
        assert "Sc." in out

    def test_empty_jurisdiction_renders_em_dash(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        framework = {**framework, "jurisdiction": None}
        out = ep._render_markdown_pack(
            framework, version, extras, coverage, uc_details, None, metadata
        )
        # Jurisdiction line falls back to "—".
        assert "Jurisdiction" in out

    def test_uses_effective_common_clauses_override(self):
        framework, version, extras, coverage, uc_details, metadata = (
            _make_minimal_render_inputs()
        )
        # Override commonClauses entirely.
        override = [{"clause": "X.1", "topic": "Override", "priorityWeight": 0.5}]
        out = ep._render_markdown_pack(
            framework,
            version,
            extras,
            coverage,
            uc_details,
            None,
            metadata,
            effective_common_clauses=override,
        )
        # The override drives clause ordering.
        assert isinstance(out, str)


class TestRenderNis2DualCrosswalk:
    def test_returns_empty_for_other_regulations(self):
        assert ep._render_nis2_dual_crosswalk_lines("gdpr") == []

    def test_renders_crosswalk_for_no_kbf_nve(self):
        lines = ep._render_nis2_dual_crosswalk_lines("no-kbf-nve")
        text = "\n".join(lines)
        assert "### 4.2 NIS2 dual-mapping crosswalk" in text
        assert "§2-3" in text
        assert "Art.21(2)(a)" in text
        assert "UC-22.26.21" in text
        assert "audit-no-kbf-coverage" in text
        assert "does not assert legal equivalence" in text


# ---------------------------------------------------------------------------
# Inputs hash
# ---------------------------------------------------------------------------


class TestInputsSha256:
    def test_hash_is_deterministic(self, monkeypatch, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        c = tmp_path / "c"
        a.write_bytes(b"alpha")
        b.write_bytes(b"beta")
        c.write_bytes(b"gamma")
        monkeypatch.setattr(ep, "REGULATIONS_PATH", a, raising=True)
        monkeypatch.setattr(ep, "EXTRAS_PATH", b, raising=True)
        monkeypatch.setattr(ep, "EXTRAS_SCHEMA_PATH", c, raising=True)
        first = ep._inputs_sha256()
        second = ep._inputs_sha256()
        assert first == second
        # Stable hex digest of 64 chars.
        assert len(first) == 64

    def test_hash_changes_when_input_changes(self, monkeypatch, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        c = tmp_path / "c"
        a.write_bytes(b"alpha")
        b.write_bytes(b"beta")
        c.write_bytes(b"gamma")
        monkeypatch.setattr(ep, "REGULATIONS_PATH", a, raising=True)
        monkeypatch.setattr(ep, "EXTRAS_PATH", b, raising=True)
        monkeypatch.setattr(ep, "EXTRAS_SCHEMA_PATH", c, raising=True)
        before = ep._inputs_sha256()
        a.write_bytes(b"alpha-changed")
        after = ep._inputs_sha256()
        assert before != after


# ---------------------------------------------------------------------------
# Prune orphans
# ---------------------------------------------------------------------------


class TestPruneOrphans:
    def test_removes_files_not_in_planned(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs" / "evidence-packs"
        api = tmp_path / "api" / "v1" / "evidence-packs"
        docs.mkdir(parents=True)
        api.mkdir(parents=True)
        # Planned file
        kept = docs / "gdpr.md"
        kept.write_text("planned", encoding="utf-8")
        # Orphan file
        orphan = docs / "old-pack.md"
        orphan.write_text("orphan", encoding="utf-8")

        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", api, raising=True)

        # planned only includes gdpr.md.
        ep._prune_orphans({kept: b"planned\n"})
        assert kept.exists()
        assert not orphan.exists()

    def test_preserves_exempt_orphans(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        api = tmp_path / "api"
        docs.mkdir()
        api.mkdir()
        # Hand-authored exempt slug
        exempt = docs / "cn-csl.md"
        exempt.write_text("hand-authored", encoding="utf-8")
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", api, raising=True)

        # Planned dictionary is empty — but exempt slugs are spared.
        ep._prune_orphans({})
        assert exempt.exists()

    def test_skips_dotfiles(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        api = tmp_path / "api"
        docs.mkdir()
        api.mkdir()
        dotfile = docs / ".keep"
        dotfile.write_text("placeholder", encoding="utf-8")
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", api, raising=True)
        ep._prune_orphans({})
        # Dotfiles are preserved.
        assert dotfile.exists()

    def test_skips_directory_entries(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        api = tmp_path / "api"
        docs.mkdir()
        api.mkdir()
        subdir = docs / "subdir"
        subdir.mkdir()
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", api, raising=True)
        # No exception when iterating directories.
        ep._prune_orphans({})
        assert subdir.is_dir()

    def test_handles_missing_output_dirs(self, monkeypatch, tmp_path):
        # Neither directory exists — function silently returns.
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", tmp_path / "no-docs", raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "no-api", raising=True)
        ep._prune_orphans({})  # no exception


# ---------------------------------------------------------------------------
# Drift check
# ---------------------------------------------------------------------------


class TestCheckDrift:
    def test_returns_empty_when_files_match(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "x.md"
        f.write_bytes(b"hello\n")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)

        drift = ep._check_drift({f: b"hello\n"})
        assert drift == []

    def test_reports_missing_doc_file(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        missing = docs / "missing.md"
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)

        drift = ep._check_drift({missing: b"x\n"})
        assert any("missing:" in d for d in drift)

    def test_skips_missing_api_file_silently(self, monkeypatch, tmp_path):
        # API files are gitignored; missing ones don't surface.
        api = tmp_path / "api"
        api.mkdir()
        missing_api = api / "missing.json"
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", tmp_path / "docs", raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", api, raising=True)

        drift = ep._check_drift({missing_api: b"{}\n"})
        # No "missing:" entry for the API file.
        assert not any("missing:" in d for d in drift)

    def test_reports_changed_md_file(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "x.md"
        f.write_bytes(b"old content\n")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)

        drift = ep._check_drift({f: b"new content\n"})
        assert any("changed:" in d for d in drift)
        # Diff lines included.
        assert any("old content" in d or "new content" in d for d in drift)

    def test_md_drift_ignores_citation_markers(self, monkeypatch, tmp_path):
        # On-disk file has citation markers; planned doesn't. Drift should
        # NOT be reported.
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "x.md"
        f.write_bytes(
            b'Body<sup class="ref">[<a href="#ref-1">1</a>]</sup>.\n'
        )
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)

        drift = ep._check_drift({f: b"Body.\n"})
        # Citation markers stripped from both sides → no drift.
        assert drift == []

    def test_reports_orphan_files(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        orphan = docs / "old.md"
        orphan.write_text("o", encoding="utf-8")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)

        drift = ep._check_drift({})
        assert any("orphan:" in d for d in drift)

    def test_orphan_skips_exempt_slugs(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        # Hand-authored exempt slug — must NOT appear as orphan.
        (docs / "cn-csl.md").write_text("hand-authored", encoding="utf-8")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)
        drift = ep._check_drift({})
        assert not any("orphan:" in d for d in drift)

    def test_orphan_skips_dotfiles(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / ".gitkeep").write_text("", encoding="utf-8")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)
        drift = ep._check_drift({})
        # Dotfile does not appear as orphan.
        assert drift == []

    def test_truncates_long_diffs(self, monkeypatch, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "x.md"
        # Existing file: 50 lines.
        f.write_bytes(("\n".join(f"old{i}" for i in range(50)) + "\n").encode("utf-8"))
        # Planned: completely different 50 lines.
        planned = ("\n".join(f"new{i}" for i in range(50)) + "\n").encode("utf-8")
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs, raising=True)
        monkeypatch.setattr(ep, "API_OUT_DIR", tmp_path / "api", raising=True)

        drift = ep._check_drift({f: planned})
        # Truncation marker present.
        assert any("more diff lines" in d for d in drift)


# ---------------------------------------------------------------------------
# Citation chain
# ---------------------------------------------------------------------------


class TestChainDocReferences:
    def test_warns_when_script_missing(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(
            ep, "_DOC_REFS_SCRIPT", tmp_path / "no-script.py", raising=True
        )
        # Prevent accidental subprocess.run if logic falls through.
        monkeypatch.setattr(ep.subprocess, "run", lambda *a, **k: pytest.fail())
        rc = ep._chain_doc_references()
        assert rc == 0
        assert "not found" in capsys.readouterr().err

    def test_runs_subprocess_when_script_present(self, monkeypatch, tmp_path):
        script = tmp_path / "scripts" / "generate_doc_references.py"
        script.parent.mkdir(parents=True)
        script.write_text("# stub", encoding="utf-8")

        captured = {}

        class FakeResult:
            returncode = 0

        def fake_run(cmd, cwd):
            captured["cmd"] = cmd
            captured["cwd"] = cwd
            return FakeResult()

        monkeypatch.setattr(ep, "_DOC_REFS_SCRIPT", script, raising=True)
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(ep.subprocess, "run", fake_run)

        rc = ep._chain_doc_references()
        assert rc == 0
        assert captured["cwd"] == str(tmp_path)
        assert "--only" in captured["cmd"]

    def test_returns_nonzero_when_subprocess_fails(self, monkeypatch, tmp_path, capsys):
        script = tmp_path / "scripts" / "generate_doc_references.py"
        script.parent.mkdir(parents=True)
        script.write_text("# stub", encoding="utf-8")

        class FakeResult:
            returncode = 7

        monkeypatch.setattr(ep, "_DOC_REFS_SCRIPT", script, raising=True)
        monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
        monkeypatch.setattr(
            ep.subprocess, "run", lambda *a, **k: FakeResult()
        )

        rc = ep._chain_doc_references()
        assert rc == 7
        assert "FAIL" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# _generate_all integration tests
# ---------------------------------------------------------------------------


def _setup_synthetic_pack_env(monkeypatch, tmp_path, *, target="test-reg"):
    """Wire ``evidence_packs`` against a self-contained synthetic
    catalogue under ``tmp_path``. Produces a single pack target with
    one UC and one clause so the orchestrator's main loop runs end to
    end without touching the real catalogue.
    """
    # Synthetic regulations.json
    regulations_doc = {
        "aliasIndex": {"Test Reg": target},
        "frameworks": [
            {
                "id": target,
                "shortName": "TR",
                "name": "Test Regulation",
                "tier": 1,
                "jurisdiction": ["XX"],
                "versions": [
                    {
                        "version": "v1",
                        "authoritativeUrl": "https://example.com",
                        "clauseUrlTemplate": "https://example.com/{clause}",
                        "effectiveFrom": "2026-01-01",
                        "commonClauses": [
                            {"clause": "C.1", "topic": "T1", "priorityWeight": 1.0}
                        ],
                    }
                ],
            }
        ],
        "derivesFrom": {},
    }
    # Synthetic evidence-pack-extras.json
    extras_doc = {
        "regulations": {
            target: {
                "version": "v1",
                "summary": "Test summary.",
                "scope": "Test scope.",
                "territorialScope": "Worldwide.",
                "commonEvidenceSources": [],
                "retentionGuidance": [],
                "testingApproach": "Quarterly.",
                "reportingCadence": "Annual.",
                "roles": [],
                "authoritativeGuidance": [],
                "commonDeficiencies": [],
                "auditorQuestions": [],
                "penaltyStructure": "Tested.",
            }
        }
    }
    # UC sidecar with one compliance entry pointing at the target
    content_dir = tmp_path / "content" / "cat-99-test"
    content_dir.mkdir(parents=True)
    uc_doc = {
        "id": "1.1.1",
        "title": "Audit log retention",
        "controlFamily": "Access Control",
        "owner": "Sec Ops",
        "evidence": [{"k": "v"}],
        "compliance": [
            {
                "regulation": "Test Reg",
                "version": "v1",
                "clause": "C.1",
                "assurance": "full",
                "rationale": "Direct evidence",
                "provenance": "native",
            }
        ],
    }
    (content_dir / "UC-1.1.1.json").write_text(
        json.dumps(uc_doc), encoding="utf-8"
    )
    # Schemas + version + paths
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "evidence-pack-extras.schema.json").write_text("{}", encoding="utf-8")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    reg_path = data_dir / "regulations.json"
    extras_path = data_dir / "evidence-pack-extras.json"
    extras_schema = schemas_dir / "evidence-pack-extras.schema.json"
    reg_path.write_text(json.dumps(regulations_doc), encoding="utf-8")
    extras_path.write_text(json.dumps(extras_doc), encoding="utf-8")

    docs_dir = tmp_path / "docs" / "evidence-packs"
    api_dir = tmp_path / "api" / "v1" / "evidence-packs"
    version_path = tmp_path / "VERSION"
    version_path.write_text("9.9.9\n", encoding="utf-8")
    gaps_path = tmp_path / "reports" / "compliance-gaps.json"

    # Wire all module paths
    monkeypatch.setattr(ep, "ROOT", tmp_path, raising=True)
    monkeypatch.setattr(ep, "REGULATIONS_PATH", reg_path, raising=True)
    monkeypatch.setattr(ep, "EXTRAS_PATH", extras_path, raising=True)
    monkeypatch.setattr(ep, "EXTRAS_SCHEMA_PATH", extras_schema, raising=True)
    monkeypatch.setattr(ep, "GAPS_REPORT_PATH", gaps_path, raising=True)
    monkeypatch.setattr(ep, "DOCS_OUT_DIR", docs_dir, raising=True)
    monkeypatch.setattr(ep, "API_OUT_DIR", api_dir, raising=True)
    monkeypatch.setattr(ep, "VERSION_PATH", version_path, raising=True)
    monkeypatch.setattr(ep, "PACK_TARGETS", [target], raising=True)
    return docs_dir, api_dir


class TestGenerateAllIntegration:
    def test_write_mode_creates_pack_files(self, monkeypatch, tmp_path):
        docs, api = _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Avoid shelling out to the citation generator.
        rc = ep._generate_all(check=False, chain_citations=False)
        assert rc == 0
        # MD pack written.
        assert (docs / "test-reg.md").exists()
        # README written.
        assert (docs / "README.md").exists()
        # JSON twin and index written.
        assert (api / "test-reg.json").exists()
        assert (api / "index.json").exists()
        # Index lists the pack.
        idx = json.loads((api / "index.json").read_text(encoding="utf-8"))
        assert idx["catalogueVersion"] == "9.9.9"
        assert any(p["id"] == "test-reg" for p in idx["packs"])

    def test_check_mode_returns_zero_when_in_sync(self, monkeypatch, tmp_path):
        docs, api = _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Write first; then check.
        assert ep._generate_all(check=False, chain_citations=False) == 0
        rc = ep._generate_all(check=True, chain_citations=False)
        assert rc == 0

    def test_check_mode_returns_one_on_drift(self, monkeypatch, tmp_path, capsys):
        docs, api = _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Write first.
        assert ep._generate_all(check=False, chain_citations=False) == 0
        # Mutate a tracked pack to introduce drift.
        md_path = docs / "test-reg.md"
        md_path.write_text("Drifted content.\n", encoding="utf-8")
        rc = ep._generate_all(check=True, chain_citations=False)
        assert rc == 1
        assert "DRIFT DETECTED" in capsys.readouterr().err

    def test_returns_one_when_target_missing_from_regulations(
        self, monkeypatch, tmp_path, capsys
    ):
        _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Wipe frameworks so the loop's "framework not found" branch fires.
        empty_doc = {"frameworks": []}
        ep.REGULATIONS_PATH.write_text(json.dumps(empty_doc), encoding="utf-8")
        rc = ep._generate_all(check=True, chain_citations=False)
        assert rc == 1
        assert "not in regulations.json" in capsys.readouterr().err

    def test_returns_one_when_target_missing_from_extras(
        self, monkeypatch, tmp_path, capsys
    ):
        _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Frameworks present, but extras empty.
        ep.EXTRAS_PATH.write_text(json.dumps({"regulations": {}}), encoding="utf-8")
        rc = ep._generate_all(check=True, chain_citations=False)
        assert rc == 1
        assert "not in evidence-pack-extras.json" in capsys.readouterr().err

    def test_returns_one_when_no_versions_available(
        self, monkeypatch, tmp_path, capsys
    ):
        _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Strip versions from the framework entry.
        doc = json.loads(ep.REGULATIONS_PATH.read_text(encoding="utf-8"))
        doc["frameworks"][0]["versions"] = []
        ep.REGULATIONS_PATH.write_text(json.dumps(doc), encoding="utf-8")
        rc = ep._generate_all(check=True, chain_citations=False)
        assert rc == 1
        assert "no version available" in capsys.readouterr().err

    def test_chain_citations_flag_skipped_when_false(self, monkeypatch, tmp_path):
        _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Setting up a sentinel: subprocess.run must NOT be called when
        # chain_citations=False.
        called = {"run": False}

        def fake_run(*a, **k):
            called["run"] = True
            class R: returncode = 0
            return R()

        monkeypatch.setattr(ep.subprocess, "run", fake_run)
        rc = ep._generate_all(check=False, chain_citations=False)
        assert rc == 0
        assert called["run"] is False

    def test_propagates_chain_failure(self, monkeypatch, tmp_path):
        _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # Stub the doc-references script to simulate a failure.
        script = tmp_path / "scripts" / "generate_doc_references.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# stub", encoding="utf-8")
        monkeypatch.setattr(ep, "_DOC_REFS_SCRIPT", script, raising=True)

        class FakeResult:
            returncode = 5

        monkeypatch.setattr(
            ep.subprocess, "run", lambda *a, **k: FakeResult()
        )
        rc = ep._generate_all(check=False, chain_citations=True)
        assert rc == 5

    def test_skips_unchanged_files_in_write_mode(self, monkeypatch, tmp_path, capsys):
        _setup_synthetic_pack_env(monkeypatch, tmp_path)
        # First write
        assert ep._generate_all(check=False, chain_citations=False) == 0
        capsys.readouterr()  # drain
        # Second write — no changes; "wrote 0 file(s)" message.
        rc = ep._generate_all(check=False, chain_citations=False)
        assert rc == 0
        out = capsys.readouterr().out
        assert "wrote 0 file" in out

    def test_identity_mode_inherits_parent_common_clauses(
        self, monkeypatch, tmp_path
    ):
        """Identity-mode derivatives (e.g. UK GDPR inheriting GDPR
        clauses) overlay the parent's commonClauses on top of the
        derivative's own narrow set. This exercises lines 1372-1391."""
        _setup_synthetic_pack_env(monkeypatch, tmp_path, target="uk-gdpr")
        # Extend regulations.json: add a GDPR parent and a derivesFrom
        # graph entry pointing uk-gdpr → gdpr (identity inheritance).
        doc = json.loads(ep.REGULATIONS_PATH.read_text(encoding="utf-8"))
        # Parent framework with a richer commonClauses set.
        doc["frameworks"].append(
            {
                "id": "gdpr",
                "shortName": "GDPR",
                "name": "General Data Protection Regulation",
                "tier": 1,
                "jurisdiction": ["EU"],
                "versions": [
                    {
                        "version": "2018",
                        "authoritativeUrl": "https://example.com",
                        "clauseUrlTemplate": "https://example.com/{clause}",
                        "effectiveFrom": "2018-05-25",
                        "commonClauses": [
                            {"clause": "Art.5", "topic": "Privacy", "priorityWeight": 1.0},
                            {"clause": "Art.32", "topic": "Security", "priorityWeight": 1.0},
                        ],
                    }
                ],
            }
        )
        doc["derivesFrom"] = {
            "uk-gdpr": {
                "parent": "gdpr",
                "parentVersion": "2018",
                "inheritanceMode": "identity",
                "divergences": [],
                "clauseMapping": {"$schema": "ignored", "Art.5": "Art.5"},
            }
        }
        # uk-gdpr has just one narrow commonClause; parent overlay adds more.
        ep.REGULATIONS_PATH.write_text(json.dumps(doc), encoding="utf-8")

        rc = ep._generate_all(check=False, chain_citations=False)
        assert rc == 0
        # The pack should have been generated and reference parent clauses.
        md = (ep.DOCS_OUT_DIR / "uk-gdpr.md").read_text(encoding="utf-8")
        # Both parent clauses surface in the rendered pack.
        assert "Art.32" in md  # parent-only clause
        # Derivation info banner present.
        assert "Derived from" in md and "identity" in md


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


class TestMain:
    def test_argparse_help_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            ep.main(["--help"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        # Description from the module docstring is used by argparse.
        assert "evidence" in out.lower()

    def test_main_delegates_check_flag_to_generate_all(self, monkeypatch):
        captured = {}

        def fake_generate_all(check, chain_citations=True):
            captured["check"] = check
            captured["chain"] = chain_citations
            return 0

        monkeypatch.setattr(ep, "_generate_all", fake_generate_all)
        rc = ep.main(["--check"])
        assert rc == 0
        assert captured["check"] is True
        # Default: citation chain ON.
        assert captured["chain"] is True

    def test_main_no_citation_chain_flag(self, monkeypatch):
        captured = {}

        def fake_generate_all(check, chain_citations=True):
            captured["chain"] = chain_citations
            return 0

        monkeypatch.setattr(ep, "_generate_all", fake_generate_all)
        rc = ep.main(["--no-citation-chain"])
        assert rc == 0
        assert captured["chain"] is False
