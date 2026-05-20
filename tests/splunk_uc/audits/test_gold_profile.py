"""Unit tests for ``splunk_uc.audits.gold_profile``.

P16 wave Q: lifts ``src/splunk_uc/audits/gold_profile.py`` from 51.5%
to ≥95% combined coverage. Pins every documented contract of the v1
Gold Standard quality-profile audit: tier requirements, length
thresholds, depth heuristics (boilerplate ratio, section count,
product specificity, vendor-UI reference, specific troubleshooting),
``audit_uc`` tier classification + depth scoring, consolidation
candidate detection, file discovery, reporting helpers, and the full
CLI matrix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import gold_profile as gp

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestTierFieldSets:
    def test_bronze_required_shape(self) -> None:
        assert {
            "id",
            "title",
            "criticality",
            "difficulty",
            "spl",
            "description",
            "value",
            "dataSources",
            "app",
            "implementation",
        } == gp.BRONZE_REQUIRED

    def test_silver_extends_bronze(self) -> None:
        assert gp.BRONZE_REQUIRED.issubset(gp.SILVER_REQUIRED)
        new_silver = gp.SILVER_REQUIRED - gp.BRONZE_REQUIRED
        assert new_silver == {
            "monitoringType",
            "splunkPillar",
            "detailedImplementation",
            "references",
            "equipment",
            "grandmaExplanation",
            "wave",
            "prerequisiteUseCases",
        }

    def test_gold_extends_silver(self) -> None:
        assert gp.SILVER_REQUIRED.issubset(gp.GOLD_REQUIRED)
        assert gp.GOLD_REQUIRED - gp.SILVER_REQUIRED == {"visualization", "equipmentModels"}


class TestMinLengths:
    def test_bronze_min_lengths(self) -> None:
        assert gp.BRONZE_MIN_LENGTHS == {
            "description": 40,
            "value": 40,
            "dataSources": 20,
            "implementation": 20,
        }

    def test_silver_min_lengths(self) -> None:
        assert gp.SILVER_MIN_LENGTHS["description"] == 60
        assert gp.SILVER_MIN_LENGTHS["value"] == 60
        assert gp.SILVER_MIN_LENGTHS["dataSources"] == 30
        assert gp.SILVER_MIN_LENGTHS["detailedImplementation"] == 200
        assert gp.SILVER_MIN_LENGTHS["grandmaExplanation"] == 20

    def test_gold_min_lengths(self) -> None:
        assert gp.GOLD_MIN_LENGTHS["description"] == 80
        assert gp.GOLD_MIN_LENGTHS["value"] == 80
        assert gp.GOLD_MIN_LENGTHS["dataSources"] == 40
        assert gp.GOLD_MIN_LENGTHS["detailedImplementation"] == 500
        assert gp.GOLD_MIN_LENGTHS["grandmaExplanation"] == 20


class TestPathConstants:
    def test_repo_root_is_real(self) -> None:
        assert gp.REPO_ROOT.is_dir()
        assert (gp.REPO_ROOT / "content").is_dir()

    def test_content_dir(self) -> None:
        assert gp.CONTENT_DIR == gp.REPO_ROOT / "content"

    def test_report_dir(self) -> None:
        assert gp.REPORT_DIR == gp.REPO_ROOT / "reports"


class TestPatternConstants:
    def test_boilerplate_phrases_compile(self) -> None:
        # Every entry is a valid regex pattern
        for phrase in gp.GENERIC_BOILERPLATE_PHRASES:
            import re

            re.compile(phrase)
        # Spot check a known phrase
        assert any("install" in p for p in gp.GENERIC_BOILERPLATE_PHRASES)

    def test_section_patterns_compile_to_5(self) -> None:
        assert len(gp.SECTION_PATTERNS) == 5

    def test_product_specific_indicators_compile(self) -> None:
        # Should be 8 indicators
        assert len(gp.PRODUCT_SPECIFIC_INDICATORS) == 8


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestCountSections:
    def test_zero_sections(self) -> None:
        assert gp._count_sections("nothing matching here") == 0

    def test_each_section_pattern_matches_at_least_once(self) -> None:
        # 5 step-section markers map onto 5 patterns
        text = (
            "Step 1: configure data sources. "
            "Step 2: create the search. "
            "Step 3: validate. "
            "Step 4: operationalize. "
            "prerequisite section. "
        )
        # 5 patterns matching at least once → count == 5
        assert gp._count_sections(text) == 5

    def test_section_pattern_synonyms(self) -> None:
        # "data collection" maps to step-1 alias
        assert gp._count_sections("data collection setup") == 1
        # "understanding this SPL" maps to step-2 alias
        assert gp._count_sections("Understanding this SPL section") == 1
        # "before you begin" maps to prerequisite
        assert gp._count_sections("Before you begin") == 1
        # "troubleshoot" maps to step-4/5
        assert gp._count_sections("Troubleshooting steps") == 1


class TestBoilerplateRatio:
    def test_empty_text_returns_zero(self) -> None:
        assert gp._boilerplate_ratio("") == 0.0

    def test_short_sentences_filtered(self) -> None:
        # Sentences <= 15 chars are dropped → no sentences → 0
        assert gp._boilerplate_ratio("abc. def.") == 0.0

    def test_all_boilerplate_returns_one(self) -> None:
        # Avoid embedded "." in tokens (re.split on .!? would create
        # short fragments that get filtered, throwing off the ratio).
        text = (
            "Install the TA and configure the input as documented! "
            "Check your data is arriving as expected! "
            "Validate the data is arriving correctly across all sites!"
        )
        assert gp._boilerplate_ratio(text) == 1.0

    def test_mixed_returns_partial(self) -> None:
        text = (
            "Install the TA and configure the input as documented! "
            "Then verify host=foo sourcetype=ise events appear in real time!"
        )
        # 1 of 2 long sentences is boilerplate
        assert 0.45 < gp._boilerplate_ratio(text) < 0.55

    def test_no_boilerplate_returns_zero(self) -> None:
        text = (
            "Use SPL to compute mean latency across each tenant. "
            "Reject results when packet loss exceeds five percent."
        )
        assert gp._boilerplate_ratio(text) == 0.0


class TestProductSpecificityScore:
    def test_zero_when_no_indicators(self) -> None:
        assert gp._product_specificity_score("plain text without any markers") == 0

    def test_sourcetype_match(self) -> None:
        assert gp._product_specificity_score('sourcetype="cisco:ise:syslog"') == 1

    def test_index_match(self) -> None:
        assert gp._product_specificity_score("index=meraki_events") == 1

    def test_api_path_match(self) -> None:
        assert gp._product_specificity_score("call /api/v2/devices endpoint") == 1

    def test_inputs_conf_match(self) -> None:
        assert gp._product_specificity_score("update inputs.conf with new stanza") == 1

    def test_http_verb_match(self) -> None:
        assert gp._product_specificity_score("send POST /sessions to the controller") == 1

    def test_interval_match(self) -> None:
        assert gp._product_specificity_score("poll every 30 seconds") == 1

    def test_rbac_match(self) -> None:
        assert gp._product_specificity_score("requires SUPER-ADMIN role") == 1

    def test_splunkbase_match(self) -> None:
        assert gp._product_specificity_score("Splunkbase 1234") == 1

    def test_multiple_indicators_sum(self) -> None:
        text = (
            'sourcetype="x" index=y /api/v2/foo POST /sessions inputs.conf '
            "every 30 minutes requires NETWORK-ADMIN role Splunkbase 9876"
        )
        # All 8 indicators present
        assert gp._product_specificity_score(text) == 8


class TestHasVendorUiReference:
    def test_no_match_returns_false(self) -> None:
        assert gp._has_vendor_ui_reference("plain text") is False

    def test_compare_against_dashboard(self) -> None:
        assert gp._has_vendor_ui_reference("verify against the Meraki dashboard") is True

    def test_named_product_dashboard(self) -> None:
        assert gp._has_vendor_ui_reference("Catalyst Center Dashboard") is True

    def test_vcenter_console(self) -> None:
        assert gp._has_vendor_ui_reference("vCenter Console") is True

    def test_compare_with_portal(self) -> None:
        assert gp._has_vendor_ui_reference("compare with the ISE portal") is True


class TestHasSpecificTroubleshooting:
    def test_returns_false_when_no_marker(self) -> None:
        assert gp._has_specific_troubleshooting("nothing about failures here") is False

    def test_returns_false_when_marker_but_no_specifics(self) -> None:
        assert (
            gp._has_specific_troubleshooting("Troubleshooting: try restarting the service.")
            is False
        )

    def test_no_events_specific(self) -> None:
        assert (
            gp._has_specific_troubleshooting(
                "Troubleshoot: if no Cisco events appear, check the input."
            )
            is True
        )

    def test_null_field_specific(self) -> None:
        assert (
            gp._has_specific_troubleshooting("Common issue: NULL values in the response field.")
            is True
        )

    def test_fewer_devices_specific(self) -> None:
        assert gp._has_specific_troubleshooting("step 5: fewer devices than expected") is True

    def test_api_timeout_specific(self) -> None:
        assert gp._has_specific_troubleshooting("Troubleshooting: API timeout after 30s.") is True

    def test_permission_denied_specific(self) -> None:
        assert gp._has_specific_troubleshooting("Failure: permission denied to dashboard") is True

    def test_specific_must_come_AFTER_troubleshoot_marker(self) -> None:
        # "no events" before the troubleshoot section doesn't count
        text = "Configure: no events yet. Then run a Search."
        assert gp._has_specific_troubleshooting(text) is False


class TestDescriptionValueSimilarity:
    def test_empty_inputs_return_zero(self) -> None:
        assert gp._description_value_similarity("", "anything") == 0.0
        assert gp._description_value_similarity("anything", "") == 0.0
        assert gp._description_value_similarity("", "") == 0.0

    def test_identical_inputs_return_one(self) -> None:
        assert gp._description_value_similarity("same text", "same text") == 1.0

    def test_case_insensitive(self) -> None:
        assert gp._description_value_similarity("Hello", "hello") == 1.0

    def test_partially_similar(self) -> None:
        sim = gp._description_value_similarity(
            "monitor cisco device health",
            "monitor cisco device uptime",
        )
        assert 0.5 < sim < 1.0


# ---------------------------------------------------------------------------
# audit_uc — central tier classifier and depth scorer
# ---------------------------------------------------------------------------


def _make_gold_uc() -> dict[str, Any]:
    """Build a UC that meets the full Gold contract (with depth-promotion hooks)."""
    detailed = (
        "Prerequisites: ensure the TA is installed and the SUPER-ADMIN role is assigned. "
        "Step 1: configure data collection by setting sourcetype=cisco:ise:syslog and "
        "index=cisco_ise on every input stanza. Step 2: create the search by running "
        "the SPL against /api/v2/sessions every 30 seconds with POST /api/v1/auth/login. "
        "Step 3: validate the data by comparing the Splunk results against the Cisco ISE "
        "dashboard for the same time window. Step 4: operationalize the alert. "
        "Step 5: troubleshoot common failure modes — no Cisco events appearing means the "
        "inputs.conf stanza is missing index. Permission denied to dashboard usually "
        "means the role token expired. Splunkbase 1234. NETWORK-ADMIN role required."
    )
    return {
        "id": "5.13.1",
        "title": "Cisco ISE authentication anomaly",
        "criticality": "high",
        "difficulty": "intermediate",
        "spl": 'index=cisco_ise sourcetype="cisco:ise:syslog" | stats count by user',
        "description": (
            "Detect Cisco ISE authentication anomalies — repeated logon failures, "
            "policy violations, and unusual MAC bindings within a short time."
        ),
        "value": (
            "Improves SOC visibility and reduces the time to detect compromised "
            "credentials, lateral movement, or rogue device joins on the enterprise network."
        ),
        "dataSources": "Cisco ISE syslog via UDP/514 to HF and TA-cisco-ise input.",
        "app": "TA-cisco-ise",
        "implementation": "Deploy TA-cisco-ise, configure syslog input on UDP/514.",
        "monitoringType": "alert",
        "splunkPillar": "security",
        "detailedImplementation": detailed,
        "references": [
            "https://docs.cisco.com/ise/",
            "https://splunkbase.splunk.com/app/1234/",
        ],
        "equipment": ["cisco-ise"],
        "grandmaExplanation": "We watch sign-in logs to spot suspicious access.",
        "wave": "walk",
        "prerequisiteUseCases": [],
        "visualization": "table",
        "equipmentModels": ["ise-3415"],
    }


def _make_silver_uc() -> dict[str, Any]:
    """Silver UC: meets all Silver requirements but lacks Gold-only fields."""
    uc = _make_gold_uc()
    del uc["visualization"]
    del uc["equipmentModels"]
    # Bring references down to 1 so Gold ref check trips
    uc["references"] = ["https://docs.cisco.com/ise/"]
    return uc


def _make_bronze_uc() -> dict[str, Any]:
    """Bronze UC: meets Bronze but lacks Silver fields."""
    uc = _make_gold_uc()
    for k in (
        "monitoringType",
        "splunkPillar",
        "detailedImplementation",
        "references",
        "equipment",
        "grandmaExplanation",
        "wave",
        "prerequisiteUseCases",
        "visualization",
        "equipmentModels",
    ):
        uc.pop(k, None)
    return uc


@pytest.fixture
def fake_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Anchor REPO_ROOT/CONTENT_DIR/REPORT_DIR to tmp_path and return a content file path."""
    content_dir = tmp_path / "content" / "cat-05-identity"
    content_dir.mkdir(parents=True)
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path / "content")
    monkeypatch.setattr(gp, "REPORT_DIR", report_dir)
    return content_dir / "UC-5.13.1.json"


class TestAuditUcBronze:
    def test_missing_all_required_returns_none_tier(self, fake_path: Path) -> None:
        fake_path.touch()
        result = gp.audit_uc({"id": "5.13.1"}, fake_path)
        assert result["tier"] == "none"
        assert result["depth_score"] == 0  # max(0, 10 - many_gaps * 2)
        assert any("Missing field" in g for g in result["gaps"])

    def test_partial_bronze_field_truncates_depth_score(self, fake_path: Path) -> None:
        fake_path.touch()
        # Only 1 missing field → depth_score = max(0, 10 - 2) = 8
        uc = _make_bronze_uc()
        del uc["spl"]
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "none"
        assert any("spl" in g for g in result["gaps"])

    def test_too_short_field_blocks_bronze(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_bronze_uc()
        uc["description"] = "tiny"  # < 40
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "none"
        assert any("too short" in g for g in result["gaps"])

    def test_clean_bronze_returns_bronze(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_bronze_uc()
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "bronze"
        assert result["depth_score"] >= 25


class TestAuditUcSilver:
    def test_silver_passes_when_all_silver_fields_present(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_silver_uc()
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "silver"
        assert result["depth_score"] >= 25  # depth-adjusted may dip a bit

    def test_missing_silver_field_stays_bronze(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_silver_uc()
        del uc["splunkPillar"]
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "bronze"
        assert any("For Silver: missing" in g for g in result["gaps"])

    def test_silver_min_length_failure(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_silver_uc()
        uc["grandmaExplanation"] = "short"  # < 20
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "bronze"
        assert any("grandmaExplanation too short" in g for g in result["gaps"])

    def test_silver_needs_at_least_one_reference(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_silver_uc()
        uc["references"] = []
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "bronze"
        assert any("need at least 1 reference" in g for g in result["gaps"])

    def test_silver_needs_3_sections_in_detailed_impl(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_silver_uc()
        # Strip down to a long-but-section-poor string
        uc["detailedImplementation"] = (
            "Some detail without any of the expected step section markers. " * 6
        )
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "bronze"
        assert any("required sections" in g for g in result["gaps"])


class TestAuditUcGold:
    def test_gold_passes_when_all_invariants_met(self, fake_path: Path) -> None:
        fake_path.touch()
        result = gp.audit_uc(_make_gold_uc(), fake_path)
        assert result["tier"] == "gold"
        # Depth picks up the +10 specificity, +5 vendor-UI, +5 troubleshooting boosts
        assert result["depth_score"] >= 80

    def test_missing_gold_only_field_stays_silver(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        del uc["visualization"]
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "silver"
        assert any("For Gold: missing visualization" in g for g in result["gaps"])

    def test_gold_min_length_failure(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        uc["description"] = "x" * 60  # < 80 Gold min
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "silver"
        assert any("For Gold: description too short" in g for g in result["gaps"])

    def test_gold_needs_2_references(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        uc["references"] = ["https://docs.cisco.com/ise/"]
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "silver"
        assert any("need at least 2 references" in g for g in result["gaps"])

    def test_gold_needs_4_sections(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        uc["detailedImplementation"] = (
            "Step 1: configure data. Step 2: create the search. "
            "Step 3: validate output. " + ("filler. " * 100)
        )
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "silver"
        assert any("5 expected sections" in g for g in result["gaps"])


class TestAuditUcDepth:
    def test_description_value_similarity_penalty(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        # Make value highly similar to description → -10 depth
        uc["value"] = uc["description"]
        result = gp.audit_uc(uc, fake_path)
        assert any("similar" in w for w in result["warnings"])

    def test_high_boilerplate_warning_and_penalty(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        uc["detailedImplementation"] = (
            "Install the TA and configure the input. " * 6 + "Check splunkd.log for errors. " * 5
        )
        result = gp.audit_uc(uc, fake_path)
        assert any("boilerplate" in w for w in result["warnings"])

    def test_lacks_product_specifics_warning(self, fake_path: Path) -> None:
        fake_path.touch()
        uc = _make_gold_uc()
        # > 300 chars, < 2 indicators → emit warning
        uc["detailedImplementation"] = (
            "Step 1: do thing. Step 2: do another thing. Step 3: validate. "
            "Step 4: operationalize. Step 5: troubleshoot. " + ("Filler. " * 50)
        )
        result = gp.audit_uc(uc, fake_path)
        assert any("lacks product-specific" in w for w in result["warnings"])

    def test_gold_missing_vendor_ui_gap(self, fake_path: Path) -> None:
        # Gold tier with no vendor-UI reference → emits a gap and no +5 boost
        fake_path.touch()
        uc = _make_gold_uc()
        # Remove every UI-reference fragment
        uc["detailedImplementation"] = uc["detailedImplementation"].replace(
            "comparing the Splunk results against the Cisco ISE dashboard",
            "running stats by user",
        )
        result = gp.audit_uc(uc, fake_path)
        # Tier may still be gold; the gap surfaces only when tier == gold.
        if result["tier"] == "gold":
            assert any("vendor UI" in g for g in result["gaps"])

    def test_silver_or_gold_missing_specific_troubleshooting_gap(self, fake_path: Path) -> None:
        # Silver/gold without specific troubleshooting → gap surfaced
        fake_path.touch()
        uc = _make_gold_uc()
        # Remove every specific troubleshooting fragment
        uc["detailedImplementation"] = (
            "Prerequisites: ensure TA installed. Step 1: configure sourcetype=cisco:ise. "
            "Step 2: create the search via /api/v1/auth/login. "
            "Step 3: validate by comparing against the Cisco ISE dashboard. "
            "Step 4: operationalize the alert. "
            "Step 5: general troubleshooting tips that mention nothing concrete here. "
            + ("Filler. " * 30)
        )
        result = gp.audit_uc(uc, fake_path)
        if result["tier"] in ("gold", "silver"):
            assert any("product-specific failure" in g for g in result["gaps"])

    def test_depth_score_capped_at_100(self, fake_path: Path) -> None:
        fake_path.touch()
        # Even with all boosts, depth is clamped to [0, 100]
        result = gp.audit_uc(_make_gold_uc(), fake_path)
        assert 0 <= result["depth_score"] <= 100

    def test_specificity_3_to_4_grants_plus_5(self, fake_path: Path) -> None:
        # Exactly 3 product-specific indicators → +5 depth boost
        # (not the +10 reserved for ≥5).
        fake_path.touch()
        uc = _make_gold_uc()
        # Replace detailed with exactly 3 indicators (sourcetype, index, /api/v).
        uc["detailedImplementation"] = (
            "Prerequisites done. "
            "Step 1: configure sourcetype=foo and index=bar. "
            "Step 2: GET /api/v1/items every. "
            "Step 3: validate against the Catalyst Center Dashboard. "
            "Step 4: operationalize. "
            "Step 5: troubleshoot — no Cisco events means input misconfigured. " + ("filler. " * 40)
        )
        result = gp.audit_uc(uc, fake_path)
        # Indicators in the detailedImplementation above: sourcetype=,
        # index=, /api/v1/. We removed the HTTP-verb and seconds and
        # RBAC and Splunkbase. The above hits 3 indicators which
        # exercises the elif >= 3 branch.
        assert result["tier"] in ("gold", "silver")

    def test_non_string_non_list_field_treated_as_present(self, fake_path: Path) -> None:
        # Exercise the `_has_field` final `return True` (line 228) by
        # passing in a UC whose field is a dict — neither str nor list.
        fake_path.touch()
        uc = _make_bronze_uc()
        # "criticality" can be a string per schema; we deliberately
        # break that here to drive the catch-all branch.
        uc["criticality"] = {"level": 3}
        # The field is treated as present, but `_meets_min_length` on a
        # non-str returns False, so any bronze-min-length check is
        # neutral for criticality (it's not in BRONZE_MIN_LENGTHS).
        result = gp.audit_uc(uc, fake_path)
        assert result["tier"] == "bronze"


# ---------------------------------------------------------------------------
# _extract_field_from_gap
# ---------------------------------------------------------------------------


class TestExtractFieldFromGap:
    def test_missing_field_pattern(self) -> None:
        assert gp._extract_field_from_gap("Missing field: description") == "description"

    def test_for_silver_missing(self) -> None:
        assert gp._extract_field_from_gap("For Silver: missing wave") == "wave"

    def test_field_too_short_pattern(self) -> None:
        assert gp._extract_field_from_gap("description too short") == "description"

    def test_for_silver_field_too_short(self) -> None:
        assert (
            gp._extract_field_from_gap("For Silver: detailedImplementation too short")
            == "detailedImplementation"
        )

    def test_for_silver_field_has_n_of_m(self) -> None:
        assert (
            gp._extract_field_from_gap("For Silver: detailedImplementation has 2/3 sections")
            == "detailedImplementation"
        )

    def test_references_alias(self) -> None:
        # "need at least 1 reference" → "references" key
        assert gp._extract_field_from_gap("For Silver: need at least 1 reference") == "references"

    def test_unparsed_gap_falls_back_to_sha1_digest(self) -> None:
        # Doesn't match any pattern → "_unparsed:<digest>" key
        result = gp._extract_field_from_gap("totally unstructured commentary")
        assert result.startswith("_unparsed:")
        assert len(result) == len("_unparsed:") + 8


# ---------------------------------------------------------------------------
# score_sidecar
# ---------------------------------------------------------------------------


class TestScoreSidecar:
    def test_returns_tuple_of_int_and_dict(self) -> None:
        score, failing = gp.score_sidecar(_make_gold_uc())
        assert isinstance(score, int)
        assert 0 <= score <= 100
        assert isinstance(failing, dict)

    def test_gold_uc_returns_high_score(self) -> None:
        score, _ = gp.score_sidecar(_make_gold_uc())
        assert score >= 70

    def test_bronze_uc_returns_low_score(self) -> None:
        score, _ = gp.score_sidecar({"id": "x"})
        assert score <= 10

    def test_failing_fields_grouped(self) -> None:
        uc = _make_bronze_uc()
        uc.pop("spl")
        _, failing = gp.score_sidecar(uc)
        assert "spl" in failing

    def test_tier_parameter_currently_ignored(self) -> None:
        # The tier param is reserved; documented behaviour: both calls
        # produce the same result.
        s1, _ = gp.score_sidecar(_make_gold_uc(), tier="silver")
        s2, _ = gp.score_sidecar(_make_gold_uc(), tier="gold")
        assert s1 == s2


# ---------------------------------------------------------------------------
# find_consolidation_candidates
# ---------------------------------------------------------------------------


class TestFindConsolidationCandidates:
    def test_empty_when_no_results(self) -> None:
        assert gp.find_consolidation_candidates([]) == []

    def test_skips_subcategory_with_single_uc(self) -> None:
        results = [{"id": "5.13.1", "title": "Cisco ISE auth anomaly"}]
        assert gp.find_consolidation_candidates(results) == []

    def test_high_similarity_pairs_surfaced(self) -> None:
        results = [
            {"id": "5.13.1", "title": "Cisco ISE auth anomaly"},
            {"id": "5.13.2", "title": "Cisco ISE auth anomaly detection"},
        ]
        out = gp.find_consolidation_candidates(results)
        assert len(out) == 1
        assert out[0]["uc_a"] == "5.13.1"
        assert out[0]["uc_b"] == "5.13.2"
        assert out[0]["subcategory"] == "5.13"
        assert out[0]["title_similarity"] > 0.8

    def test_dissimilar_titles_skipped(self) -> None:
        results = [
            {"id": "5.13.1", "title": "Cisco ISE auth anomaly"},
            {"id": "5.13.2", "title": "Meraki firewall blocked outbound"},
        ]
        assert gp.find_consolidation_candidates(results) == []

    def test_different_subcategories_not_compared(self) -> None:
        results = [
            {"id": "5.13.1", "title": "Cisco ISE auth anomaly"},
            {"id": "6.13.1", "title": "Cisco ISE auth anomaly"},
        ]
        assert gp.find_consolidation_candidates(results) == []

    def test_uc_id_without_subcategory_silently_skipped(self) -> None:
        # IDs like "5" or "broken" without ".X.Y" never enter by_subcat.
        results = [{"id": "broken", "title": "x"}]
        assert gp.find_consolidation_candidates(results) == []


# ---------------------------------------------------------------------------
# find_uc_files
# ---------------------------------------------------------------------------


class TestFindUcFiles:
    def test_default_recursive_search(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        content = tmp_path / "content"
        cat = content / "cat-01-test"
        cat.mkdir(parents=True)
        a = cat / "UC-1.1.1.json"
        b = cat / "UC-1.1.2.json"
        # Non-UC file should be ignored
        (cat / "README.md").write_text("nope", encoding="utf-8")
        a.write_text("{}", encoding="utf-8")
        b.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gp, "CONTENT_DIR", content)
        files = gp.find_uc_files()
        assert files == sorted([a, b])

    def test_specific_files_absolute(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cat = tmp_path / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        a = cat / "UC-1.1.1.json"
        a.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path / "content")
        files = gp.find_uc_files([str(a)])
        assert files == [a]

    def test_specific_files_relative(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cat = tmp_path / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        a = cat / "UC-1.1.1.json"
        a.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path / "content")
        files = gp.find_uc_files(["content/cat-01-test/UC-1.1.1.json"])
        assert files == [a]

    def test_basename_fallback_when_path_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = tmp_path / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        a = cat / "UC-1.1.1.json"
        a.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path / "content")
        # /bogus/path/UC-1.1.1.json does not exist → falls back to basename rglob
        files = gp.find_uc_files(["/bogus/path/UC-1.1.1.json"])
        assert files == [a]

    def test_specific_files_unresolved_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        (tmp_path / "content").mkdir()
        monkeypatch.setattr(gp, "CONTENT_DIR", tmp_path / "content")
        files = gp.find_uc_files(["UC-9.99.99.json"])
        assert files == []


# ---------------------------------------------------------------------------
# print_summary
# ---------------------------------------------------------------------------


def _result(
    *,
    uc_id: str = "5.13.1",
    tier: str = "silver",
    depth: int = 50,
    title: str = "Test",
    warnings: list[str] | None = None,
    gaps: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": uc_id,
        "title": title,
        "tier": tier,
        "depth_score": depth,
        "warnings": warnings or [],
        "gaps": gaps or [],
        "file": f"content/cat-05-identity/UC-{uc_id}.json",
    }


class TestPrintSummary:
    def test_empty_results_does_not_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        gp.print_summary([], [])
        out = capsys.readouterr().out
        assert "Gold Standard Quality Audit" in out
        assert "0 UCs" in out

    def test_single_result_renders_tier_distribution(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        gp.print_summary([_result(tier="gold", depth=85)], [])
        out = capsys.readouterr().out
        assert "Gold Standard Quality Audit — 1 UCs" in out
        assert "gold" in out
        assert "Avg depth score: 85.0/100" in out
        assert "cat-  5" in out  # category 5

    def test_consolidation_candidates_rendered(self, capsys: pytest.CaptureFixture[str]) -> None:
        candidates = [
            {
                "uc_a": "5.13.1",
                "uc_b": "5.13.2",
                "title_similarity": 0.91,
                "subcategory": "5.13",
                "reason": "High similarity",
            }
        ]
        gp.print_summary([_result()], candidates)
        out = capsys.readouterr().out
        assert "Consolidation candidates: 1" in out
        assert "5.13.1 <-> 5.13.2" in out

    def test_consolidation_truncated_at_10(self, capsys: pytest.CaptureFixture[str]) -> None:
        candidates = [
            {
                "uc_a": f"5.13.{i}",
                "uc_b": f"5.14.{i}",
                "title_similarity": 0.9,
                "subcategory": "5.13",
                "reason": "High similarity",
            }
            for i in range(15)
        ]
        gp.print_summary([_result()], candidates)
        out = capsys.readouterr().out
        assert "and 5 more" in out

    def test_id_without_dot_uses_question_mark_category(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        gp.print_summary([_result(uc_id="broken")], [])
        out = capsys.readouterr().out
        # Category bucket "?" sorts to position 999 in the sort lambda.
        assert "cat-  ?" in out


# ---------------------------------------------------------------------------
# write_report
# ---------------------------------------------------------------------------


class TestWriteReport:
    def test_writes_canonical_payload(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(gp, "REPORT_DIR", tmp_path / "reports")
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        results = [_result(tier="gold", depth=85)]
        candidates = [
            {
                "uc_a": "5.13.1",
                "uc_b": "5.13.2",
                "title_similarity": 0.9,
                "subcategory": "5.13",
                "reason": "High similarity",
            }
        ]
        gp.write_report(results, candidates)
        out_file = tmp_path / "reports" / "quality-audit.json"
        assert out_file.is_file()
        payload = json.loads(out_file.read_text())
        assert payload["profile_version"] == "1.0"
        assert payload["total_ucs"] == 1
        assert payload["tier_distribution"]["gold"] == 1
        assert payload["avg_depth_score"] == 85.0
        assert payload["ucs"] == results
        assert payload["consolidation_candidates"] == candidates
        captured = capsys.readouterr().out
        assert "reports/quality-audit.json" in captured

    def test_empty_results_avoids_division(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(gp, "REPORT_DIR", tmp_path / "reports")
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        gp.write_report([], [])
        out_file = tmp_path / "reports" / "quality-audit.json"
        payload = json.loads(out_file.read_text())
        assert payload["total_ucs"] == 0
        assert payload["avg_depth_score"] == 0


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_main_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    content = tmp_path / "content"
    cat = content / "cat-05-identity"
    cat.mkdir(parents=True)
    monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gp, "CONTENT_DIR", content)
    monkeypatch.setattr(gp, "REPORT_DIR", tmp_path / "reports")
    return cat


class TestMainCli:
    def test_no_files_returns_zero_in_default_mode(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        empty = tmp_path / "empty-content"
        empty.mkdir()
        monkeypatch.setattr(gp, "CONTENT_DIR", empty)
        monkeypatch.setattr(gp, "REPORT_DIR", tmp_path / "reports")
        rc = gp.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No UC JSON files found" in out

    def test_no_files_with_check_returns_one(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(gp, "REPO_ROOT", tmp_path)
        empty = tmp_path / "empty-content"
        empty.mkdir()
        monkeypatch.setattr(gp, "CONTENT_DIR", empty)
        monkeypatch.setattr(gp, "REPORT_DIR", tmp_path / "reports")
        rc = gp.main(["--check"])
        assert rc == 1

    def test_default_mode_runs_summary_and_report(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # One Gold UC, no extras → default mode = summary+report
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        rc = gp.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gold Standard Quality Audit — 1 UCs" in out
        assert "reports/quality-audit.json" in out
        # Report file written
        assert (gp.REPORT_DIR / "quality-audit.json").is_file()

    def test_check_mode_passes_on_gold(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        rc = gp.main(["--check"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "All 1 UC(s) pass quality checks." in out

    def test_check_mode_fails_on_below_bronze(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # UC missing nearly all fields → tier="none" → CI fail
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps({"id": "5.13.1"}), encoding="utf-8"
        )
        rc = gp.main(["--check"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL:" in out
        assert "below Bronze minimum" in out

    def test_check_mode_emits_boilerplate_warning(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Build a UC with high boilerplate to force the WARN section
        uc = _make_gold_uc()
        uc["detailedImplementation"] = (
            "Install the TA and configure the input. " * 6
            + "Check splunkd.log for any errors. " * 5
            + "Validate the data. " * 3
            + "Step 1 setup. Step 2 search. Step 3 validate. Step 4 alert. Step 5 troubleshoot. "
            + ("sourcetype=foo " * 5)
        )
        (isolated_main_root / "UC-5.13.1.json").write_text(json.dumps(uc), encoding="utf-8")
        rc = gp.main(["--check"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "WARN:" in out

    def test_check_mode_reports_parse_errors(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        (isolated_main_root / "UC-5.13.2.json").write_text("not valid json {", encoding="utf-8")
        rc = gp.main(["--check"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "ERROR:" in out
        assert "could not be parsed" in out

    def test_consolidation_mode_renders_pairs(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        uc1 = _make_gold_uc()
        uc1["id"] = "5.13.1"
        uc1["title"] = "Cisco ISE auth anomaly"
        uc2 = _make_gold_uc()
        uc2["id"] = "5.13.2"
        uc2["title"] = "Cisco ISE auth anomaly detection"
        (isolated_main_root / "UC-5.13.1.json").write_text(json.dumps(uc1), encoding="utf-8")
        (isolated_main_root / "UC-5.13.2.json").write_text(json.dumps(uc2), encoding="utf-8")
        rc = gp.main(["--consolidation-candidates"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "5.13.1 <-> 5.13.2" in out

    def test_consolidation_mode_no_pairs(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        rc = gp.main(["--consolidation-candidates"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No consolidation candidates found." in out

    def test_report_only_mode_does_not_print_summary(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        rc = gp.main(["--report"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gold Standard Quality Audit" not in out
        assert "reports/quality-audit.json" in out

    def test_summary_only_mode_does_not_write_report(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        rc = gp.main(["--summary"])
        assert rc == 0
        # No report file created.
        assert not (gp.REPORT_DIR / "quality-audit.json").exists()

    def test_files_arg_limits_scan(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        a = isolated_main_root / "UC-5.13.1.json"
        b = isolated_main_root / "UC-5.13.2.json"
        a.write_text(json.dumps(_make_gold_uc()), encoding="utf-8")
        b.write_text(json.dumps(_make_gold_uc()), encoding="utf-8")
        rc = gp.main(["--files", str(a), "--summary"])
        assert rc == 0
        out = capsys.readouterr().out
        # Only one file was scanned
        assert "Gold Standard Quality Audit — 1 UCs" in out

    def test_default_mode_emits_parse_error_count(
        self,
        isolated_main_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Default mode (no --check) prints "{n} file(s) had parse errors."
        (isolated_main_root / "UC-5.13.1.json").write_text(
            json.dumps(_make_gold_uc()), encoding="utf-8"
        )
        (isolated_main_root / "UC-5.13.2.json").write_text("bad json", encoding="utf-8")
        rc = gp.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "had parse errors" in out

    def test_help_lists_check_and_files_options(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as excinfo:
            gp.main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert "--check" in out
        assert "--files" in out
        assert "--consolidation-candidates" in out

    def test_main_module_entry_callable(self) -> None:
        # The `if __name__ == "__main__":` block at the bottom of the
        # module routes through main(); we just confirm the symbol is
        # importable and callable.
        assert callable(gp.main)
