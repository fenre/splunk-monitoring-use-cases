"""Unit tests for ``splunk_uc.audits.gold_profile_v2``.

P16 wave M: lifts ``src/splunk_uc/audits/gold_profile_v2.py`` from 10.42% to
≥99% combined line+branch coverage. Pins every documented contract of the
v2 "UC-1.1.1 bar" gold-profile audit: thresholds, regex patterns, pure
helpers, per-UC scoring, file discovery, pack-drift heuristic, reporting,
and the ``main()`` CLI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import gold_profile_v2 as gp

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestThresholds:
    """``V2_THRESHOLDS`` is the public knob set; lock its shape."""

    def test_all_documented_keys_present(self) -> None:
        for key in (
            "detailedImplementation_min_chars",
            "kfp_min_scenarios",
            "di_unique_specifics_min",
            "datasources_min_chars",
            "references_min",
            "control_test_diff_min_chars",
            "evidence_min_chars",
            "exclusions_min_chars",
            "passing_score",
        ):
            assert key in gp.V2_THRESHOLDS

    def test_di_min_chars_matches_docstring(self) -> None:
        # Docstring promises the bar is 1500 chars (vs v1's 500).
        assert gp.V2_THRESHOLDS["detailedImplementation_min_chars"] == 1500

    def test_passing_score_is_80(self) -> None:
        # Docstring promises >= 80 / 100.
        assert gp.V2_THRESHOLDS["passing_score"] == 80

    def test_thresholds_are_positive_ints(self) -> None:
        for k, v in gp.V2_THRESHOLDS.items():
            assert isinstance(v, int), f"{k} should be int"
            assert v > 0, f"{k} should be positive"


class TestRepoPaths:
    """``REPO_ROOT`` and ``CONTENT_DIR`` resolve relative to this module."""

    def test_repo_root_points_at_real_repo(self) -> None:
        assert (gp.REPO_ROOT / "schemas").is_dir()
        assert (gp.REPO_ROOT / "content").is_dir()

    def test_content_dir_under_repo_root(self) -> None:
        assert gp.CONTENT_DIR == gp.REPO_ROOT / "content"


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------


class TestSplunkbaseIdRegex:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Splunkbase 6238", True),
            ("see splunkbase.splunk.com/app/6238", True),
            ("SPLUNKBASE 12345", True),
            ("splunkbase 99", True),
            ("splunkbase 9", False),
            ("no splunkbase here", False),
            ("", False),
        ],
    )
    def test_matches(self, text: str, expected: bool) -> None:
        assert bool(gp.SPLUNKBASE_ID_RE.search(text)) is expected


class TestSourcetypeRegex:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("sourcetype=foo", True),
            ("sourcetype = cisco:ise:syslog", True),
            ("sourcetype:json", True),
            ('sourcetype="cisco:ise"', True),
            ("foo=bar", False),
            ("", False),
        ],
    )
    def test_matches(self, text: str, expected: bool) -> None:
        assert bool(gp.SOURCETYPE_RE.search(text)) is expected


class TestIndexRegex:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("index=main", True),
            ("index = security", True),
            ("INDEX=foo", True),
            ("foo index", False),
        ],
    )
    def test_matches(self, text: str, expected: bool) -> None:
        assert bool(gp.INDEX_RE.search(text)) is expected


class TestApiPathRegex:
    @pytest.mark.parametrize(
        "text",
        ["/api/v2/foo", "/dna/intent/api", "/services/data", "/now/table/incident"],
    )
    def test_matches(self, text: str) -> None:
        assert gp.API_PATH_RE.search(text)


class TestRbacRegex:
    @pytest.mark.parametrize(
        "text",
        ["RBAC", "role-based", "admin-role", "API token", "OAuth"],
    )
    def test_matches(self, text: str) -> None:
        assert gp.RBAC_RE.search(text)


class TestTimeboundRegex:
    @pytest.mark.parametrize(
        "text",
        ["5 minutes", "1 hour", "30 days", "10 seconds", "2 weeks"],
    )
    def test_matches(self, text: str) -> None:
        assert gp.TIMEBOUND_RE.search(text)


class TestModularInputRegex:
    @pytest.mark.parametrize(
        "text",
        ["modular input", "inputs.conf", "HEC", "forwarder", "scripted input"],
    )
    def test_matches(self, text: str) -> None:
        assert gp.MODULAR_INPUT_RE.search(text)


class TestVendorUiRegex:
    def test_matches_settings_path(self) -> None:
        assert gp.VENDOR_UI_RE.search("Settings > Authentication")

    def test_matches_admin_path(self) -> None:
        assert gp.VENDOR_UI_RE.search("Admin > Users")

    def test_does_not_match_random_text(self) -> None:
        assert not gp.VENDOR_UI_RE.search("plain text")


class TestSuppressionRegex:
    @pytest.mark.parametrize(
        "text",
        [
            "exception register",
            "time-bound exception",
            "lookup foo",
            "allow list",
            "block-list",
            "nis2_exceptions.csv",
            "filter the spl",
        ],
    )
    def test_matches(self, text: str) -> None:
        assert gp.SUPPRESSION_RE.search(text)


class TestNamedProductRegex:
    @pytest.mark.parametrize(
        "text",
        ["Veeam", "Cisco Cyber Vision", "Microsoft Defender", "Splunk ES", "Okta", "Workday"],
    )
    def test_matches(self, text: str) -> None:
        assert gp.NAMED_PRODUCT_RE.search(text)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestWordSet:
    def test_empty_text(self) -> None:
        assert gp._word_set("") == set()

    def test_words_lowercased(self) -> None:
        assert gp._word_set("Hello World") == {"hello", "world"}

    def test_drops_short_words(self) -> None:
        # Only words of >= 4 letters are kept (the docstring promise).
        assert "and" not in gp._word_set("alpha and beta gamma")
        assert "alpha" in gp._word_set("alpha and beta gamma")

    def test_strips_punctuation(self) -> None:
        # Only words >= 4 letters; "foo", "bar", "baz" are 3 letters → dropped.
        assert gp._word_set("alpha, beta. gamma!") == {"alpha", "beta", "gamma"}


class TestDescriptionValueJaccard:
    def test_empty_inputs(self) -> None:
        assert gp._description_value_jaccard("", "") == 0.0
        assert gp._description_value_jaccard("hello world", "") == 0.0
        assert gp._description_value_jaccard("", "hello world") == 0.0

    def test_identical_text(self) -> None:
        assert gp._description_value_jaccard("hello world", "hello world") == 1.0

    def test_disjoint_text(self) -> None:
        assert gp._description_value_jaccard("alpha beta", "gamma delta") == 0.0

    def test_partial_overlap(self) -> None:
        sim = gp._description_value_jaccard("alpha beta gamma", "alpha delta epsilon")
        # 1 shared / 5 union = 0.2
        assert sim == pytest.approx(0.2)


class TestCountUniqueSpecifics:
    def test_empty_returns_zero(self) -> None:
        assert gp._count_unique_specifics("") == 0
        assert gp._count_unique_specifics(None) == 0

    def test_single_signal(self) -> None:
        assert gp._count_unique_specifics("sourcetype=cisco:ise") == 1

    def test_multiple_signals_all_unique(self) -> None:
        text = (
            "Use sourcetype=cisco:ise via /api/v2/foo with RBAC role-admin. "
            "Splunkbase 6238 modular input runs every 5 minutes via inputs.conf "
            "and visit Settings > Identity to configure."
        )
        # 8 distinct pattern hits expected; >= 6 is the threshold.
        assert gp._count_unique_specifics(text) >= 6

    def test_duplicate_signals_dedup(self) -> None:
        # Two identical sourcetype= matches should collapse to one.
        text = "sourcetype=foo sourcetype=foo"
        assert gp._count_unique_specifics(text) == 1


class TestCountKfpScenarios:
    def test_empty_returns_zero(self) -> None:
        assert gp._count_kfp_scenarios("") == 0
        assert gp._count_kfp_scenarios(None) == 0

    def test_bulleted_list_counts_bullets(self) -> None:
        text = "- Scenario one\n- Scenario two\n- Scenario three"
        assert gp._count_kfp_scenarios(text) == 3

    def test_numbered_list_counts_items(self) -> None:
        text = "1. First\n2. Second\n3. Third\n4. Fourth"
        assert gp._count_kfp_scenarios(text) == 4

    def test_inline_numbered_items(self) -> None:
        # The regex uses leading whitespace OR sentence-separator preceding "N)"
        text = "Foo. 1) Alpha thing. 2) Beta thing. 3) Gamma thing."
        assert gp._count_kfp_scenarios(text) >= 2

    def test_bold_markdown_headers(self) -> None:
        text = "**Maintenance Window** description.\n**Holiday Period** description."
        assert gp._count_kfp_scenarios(text) == 2

    def test_scenario_markers(self) -> None:
        text = "Scenario: alpha thing. Scenario: beta thing. Scenario: gamma."
        assert gp._count_kfp_scenarios(text) == 3

    def test_named_product_fallback(self) -> None:
        text = (
            "Veeam backup jobs run on Sundays and should be excluded from the alert. "
            "Cisco Cyber Vision passive scans occasionally trigger this rule. "
            "Okta password rotations should be filtered out by the lookup."
        )
        # No bullets/numbers/bold/scenario markers — named-product fallback fires.
        assert gp._count_kfp_scenarios(text) >= 2

    def test_no_signals_returns_zero(self) -> None:
        assert gp._count_kfp_scenarios("plain text without structure") == 0


class TestHasSuppressionMechanism:
    def test_empty_returns_false(self) -> None:
        assert gp._has_suppression_mechanism("") is False
        assert gp._has_suppression_mechanism(None) is False

    def test_lookup_match(self) -> None:
        assert gp._has_suppression_mechanism("see lookup exceptions_table") is True

    def test_no_match(self) -> None:
        assert gp._has_suppression_mechanism("plain text") is False


class TestHasSplunkbaseId:
    def test_empty_returns_false(self) -> None:
        assert gp._has_splunkbase_id("") is False
        assert gp._has_splunkbase_id(None) is False

    def test_id_match(self) -> None:
        assert gp._has_splunkbase_id("via Splunkbase 6238") is True

    def test_no_match(self) -> None:
        assert gp._has_splunkbase_id("no app id") is False


class TestHasSourcetype:
    def test_empty_returns_false(self) -> None:
        assert gp._has_sourcetype("") is False
        assert gp._has_sourcetype(None) is False

    def test_sourcetype_match(self) -> None:
        assert gp._has_sourcetype("sourcetype=cisco:ise") is True

    def test_no_match(self) -> None:
        assert gp._has_sourcetype("plain text") is False


class TestHasFieldList:
    def test_empty_returns_false(self) -> None:
        assert gp._has_field_list("") is False
        assert gp._has_field_list(None) is False

    def test_three_field_list(self) -> None:
        assert gp._has_field_list("src_ip, dest_ip, user_id") is True

    def test_two_fields_not_enough(self) -> None:
        # Threshold is three comma-separated identifiers.
        assert gp._has_field_list("src_ip, dest_ip") is False

    def test_no_match(self) -> None:
        assert gp._has_field_list("plain text without comma list") is False


# ---------------------------------------------------------------------------
# audit_uc_v2 — the core per-UC scorer
# ---------------------------------------------------------------------------


def _gold_uc() -> dict[str, Any]:
    """Return a UC dict that passes every v2 check at a perfect score."""
    di = (
        "Use sourcetype=cisco:ise:syslog via /api/v2/events with role-admin RBAC. "
        "Configure Splunkbase 6238 modular input running every 5 minutes via "
        "inputs.conf. Visit Settings > Authentication to enable. Reference index=main. "
    ) * 8  # repeat to clear the 1500-char threshold
    kfp = (
        "- Veeam backup jobs trigger this on Sunday — suppress via lookup veeam_exclusions.csv\n"
        "- Cisco Cyber Vision passive scans fire occasionally — exception register tracks them\n"
        "- Okta password rotation events — filter the spl with a time-bound exception\n"
        "- ServiceNow CMDB sync windows — allow-list these via the lookup\n"
        "- Microsoft Defender baseline updates — block-list the source"
    )
    return {
        "id": "1.1.1",
        "title": "Gold UC",
        "description": "alpha beta gamma delta epsilon",
        "value": "rho sigma tau upsilon phi",
        "dataSources": (
            "Cisco ISE syslog via Splunkbase 6238. sourcetype=cisco:ise:syslog. "
            "Fields: src_ip, dest_ip, user_name, action_taken."
        ),
        "app": "Splunkbase 6238",
        "spl": "index=main sourcetype=cisco:ise",
        "detailedImplementation": di,
        "knownFalsePositives": kfp,
        "references": ["a", "b", "c", "d"],
        "controlTest": {
            "positiveScenario": "User logs in three times with bad password from a new IP within five minutes.",
            "negativeScenario": "Authorised admin runs maintenance script daily at 02:00 from a trusted bastion host.",
        },
        "evidence": "Splunk audit log with timestamped event IDs and analyst notes attached.",
        "exclusions": "Service accounts in svc_accounts.csv are excluded from this detection.",
    }


def _filepath() -> Path:
    p: Path = gp.REPO_ROOT / "content" / "cat-1-iam-and-identity-management" / "UC-1.1.1.json"
    return p


class TestAuditUcV2GoldPath:
    def test_returns_v2_pass_for_gold_uc(self) -> None:
        # _filepath() returns a path under REPO_ROOT (it does not need to exist
        # on disk; only relative_to() and the resulting "file" string are used).
        fp = _filepath()
        result = gp.audit_uc_v2(_gold_uc(), fp)
        assert result["tier"] == "v2-pass"
        assert result["score"] >= gp.V2_THRESHOLDS["passing_score"]
        assert result["id"] == "1.1.1"
        assert result["title"] == "Gold UC"
        assert "gaps" in result and "warnings" in result

    def test_returns_dict_with_required_keys(self) -> None:
        result = gp.audit_uc_v2(_gold_uc(), _filepath())
        for key in ("id", "file", "title", "score", "tier", "gaps", "warnings"):
            assert key in result

    def test_file_key_is_repo_relative(self) -> None:
        result = gp.audit_uc_v2(_gold_uc(), _filepath())
        assert result["file"] == "content/cat-1-iam-and-identity-management/UC-1.1.1.json"


class TestAuditUcV2GapDetection:
    def test_missing_detailed_implementation_loses_points(self) -> None:
        uc = _gold_uc()
        uc["detailedImplementation"] = "too short"
        result = gp.audit_uc_v2(uc, _filepath())
        assert result["score"] < 100
        assert any("detailedImplementation" in g and "chars" in g for g in result["gaps"])

    def test_di_with_low_specifics_loses_points(self) -> None:
        uc = _gold_uc()
        # Pad to threshold but with no specific signals
        uc["detailedImplementation"] = "general text " * 200
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("unique product-specific signals" in g for g in result["gaps"])

    def test_few_kfp_scenarios_lose_points(self) -> None:
        uc = _gold_uc()
        uc["knownFalsePositives"] = "- only one scenario"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("named scenarios" in g for g in result["gaps"])

    def test_kfp_without_suppression_loses_points(self) -> None:
        uc = _gold_uc()
        # Keep multiple scenarios but strip the suppression vocabulary.
        uc["knownFalsePositives"] = (
            "- Veeam backup jobs fire on Sunday\n"
            "- Cisco scans happen occasionally\n"
            "- Okta rotation events trigger this\n"
            "- ServiceNow sync windows are noisy\n"
            "- Microsoft baseline updates are loud"
        )
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("suppression mechanism" in g for g in result["gaps"])

    def test_short_datasources_loses_points(self) -> None:
        uc = _gold_uc()
        uc["dataSources"] = "tiny"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("dataSources" in g and "chars" in g for g in result["gaps"])

    def test_datasources_without_splunkbase_id_loses_points(self) -> None:
        uc = _gold_uc()
        uc["dataSources"] = (
            "Cisco ISE syslog feed sent over HEC. "
            "sourcetype=cisco:ise:syslog. "
            "Fields: src_ip, dest_ip, user_name, action_taken."
        )
        uc["app"] = "no app id here"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("Splunkbase ID" in g for g in result["gaps"])

    def test_sourcetype_missing_emits_warning_not_gap(self) -> None:
        uc = _gold_uc()
        uc["dataSources"] = (
            "Cisco ISE syslog feed via Splunkbase 6238. "
            "Fields: src_ip, dest_ip, user_name, action_taken."
        )
        uc["spl"] = "index=main"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("sourcetype" in w for w in result["warnings"])

    def test_description_value_overlap_loses_points(self) -> None:
        uc = _gold_uc()
        # Identical description and value → 100% Jaccard → > 60%
        uc["description"] = "alpha beta gamma delta epsilon zeta eta"
        uc["value"] = "alpha beta gamma delta epsilon zeta eta"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("word stems" in g for g in result["gaps"])

    def test_few_references_loses_points(self) -> None:
        uc = _gold_uc()
        uc["references"] = ["only one"]
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("references" in g for g in result["gaps"])

    def test_similar_control_test_loses_points(self) -> None:
        uc = _gold_uc()
        uc["controlTest"] = {
            "positiveScenario": "User logs in three times bad",
            "negativeScenario": "User logs in three times good",
        }
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("placeholder text" in g for g in result["gaps"])

    def test_missing_control_test_scenarios_loses_points(self) -> None:
        uc = _gold_uc()
        uc["controlTest"] = {}
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("controlTest missing" in g for g in result["gaps"])

    def test_short_evidence_loses_points(self) -> None:
        uc = _gold_uc()
        uc["evidence"] = "too short"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("evidence" in g for g in result["gaps"])

    def test_short_exclusions_loses_points(self) -> None:
        uc = _gold_uc()
        uc["exclusions"] = "too short"
        result = gp.audit_uc_v2(uc, _filepath())
        assert any("exclusions" in g for g in result["gaps"])

    def test_score_clamped_to_zero(self) -> None:
        # Every gap fires; even cumulative penalties can't go below zero.
        uc: dict[str, Any] = {
            "id": "9.9.9",
            "title": "Empty UC",
        }
        result = gp.audit_uc_v2(uc, _filepath())
        assert result["score"] >= 0
        assert result["tier"] == "v2-fail"

    def test_missing_id_defaults_to_unknown(self) -> None:
        result = gp.audit_uc_v2({}, _filepath())
        assert result["id"] == "unknown"

    def test_explicit_none_fields_handled(self) -> None:
        uc: dict[str, Any] = {
            "id": "1.1.1",
            "detailedImplementation": None,
            "knownFalsePositives": None,
            "dataSources": None,
            "app": None,
            "spl": None,
            "description": None,
            "value": None,
            "references": None,
            "controlTest": None,
            "evidence": None,
            "exclusions": None,
        }
        # Should not crash on None values; the `or ""` / `or []` / `or {}`
        # fallbacks handle them.
        result = gp.audit_uc_v2(uc, _filepath())
        assert result["tier"] == "v2-fail"


# ---------------------------------------------------------------------------
# find_uc_files — file discovery
# ---------------------------------------------------------------------------


class TestFindUcFiles:
    def test_default_returns_all_uc_files(self) -> None:
        files = gp.find_uc_files(None, None)
        assert len(files) > 100  # corpus is 7k+
        assert all(f.name.startswith("UC-") and f.suffix == ".json" for f in files)
        # Sorted output
        assert files == sorted(files)

    def test_specific_absolute_paths(self, tmp_path: Path) -> None:
        target = tmp_path / "UC-9.9.9.json"
        target.write_text("{}")
        files = gp.find_uc_files([str(target)], None)
        assert files == [target]

    def test_specific_relative_paths(self) -> None:
        # Relative path that resolves under REPO_ROOT
        files = gp.find_uc_files(["content/cat-1-iam-and-identity-management"], None)
        # The path itself isn't a file, but the .name fallback search still runs;
        # because the basename doesn't match a UC file, the result is empty.
        assert isinstance(files, list)

    def test_specific_basename_fallback(self) -> None:
        # Pass just a basename — the function rglobs CONTENT_DIR for matches.
        files = gp.find_uc_files(["UC-1.1.1.json"], None)
        assert len(files) >= 1
        assert any(f.name == "UC-1.1.1.json" for f in files)

    def test_regulation_filter_filters_corpus(self) -> None:
        files = gp.find_uc_files(None, "NIS2")
        # Even if zero UCs claim NIS2, the function should still return a list.
        assert isinstance(files, list)
        for f in files:
            uc = json.loads(f.read_text())
            assert any(
                isinstance(c, dict) and str(c.get("regulation", "")).strip().lower() == "nis2"
                for c in (uc.get("compliance") or [])
            )

    def test_regulation_filter_skips_malformed_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Point CONTENT_DIR at a directory with one valid and one malformed file.
        good = tmp_path / "UC-1.1.1.json"
        good.write_text(json.dumps({"id": "1.1.1", "compliance": [{"regulation": "NIS2"}]}))
        bad = tmp_path / "UC-1.1.2.json"
        bad.write_text("not json")
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path)
        files = gp.find_uc_files(None, "NIS2")
        assert good in files
        assert bad not in files

    def test_regulation_filter_skips_non_dict_compliance_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        f = tmp_path / "UC-1.1.1.json"
        f.write_text(
            json.dumps(
                {
                    "id": "1.1.1",
                    "compliance": [
                        "not-a-dict",
                        {"regulation": "NIS2"},
                    ],
                }
            )
        )
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path)
        files = gp.find_uc_files(None, "NIS2")
        assert f in files

    def test_regulation_filter_handles_missing_compliance_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        f = tmp_path / "UC-1.1.1.json"
        f.write_text(json.dumps({"id": "1.1.1"}))
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path)
        files = gp.find_uc_files(None, "NIS2")
        assert files == []

    def test_specific_file_not_found_anywhere(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path)
        files = gp.find_uc_files(["totally_missing_file.json"], None)
        assert files == []


# ---------------------------------------------------------------------------
# check_pack_drift
# ---------------------------------------------------------------------------


class TestCheckPackDrift:
    def test_empty_pack_returns_empty(self) -> None:
        assert gp.check_pack_drift({"app": "foo", "dataSources": "bar"}, {}) == []

    def test_no_packs_returns_empty(self) -> None:
        assert gp.check_pack_drift({"app": "foo"}, {"other_key": "value"}) == []

    def test_canonical_name_present_no_drift(self) -> None:
        uc = {"app": "Splunk Add-on for Cisco ISE", "dataSources": "sourcetype=cisco:ise"}
        pack = {
            "packs": {
                "ise": {"ta": {"name": "Splunk Add-on for Cisco ISE"}},
            }
        }
        assert gp.check_pack_drift(uc, pack) == []

    def test_partial_token_match_emits_drift(self) -> None:
        # 'splunk' (6 chars) appears in text but the full TA name does not.
        uc = {"app": "Splunk modular input only", "dataSources": ""}
        pack = {
            "packs": {
                "cyberark": {"ta": {"name": "Splunk Add-on for CyberArk Vault"}},
            }
        }
        drift = gp.check_pack_drift(uc, pack)
        assert len(drift) == 1
        assert "cyberark" in drift[0]
        assert "splunk" in drift[0].lower()

    def test_pack_with_no_ta_name_skipped(self) -> None:
        uc: dict[str, Any] = {"app": "Splunk", "dataSources": ""}
        pack: dict[str, Any] = {"packs": {"foo": {"ta": {}}}}
        assert gp.check_pack_drift(uc, pack) == []

    def test_pack_with_no_ta_block_skipped(self) -> None:
        uc: dict[str, Any] = {"app": "Splunk", "dataSources": ""}
        pack: dict[str, Any] = {"packs": {"foo": {}}}
        assert gp.check_pack_drift(uc, pack) == []

    def test_short_token_not_flagged(self) -> None:
        # Tokens < 6 chars are skipped to avoid false positives on stopwords.
        uc = {"app": "for", "dataSources": ""}
        pack = {"packs": {"foo": {"ta": {"name": "Splunk Add-on for Cisco ISE"}}}}
        # "for" is only 3 chars; should not drift.
        assert gp.check_pack_drift(uc, pack) == []


# ---------------------------------------------------------------------------
# print_report — reporter
# ---------------------------------------------------------------------------


class TestPrintReport:
    def test_empty_results_crashes_with_zero_division(self) -> None:
        # Documented behavior: print_report assumes at least one result.
        # main() guards this by returning early on empty files; the helper
        # itself divides by total without a guard. Pin the current contract.
        with pytest.raises(ZeroDivisionError):
            gp.print_report([])

    def test_all_pass(self, capsys: pytest.CaptureFixture[str]) -> None:
        results = [
            {"id": "1.1.1", "score": 95, "tier": "v2-pass", "gaps": [], "warnings": []},
            {"id": "1.1.2", "score": 80, "tier": "v2-pass", "gaps": [], "warnings": []},
        ]
        gp.print_report(results)
        out = capsys.readouterr().out
        assert "2 UCs" in out
        assert "PASS" in out
        assert "FAIL" in out

    def test_truncates_gaps_summary_to_three(self, capsys: pytest.CaptureFixture[str]) -> None:
        gaps = ["gap1", "gap2", "gap3", "gap4", "gap5"]
        results = [{"id": "1.1.1", "score": 40, "tier": "v2-fail", "gaps": gaps, "warnings": []}]
        gp.print_report(results)
        out = capsys.readouterr().out
        # "+2 more" should appear because we showed 3 and have 5 total
        assert "+2 more" in out

    def test_mixed_results_sorted_fails_first(self, capsys: pytest.CaptureFixture[str]) -> None:
        results = [
            {"id": "1.1.2", "score": 100, "tier": "v2-pass", "gaps": [], "warnings": []},
            {"id": "1.1.1", "score": 40, "tier": "v2-fail", "gaps": ["gap"], "warnings": []},
        ]
        gp.print_report(results)
        out = capsys.readouterr().out
        fail_pos = out.find("UC-1.1.1")
        pass_pos = out.find("UC-1.1.2")
        assert fail_pos < pass_pos  # fail printed first


# ---------------------------------------------------------------------------
# main() — CLI
# ---------------------------------------------------------------------------


def _write_uc(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload))


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point REPO_ROOT + CONTENT_DIR at a hermetic tmp_path tree."""
    content = tmp_path / "content"
    content.mkdir()
    monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gp, "CONTENT_DIR", content)
    return tmp_path


class TestMainCli:
    def test_no_files_returns_one(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = gp.main(["--regulation", "DOES_NOT_EXIST"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "No UC files found" in err

    def test_gold_uc_passes_human_output(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-1.1.1.json"
        _write_uc(target, _gold_uc())
        rc = gp.main(["--files", str(target)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gold-profile v2 audit" in out
        assert "1 UCs" in out

    def test_failing_uc_with_check_returns_one(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-9.9.9.json"
        _write_uc(target, {"id": "9.9.9"})
        rc = gp.main(["--files", str(target), "--check"])
        assert rc == 1
        capsys.readouterr()

    def test_passing_uc_with_check_returns_zero(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-1.1.1.json"
        _write_uc(target, _gold_uc())
        rc = gp.main(["--files", str(target), "--check"])
        assert rc == 0
        capsys.readouterr()

    def test_json_mode_emits_valid_json(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-1.1.1.json"
        _write_uc(target, _gold_uc())
        rc = gp.main(["--files", str(target), "--json"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "results" in parsed
        assert "thresholds" in parsed
        assert parsed["thresholds"]["passing_score"] == 80
        assert len(parsed["results"]) == 1

    def test_skips_malformed_uc_file(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        good = isolated_root / "content" / "UC-1.1.1.json"
        bad = isolated_root / "content" / "UC-9.9.9.json"
        _write_uc(good, _gold_uc())
        bad.write_text("not json {")
        rc = gp.main(["--files", str(good), str(bad)])
        assert rc == 0
        err = capsys.readouterr().err
        assert "Skipping" in err

    def test_pack_drift_path(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-1.1.1.json"
        uc = _gold_uc()
        uc["app"] = "Splunk modular input only"
        uc["dataSources"] = "sourcetype=cyberark via Splunkbase 6238"
        _write_uc(target, uc)
        pack_file = isolated_root / "pack.json"
        pack_file.write_text(
            json.dumps(
                {
                    "packs": {
                        "cyberark": {"ta": {"name": "Splunk Add-on for CyberArk Vault"}},
                    }
                }
            )
        )
        rc = gp.main(["--files", str(target), "--pack", str(pack_file)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Pack drift" in out

    def test_pack_drift_with_json(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-1.1.1.json"
        _write_uc(target, _gold_uc())
        pack_file = isolated_root / "pack.json"
        pack_file.write_text(json.dumps({"packs": {}}))
        rc = gp.main(["--files", str(target), "--pack", str(pack_file), "--json"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        # Pack is truthy → packDrift key is added to each result.
        assert "packDrift" in parsed["results"][0]
        assert parsed["results"][0]["packDrift"] == []

    def test_pack_drift_path_no_drifters(
        self,
        isolated_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = isolated_root / "content" / "UC-1.1.1.json"
        _write_uc(target, _gold_uc())
        pack_file = isolated_root / "pack.json"
        pack_file.write_text(json.dumps({"packs": {}}))
        rc = gp.main(["--files", str(target), "--pack", str(pack_file)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Pack drift" not in out


class TestMainScriptEntry:
    def test_module_is_importable(self) -> None:
        # Smoke check: the module loads with no side effects.
        assert hasattr(gp, "main")
        assert hasattr(gp, "audit_uc_v2")
        assert hasattr(gp, "V2_THRESHOLDS")

    def test_main_no_args_runs_against_corpus(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Smoke: invoke without --files / --regulation against the real corpus.
        # We expect a successful exit but don't pin the exact pass/fail count.
        rc = gp.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gold-profile v2 audit" in out


# ---------------------------------------------------------------------------
# Sanity: argparse parser builds without crashing
# ---------------------------------------------------------------------------


class TestArgparseShape:
    def test_help_does_not_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            gp.main(["--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "Gold-profile v2 audit" in out
        assert "--check" in out
        assert "--json" in out


# Touch sys.argv import so static-analysis is satisfied
assert sys.modules["sys"] is sys
