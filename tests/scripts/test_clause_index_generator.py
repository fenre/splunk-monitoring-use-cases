"""Coverage-uplift suite for ``splunk_uc.generators.clause_index``.

The module had 0% test coverage prior to this file. The strategy is:

* Pure helpers (``clause_id``, ``clause_filename``, ``_slugify_regulation``,
  ``fill_clause_url``, ``_compare_assurance``, ``_assurance_breakdown``,
  ``_top_assurance``, ``_mode_breakdown``, ``_coverage_state``,
  ``build_clause_buckets``, ``build_regulation_lookup``,
  ``build_clause_detail``, ``build_index``) — exercise directly with
  hand-crafted fixtures.
* IO helpers (``_read_version``, ``_deterministic_timestamp``,
  ``_write_json``, ``_load_json``, ``_hash_tree``) — exercise with
  ``tmp_path`` and ``monkeypatch`` on environment / module constants.
* Orchestration (``generate``, ``_check_drift``, ``main``) — drive a
  small fixture catalogue through ``tmp_path``-rooted constants and
  inject UC / regulation payloads via the public ``generate`` signature.

All tests are hermetic: no real CWD, no real network, no real git.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

SRC_DIR = pathlib.Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.generators import clause_index as ci  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _uc(uc_id: str, compliance: list[dict[str, Any]] | Any) -> dict[str, Any]:
    return {
        "id": uc_id,
        "title": f"Use case {uc_id}",
        "criticality": "high",
        "compliance": compliance,
    }


def _regulations() -> dict[str, Any]:
    return {
        "frameworks": [
            {
                "id": "gdpr",
                "name": "GDPR",
                "shortName": "GDPR",
                "tier": 1,
                "versions": [
                    {
                        "version": "2016/679",
                        "authoritativeUrl": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
                        "clauseUrlTemplate": "https://gdpr-info.eu/{clause}/",
                        "commonClauses": [
                            {
                                "clause": "Art.32",
                                "topic": "Security of processing",
                                "priorityWeight": 0.9,
                                "obligationText": "Implement appropriate measures.",
                                "obligationSource": (
                                    "https://gdpr-info.eu/art-32-gdpr/"
                                ),
                            },
                            {
                                "clause": "Art.30",
                                "topic": "Records of processing",
                                "priorityWeight": 0.7,
                            },
                        ],
                    },
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Deterministic IO helpers
# ---------------------------------------------------------------------------


def test_deterministic_timestamp_uses_source_date_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    out = ci._deterministic_timestamp()
    expected = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(1700000000))
    assert out == expected


def test_deterministic_timestamp_ignores_non_digit_source_date_epoch_and_uses_git(
    monkeypatch,
):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-int")

    class _Result:
        stdout = "1234567890\n"

    def fake_run(*_a, **_k):
        return _Result()

    monkeypatch.setattr(ci.subprocess, "run", fake_run)
    out = ci._deterministic_timestamp()
    expected = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(1234567890))
    assert out == expected


def test_deterministic_timestamp_falls_back_to_walltime_when_git_missing(monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

    def fake_run(*_a, **_k):
        raise FileNotFoundError("no git")

    monkeypatch.setattr(ci.subprocess, "run", fake_run)
    out = ci._deterministic_timestamp()
    # Should match the wall-clock format (we can't assert the exact value).
    assert out.endswith("Z") and "T" in out


def test_deterministic_timestamp_handles_git_returning_non_digit(monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

    class _Result:
        stdout = "garbage\n"

    monkeypatch.setattr(ci.subprocess, "run", lambda *_a, **_k: _Result())
    out = ci._deterministic_timestamp()
    assert out.endswith("Z")


def test_deterministic_timestamp_handles_git_timeout(monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

    def fake_run(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd="git", timeout=3)

    monkeypatch.setattr(ci.subprocess, "run", fake_run)
    out = ci._deterministic_timestamp()
    assert out.endswith("Z")


def test_deterministic_timestamp_handles_git_called_process_error(monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

    def fake_run(*_a, **_k):
        raise subprocess.CalledProcessError(returncode=1, cmd="git")

    monkeypatch.setattr(ci.subprocess, "run", fake_run)
    out = ci._deterministic_timestamp()
    assert out.endswith("Z")


def test_read_version_returns_file_contents(monkeypatch, tmp_path: Path):
    vf = tmp_path / "VERSION"
    vf.write_text("9.4.2\n", encoding="utf-8")
    monkeypatch.setattr(ci, "VERSION_FILE", vf)
    assert ci._read_version() == "9.4.2"


def test_read_version_defaults_when_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(ci, "VERSION_FILE", tmp_path / "no-such-file")
    assert ci._read_version() == "0.0.0"


def test_write_and_load_json_roundtrip(tmp_path: Path):
    target = tmp_path / "nested" / "x.json"
    ci._write_json(target, {"b": 2, "a": 1})
    assert target.exists()
    raw = target.read_text(encoding="utf-8")
    # Deterministic ordering ⇒ "a" precedes "b".
    assert raw.index("\"a\"") < raw.index("\"b\"")
    assert ci._load_json(target) == {"a": 1, "b": 2}


# ---------------------------------------------------------------------------
# Clause-ID normalisation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reg,version,clause,expected",
    [
        ("gdpr", "2016/679", "Art.32", "gdpr@2016/679#Art.32"),
        (
            "hipaa-security",
            "2013-final",
            "§164.312(b)",
            "hipaa-security@2013-final#§164.312(b)",
        ),
    ],
)
def test_clause_id(reg, version, clause, expected):
    assert ci.clause_id(reg, version, clause) == expected


def test_clause_filename_and_reverse_round_trip_for_simple_id():
    canonical = ci.clause_id("gdpr", "2016/679", "Art.32")
    fname = ci.clause_filename(canonical)
    assert fname.endswith(".json")
    assert "/" not in fname
    assert "@" not in fname
    assert ci.reverse_clause_filename(fname) == canonical


def test_clause_filename_handles_special_chars():
    canonical = ci.clause_id("hipaa-security", "2013-final", "§164.312(b)")
    fname = ci.clause_filename(canonical)
    assert fname.endswith(".json")
    # URL-encoded section sign, parenthesis preserved (in safe set).
    assert "%C2%A7" in fname
    # Round-trip restores the original.
    assert ci.reverse_clause_filename(fname) == canonical


def test_reverse_clause_filename_rejects_unexpected_shape():
    with pytest.raises(ValueError, match="unexpected clause filename shape"):
        ci.reverse_clause_filename("not__a__valid__name.json")


def test_reverse_clause_filename_restores_slash_in_version_only_once():
    # Mimic a version that originally had a slash but got URL-encoded out.
    encoded = ci.clause_filename(ci.clause_id("gdpr", "2016/679", "Art.32"))
    canonical = ci.reverse_clause_filename(encoded)
    assert canonical == "gdpr@2016/679#Art.32"


def test_reverse_clause_filename_restores_underscore_to_slash_when_needed():
    # Hand-crafted filename whose version slot already had its '/' replaced
    # by '_' (the defensive _RESTORE_SLASH path). This is not produced by
    # ``clause_filename`` today — ``urllib.parse.quote`` keeps '/' as
    # '%2F' — but the regex is kept for filenames authored upstream that
    # took the literal-underscore route.
    assert (
        ci.reverse_clause_filename("gdpr__2016_679__Art.32.json")
        == "gdpr@2016/679#Art.32"
    )


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (None, "partial", "partial"),
        ("full", None, "full"),
        ("partial", "full", "full"),
        ("contributing", "partial", "partial"),
        ("full", "full", "full"),
        (None, None, ""),
        ("contributing", "", "contributing"),
    ],
)
def test_compare_assurance(a, b, expected):
    assert ci._compare_assurance(a, b) == expected


def test_uc_sort_key_with_valid_id():
    assert ci._uc_sort_key({"id": "1.2.3"}) == (1, 2, 3)


def test_uc_sort_key_with_invalid_id():
    assert ci._uc_sort_key({"id": "not-an-id"}) == (10**6, 10**6, 10**6)
    assert ci._uc_sort_key({}) == (10**6, 10**6, 10**6)


def test_slugify_regulation_normalises_separators():
    assert ci._slugify_regulation("PCI-DSS") == "pci-dss"
    assert ci._slugify_regulation(" NIST 800-53 ") == "nist-800-53"
    assert ci._slugify_regulation("GDPR") == "gdpr"
    assert ci._slugify_regulation("--Edge--") == "edge"


def test_assurance_breakdown_counts_known_and_unknown():
    entries = [
        {"assurance": "full"},
        {"assurance": "partial"},
        {"assurance": "contributing"},
        {"assurance": "partial"},
        {"assurance": "non-standard"},
        {},
    ]
    out = ci._assurance_breakdown(entries)
    assert out == {"full": 1, "partial": 2, "contributing": 1, "unknown": 2}


def test_top_assurance_picks_highest_rank():
    entries = [
        {"assurance": "contributing"},
        {"assurance": "partial"},
        {"assurance": "full"},
    ]
    assert ci._top_assurance(entries) == "full"


def test_top_assurance_returns_none_when_all_missing():
    assert ci._top_assurance([{}, {"assurance": ""}]) is None


def test_mode_breakdown_aggregates_modes():
    entries = [
        {"mode": "satisfies"},
        {"mode": "detects-violation-of"},
        {"mode": "satisfies"},
        {},
    ]
    out = ci._mode_breakdown(entries)
    assert out["satisfies"] == 2
    assert out["detects-violation-of"] == 1
    assert out["unspecified"] == 1


def test_coverage_state_uncovered_when_empty():
    assert ci._coverage_state([]) == "uncovered"


def test_coverage_state_covered_full_when_full_satisfies_present():
    entries = [{"assurance": "full", "mode": "satisfies"}]
    assert ci._coverage_state(entries) == "covered-full"


def test_coverage_state_covered_partial_when_only_partial_satisfies():
    entries = [
        {"assurance": "partial", "mode": "satisfies"},
        {"assurance": "contributing", "mode": "satisfies"},
    ]
    assert ci._coverage_state(entries) == "covered-partial"


def test_coverage_state_contributing_only_when_no_satisfies_full_or_partial():
    entries = [
        {"assurance": "contributing", "mode": "satisfies"},
        {"assurance": "full", "mode": "detects-violation-of"},
    ]
    assert ci._coverage_state(entries) == "contributing-only"


# ---------------------------------------------------------------------------
# Bucket / lookup builders
# ---------------------------------------------------------------------------


def test_build_clause_buckets_skips_non_list_and_non_mapping_entries():
    ucs = [
        _uc("1.1.1", "not-a-list"),
        _uc(
            "1.1.2",
            [
                "string-entry",  # skipped (not a Mapping)
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32"},
            ],
        ),
        _uc(
            "1.1.3",
            [
                {"regulation": "", "version": "v", "clause": "c"},  # blank reg
                {"regulation": "GDPR", "version": "", "clause": "c"},  # blank ver
                {"regulation": "GDPR", "version": "v", "clause": ""},  # blank cla
                {"regulation": 1, "version": "v", "clause": "c"},  # wrong type
            ],
        ),
    ]
    buckets = ci.build_clause_buckets(ucs)
    key = ("gdpr", "2016/679", "Art.32")
    assert key in buckets
    assert len(buckets[key]) == 1
    assert buckets[key][0]["ucId"] == "1.1.2"


def test_build_clause_buckets_propagates_enrichment_fields():
    ucs = [
        _uc(
            "5.4.3",
            [
                {
                    "regulation": "PCI-DSS",
                    "version": "4.0",
                    "clause": "10.2.1",
                    "mode": "satisfies",
                    "assurance": "full",
                    "assurance_rationale": "Audited weekly",
                    "controlObjective": "log retention",
                    "evidenceArtifact": "audit_log",
                    "provenance": "internal",
                    "clauseUrl": "https://example.com",
                    "legalCaveat": "see SLA",
                    "smeCaveat": "tune thresholds",
                }
            ],
        )
    ]
    buckets = ci.build_clause_buckets(ucs)
    bucket = buckets[("pci-dss", "4.0", "10.2.1")]
    assert bucket[0]["assuranceRationale"] == "Audited weekly"
    assert bucket[0]["regulationLabel"] == "PCI-DSS"
    assert bucket[0]["category"] == 5


def test_build_regulation_lookup_skips_invalid_frameworks_versions_clauses():
    regs = {
        "frameworks": [
            {"id": 123},  # invalid id type
            {
                "id": "gdpr",
                "versions": [
                    {"version": None, "commonClauses": []},  # invalid version
                    {
                        "version": "2016/679",
                        "commonClauses": [
                            {"clause": 5},  # invalid clause type
                            {
                                "clause": "Art.32",
                                "topic": "Security of processing",
                                "priorityWeight": 0.9,
                            },
                        ],
                    },
                ],
            },
        ],
    }
    lookup = ci.build_regulation_lookup(regs)
    assert ("gdpr", "2016/679", "Art.32") in lookup
    entry = lookup[("gdpr", "2016/679", "Art.32")]
    assert entry["topic"] == "Security of processing"
    assert entry["regulationId"] == "gdpr"
    # Only the valid clause survived.
    assert len(lookup) == 1


def test_build_regulation_lookup_handles_framework_without_versions_and_names():
    regs = {
        "frameworks": [
            {"id": "tiny", "versions": []},  # no clauses ⇒ no lookup rows
        ]
    }
    assert ci.build_regulation_lookup(regs) == {}


def test_build_regulation_lookup_falls_back_to_shortname_or_id_for_name():
    regs = {
        "frameworks": [
            {
                "id": "abc",
                "shortName": "ABC",
                "versions": [
                    {
                        "version": "1.0",
                        "commonClauses": [
                            {"clause": "1", "topic": "alpha"},
                        ],
                    }
                ],
            },
            {
                "id": "xyz",
                "versions": [
                    {
                        "version": "1.0",
                        "commonClauses": [
                            {"clause": "1", "topic": "omega"},
                        ],
                    }
                ],
            },
        ]
    }
    lookup = ci.build_regulation_lookup(regs)
    abc = lookup[("abc", "1.0", "1")]
    xyz = lookup[("xyz", "1.0", "1")]
    assert abc["regulationName"] == "ABC"
    assert abc["regulationShortName"] == "ABC"
    assert xyz["regulationName"] == "xyz"
    assert xyz["regulationShortName"] == "xyz"


# ---------------------------------------------------------------------------
# fill_clause_url
# ---------------------------------------------------------------------------


def test_fill_clause_url_prefers_explicit_uc_value():
    assert (
        ci.fill_clause_url(
            "https://uc-pref.example/x",
            {"obligationSource": "https://ignored"},
        )
        == "https://uc-pref.example/x"
    )


def test_fill_clause_url_returns_none_when_no_uc_value_and_no_lookup():
    assert ci.fill_clause_url(None, None) is None


def test_fill_clause_url_uses_obligation_source_when_available():
    assert (
        ci.fill_clause_url(None, {"obligationSource": "https://obs.example/x"})
        == "https://obs.example/x"
    )


def test_fill_clause_url_uses_template_when_obligation_source_missing():
    out = ci.fill_clause_url(
        None,
        {
            "clauseUrlTemplate": "https://gdpr-info.eu/{clause}/",
            "clause": "Art.32",
        },
    )
    assert out == "https://gdpr-info.eu/Art.32/"


def test_fill_clause_url_falls_back_to_authoritative_url():
    out = ci.fill_clause_url(
        None,
        {
            "authoritativeUrl": "https://eur-lex.example/oj",
        },
    )
    assert out == "https://eur-lex.example/oj"


def test_fill_clause_url_returns_none_when_lookup_has_only_invalid_fields():
    out = ci.fill_clause_url(None, {"authoritativeUrl": 42, "clause": 5})
    assert out is None


# ---------------------------------------------------------------------------
# build_clause_detail
# ---------------------------------------------------------------------------


def test_build_clause_detail_with_reg_entry_and_full_assurance():
    bucket = [
        {
            "ucId": "1.1.1",
            "ucTitle": "Test UC",
            "category": 1,
            "mode": "satisfies",
            "assurance": "full",
            "assuranceRationale": "fully tested",
            "controlObjective": "objective",
            "evidenceArtifact": "evidence",
            "provenance": "internal",
            "clauseUrl": None,
            "criticality": "high",
            "legalCaveat": None,
            "smeCaveat": None,
        }
    ]
    reg_entry = {
        "regulationId": "gdpr",
        "regulationName": "GDPR",
        "regulationShortName": "GDPR",
        "tier": 1,
        "version": "2016/679",
        "clause": "Art.32",
        "topic": "Security of processing",
        "priorityWeight": 0.9,
        "obligationText": "Implement appropriate measures.",
        "obligationSource": "https://gdpr-info.eu/art-32-gdpr/",
        "authoritativeUrl": "https://eur-lex.example/oj",
        "clauseUrlTemplate": "https://gdpr-info.eu/{clause}/",
    }
    detail = ci.build_clause_detail(
        reg_slug="gdpr",
        version="2016/679",
        clause="Art.32",
        bucket_entries=bucket,
        reg_entry=reg_entry,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    assert detail["coverageState"] == "covered-full"
    assert detail["coveringUcCount"] == 1
    assert detail["gapNote"] is None
    # clauseUrl fills from obligationSource.
    assert (
        detail["coveringUcs"][0]["clauseUrl"]
        == "https://gdpr-info.eu/art-32-gdpr/"
    )


def test_build_clause_detail_without_reg_entry_uses_slug_as_fallback():
    bucket = [
        {
            "ucId": "5.4.3",
            "ucTitle": "",
            "category": 5,
            "mode": "satisfies",
            "assurance": "partial",
            "assuranceRationale": None,
            "controlObjective": None,
            "evidenceArtifact": None,
            "provenance": None,
            "clauseUrl": None,
            "criticality": None,
            "legalCaveat": None,
            "smeCaveat": None,
        }
    ]
    detail = ci.build_clause_detail(
        reg_slug="orphan-reg",
        version="1.0",
        clause="X.1",
        bucket_entries=bucket,
        reg_entry=None,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    assert detail["regulationId"] == "orphan-reg"
    # When reg_entry is None and coverage is non-empty + partial → no gapNote.
    assert detail["gapNote"] is None
    assert detail["coverageState"] == "covered-partial"


def test_build_clause_detail_emits_uncovered_gap_note_when_reg_entry_known():
    reg_entry = {
        "regulationId": "gdpr",
        "regulationShortName": "GDPR",
        "regulationName": "GDPR",
        "tier": 1,
        "version": "2016/679",
        "clause": "Art.30",
        "topic": "Records of processing",
        "priorityWeight": 0.7,
    }
    detail = ci.build_clause_detail(
        reg_slug="gdpr",
        version="2016/679",
        clause="Art.30",
        bucket_entries=[],
        reg_entry=reg_entry,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    assert detail["coverageState"] == "uncovered"
    assert detail["gapNote"] is not None
    assert "Records of processing" in detail["gapNote"]


def test_build_clause_detail_uncovered_without_reg_entry_omits_gap_note():
    detail = ci.build_clause_detail(
        reg_slug="ghost-reg",
        version="0.1",
        clause="C.1",
        bucket_entries=[],
        reg_entry=None,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    # `reg_entry is None` path → leaves gapNote untouched (None).
    assert detail["coverageState"] == "uncovered"
    assert detail["gapNote"] is None


def test_build_clause_detail_contributing_only_emits_gap_note():
    bucket = [
        {
            "ucId": "1.1.1",
            "ucTitle": "Contrib UC",
            "category": 1,
            "mode": "satisfies",
            "assurance": "contributing",
            "assuranceRationale": None,
            "controlObjective": None,
            "evidenceArtifact": None,
            "provenance": None,
            "clauseUrl": None,
            "criticality": "low",
            "legalCaveat": None,
            "smeCaveat": None,
        }
    ]
    reg_entry = {
        "regulationId": "pci-dss",
        "regulationShortName": "PCI",
        "regulationName": "PCI DSS",
        "tier": 1,
        "version": "4.0",
        "clause": "10.2.1",
        "topic": "Audit logging",
    }
    detail = ci.build_clause_detail(
        reg_slug="pci-dss",
        version="4.0",
        clause="10.2.1",
        bucket_entries=bucket,
        reg_entry=reg_entry,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    assert detail["coverageState"] == "contributing-only"
    assert detail["gapNote"]
    assert "contributing" in detail["gapNote"]


def test_build_clause_detail_handles_non_string_regulation_id_in_reg_entry():
    bucket: list[dict[str, Any]] = []
    reg_entry = {
        "regulationId": 123,  # forces the fallback to reg_slug
        "regulationName": "X",
        "regulationShortName": "X",
        "tier": 2,
        "version": "1.0",
        "clause": "1.0",
    }
    detail = ci.build_clause_detail(
        reg_slug="fallback-reg",
        version="1.0",
        clause="1.0",
        bucket_entries=bucket,
        reg_entry=reg_entry,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    assert detail["regulationId"] == "fallback-reg"


def test_build_clause_detail_orders_covering_ucs_by_assurance_then_id():
    bucket = [
        {
            "ucId": "1.1.10",
            "ucTitle": "Lower id contribution",
            "category": 1,
            "mode": "satisfies",
            "assurance": "contributing",
            "assuranceRationale": None,
            "controlObjective": None,
            "evidenceArtifact": None,
            "provenance": None,
            "clauseUrl": None,
            "criticality": "low",
            "legalCaveat": None,
            "smeCaveat": None,
        },
        {
            "ucId": "1.1.2",
            "ucTitle": "Higher id full",
            "category": 1,
            "mode": "satisfies",
            "assurance": "full",
            "assuranceRationale": None,
            "controlObjective": None,
            "evidenceArtifact": None,
            "provenance": None,
            "clauseUrl": None,
            "criticality": "high",
            "legalCaveat": None,
            "smeCaveat": None,
        },
    ]
    reg_entry = {
        "regulationId": "demo",
        "regulationShortName": "Demo",
        "regulationName": "Demo Framework",
        "tier": 1,
        "version": "1",
        "clause": "1",
        "topic": "Topic",
        "priorityWeight": 0.5,
    }
    detail = ci.build_clause_detail(
        reg_slug="demo",
        version="1",
        clause="1",
        bucket_entries=bucket,
        reg_entry=reg_entry,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
    )
    ids = [u["ucId"] for u in detail["coveringUcs"]]
    # "full" must come before "contributing" regardless of UC id.
    assert ids == ["1.1.2", "1.1.10"]


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------


def test_build_index_aggregates_counts_and_sorts_rows():
    details = [
        {
            "clauseId": "gdpr@2016/679#Art.32",
            "regulationId": "gdpr",
            "regulationShortName": "GDPR",
            "tier": 1,
            "version": "2016/679",
            "clause": "Art.32",
            "topic": "Security",
            "priorityWeight": 0.9,
            "obligationText": "Implement.",
            "coverageState": "covered-full",
            "topAssurance": "full",
            "coveringUcCount": 1,
            "coveringUcs": [{"ucId": "1.1.1"}],
            "assuranceBreakdown": {"full": 1},
            "endpoint": "/api/v1/compliance/clauses/gdpr__2016_679__Art.32.json",
        },
        {
            "clauseId": "gdpr@2016/679#Art.30",
            "regulationId": "gdpr",
            "regulationShortName": "GDPR",
            "tier": 1,
            "version": "2016/679",
            "clause": "Art.30",
            "topic": "Records",
            "priorityWeight": 0.7,
            "obligationText": None,
            "coverageState": "uncovered",
            "topAssurance": None,
            "coveringUcCount": 0,
            "coveringUcs": [],
            "assuranceBreakdown": {"full": 0},
            "endpoint": "/api/v1/compliance/clauses/gdpr__2016_679__Art.30.json",
        },
    ]
    index = ci.build_index(
        details,
        generated_at="2026-05-20T00:00:00Z",
        api_version="v1",
        catalogue_version="9.4.2",
    )
    assert index["totalClauses"] == 2
    assert index["coverageStateCounts"]["covered-full"] == 1
    assert index["coverageStateCounts"]["uncovered"] == 1
    # tier 1 has both states represented.
    assert index["tierCoverageStateCounts"]["1"]["covered-full"] == 1
    assert index["clausesByRegulation"]["gdpr"] == 2
    assert [r["clause"] for r in index["clauses"]] == ["Art.30", "Art.32"]


def test_build_index_handles_detail_without_tier():
    details = [
        {
            "clauseId": "demo@1#1",
            "regulationId": "demo",
            "regulationShortName": "Demo",
            "tier": None,
            "version": "1",
            "clause": "1",
            "topic": None,
            "priorityWeight": None,
            "obligationText": None,
            "coverageState": "uncovered",
            "topAssurance": None,
            "coveringUcCount": 0,
            "coveringUcs": [],
            "assuranceBreakdown": {},
            "endpoint": "/api/v1/compliance/clauses/demo__1__1.json",
        }
    ]
    out = ci.build_index(details, "2026-05-20T00:00:00Z", "v1", "9.4.2")
    # tier_counts must NOT include the None tier in tierCoverageStateCounts.
    assert "None" not in out["tierCoverageStateCounts"]
    assert out["tierCoverageStateCounts"] == {}


# ---------------------------------------------------------------------------
# load_ucs / load_regulations (filesystem-touching helpers)
# ---------------------------------------------------------------------------


def _wire_repo(monkeypatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "content" / "cat-01-foo").mkdir(parents=True)
    (repo / "data").mkdir()
    (repo / "api" / "v1" / "compliance" / "clauses").mkdir(parents=True)
    (repo / "VERSION").write_text("9.4.2\n", encoding="utf-8")
    monkeypatch.setattr(ci, "REPO_ROOT", repo)
    monkeypatch.setattr(ci, "REGULATIONS_PATH", repo / "data" / "regulations.json")
    monkeypatch.setattr(ci, "OUT_DIR", repo / "api" / "v1" / "compliance" / "clauses")
    monkeypatch.setattr(ci, "VERSION_FILE", repo / "VERSION")
    return repo


def test_load_ucs_skips_uc_without_string_id(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        json.dumps({"id": "1.1.1", "title": "Hello"}), encoding="utf-8"
    )
    (repo / "content" / "cat-01-foo" / "UC-1.1.2.json").write_text(
        json.dumps({"id": 123}), encoding="utf-8"
    )
    out = ci.load_ucs()
    ids = [u["id"] for u in out]
    assert ids == ["1.1.1"]
    # _sourcePath added relative to the repo root.
    assert out[0]["_sourcePath"].startswith("content/cat-01-foo/")


def test_load_ucs_aborts_on_malformed_json(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        "{ not json", encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="invalid JSON"):
        ci.load_ucs()


def test_load_regulations_rejects_non_object(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(SystemExit, match="top-level payload"):
        ci.load_regulations()


def test_load_regulations_returns_dict(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text(
        json.dumps({"frameworks": []}), encoding="utf-8"
    )
    out = ci.load_regulations()
    assert out == {"frameworks": []}


# ---------------------------------------------------------------------------
# generate / _hash_tree / _check_drift / main
# ---------------------------------------------------------------------------


def test_generate_writes_index_and_per_clause_files(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    repo = _wire_repo(monkeypatch, tmp_path)
    # Pre-populate one UC and the regulations payload.
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        json.dumps(
            _uc(
                "1.1.1",
                [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations()), encoding="utf-8"
    )
    out_dir = repo / "api" / "v1" / "compliance" / "clauses"
    # Stale file that should be wiped by the rmtree+remake step.
    (out_dir / "stale.json").write_text("{}", encoding="utf-8")
    index = ci.generate(out_dir)
    assert index["totalClauses"] == 2
    assert (out_dir / "index.json").exists()
    detail_files = sorted(p.name for p in out_dir.glob("*.json"))
    # 2 detail files + index.json; the stale file should be gone.
    assert "stale.json" not in detail_files
    assert "index.json" in detail_files


def test_generate_handles_uc_only_clauses_without_lookup(monkeypatch, tmp_path: Path):
    """Bucket key with no matching commonClause should still produce detail."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-02-bar" / "UC-2.1.1.json").parent.mkdir(parents=True)
    (repo / "content" / "cat-02-bar" / "UC-2.1.1.json").write_text(
        json.dumps(
            _uc(
                "2.1.1",
                [
                    {
                        "regulation": "OnlyOnUc",
                        "version": "1.0",
                        "clause": "X.1",
                        "mode": "satisfies",
                        "assurance": "partial",
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps({"frameworks": []}), encoding="utf-8"
    )
    out_dir = repo / "api" / "v1" / "compliance" / "clauses"
    index = ci.generate(out_dir)
    # The detail still appears for the UC-only clause.
    assert index["totalClauses"] == 1
    assert index["clauses"][0]["regulationId"] == "onlyonuc"


def test_generate_accepts_explicit_ucs_and_regulations(tmp_path: Path):
    """The dependency-injection signature should bypass the loaders."""
    out_dir = tmp_path / "out"
    os.environ["SOURCE_DATE_EPOCH"] = "1700000000"
    try:
        index = ci.generate(
            out_dir,
            ucs=[_uc(
                "1.1.1",
                [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            )],
            regulations=_regulations(),
        )
    finally:
        del os.environ["SOURCE_DATE_EPOCH"]
    assert index["totalClauses"] == 2
    assert (out_dir / "index.json").exists()


def test_hash_tree_returns_empty_hash_for_missing_root(tmp_path: Path):
    h = ci._hash_tree(tmp_path / "missing")
    assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_hash_tree_changes_when_contents_change(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.json").write_text("{}", encoding="utf-8")
    h1 = ci._hash_tree(root)
    (root / "b.json").write_text("{}", encoding="utf-8")
    h2 = ci._hash_tree(root)
    assert h1 != h2


def test_hash_tree_skips_directory_entries(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.json").write_text("{}", encoding="utf-8")
    # rglob('*') yields both 'a.json' and the 'sub/' directory; the latter
    # exercises the ``if p.is_file()`` False branch.
    (root / "sub").mkdir()
    (root / "sub" / "b.json").write_text("{}", encoding="utf-8")
    h = ci._hash_tree(root)
    assert isinstance(h, str) and len(h) == 64


def test_check_drift_returns_zero_when_committed_matches(
    monkeypatch, tmp_path: Path, capsys
):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        json.dumps(
            _uc(
                "1.1.1",
                [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations()), encoding="utf-8"
    )
    out_dir = repo / "api" / "v1" / "compliance" / "clauses"
    ci.generate(out_dir)  # populate the committed tree.
    capsys.readouterr()
    rc = ci._check_drift()
    msg = capsys.readouterr().err
    assert rc == 0
    assert "up to date" in msg


def test_check_drift_returns_one_when_committed_diverges(
    monkeypatch, tmp_path: Path, capsys
):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        json.dumps(
            _uc(
                "1.1.1",
                [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations()), encoding="utf-8"
    )
    # Don't populate OUT_DIR → drift is guaranteed.
    rc = ci._check_drift()
    msg = capsys.readouterr().err
    assert rc == 1
    assert "out of date" in msg


def test_main_check_routes_to_drift(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "data" / "regulations.json").write_text(
        json.dumps({"frameworks": []}), encoding="utf-8"
    )
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    # OUT_DIR is empty whereas a fresh generate() into a temp dir would
    # produce an index.json — that mismatch is exactly what ``--check``
    # exists to detect, so rc=1 confirms the branch was taken.
    rc = ci.main(["--check"])
    assert rc == 1


def test_main_check_returns_zero_when_tree_already_matches(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        json.dumps(
            _uc(
                "1.1.1",
                [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations()), encoding="utf-8"
    )
    # Populate the committed tree first so the drift check matches.
    ci.generate(repo / "api" / "v1" / "compliance" / "clauses")
    rc = ci.main(["--check"])
    assert rc == 0


def test_main_write_mode_logs_summary(monkeypatch, tmp_path: Path, capsys):
    repo = _wire_repo(monkeypatch, tmp_path)
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        json.dumps(
            _uc(
                "1.1.1",
                [
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "mode": "satisfies",
                        "assurance": "full",
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations()), encoding="utf-8"
    )
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    rc = ci.main([])
    out = capsys.readouterr().err
    assert rc == 0
    assert "Wrote" in out and "clauses" in out


def test_main_propagates_system_exit(monkeypatch, tmp_path: Path):
    repo = _wire_repo(monkeypatch, tmp_path)
    # malformed JSON triggers SystemExit from load_ucs.
    (repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
        "{ broken", encoding="utf-8"
    )
    (repo / "data" / "regulations.json").write_text(
        json.dumps(_regulations()), encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        ci.main([])


def test_main_catches_unexpected_exception(monkeypatch, tmp_path: Path, capsys):
    _wire_repo(monkeypatch, tmp_path)

    def boom(*_a, **_k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ci, "generate", boom)
    rc = ci.main([])
    err = capsys.readouterr().err
    assert rc == 2
    assert "UNEXPECTED ERROR" in err and "kaboom" in err
