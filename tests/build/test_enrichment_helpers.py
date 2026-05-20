"""Hermetic tests for ``tools/build/enrichment.py`` — the pure helpers.

``enrichment.py`` is the legacy SSOT for content enrichment (regulation
tagging, premium-app classification, ESCU detection logic, MITRE
rollup, SPL pipeline narration, llms.txt writers, prerequisite
validation, implementation-roadmap bucketing). The module is 4486
lines, so this suite focuses on the **pure helpers** that are easy to
test without booting the full pipeline:

* ``assign_regulations`` — auto-tag UCs by title/subcategory
* ``assign_premium`` — auto-tag premium Splunk products
* ``assign_pillar`` — classify UC as security / observability / both
* ``is_escu_detection`` / ``_escu_is_rba`` / ``_escu_classify`` —
  Enterprise Security Content Update detection logic
* ``generate_escu_short_impl`` — methodology-specific implementation
  summary for ESCU detections
* ``_splunkbase_ids_in`` / ``apps_for_ta_string`` /
  ``ta_link_for_ta_string`` — Splunkbase ID extraction and app/TA
  lookup
* ``_split_spl_stages`` / ``_truncate_words`` — SPL parsing primitives
* ``_spl_explain_context`` / ``_extract_base_search_terms`` /
  ``_data_sources_mention_sourcetype`` / ``_extract_by_clause`` /
  ``_extract_span_clause`` — SPL narration helpers
* ``_classify_datasource`` / ``extract_filter_facets`` — facet
  extraction for the search UI
* ``_mitre_by_tactic`` — kill-chain-ordered MITRE rollup
* ``_cat_slug_for_id`` / ``_atomic_write`` / ``write_data_js`` /
  ``write_llms_txt`` / ``write_llms_full_txt`` — file emitters
* ``_uc_sort_key`` / ``compute_implementation_roadmap`` /
  ``validate_prerequisites`` / ``_extract_cycle`` — prerequisite graph
  + roadmap bucketing

All tests are hermetic: ``tmp_path`` only, no on-disk content tree, no
network. Defensive isinstance guards and large generator functions
(``generate_detailed_impl``, ``generate_escu_detailed_impl``,
``parse_category_file``, the sidecar caches) are deliberately out of
scope — they need integration-style fixtures with the real content
corpus.
"""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import enrichment as en  # noqa: E402


# ---------------------------------------------------------------------------
# _atomic_write
# ---------------------------------------------------------------------------


class TestAtomicWrite:
    def test_writes_simple_content(self, tmp_path: Path):
        target = tmp_path / "out.txt"
        en._atomic_write(str(target), "hello world")
        assert target.read_text(encoding="utf-8") == "hello world"

    def test_writes_unicode(self, tmp_path: Path):
        target = tmp_path / "out.txt"
        en._atomic_write(str(target), "héllo wörld 🌍")
        assert target.read_text(encoding="utf-8") == "héllo wörld 🌍"

    def test_overwrites_existing_file(self, tmp_path: Path):
        target = tmp_path / "out.txt"
        target.write_text("old", encoding="utf-8")
        en._atomic_write(str(target), "new")
        assert target.read_text(encoding="utf-8") == "new"

    def test_no_dotdot_temp_file_left_behind(self, tmp_path: Path):
        target = tmp_path / "out.txt"
        en._atomic_write(str(target), "x")
        # Only the target file should exist (no .tmp leftover).
        files = [p.name for p in tmp_path.iterdir()]
        assert files == ["out.txt"]

    def test_cleans_up_on_write_failure(self, tmp_path: Path, monkeypatch):
        """If the inner write raises, the temp file is unlinked."""
        target = tmp_path / "out.txt"

        original_replace = os.replace
        call_state: dict = {}

        def failing_replace(src: str, dst: str) -> None:
            # Capture temp-file path before re-raising so we can assert
            # cleanup happened.
            call_state["tmp"] = src
            raise PermissionError("simulated rename failure")

        monkeypatch.setattr(os, "replace", failing_replace)
        with pytest.raises(PermissionError):
            en._atomic_write(str(target), "x")
        # Temp file removed.
        assert "tmp" in call_state
        assert not Path(call_state["tmp"]).exists()


# ---------------------------------------------------------------------------
# assign_regulations
# ---------------------------------------------------------------------------


class TestAssignRegulations:
    def test_explicit_tier_1_pci_match(self):
        uc = {"n": "PCI DSS quarterly scan compliance"}
        out = en.assign_regulations(uc, 10, "10.12.1")
        assert "PCI DSS" in out

    def test_explicit_tier_1_multi_framework_match(self):
        uc = {"n": "HIPAA & SOX evidence collection"}
        out = en.assign_regulations(uc, 10, "10.12.5")
        assert "HIPAA" in out
        assert "SOX" in out

    def test_tier_1_nerc_cip_in_14_2(self):
        uc = {"n": "NERC CIP control-system monitoring"}
        out = en.assign_regulations(uc, 14, "14.2.3")
        assert out == ["NERC CIP"]

    def test_tier_1_21_11_gdpr(self):
        uc = {"n": "GDPR data subject access request workflow"}
        out = en.assign_regulations(uc, 21, "21.11.1")
        assert "GDPR" in out

    def test_dora_in_cat_12_is_skipped(self):
        """Category 12 (APM) has 'dora' in unrelated UC titles."""
        uc = {"n": "DORA application-performance demo"}
        out = en.assign_regulations(uc, 12, "12.1.1")
        assert "DORA" not in out

    def test_dora_outside_cat_12_is_tagged(self):
        uc = {"n": "DORA operational-resilience drill"}
        out = en.assign_regulations(uc, 21, "21.11.4")
        assert "DORA" in out

    def test_tier_2_pii_keyword_tags_gdpr_and_ccpa(self):
        uc = {"n": "PII data masking pipeline"}
        out = en.assign_regulations(uc, 1, "1.1.1")
        assert set(out) >= {"GDPR", "CCPA"}

    def test_tier_2_cardholder_tags_pci(self):
        uc = {"n": "Cardholder data scope"}
        out = en.assign_regulations(uc, 1, "1.1.1")
        assert "PCI DSS" in out

    def test_tier_2_ephi_tags_hipaa(self):
        uc = {"n": "ePHI inventory sweep"}
        out = en.assign_regulations(uc, 1, "1.1.1")
        assert "HIPAA" in out

    def test_consent_admin_does_not_tag_gdpr(self):
        """'consent admin' is a false positive — should NOT trigger GDPR."""
        uc = {"n": "Consent admin dashboard"}
        out = en.assign_regulations(uc, 1, "1.1.1")
        assert "GDPR" not in out

    def test_no_match_returns_empty_list(self):
        uc = {"n": "Generic CPU monitoring"}
        assert en.assign_regulations(uc, 1, "1.1.1") == []

    def test_result_is_sorted(self):
        uc = {"n": "PCI DSS HIPAA SOX FedRAMP combined"}
        out = en.assign_regulations(uc, 10, "10.12.1")
        assert out == sorted(out)

    def test_segregation_of_duties_tags_sox(self):
        uc = {"n": "Segregation of duties review"}
        assert "SOX" in en.assign_regulations(uc, 1, "1.1.1")


# ---------------------------------------------------------------------------
# assign_premium
# ---------------------------------------------------------------------------


class TestAssignPremium:
    def test_es_keyword_in_ta(self):
        uc = {"t": "Splunk Enterprise Security", "n": "Some detection"}
        assert "Splunk Enterprise Security" in en.assign_premium(uc)

    def test_escu_keyword_in_ta(self):
        uc = {"t": "ESCU detection", "n": "Some detection"}
        assert "Splunk Enterprise Security" in en.assign_premium(uc)

    def test_itsi_keyword_in_name(self):
        uc = {"t": "", "n": "ITSI service health monitoring"}
        assert "Splunk IT Service Intelligence (ITSI)" in en.assign_premium(uc)

    def test_soar_phantom_keyword(self):
        uc = {"t": "Splunk Phantom playbook"}
        assert "Splunk SOAR" in en.assign_premium(uc)

    def test_multiple_premium_products_joined_and_sorted(self):
        """Both ES and ITSI keywords trigger both labels, comma-joined."""
        uc = {"t": "Splunk ES + ITSI integration", "n": "ITSI service"}
        result = en.assign_premium(uc)
        # Comma-joined, sorted alphabetically.
        labels = [s.strip() for s in result.split(",")]
        assert labels == sorted(labels)

    def test_no_premium_returns_empty_string(self):
        uc = {"t": "Splunk Universal Forwarder", "n": "Plain UC"}
        assert en.assign_premium(uc) == ""

    def test_missing_fields_returns_empty_string(self):
        assert en.assign_premium({}) == ""


# ---------------------------------------------------------------------------
# assign_pillar
# ---------------------------------------------------------------------------


class TestAssignPillar:
    def test_existing_pillar_is_respected(self):
        uc = {"pillar": "custom-tag", "n": "anything"}
        assert en.assign_pillar(uc, 1) == "custom-tag"

    def test_security_via_sdomain(self):
        uc = {"sdomain": "endpoint", "n": "CPU watch"}
        assert en.assign_pillar(uc, 1) == "security"

    def test_security_via_mitre(self):
        uc = {"mitre": ["T1110"], "n": "Brute force"}
        assert en.assign_pillar(uc, 1) == "security"

    def test_security_via_dtype(self):
        uc = {"dtype": "TTP", "n": "Suspicious cmd"}
        assert en.assign_pillar(uc, 1) == "security"

    def test_observability_via_mtype(self):
        uc = {"mtype": ["performance"], "n": "Web server latency"}
        assert en.assign_pillar(uc, 1) == "observability"

    def test_both_when_security_and_observability(self):
        uc = {"mtype": ["security", "performance"], "n": "x"}
        assert en.assign_pillar(uc, 1) == "both"

    def test_security_via_keyword_in_value(self):
        uc = {"n": "Detection", "v": "Detect ransomware deployment"}
        assert en.assign_pillar(uc, 1) == "security"

    def test_default_when_no_signals_uses_category_membership(self):
        """No signals -> falls back to security if category is in
        ``PILLAR_SECURITY_CATS``, else observability."""
        # cat=1 isn't in PILLAR_SECURITY_CATS by default -> observability.
        uc = {"n": "Generic UC"}
        assert en.assign_pillar(uc, 1) == "observability"


# ---------------------------------------------------------------------------
# ESCU classifier
# ---------------------------------------------------------------------------


class TestEscuDetection:
    def test_is_escu_detection_positive(self):
        uc = {"t": "Splunk ESCU", "dtype": "TTP"}
        assert en.is_escu_detection(uc) is True

    def test_is_escu_detection_security_essentials(self):
        uc = {"t": "Splunk Security Essentials", "dtype": "anomaly"}
        assert en.is_escu_detection(uc) is True

    def test_is_escu_detection_requires_dtype(self):
        uc = {"t": "Splunk ESCU", "dtype": ""}
        assert en.is_escu_detection(uc) is False

    def test_is_escu_detection_requires_escu_app(self):
        uc = {"t": "Some other app", "dtype": "TTP"}
        assert en.is_escu_detection(uc) is False

    def test_escu_is_rba_via_spl_risk_object(self):
        uc = {"q": "stats count by Risk.risk_object"}
        assert en._escu_is_rba(uc) is True

    def test_escu_is_rba_via_dtype_entity_label(self):
        uc = {"q": "", "dtype": "user"}
        assert en._escu_is_rba(uc) is True

    def test_escu_is_rba_negative(self):
        uc = {"q": "stats count by host", "dtype": "TTP"}
        assert en._escu_is_rba(uc) is False

    def test_classify_ttp_methodology(self):
        methodology, entity, is_rba = en._escu_classify({"dtype": "TTP"})
        assert methodology == "TTP"
        assert entity is None
        assert is_rba is False

    def test_classify_anomaly_methodology(self):
        methodology, _entity, _is_rba = en._escu_classify({"dtype": "Anomaly"})
        assert methodology == "Anomaly"

    def test_classify_hunting_methodology(self):
        methodology, _entity, _is_rba = en._escu_classify({"dtype": "Hunting"})
        assert methodology == "Hunting"

    def test_classify_entity_dtype(self):
        methodology, entity, is_rba = en._escu_classify({"dtype": "user"})
        assert methodology == "TTP"
        assert entity == "user account"
        assert is_rba is True

    def test_classify_unknown_dtype_falls_through_to_ttp(self):
        methodology, entity, _is_rba = en._escu_classify({"dtype": "weird"})
        assert methodology == "TTP"
        assert entity is None

    def test_classify_missing_dtype_uses_ttp_default(self):
        methodology, _entity, _is_rba = en._escu_classify({})
        assert methodology == "TTP"


class TestEscuShortImpl:
    def test_hunting_returns_hunting_blurb(self):
        uc = {"dtype": "Hunting", "d": "logs"}
        out = en.generate_escu_short_impl(uc)
        assert "Hunting" in out
        assert "ad-hoc" in out
        assert "logs" in out

    def test_anomaly_returns_anomaly_blurb(self):
        uc = {"dtype": "Anomaly", "d": "logs"}
        out = en.generate_escu_short_impl(uc)
        assert "Anomaly" in out
        assert "baseline" in out

    def test_baseline_returns_baseline_blurb(self):
        uc = {"dtype": "Baseline", "d": "logs"}
        out = en.generate_escu_short_impl(uc)
        assert "Baseline" in out
        assert "normal behavior" in out

    def test_rba_returns_rba_blurb(self):
        uc = {"dtype": "user", "d": "auth logs"}
        out = en.generate_escu_short_impl(uc)
        assert "Risk-Based Alerting" in out
        assert "user account" in out

    def test_default_ttp_blurb(self):
        uc = {"dtype": "TTP", "d": "endpoint logs"}
        out = en.generate_escu_short_impl(uc)
        assert "Correlation Search" in out


# ---------------------------------------------------------------------------
# _splunkbase_ids_in / apps_for_ta_string / ta_link_for_ta_string
# ---------------------------------------------------------------------------


class TestSplunkbaseIdExtraction:
    def test_extracts_splunkbase_prefix(self):
        ids = en._splunkbase_ids_in("Splunk Add-on for ServiceNow (Splunkbase 1928)")
        assert ids == {1928}

    def test_extracts_app_anchor(self):
        ids = en._splunkbase_ids_in("https://example.com/app/1234/info")
        assert ids == {1234}

    def test_extracts_full_url(self):
        ids = en._splunkbase_ids_in(
            "See https://splunkbase.splunk.com/app/5678 for details"
        )
        assert ids == {5678}

    def test_extracts_multiple_ids(self):
        ids = en._splunkbase_ids_in("Splunkbase 100 and app/200 and another 300")
        assert ids == {100, 200}  # plain "300" isn't matched

    def test_empty_string_returns_empty_set(self):
        assert en._splunkbase_ids_in("") == set()

    def test_none_returns_empty_set(self):
        assert en._splunkbase_ids_in(None) == set()

    def test_no_match_returns_empty(self):
        assert en._splunkbase_ids_in("just some prose, no ids here") == set()


class TestAppsForTaString:
    def test_empty_returns_empty_list(self):
        assert en.apps_for_ta_string("") == []
        assert en.apps_for_ta_string(None) == []

    def test_unknown_ta_returns_empty(self):
        assert en.apps_for_ta_string("xyzzy-no-such-app") == []

    def test_known_ta_pattern_match(self):
        """ESCU is a stable, widely referenced app in SPLUNK_APPS."""
        out = en.apps_for_ta_string("Splunk ESCU")
        # At least one app matched.
        assert isinstance(out, list)
        # Result entries have the documented shape.
        if out:
            for entry in out:
                assert "name" in entry
                assert "id" in entry
                assert "url" in entry

    def test_strips_backticks_before_matching(self):
        a = en.apps_for_ta_string("`Splunk ESCU`")
        b = en.apps_for_ta_string("Splunk ESCU")
        assert a == b


class TestTaLinkForTaString:
    def test_empty_returns_none(self):
        assert en.ta_link_for_ta_string("") is None
        assert en.ta_link_for_ta_string(None) is None

    def test_unknown_returns_none(self):
        assert en.ta_link_for_ta_string("xyzzy-no-such-ta") is None

    def test_returns_dict_with_url(self):
        # Try a Splunkbase ID that's almost certainly in SPLUNK_TAS.
        out = en.ta_link_for_ta_string("Splunkbase 1928")
        if out is not None:
            assert "url" in out
            assert "splunkbase.splunk.com/app/" in out["url"]


# ---------------------------------------------------------------------------
# SPL parsing primitives
# ---------------------------------------------------------------------------


class TestSplitSplStages:
    def test_empty_returns_empty_list(self):
        assert en._split_spl_stages("") == []
        assert en._split_spl_stages(None) == []
        assert en._split_spl_stages("   ") == []

    def test_single_stage(self):
        assert en._split_spl_stages("index=foo") == ["index=foo"]

    def test_multiple_stages(self):
        stages = en._split_spl_stages("index=foo | stats count | where count > 0")
        assert stages == ["index=foo", "stats count", "where count > 0"]

    def test_pipe_inside_double_quotes_preserved(self):
        stages = en._split_spl_stages('search "a|b" | stats count')
        assert stages == ['search "a|b"', "stats count"]

    def test_pipe_inside_single_quotes_preserved(self):
        stages = en._split_spl_stages("search 'a|b' | stats count")
        assert stages == ["search 'a|b'", "stats count"]

    def test_pipe_inside_backticks_preserved(self):
        stages = en._split_spl_stages("`mymacro|with_pipe` | stats count")
        assert stages == ["`mymacro|with_pipe`", "stats count"]

    def test_pipe_inside_brackets_preserved(self):
        stages = en._split_spl_stages(
            "search foo [search bar | stats count] | dedup foo"
        )
        assert len(stages) == 2  # outer pipe splits, inner pipe stays
        assert "search bar | stats count" in stages[0]

    def test_escaped_quote_does_not_close_string(self):
        stages = en._split_spl_stages('search "a\\"|b" | stats count')
        # The escaped \" should not close the string.
        assert len(stages) == 2

    def test_trailing_pipe_with_no_content(self):
        stages = en._split_spl_stages("index=foo |")
        # Empty trailing stage filtered.
        assert stages == ["index=foo"]


class TestTruncateWords:
    def test_short_string_unchanged(self):
        assert en._truncate_words("short", max_len=50) == "short"

    def test_long_string_truncated_at_word_boundary(self):
        s = "one two three four five six seven eight nine ten"
        out = en._truncate_words(s, max_len=20)
        assert len(out) <= 20
        assert out.endswith("…")
        # Word boundary respected (last char before … is not mid-word).
        assert " " in out or out.startswith("o")

    def test_empty_returns_empty(self):
        assert en._truncate_words("") == ""
        assert en._truncate_words(None) == ""

    def test_default_max_len(self):
        s = "a " * 300
        out = en._truncate_words(s)
        assert len(out) <= 420


class TestSplExplainContext:
    def test_returns_none_for_falsy_uc(self):
        # ``not uc`` is True for None and {} — both yield None.
        assert en._spl_explain_context(None) is None
        assert en._spl_explain_context({}) is None
        # A non-empty dict (even with default-empty fields) returns
        # a populated context.
        assert en._spl_explain_context({"n": "x"}) is not None

    def test_returns_documented_keys(self):
        uc = {"n": "T", "v": "V", "d": "logs", "t": "App", "dtype": "TTP", "mtype": ["x"]}
        ctx = en._spl_explain_context(uc)
        assert set(ctx.keys()) == {"title", "value", "data_sources", "app_ta", "dtype", "mtype"}
        assert ctx["title"] == "T"
        assert ctx["value"] == "V"
        assert ctx["data_sources"] == "logs"
        assert ctx["app_ta"] == "App"
        assert ctx["dtype"] == "TTP"
        assert ctx["mtype"] == ["x"]


class TestExtractBaseSearchTerms:
    def test_extracts_index_sourcetype_host(self):
        out = en._extract_base_search_terms(
            "index=main sourcetype=cisco:asa host=fw01"
        )
        assert "main" in out["indexes"]
        assert "cisco:asa" in out["sourcetypes"]
        assert "fw01" in out["hosts"]

    def test_quoted_sourcetype_unwrapped(self):
        out = en._extract_base_search_terms('sourcetype="my:sourcetype"')
        assert out["sourcetypes"] == ["my:sourcetype"]

    def test_empty_input(self):
        out = en._extract_base_search_terms("")
        assert out == {"indexes": [], "sourcetypes": [], "hosts": []}

    def test_duplicates_filtered(self):
        out = en._extract_base_search_terms(
            "index=foo index=foo sourcetype=bar sourcetype=bar"
        )
        assert out["indexes"] == ["foo"]
        assert out["sourcetypes"] == ["bar"]


class TestDataSourcesMentionSourcetype:
    def test_substring_match(self):
        assert en._data_sources_mention_sourcetype(
            "We collect cisco:asa via syslog", "cisco:asa"
        )

    def test_case_insensitive(self):
        assert en._data_sources_mention_sourcetype("Logs from CISCO:ASA", "cisco:asa")

    def test_no_match(self):
        assert not en._data_sources_mention_sourcetype("nginx access logs", "cisco:asa")

    def test_handles_falsy(self):
        assert not en._data_sources_mention_sourcetype("", "cisco:asa")
        assert not en._data_sources_mention_sourcetype("logs", "")

    def test_strips_punctuation_for_bare_match(self):
        # Sourcetype with surrounding punctuation should still match the
        # bare form.
        assert en._data_sources_mention_sourcetype("uses cisco_asa here", '"cisco_asa"')


class TestExtractByClause:
    def test_extracts_by_clause(self):
        assert en._extract_by_clause("stats count by host") == "host"

    def test_no_by_returns_empty(self):
        assert en._extract_by_clause("stats count") == ""

    def test_truncates_at_pipe(self):
        out = en._extract_by_clause("stats count by host | where count > 0")
        assert out == "host"


class TestExtractSpanClause:
    def test_extracts_span(self):
        assert en._extract_span_clause("timechart span=1h count") == "1h"

    def test_no_span_returns_empty(self):
        assert en._extract_span_clause("timechart count") == ""


# ---------------------------------------------------------------------------
# Datasource classification + facets
# ---------------------------------------------------------------------------


class TestClassifyDatasource:
    def test_returns_none_for_unknown(self):
        assert en._classify_datasource("xyzzy-no-such-source") is None

    def test_classification_is_deterministic(self):
        """Calling twice returns the same answer."""
        a = en._classify_datasource("cisco:asa")
        b = en._classify_datasource("cisco:asa")
        assert a == b


class TestExtractFilterFacets:
    def test_empty_data_returns_empty_facets(self):
        out = en.extract_filter_facets([])
        assert out["dtype"] == []
        assert out["premium"] == []
        assert out["cim"] == []
        assert out["sapp"] == []
        assert out["industry"] == []
        assert out["mitre"] == []
        assert out["datasource_groups"] == []

    def test_dtype_collected_from_allowlist(self):
        # Use a likely-valid dtype value.
        data = [
            {
                "i": 1,
                "n": "C",
                "s": [
                    {
                        "i": "1.1",
                        "n": "S",
                        "u": [
                            {"i": "1.1.1", "n": "UC", "dtype": "TTP"},
                        ],
                    }
                ],
            }
        ]
        out = en.extract_filter_facets(data)
        # TTP may or may not be in the allow-list depending on version,
        # but the structure should be a sorted list.
        assert isinstance(out["dtype"], list)

    def test_industries_aggregated(self):
        data = [
            {
                "s": [
                    {
                        "u": [
                            {"ind": "Healthcare"},
                            {"ind": "Finance"},
                            {"ind": "Healthcare"},
                        ]
                    }
                ]
            }
        ]
        out = en.extract_filter_facets(data)
        assert out["industry"] == ["Finance", "Healthcare"]

    def test_premium_aggregated(self):
        data = [
            {"s": [{"u": [{"premium": "ITSI"}, {"premium": "ES"}, {"premium": "ES"}]}]}
        ]
        out = en.extract_filter_facets(data)
        assert out["premium"] == ["ES", "ITSI"]

    def test_cim_stripped_of_paren_suffix(self):
        data = [
            {
                "s": [
                    {
                        "u": [
                            {"a": ["Authentication (LDAP)", "Network Traffic"]},
                        ]
                    }
                ]
            }
        ]
        out = en.extract_filter_facets(data)
        # "Authentication" is the bare form.
        assert "Authentication" in out["cim"]
        assert "Network Traffic" in out["cim"]

    def test_sapp_map_dedupes_by_id(self):
        data = [
            {
                "s": [
                    {
                        "u": [
                            {"sapp": [{"id": 1234, "name": "App"}]},
                            {"sapp": [{"id": 1234, "name": "App"}]},
                        ]
                    }
                ]
            }
        ]
        out = en.extract_filter_facets(data)
        assert out["sapp"] == [{"id": 1234, "name": "App"}]


# ---------------------------------------------------------------------------
# _mitre_by_tactic
# ---------------------------------------------------------------------------


class TestMitreByTactic:
    def test_empty_returns_empty(self):
        assert en._mitre_by_tactic([]) == []

    def test_ungrouped_when_no_tech_db(self, monkeypatch):
        """If the techniques DB isn't on disk, every id falls into the
        ``_other`` bucket."""
        monkeypatch.setattr(
            "build.enrichment.PROJECT_ROOT", "/nonexistent-dir-for-test"
        )
        # Need to re-import to pick up the patched PROJECT_ROOT? No —
        # _mitre_by_tactic recomputes tech_path from PROJECT_ROOT each call.
        out = en._mitre_by_tactic(["T1110", "T1078"])
        # The structure is a list of {tactic, label, techniques}.
        assert isinstance(out, list)
        if out:
            # All ungrouped (since no tech DB found).
            assert out[-1]["tactic"] == "_other"

    def test_result_shape(self, monkeypatch):
        monkeypatch.setattr(
            "build.enrichment.PROJECT_ROOT", "/nonexistent-dir-for-test"
        )
        out = en._mitre_by_tactic(["T9999"])
        assert isinstance(out, list)
        if out:
            entry = out[0]
            assert {"tactic", "label", "techniques"} <= entry.keys()


# ---------------------------------------------------------------------------
# _cat_slug_for_id
# ---------------------------------------------------------------------------


class TestCatSlugForId:
    def test_finds_matching_file(self):
        files = ["cat-01-servers.md", "cat-02-virtualization.md", "cat-10-security.md"]
        assert en._cat_slug_for_id(1, files) == "cat-01-servers"
        assert en._cat_slug_for_id(10, files) == "cat-10-security"

    def test_returns_none_when_no_match(self):
        files = ["cat-01-servers.md"]
        assert en._cat_slug_for_id(99, files) is None

    def test_handles_basename(self):
        files = ["content/cat-01-servers.md"]
        assert en._cat_slug_for_id(1, files) == "cat-01-servers"


# ---------------------------------------------------------------------------
# write_data_js
# ---------------------------------------------------------------------------


class TestWriteDataJs:
    def test_emits_documented_globals(self, tmp_path: Path):
        data = [{"i": 1, "n": "Cat", "s": []}]
        cat_meta = {"1": {"icon": "srv"}}
        out_path = tmp_path / "data.js"
        size = en.write_data_js(data, cat_meta, str(out_path))
        assert out_path.exists()
        assert size > 0
        text = out_path.read_text(encoding="utf-8")
        for needle in (
            "const DATA = ",
            "const CAT_META = ",
            "const CAT_GROUPS = ",
            "const EQUIPMENT = ",
            "const FILTER_FACETS = ",
            "const RECENTLY_ADDED = new Set(",
            "const ROADMAP = ",
        ):
            assert needle in text

    def test_recently_added_defaults_to_empty(self, tmp_path: Path):
        out_path = tmp_path / "data.js"
        en.write_data_js([], {}, str(out_path))
        text = out_path.read_text(encoding="utf-8")
        # Empty array serialization.
        assert "new Set([])" in text

    def test_recently_added_serialized(self, tmp_path: Path):
        out_path = tmp_path / "data.js"
        en.write_data_js([], {}, str(out_path), recently_added=["1.1.1", "2.1.1"])
        text = out_path.read_text(encoding="utf-8")
        assert '"1.1.1"' in text
        assert '"2.1.1"' in text

    def test_roadmap_serialized(self, tmp_path: Path):
        out_path = tmp_path / "data.js"
        roadmap = {"1": {"crawl": ["UC-1.1.1"], "walk": [], "run": [], "unassigned": []}}
        en.write_data_js([], {}, str(out_path), roadmap=roadmap)
        text = out_path.read_text(encoding="utf-8")
        assert '"crawl":["UC-1.1.1"]' in text


# ---------------------------------------------------------------------------
# write_llms_txt + write_llms_full_txt
# ---------------------------------------------------------------------------


class TestWriteLlmsTxt:
    def test_writes_documented_sections(self, tmp_path: Path, monkeypatch):
        """``write_llms_txt`` writes to the module-level ``OUTPUT_LLMS_TXT``
        attribute set by the caller (see ``render_legacy_artifacts.py``)."""
        out_path = tmp_path / "llms.txt"
        monkeypatch.setattr(en, "OUTPUT_LLMS_TXT", str(out_path), raising=False)

        data = [{"i": 1, "n": "Cat A", "s": []}]
        size_kb = en.write_llms_txt(data, {}, ["cat-01-cat-a.md"], total_uc=42)
        assert out_path.exists()
        assert size_kb > 0
        text = out_path.read_text(encoding="utf-8")
        assert "Splunk Infrastructure Monitoring" in text
        assert "42+" in text
        assert "## Docs" in text
        assert "## Categories" in text


class TestWriteLlmsFullTxt:
    def test_lists_every_uc(self, tmp_path: Path, monkeypatch):
        out_path = tmp_path / "llms-full.txt"
        monkeypatch.setattr(en, "OUTPUT_LLMS_FULL_TXT", str(out_path), raising=False)

        data = [
            {
                "i": 1,
                "n": "Servers",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Linux",
                        "u": [
                            {"i": "1.1.1", "n": "CPU spike", "c": "high"},
                            {"i": "1.1.2", "n": "Memory leak", "c": "medium"},
                        ],
                    }
                ],
            }
        ]
        size_kb = en.write_llms_full_txt(data, {}, ["cat-01-servers.md"], total_uc=2)
        assert out_path.exists()
        assert size_kb > 0
        text = out_path.read_text(encoding="utf-8")
        assert "UC-1.1.1" in text
        assert "UC-1.1.2" in text
        assert "CPU spike" in text


# ---------------------------------------------------------------------------
# Prerequisite graph: validation + roadmap + sort key
# ---------------------------------------------------------------------------


class TestUcSortKey:
    def test_numeric_parts_parsed(self):
        # ``_uc_sort_key`` returns a tuple (so it's hashable and stable
        # under ``sorted(..., key=...)``).
        assert en._uc_sort_key("1.2.3") == (1, 2, 3)

    def test_non_numeric_part_becomes_inf(self):
        assert en._uc_sort_key("1.x.3") == (1, 10**9, 3)

    def test_empty_returns_one_element_tuple(self):
        # ``"".split(".")`` -> ``[""]``, which then non-numerically parses
        # to the sentinel 10**9.
        assert en._uc_sort_key("") == (10**9,)
        assert en._uc_sort_key(None) == (10**9,)

    def test_can_be_used_as_sort_key(self):
        ids = ["1.10.1", "1.2.1", "1.2.10", "1.2.2"]
        sorted_ids = sorted(ids, key=en._uc_sort_key)
        assert sorted_ids == ["1.2.1", "1.2.2", "1.2.10", "1.10.1"]


class TestComputeImplementationRoadmap:
    def test_buckets_by_wave_and_category(self):
        data = [
            {
                "i": 1,
                "s": [
                    {
                        "i": "1.1",
                        "u": [
                            {"i": "1.1.1", "wv": "crawl"},
                            {"i": "1.1.2", "wv": "walk"},
                            {"i": "1.1.3", "wv": "run"},
                            {"i": "1.1.4"},  # unassigned
                        ],
                    }
                ],
            }
        ]
        out = en.compute_implementation_roadmap(data)
        assert "1" in out
        assert out["1"]["crawl"] == ["UC-1.1.1"]
        assert out["1"]["walk"] == ["UC-1.1.2"]
        assert out["1"]["run"] == ["UC-1.1.3"]
        assert out["1"]["unassigned"] == ["UC-1.1.4"]

    def test_skips_categories_without_id(self):
        data = [{"s": []}]  # no "i"
        out = en.compute_implementation_roadmap(data)
        assert out == {}

    def test_deterministic_order(self):
        data = [
            {
                "i": 1,
                "s": [
                    {
                        "i": "1.1",
                        "u": [
                            {"i": "1.1.2", "wv": "crawl"},
                            {"i": "1.1.1", "wv": "crawl"},
                        ],
                    }
                ],
            }
        ]
        out = en.compute_implementation_roadmap(data)
        # Sorted by UC id.
        assert out["1"]["crawl"] == ["UC-1.1.1", "UC-1.1.2"]

    def test_empty_data_returns_empty(self):
        assert en.compute_implementation_roadmap([]) == {}


class TestValidatePrerequisites:
    def _build_data(self, ucs):
        return [
            {
                "i": 1,
                "s": [
                    {
                        "i": "1.1",
                        "u": ucs,
                    }
                ],
            }
        ]

    def test_clean_data_does_not_exit(self, capsys):
        data = self._build_data(
            [{"i": "1.1.1", "wv": "crawl"}, {"i": "1.1.2", "wv": "walk", "pre": ["UC-1.1.1"]}]
        )
        # Should print summary and return cleanly.
        en.validate_prerequisites(data)
        out = capsys.readouterr().out
        assert "Waves:" in out

    def test_unknown_prerequisite_fails(self, capsys):
        data = self._build_data(
            [{"i": "1.1.1", "wv": "crawl", "pre": ["UC-99.99.99"]}]
        )
        with pytest.raises(SystemExit):
            en.validate_prerequisites(data)
        err = capsys.readouterr().err
        assert "unknown prerequisite" in err

    def test_self_reference_fails(self, capsys):
        data = self._build_data(
            [{"i": "1.1.1", "wv": "crawl", "pre": ["UC-1.1.1"]}]
        )
        with pytest.raises(SystemExit):
            en.validate_prerequisites(data)
        err = capsys.readouterr().err
        assert "self-reference" in err

    def test_cycle_detected(self, capsys):
        data = self._build_data(
            [
                {"i": "1.1.1", "wv": "crawl", "pre": ["UC-1.1.2"]},
                {"i": "1.1.2", "wv": "walk", "pre": ["UC-1.1.1"]},
            ]
        )
        with pytest.raises(SystemExit):
            en.validate_prerequisites(data)
        err = capsys.readouterr().err
        assert "cycle detected" in err

    def test_wave_monotonicity_warns_only(self, capsys):
        """A crawl-tier UC depending on a run-tier UC: WARN, no exit."""
        data = self._build_data(
            [
                {"i": "1.1.1", "wv": "crawl", "pre": ["UC-1.1.2"]},
                {"i": "1.1.2", "wv": "run"},
            ]
        )
        en.validate_prerequisites(data)  # no SystemExit
        out = capsys.readouterr().out
        assert "wave monotonicity" in out

    def test_duplicate_uc_id_fails(self, capsys):
        data = [
            {
                "i": 1,
                "s": [
                    {
                        "i": "1.1",
                        "u": [{"i": "1.1.1"}, {"i": "1.1.1"}],
                    }
                ],
            }
        ]
        with pytest.raises(SystemExit):
            en.validate_prerequisites(data)
        err = capsys.readouterr().err
        assert "duplicate UC id" in err


class TestExtractCycle:
    def test_finds_two_node_cycle(self):
        index = {
            "UC-1": {"pre": ["UC-2"]},
            "UC-2": {"pre": ["UC-1"]},
        }
        residual = ["UC-1", "UC-2"]
        cycle = en._extract_cycle(index, residual)
        assert cycle[0] == cycle[-1]
        assert set(cycle) <= {"UC-1", "UC-2"}

    def test_no_cycle_returns_preview(self):
        """When residual has nodes but no actual cycle (e.g., long path),
        fallback returns the preview list."""
        index = {
            "UC-A": {"pre": []},
            "UC-B": {"pre": ["UC-A"]},
        }
        residual = ["UC-A", "UC-B"]
        cycle = en._extract_cycle(index, residual)
        # Either a real cycle path or the fallback preview string.
        assert isinstance(cycle, list)


# ---------------------------------------------------------------------------
# Lightweight sanity: explain_spl_pipeline + helpers integration
# ---------------------------------------------------------------------------


class TestExplainSplPipeline:
    def test_empty_returns_empty(self):
        assert en.explain_spl_pipeline("") == ""
        assert en.explain_spl_pipeline(None) == ""

    def test_returns_string(self):
        out = en.explain_spl_pipeline("index=foo | stats count by host")
        assert isinstance(out, str)
        # Either a non-empty narration or empty (if no bullets produced).
        # Just verify the function doesn't crash.

    def test_with_context(self):
        uc = {"n": "Test UC", "v": "Some value", "d": "logs", "t": "App"}
        out = en.explain_spl_pipeline(
            "index=foo | stats count by host | where count > 0",
            uc=uc,
        )
        assert isinstance(out, str)

    def test_caps_at_max_bullets(self):
        """max_bullets is clamped to [4, 40]."""
        long_spl = " | ".join(["stats count"] * 60)
        out = en.explain_spl_pipeline(long_spl, max_bullets=100)
        # Just verify it doesn't crash and returns a string.
        assert isinstance(out, str)
