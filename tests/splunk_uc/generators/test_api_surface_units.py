"""Unit tests for pure helpers in ``splunk_uc.generators.api_surface``.

The module is large (~2,500 lines, 747 statements) and was at **0% line
coverage** in ``data/baselines/coverage-v9.1.0.json`` as of v9.1.0 — one
of the two top zero-coverage surfaces called out in §P16 of
``docs/health-check-2026-progress.md``.

This test file ratchets the floor from 0% by exercising the module's
pure-function helpers: deterministic string transforms, sort-key
construction, dict shaping, and the recommender extractors. We
deliberately stay away from filesystem and subprocess side-effects
(``_render``, ``_load_ucs``, ``_recommender_splunkbase_index``) — those
need full-repo fixtures and belong in a smoke-test PR, not here.

Each test is small, hermetic, and unaffected by repo content or git
state, so the runtime stays well under 1 second even when the full
``tests/`` suite expands.
"""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Mapping

import pytest

# ``api_surface`` performs ``sys.path.insert(0, '<repo>/scripts')`` at
# import time so it can grab the legacy ``equipment_lib`` helper. We
# pre-seed the same path on a copy of ``sys.path`` so the import succeeds
# when pytest is launched without ``-p scripts`` discovery.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from splunk_uc.generators import api_surface as M  # noqa: E402


# ---------------------------------------------------------------------------
# _safe_version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, "unknown"),
        ("", "unknown"),
        ("v5.2.0", "v5.2.0"),
        ("Rev. 5", "Rev.-5"),
        ("v5.2.0 errata", "v5.2.0-errata"),
        ("4.0.1 (June 2024)", "4.0.1--June-2024-"),
        ("2.0/Annex A", "2.0-Annex-A"),
    ],
)
def test_safe_version_canonicalises_unsafe_chars(raw: str | None, expected: str) -> None:
    assert M._safe_version(raw) == expected


def test_safe_version_keeps_alphanumerics_and_dots() -> None:
    assert M._safe_version("5.2.0-rc1") == "5.2.0-rc1"


# ---------------------------------------------------------------------------
# _canonicalise_cim
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Authentication.Failed_Auth", "Authentication"),
        ("authentication", "Authentication"),
        ("Network_Traffic", "Network_Traffic"),
        ("Network_Traffic.All_Traffic", "Network_Traffic"),
        ("performance.disk", "Performance"),
        ("", None),
        ("not_a_real_model", None),
    ],
)
def test_canonicalise_cim_round_trips_known_models(raw: str, expected: str | None) -> None:
    assert M._canonicalise_cim(raw) == expected


# ---------------------------------------------------------------------------
# _uc_sort_key
# ---------------------------------------------------------------------------


def test_uc_sort_key_parses_three_part_id() -> None:
    assert M._uc_sort_key({"id": "22.35.1"}) == (22, 35, 1)


def test_uc_sort_key_orders_lexically_then_numerically() -> None:
    ids = [{"id": "3.10.2"}, {"id": "3.2.10"}, {"id": "3.2.2"}, {"id": "22.1.1"}]
    sorted_ids = sorted(ids, key=M._uc_sort_key)
    assert [u["id"] for u in sorted_ids] == ["3.2.2", "3.2.10", "3.10.2", "22.1.1"]


def test_uc_sort_key_handles_missing_id_with_sentinel() -> None:
    assert M._uc_sort_key({}) == (1_000_000, 1_000_000, 1_000_000)


def test_uc_sort_key_handles_malformed_id() -> None:
    assert M._uc_sort_key({"id": "not.a.id"}) == (1_000_000, 1_000_000, 1_000_000)


# ---------------------------------------------------------------------------
# _uc_compact
# ---------------------------------------------------------------------------


def test_uc_compact_minimal_input_produces_empty_lists() -> None:
    compact = M._uc_compact({"id": "1.2.3", "title": "X"})
    assert compact["id"] == "1.2.3"
    assert compact["title"] == "X"
    assert compact["regulations"] == []
    assert compact["regulationIds"] == []
    assert compact["mitreAttack"] == []
    assert compact["equipment"] == []
    assert compact["hasControlTest"] is False


def test_uc_compact_sorts_lists_and_deduplicates_prereqs() -> None:
    uc = {
        "id": "5.1.4",
        "title": "Foo",
        "_category": 5,
        "criticality": "high",
        "monitoringType": ["Audit", "Anomaly"],
        "mitreAttack": ["T1078.004", "T1003"],
        "equipment": ["catalyst-9300", "asa-5500"],
        "prerequisiteUseCases": ["UC-5.1.1", "UC-5.1.1", "UC-5.1.2"],
        "controlTest": {"positiveScenario": "ok", "negativeScenario": "no"},
    }
    compact = M._uc_compact(uc)
    assert compact["monitoringType"] == ["Anomaly", "Audit"]
    assert compact["mitreAttack"] == ["T1003", "T1078.004"]
    assert compact["equipment"] == ["asa-5500", "catalyst-9300"]
    assert compact["prerequisiteUseCases"] == ["UC-5.1.1", "UC-5.1.2"]
    assert compact["hasControlTest"] is True


def test_uc_compact_uses_alias_map_to_normalise_regulation_ids() -> None:
    uc = {
        "id": "22.1.1",
        "title": "GDPR mapping",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art. 32"},
            {"regulation": "EU GDPR", "version": "2016/679", "clause": "Art. 33"},
        ],
    }
    alias_map: dict[str, str] = {"gdpr": "gdpr", "eu gdpr": "gdpr"}
    compact = M._uc_compact(uc, alias_to_id=alias_map)
    assert compact["regulations"] == ["EU GDPR@2016/679", "GDPR@2016/679"]
    assert compact["regulationIds"] == ["gdpr@2016/679"]


# ---------------------------------------------------------------------------
# _regulation_alias_to_id
# ---------------------------------------------------------------------------


def test_regulation_alias_to_id_includes_id_short_name_and_aliases() -> None:
    regs = {
        "frameworks": [
            {
                "id": "gdpr",
                "shortName": "GDPR",
                "aliases": ["EU GDPR", "General Data Protection Regulation"],
            }
        ]
    }
    alias_map = M._regulation_alias_to_id(regs)
    assert alias_map["gdpr"] == "gdpr"
    assert alias_map["general data protection regulation"] == "gdpr"
    assert alias_map["eu gdpr"] == "gdpr"


def test_regulation_alias_to_id_skips_frameworks_without_id() -> None:
    regs = {"frameworks": [{"shortName": "Orphan"}, {"id": "hipaa", "shortName": "HIPAA"}]}
    alias_map = M._regulation_alias_to_id(regs)
    assert "hipaa" in alias_map
    assert "orphan" not in alias_map


def test_regulation_alias_to_id_honours_explicit_alias_index_override() -> None:
    regs = {
        "frameworks": [{"id": "gdpr", "shortName": "GDPR"}, {"id": "uk-gdpr", "shortName": "UK GDPR"}],
        "aliasIndex": {"GDPR": "uk-gdpr", "$comment": "ignored"},
    }
    alias_map = M._regulation_alias_to_id(regs)
    assert alias_map["gdpr"] == "uk-gdpr"
    assert "$comment" not in alias_map


# ---------------------------------------------------------------------------
# _index_ucs_by_regulation
# ---------------------------------------------------------------------------


def test_index_ucs_by_regulation_buckets_ucs_and_clauses() -> None:
    ucs: list[Mapping[str, str | list[dict[str, str]]]] = [
        {
            "id": "22.1.1",
            "compliance": [
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art. 32"},
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art. 33"},
            ],
        },
        {
            "id": "22.1.2",
            "compliance": [
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art. 33"},
            ],
        },
    ]
    alias_map: dict[str, str] = {"gdpr": "gdpr"}
    buckets = M._index_ucs_by_regulation(ucs, alias_map)
    assert buckets["gdpr@2016/679|ucs"] == ["22.1.1", "22.1.2"]
    assert buckets["gdpr@2016/679|clauses"] == ["Art. 32", "Art. 33"]


def test_index_ucs_by_regulation_preserves_unmapped_regulations_as_lowercase() -> None:
    ucs: list[Mapping[str, str | list[dict[str, str]]]] = [
        {
            "id": "1.1.1",
            "compliance": [
                {"regulation": "NotInCatalog", "version": "v1", "clause": "X"}
            ],
        }
    ]
    buckets = M._index_ucs_by_regulation(ucs, {})
    assert "notincatalog@v1|ucs" in buckets


def test_index_ucs_by_regulation_skips_incomplete_entries() -> None:
    ucs: list[Mapping[str, str | list[dict[str, str | None]]]] = [
        {
            "id": "1.1.1",
            "compliance": [
                {"regulation": "GDPR", "version": "2016/679"},  # missing clause
                {"regulation": "GDPR", "clause": "X"},  # missing version
                {"version": "v1", "clause": "X"},  # missing regulation
            ],
        }
    ]
    assert M._index_ucs_by_regulation(ucs, {"gdpr": "gdpr"}) == {}


# ---------------------------------------------------------------------------
# _recommender_sourcetypes
# ---------------------------------------------------------------------------


def test_recommender_sourcetypes_extracts_quoted_token() -> None:
    uc = {"q": 'index=main sourcetype="access_combined" status=500', "d": ""}
    assert M._recommender_sourcetypes(uc) == ["access_combined"]


def test_recommender_sourcetypes_lowers_and_dedupes() -> None:
    uc = {
        "q": 'sourcetype="access_combined" OR sourcetype=access_combined',
        "d": 'sourcetype="Access_Combined"',
    }
    assert M._recommender_sourcetypes(uc) == ["access_combined"]


def test_recommender_sourcetypes_drops_wildcards_and_negations() -> None:
    uc = {"q": 'sourcetype="*" sourcetype=-test', "d": ""}
    assert M._recommender_sourcetypes(uc) == []


def test_recommender_sourcetypes_handles_missing_fields() -> None:
    assert M._recommender_sourcetypes({}) == []


# ---------------------------------------------------------------------------
# _recommender_cim_models
# ---------------------------------------------------------------------------


def test_recommender_cim_models_extracts_canonical_models() -> None:
    uc = {"q": "| tstats count from datamodel=Authentication.Failed_Auth by user"}
    assert M._recommender_cim_models(uc) == ["Authentication"]


def test_recommender_cim_models_handles_multiple_and_dedupes() -> None:
    uc = {
        "q": (
            "| tstats count from datamodel=Authentication.Failed_Auth "
            "| append [ tstats count from datamodel:Network_Traffic.All_Traffic ]"
        )
    }
    assert M._recommender_cim_models(uc) == ["Authentication", "Network_Traffic"]


def test_recommender_cim_models_returns_empty_for_no_datamodel() -> None:
    uc = {"q": "index=main earliest=-24h"}
    assert M._recommender_cim_models(uc) == []


def test_recommender_cim_models_ignores_unknown_model_root() -> None:
    uc = {"q": "| tstats count from datamodel=NotARealModel.X"}
    assert M._recommender_cim_models(uc) == []


# ---------------------------------------------------------------------------
# _looks_like_app_label
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label",
    [
        "Splunk Add-on for Cisco IOS",
        "Splunk Enterprise Security",
        "Splunk_TA_cisco_meraki",
        "Cisco SecureX",
    ],
)
def test_looks_like_app_label_accepts_real_app_names(label: str) -> None:
    assert M._looks_like_app_label(label) is True


@pytest.mark.parametrize(
    "fragment",
    [
        "Splunk_TA_cisco_ios",  # actually valid — sanity check both polarities
    ],
)
def test_looks_like_app_label_smoke_with_real_token(fragment: str) -> None:
    assert M._looks_like_app_label(fragment) is True


@pytest.mark.parametrize(
    "fragment",
    [
        "Splunkbase 1352)",
        "(optional)",
        "(",
        "2.3",
        "**bold**",
        "syslog logs",
        "or equivalent firewall TA",
        "https://splunkbase.splunk.com/app/1234",
        "",
    ],
)
def test_looks_like_app_label_rejects_prose_debris(fragment: str) -> None:
    assert M._looks_like_app_label(fragment) is False


def test_looks_like_app_label_accepts_short_abbreviations() -> None:
    """``API``-style 3-letter tokens are intentionally accepted: the guard
    is designed to be liberal on short labels because vendor add-ons often
    use short trademarks (``ITSI``, ``ES``, ``DSP``). False positives here
    cost a low-confidence match; false negatives cost real app coverage."""
    assert M._looks_like_app_label("API") is True
    assert M._looks_like_app_label("ITSI") is True
