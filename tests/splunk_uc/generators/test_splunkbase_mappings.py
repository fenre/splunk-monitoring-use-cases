"""Unit tests for ``splunk_uc.generators.splunkbase_mappings``.

P16 wave R: lifts ``src/splunk_uc/generators/splunkbase_mappings.py``
from 9.3% to ≥95% combined coverage. Pins every documented contract
of the v9.0 ``splunkbaseApps[]`` mapping generator: constants
(`PREMIUM_APP_IDS`, role enums, the Splunkbase id regex); I/O helpers
(`_read_json`, `_write_json_preserving_style`, `_load_catalog`);
heuristics (`_extract_premium_app_ids`, `_extract_app_field_ids`,
`_equipment_match`, `_data_source_match`, `_build_proposal`); the
idempotency check (`_existing_human_signed`, `_arrays_equal`); UC
discovery (`_discover_ucs`); in-place update (`_update_uc_in_place`);
and the full CLI matrix (`--check`, `--write`, `--uc`, `--cat`,
`--quiet`, parse errors, no-matches, catalog-empty stderr).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from splunk_uc.generators import splunkbase_mappings as sbm

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestPathConstants:
    def test_repo_root_resolves(self) -> None:
        assert sbm.REPO_ROOT.is_dir()
        assert (sbm.REPO_ROOT / "content").is_dir()

    def test_content_dir(self) -> None:
        assert sbm.CONTENT_DIR == sbm.REPO_ROOT / "content"

    def test_catalog_path(self) -> None:
        assert sbm.CATALOG_PATH == sbm.REPO_ROOT / "data" / "splunkbase-catalog.json"

    def test_overrides_path(self) -> None:
        assert sbm.OVERRIDES_PATH == sbm.REPO_ROOT / "data" / "splunkbase-catalog-overrides.json"

    def test_uc_file_glob(self) -> None:
        assert sbm.UC_FILE_GLOB == "cat-*/UC-*.json"


class TestRoleConstants:
    def test_role_constants_strings(self) -> None:
        assert sbm.ROLE_PRIMARY == "primary"
        assert sbm.ROLE_DATA_SOURCE == "data-source"
        assert sbm.ROLE_PREMIUM == "premium"
        assert sbm.ROLE_OPTIONAL == "optional"


class TestPremiumAppIds:
    def test_canonical_ids_present(self) -> None:
        # Every canonical premium-app enum value mapped to a numeric id
        for name in (
            "splunk enterprise security",
            "splunk itsi",
            "splunk soar",
            "splunk user behavior analytics",
            "splunk uba",
            "splunk app for pci compliance",
            "splunk edge hub",
            "splunk machine learning toolkit",
            "splunk mltk",
        ):
            assert isinstance(sbm.PREMIUM_APP_IDS[name], int)
            assert sbm.PREMIUM_APP_IDS[name] > 0

    def test_itsi_and_itsi_long_share_id(self) -> None:
        assert (
            sbm.PREMIUM_APP_IDS["splunk itsi"]
            == sbm.PREMIUM_APP_IDS["splunk it service intelligence"]
        )

    def test_uba_and_uba_long_share_id(self) -> None:
        assert (
            sbm.PREMIUM_APP_IDS["splunk uba"]
            == sbm.PREMIUM_APP_IDS["splunk user behavior analytics"]
        )

    def test_mltk_and_mltk_long_share_id(self) -> None:
        assert (
            sbm.PREMIUM_APP_IDS["splunk mltk"]
            == sbm.PREMIUM_APP_IDS["splunk machine learning toolkit"]
        )


class TestSplunkbaseIdRe:
    def test_matches_capitalized_splunkbase_prefix(self) -> None:
        m = sbm.SPLUNKBASE_ID_RE.search("requires Splunkbase 1234")
        assert m is not None
        assert m.group(1) == "1234"

    def test_matches_lowercase_splunkbase_prefix(self) -> None:
        m = sbm.SPLUNKBASE_ID_RE.search("see splunkbase 9876")
        assert m is not None
        assert m.group(1) == "9876"

    def test_matches_url_form(self) -> None:
        m = sbm.SPLUNKBASE_ID_RE.search("https://splunkbase.splunk.com/app/4321")
        assert m is not None
        assert m.group(1) == "4321"

    def test_rejects_2_or_1_digit_ids(self) -> None:
        assert sbm.SPLUNKBASE_ID_RE.search("Splunkbase 9") is None
        # Min length is 2 → "Splunkbase 10" is valid.
        assert sbm.SPLUNKBASE_ID_RE.search("Splunkbase 10") is not None

    def test_rejects_7_digit_ids(self) -> None:
        # Cap is 6 → "Splunkbase 1234567" matches only the first 6 chars
        # of the id, returning "123456".
        m = sbm.SPLUNKBASE_ID_RE.search("Splunkbase 1234567")
        assert m is not None
        assert m.group(1) == "123456"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


class TestReadJson:
    def test_missing_file_returns_empty_dict(self, tmp_path: pathlib.Path) -> None:
        assert sbm._read_json(tmp_path / "missing.json") == {}

    def test_valid_file_returns_parsed(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "x.json"
        p.write_text('{"a": 1, "b": "two"}', encoding="utf-8")
        assert sbm._read_json(p) == {"a": 1, "b": "two"}

    def test_invalid_json_raises(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("not valid {", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            sbm._read_json(p)


class TestWriteJsonPreservingStyle:
    def test_writes_2_space_indent_with_trailing_newline(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "uc.json"
        body = {"id": "1.1.1", "title": "Test"}
        sbm._write_json_preserving_style(p, body)
        text = p.read_text(encoding="utf-8")
        assert text.endswith("\n")
        assert '  "id":' in text
        # JSON is parseable
        assert json.loads(text) == body

    def test_does_not_sort_keys(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "uc.json"
        body = {"z": 1, "a": 2}
        sbm._write_json_preserving_style(p, body)
        text = p.read_text(encoding="utf-8")
        assert text.index('"z"') < text.index('"a"')

    def test_preserves_unicode(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "uc.json"
        body = {"name": "Café Müller"}
        sbm._write_json_preserving_style(p, body)
        text = p.read_text(encoding="utf-8")
        assert "Café Müller" in text
        assert "\\u00e9" not in text


class TestLoadCatalog:
    def test_empty_when_no_files(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sbm, "CATALOG_PATH", tmp_path / "missing.json")
        monkeypatch.setattr(sbm, "OVERRIDES_PATH", tmp_path / "missing2.json")
        assert sbm._load_catalog() == {}

    def test_catalog_only(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps(
                {
                    "apps": {
                        "1234": {"name": "x", "displayName": "X"},
                        "5678": {"name": "y", "displayName": "Y"},
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(sbm, "CATALOG_PATH", cat)
        monkeypatch.setattr(sbm, "OVERRIDES_PATH", tmp_path / "missing.json")
        apps = sbm._load_catalog()
        assert apps["1234"]["name"] == "x"
        assert apps["5678"]["displayName"] == "Y"

    def test_overrides_merge(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps({"apps": {"1234": {"name": "stale", "displayName": "Stale"}}}),
            encoding="utf-8",
        )
        overrides = tmp_path / "overrides.json"
        overrides.write_text(
            json.dumps(
                {
                    "apps": {
                        "1234": {"displayName": "Override"},  # patches existing
                        "9999": {"name": "new", "displayName": "New"},  # adds new
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(sbm, "CATALOG_PATH", cat)
        monkeypatch.setattr(sbm, "OVERRIDES_PATH", overrides)
        apps = sbm._load_catalog()
        assert apps["1234"]["name"] == "stale"  # original key preserved
        assert apps["1234"]["displayName"] == "Override"  # override wins
        assert apps["9999"]["name"] == "new"

    def test_non_dict_entries_ignored(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps(
                {
                    "apps": {
                        "1234": {"name": "ok"},
                        "5678": "this is not a dict",
                        "9999": ["nor", "this"],
                    }
                }
            ),
            encoding="utf-8",
        )
        overrides = tmp_path / "overrides.json"
        overrides.write_text(
            json.dumps({"apps": {"1234": "string-override-ignored", "8888": {"name": "ok"}}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(sbm, "CATALOG_PATH", cat)
        monkeypatch.setattr(sbm, "OVERRIDES_PATH", overrides)
        apps = sbm._load_catalog()
        assert "1234" in apps
        assert "5678" not in apps
        assert "9999" not in apps
        assert "8888" in apps  # override-only entry still added

    def test_missing_apps_key(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = tmp_path / "catalog.json"
        cat.write_text(json.dumps({"other_key": "x"}), encoding="utf-8")
        monkeypatch.setattr(sbm, "CATALOG_PATH", cat)
        monkeypatch.setattr(sbm, "OVERRIDES_PATH", tmp_path / "missing.json")
        assert sbm._load_catalog() == {}


# ---------------------------------------------------------------------------
# Heuristics: premium app ids
# ---------------------------------------------------------------------------


class TestExtractPremiumAppIds:
    def test_empty_when_no_premium_apps(self) -> None:
        assert sbm._extract_premium_app_ids({}) == []

    def test_string_form(self) -> None:
        out = sbm._extract_premium_app_ids({"premiumApps": ["Splunk Enterprise Security"]})
        assert out == [(263, "Splunk Enterprise Security")]

    def test_dict_form_with_name_key(self) -> None:
        out = sbm._extract_premium_app_ids({"premiumApps": [{"name": "Splunk ITSI"}]})
        assert out == [(1841, "Splunk ITSI")]

    def test_unknown_premium_name_skipped(self) -> None:
        assert sbm._extract_premium_app_ids({"premiumApps": ["Unknown App"]}) == []

    def test_non_str_non_dict_skipped(self) -> None:
        assert sbm._extract_premium_app_ids({"premiumApps": [123, None, ["x"]]}) == []

    def test_case_insensitive_match(self) -> None:
        out = sbm._extract_premium_app_ids({"premiumApps": ["splunk SOAR"]})
        assert out == [(5613, "splunk SOAR")]

    def test_premium_apps_none_returns_empty(self) -> None:
        assert sbm._extract_premium_app_ids({"premiumApps": None}) == []


# ---------------------------------------------------------------------------
# Heuristics: app field extraction
# ---------------------------------------------------------------------------


class TestExtractAppFieldIds:
    def test_empty_when_no_app(self) -> None:
        assert sbm._extract_app_field_ids({}) == []

    def test_non_str_app_returns_empty(self) -> None:
        assert sbm._extract_app_field_ids({"app": ["list", "not", "str"]}) == []

    def test_extracts_splunkbase_prefix(self) -> None:
        out = sbm._extract_app_field_ids({"app": "Splunkbase 1234"})
        assert out == [1234]

    def test_extracts_url_form(self) -> None:
        out = sbm._extract_app_field_ids({"app": "see https://splunkbase.splunk.com/app/9876/"})
        assert out == [9876]

    def test_dedups_repeat_ids(self) -> None:
        out = sbm._extract_app_field_ids(
            {"app": "Splunkbase 1234 ... Splunkbase 1234 ... Splunkbase 1234"}
        )
        assert out == [1234]

    def test_keeps_insertion_order(self) -> None:
        out = sbm._extract_app_field_ids({"app": "Splunkbase 9876 and Splunkbase 1234"})
        assert out == [9876, 1234]

    def test_zero_and_negative_ids_skipped(self) -> None:
        # Regex won't match "00" because that's allowed by the {2,6} rule
        # but the int parse + ``value <= 0`` guard skips zeros.
        out = sbm._extract_app_field_ids({"app": "Splunkbase 00"})
        assert out == []

    def test_unparseable_capture_group_is_skipped_silently(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Defensive-contract test for the ``except ValueError: continue``
        branch on lines 167-168.

        The shipped regex ``\\d{2,6}`` guarantees the capture group is
        always int-parseable, so the except branch is unreachable in
        production. We monkeypatch in a relaxed regex that captures the
        prefix word (e.g. ``"app"``) instead of digits to prove the
        function still degrades gracefully — i.e. it skips the unparseable
        token instead of raising. This pins the contract for any future
        regex tweak.
        """
        import re

        relaxed = re.compile(
            r"(?:Splunkbase\s+|splunkbase\.splunk\.com/app/)(\w+)",
            re.IGNORECASE,
        )
        monkeypatch.setattr(sbm, "SPLUNKBASE_ID_RE", relaxed)
        # "Splunkbase notanumber 4567 Splunkbase alsobad" → only 4567 should survive.
        out = sbm._extract_app_field_ids(
            {"app": "Splunkbase notanumber Splunkbase 4567 Splunkbase alsobad"}
        )
        assert out == [4567]


# ---------------------------------------------------------------------------
# Heuristics: equipment match
# ---------------------------------------------------------------------------


class TestEquipmentMatch:
    def test_empty_when_no_equipment(self) -> None:
        assert sbm._equipment_match({}, {"1234": {"name": "TA-cisco-meraki"}}) == []

    def test_kebab_slug_hits_kebab_in_name(self) -> None:
        cat = {"1234": {"name": "TA-cisco-meraki", "displayName": "Cisco Meraki"}}
        out = sbm._equipment_match({"equipment": ["cisco-meraki"]}, cat)
        assert out == [1234]

    def test_kebab_slug_hits_space_variant(self) -> None:
        cat = {"1234": {"displayName": "Cisco Meraki", "name": "ta-meraki"}}
        out = sbm._equipment_match({"equipment": ["cisco-meraki"]}, cat)
        assert out == [1234]

    def test_kebab_slug_hits_underscore_variant(self) -> None:
        cat = {"1234": {"name": "Splunk_TA_cisco_meraki"}}
        out = sbm._equipment_match({"equipment": ["cisco-meraki"]}, cat)
        assert out == [1234]

    def test_short_slug_filtered(self) -> None:
        # Slugs shorter than 4 chars are skipped.
        cat = {"1234": {"name": "x", "displayName": "abc"}}
        assert sbm._equipment_match({"equipment": ["abc"]}, cat) == []

    def test_equipment_models_compound_extracts_slug(self) -> None:
        # equipmentModels entries like "cisco-ise_3415" — first part is the
        # slug. Only the kebab-case form is added as a needle (unlike the
        # equipment field, which also adds space/underscore variants).
        cat = {"1234": {"name": "Splunk_TA_cisco-ise"}}
        out = sbm._equipment_match({"equipmentModels": ["cisco-ise_3415"]}, cat)
        assert out == [1234]

    def test_equipment_models_without_underscore_skipped(self) -> None:
        cat = {"1234": {"displayName": "Cisco ISE"}}
        # No underscore means no slug to split.
        assert sbm._equipment_match({"equipmentModels": ["ciscoise"]}, cat) == []

    def test_equipment_models_short_slug_filtered(self) -> None:
        # ``foo`` is the split slug — 3 chars, below the 4-char floor.
        cat = {"1234": {"name": "TA-foo"}}
        assert sbm._equipment_match({"equipmentModels": ["foo_bar"]}, cat) == []

    def test_catalog_entries_iterated_until_match(self) -> None:
        # Exercises the inner-loop "no match → next catalog entry" branch
        # in _equipment_match.
        cat = {
            "1234": {"name": "Splunk_TA_some-other-vendor"},
            "5678": {"name": "Splunk_TA_cisco-meraki"},
        }
        out = sbm._equipment_match({"equipment": ["cisco-meraki"]}, cat)
        assert out == [5678]

    def test_non_string_slug_skipped(self) -> None:
        cat = {"1234": {"name": "ta"}}
        # ints and None inside equipment are skipped.
        assert sbm._equipment_match({"equipment": [42, None]}, cat) == []

    def test_invalid_catalog_id_skipped(self) -> None:
        cat = {"not-a-number": {"name": "Cisco ISE"}, "1234": {"name": "Cisco ISE"}}
        out = sbm._equipment_match({"equipment": ["cisco-ise"]}, cat)
        assert out == [1234]

    def test_empty_haystack_skipped(self) -> None:
        cat = {"1234": {"name": "", "displayName": ""}}
        assert sbm._equipment_match({"equipment": ["cisco-meraki"]}, cat) == []

    def test_vendor_field_in_haystack(self) -> None:
        cat = {"1234": {"name": "TA", "vendor": "cisco-meraki"}}
        out = sbm._equipment_match({"equipment": ["cisco-meraki"]}, cat)
        assert out == [1234]


# ---------------------------------------------------------------------------
# Heuristics: data-source match
# ---------------------------------------------------------------------------


class TestDataSourceMatch:
    def test_empty_when_no_data_sources(self) -> None:
        assert sbm._data_source_match({}, {"1234": {"name": "x"}}) == []

    def test_text_under_8_chars_skipped(self) -> None:
        assert (
            sbm._data_source_match({"dataSources": "short"}, {"1234": {"name": "Splunk_TA"}}) == []
        )

    def test_non_str_data_sources_skipped(self) -> None:
        assert (
            sbm._data_source_match(
                {"dataSources": ["list", "form"]}, {"1234": {"name": "Splunk_TA"}}
            )
            == []
        )

    def test_name_substring_match(self) -> None:
        cat = {"1234": {"name": "Splunk_TA_cisco-meraki", "displayName": "Other"}}
        out = sbm._data_source_match({"dataSources": "Use Splunk_TA_cisco-meraki for syslog"}, cat)
        assert out == [1234]

    def test_display_name_match(self) -> None:
        cat = {"1234": {"name": "short", "displayName": "Cisco Meraki Add-on"}}
        out = sbm._data_source_match(
            {"dataSources": "Configure the Cisco Meraki Add-on properly."}, cat
        )
        assert out == [1234]

    def test_short_catalog_field_skipped(self) -> None:
        # Catalog name/displayName must be at least 8 chars.
        cat = {"1234": {"name": "short", "displayName": "tiny"}}
        assert sbm._data_source_match({"dataSources": "tiny short stuff"}, cat) == []

    def test_invalid_catalog_id_skipped(self) -> None:
        cat = {"bogus": {"name": "Splunk_TA_meraki"}, "1234": {"name": "Splunk_TA_meraki"}}
        out = sbm._data_source_match({"dataSources": "consumes Splunk_TA_meraki events"}, cat)
        assert out == [1234]


# ---------------------------------------------------------------------------
# _build_proposal — role-ranked aggregation
# ---------------------------------------------------------------------------


class TestBuildProposal:
    def test_empty_when_no_signals(self) -> None:
        assert sbm._build_proposal({}, {}) == []

    def test_primary_app_only(self) -> None:
        cat = {"1234": {"name": "TA-cisco-ise", "displayName": "Cisco ISE TA"}}
        uc = {"app": "Splunkbase 1234"}
        proposal = sbm._build_proposal(uc, cat)
        assert proposal == [
            {
                "id": 1234,
                "name": "Cisco ISE TA",
                "url": "https://splunkbase.splunk.com/app/1234",
                "role": "primary",
                "requiresSmeReview": True,
            }
        ]

    def test_premium_app_only(self) -> None:
        cat = {"263": {"displayName": "Splunk Enterprise Security"}}
        uc = {"premiumApps": ["Splunk Enterprise Security"]}
        proposal = sbm._build_proposal(uc, cat)
        assert len(proposal) == 1
        assert proposal[0]["role"] == "premium"
        assert proposal[0]["id"] == 263

    def test_primary_outranks_premium(self) -> None:
        cat = {"263": {"displayName": "Splunk Enterprise Security"}}
        uc = {
            "app": "Splunkbase 263",
            "premiumApps": ["Splunk Enterprise Security"],
        }
        proposal = sbm._build_proposal(uc, cat)
        assert len(proposal) == 1
        assert proposal[0]["role"] == "primary"

    def test_premium_outranks_data_source(self) -> None:
        cat = {
            "263": {
                "name": "TA-splunk-enterprise-security",
                "displayName": "Splunk Enterprise Security",
            }
        }
        uc = {
            "premiumApps": ["Splunk Enterprise Security"],
            "dataSources": "ingest from TA-splunk-enterprise-security",
        }
        proposal = sbm._build_proposal(uc, cat)
        assert len(proposal) == 1
        assert proposal[0]["role"] == "premium"

    def test_catalog_entry_missing_skipped(self) -> None:
        # Splunkbase id mentioned in `app` but not in the catalog → not added.
        uc = {"app": "Splunkbase 9999"}
        assert sbm._build_proposal(uc, {}) == []

    def test_catalog_entry_non_dict_skipped(self) -> None:
        # Defensive: a non-dict catalog entry never makes it through
        # `_load_catalog`, but the helper still guards against it.
        cat: dict[str, Any] = {"1234": "not-a-dict"}
        uc = {"app": "Splunkbase 1234"}
        assert sbm._build_proposal(uc, cat) == []

    def test_name_fallback_when_display_name_missing(self) -> None:
        cat = {"1234": {"name": "Fallback Name"}}
        proposal = sbm._build_proposal({"app": "Splunkbase 1234"}, cat)
        assert proposal[0]["name"] == "Fallback Name"

    def test_generic_name_fallback_when_both_missing(self) -> None:
        cat: dict[str, dict[str, Any]] = {"1234": {}}
        proposal = sbm._build_proposal({"app": "Splunkbase 1234"}, cat)
        assert proposal[0]["name"] == "Splunkbase app 1234"

    def test_url_fallback_when_missing(self) -> None:
        cat = {"1234": {"name": "Foo"}}
        proposal = sbm._build_proposal({"app": "Splunkbase 1234"}, cat)
        assert proposal[0]["url"] == "https://splunkbase.splunk.com/app/1234"

    def test_url_from_catalog_preserved(self) -> None:
        cat = {"1234": {"name": "Foo", "url": "https://example.com/foo"}}
        proposal = sbm._build_proposal({"app": "Splunkbase 1234"}, cat)
        assert proposal[0]["url"] == "https://example.com/foo"

    def test_consider_zero_id_short_circuits(self) -> None:
        # _build_proposal's nested _consider(app_id, role) guards against
        # app_id <= 0. The Splunkbase regex requires at least two digits so
        # ``Splunkbase 0`` is not extracted; reach the guard via the
        # equipment heuristic where a catalog entry has a literal "0" key.
        cat = {"0": {"name": "Splunk_TA_cisco-meraki"}}
        assert sbm._build_proposal({"equipment": ["cisco-meraki"]}, cat) == []

    def test_equipment_promotes_to_data_source_role(self) -> None:
        # Exercises the data-source role assignment path in _build_proposal
        # (the equipment loop calling _consider).
        cat = {
            "1234": {
                "name": "Splunk_TA_cisco-meraki",
                "displayName": "Cisco Meraki Add-on",
            }
        }
        proposal = sbm._build_proposal({"equipment": ["cisco-meraki"]}, cat)
        assert proposal == [
            {
                "id": 1234,
                "name": "Cisco Meraki Add-on",
                "url": "https://splunkbase.splunk.com/app/1234",
                "role": "data-source",
                "requiresSmeReview": True,
            }
        ]

    def test_latest_version_is_not_emitted(self) -> None:
        # latestVersion is deliberately not promoted to minVersion.
        cat = {"1234": {"name": "Foo", "latestVersion": "2.0.0"}}
        proposal = sbm._build_proposal({"app": "Splunkbase 1234"}, cat)
        assert "minVersion" not in proposal[0]
        assert "latestVersion" not in proposal[0]

    def test_proposal_sorted_by_id(self) -> None:
        cat = {
            "1234": {"name": "A"},
            "9999": {"name": "B"},
            "5555": {"name": "C"},
        }
        uc = {"app": "Splunkbase 9999 Splunkbase 1234 Splunkbase 5555"}
        proposal = sbm._build_proposal(uc, cat)
        assert [p["id"] for p in proposal] == [1234, 5555, 9999]


# ---------------------------------------------------------------------------
# _existing_human_signed
# ---------------------------------------------------------------------------


class TestExistingHumanSigned:
    def test_missing_key_returns_false(self) -> None:
        assert sbm._existing_human_signed({}) is False

    def test_empty_list_returns_false(self) -> None:
        assert sbm._existing_human_signed({"splunkbaseApps": []}) is False

    def test_non_list_returns_false(self) -> None:
        assert sbm._existing_human_signed({"splunkbaseApps": "not a list"}) is False

    def test_all_entries_require_sme_review_returns_false(self) -> None:
        uc = {
            "splunkbaseApps": [
                {"id": 1, "requiresSmeReview": True},
                {"id": 2, "requiresSmeReview": True},
            ]
        }
        assert sbm._existing_human_signed(uc) is False

    def test_any_signed_off_entry_returns_true(self) -> None:
        uc = {
            "splunkbaseApps": [
                {"id": 1, "requiresSmeReview": True},
                {"id": 2, "requiresSmeReview": False},  # SME signed
            ]
        }
        assert sbm._existing_human_signed(uc) is True

    def test_missing_requires_sme_field_treated_as_signed(self) -> None:
        # Default of `.get("requiresSmeReview", False)` returns False, so a
        # missing field reads as "human signed it off".
        uc = {"splunkbaseApps": [{"id": 1, "name": "Foo"}]}
        assert sbm._existing_human_signed(uc) is True

    def test_non_dict_entries_skipped(self) -> None:
        uc = {"splunkbaseApps": [{"id": 1, "requiresSmeReview": True}, "junk", None, 42]}
        assert sbm._existing_human_signed(uc) is False


# ---------------------------------------------------------------------------
# _arrays_equal
# ---------------------------------------------------------------------------


class TestArraysEqual:
    def test_identical_arrays(self) -> None:
        a = [{"id": 1, "name": "X"}]
        b = [{"id": 1, "name": "X"}]
        assert sbm._arrays_equal(a, b) is True

    def test_key_order_irrelevant(self) -> None:
        a = [{"id": 1, "name": "X"}]
        b = [{"name": "X", "id": 1}]
        assert sbm._arrays_equal(a, b) is True

    def test_different_values_not_equal(self) -> None:
        a = [{"id": 1, "name": "X"}]
        b = [{"id": 1, "name": "Y"}]
        assert sbm._arrays_equal(a, b) is False

    def test_order_matters(self) -> None:
        a = [{"id": 1}, {"id": 2}]
        b = [{"id": 2}, {"id": 1}]
        assert sbm._arrays_equal(a, b) is False

    def test_empty_arrays_equal(self) -> None:
        assert sbm._arrays_equal([], []) is True


# ---------------------------------------------------------------------------
# _discover_ucs
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_content_tree(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    content = tmp_path / "content"
    (content / "cat-01-foo").mkdir(parents=True)
    (content / "cat-05-bar").mkdir(parents=True)
    (content / "cat-22-baz").mkdir(parents=True)
    (content / "cat-01-foo" / "UC-1.1.1.json").write_text("{}", encoding="utf-8")
    (content / "cat-01-foo" / "UC-1.2.1.json").write_text("{}", encoding="utf-8")
    (content / "cat-05-bar" / "UC-5.3.7.json").write_text("{}", encoding="utf-8")
    (content / "cat-22-baz" / "UC-22.35.1.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sbm, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sbm, "CONTENT_DIR", content)
    return content


class TestDiscoverUcs:
    def test_unfiltered_returns_all(self, fake_content_tree: pathlib.Path) -> None:
        paths = sbm._discover_ucs(None, None)
        ids = sorted(p.stem for p in paths)
        assert ids == ["UC-1.1.1", "UC-1.2.1", "UC-22.35.1", "UC-5.3.7"]

    def test_filter_by_uc_id_short_form(self, fake_content_tree: pathlib.Path) -> None:
        paths = sbm._discover_ucs("1.1.1", None)
        assert len(paths) == 1
        assert paths[0].stem == "UC-1.1.1"

    def test_filter_by_uc_id_with_uc_prefix(self, fake_content_tree: pathlib.Path) -> None:
        paths = sbm._discover_ucs("UC-22.35.1", None)
        assert len(paths) == 1
        assert paths[0].stem == "UC-22.35.1"

    def test_filter_by_cat_single_digit(self, fake_content_tree: pathlib.Path) -> None:
        paths = sbm._discover_ucs(None, "5")
        ids = [p.stem for p in paths]
        assert ids == ["UC-5.3.7"]

    def test_filter_by_cat_zero_padded(self, fake_content_tree: pathlib.Path) -> None:
        # int("05") == 5 → "cat-05-" prefix matches.
        paths = sbm._discover_ucs(None, "05")
        assert len(paths) == 1
        assert paths[0].parent.name == "cat-05-bar"

    def test_filter_by_uc_and_cat_combined(self, fake_content_tree: pathlib.Path) -> None:
        # UC filter narrows to 1.1.1; cat filter '1' keeps it.
        paths = sbm._discover_ucs("1.1.1", "1")
        assert len(paths) == 1
        # cat filter '2' would exclude it.
        paths = sbm._discover_ucs("1.1.1", "2")
        assert paths == []

    def test_no_match_returns_empty(self, fake_content_tree: pathlib.Path) -> None:
        assert sbm._discover_ucs("99.99.99", None) == []


# ---------------------------------------------------------------------------
# _update_uc_in_place
# ---------------------------------------------------------------------------


class TestUpdateUcInPlace:
    def test_inserts_after_app(self) -> None:
        uc = {"id": "1.1.1", "title": "T", "app": "X", "description": "D"}
        proposal = [{"id": 1234, "role": "primary"}]
        out = sbm._update_uc_in_place(uc, proposal)
        keys = list(out.keys())
        assert keys == ["id", "title", "app", "splunkbaseApps", "description"]
        assert out["splunkbaseApps"] == proposal

    def test_replaces_existing(self) -> None:
        uc = {
            "id": "1.1.1",
            "app": "X",
            "splunkbaseApps": [{"id": 9, "role": "primary"}],
            "description": "D",
        }
        proposal = [{"id": 1234, "role": "primary"}]
        out = sbm._update_uc_in_place(uc, proposal)
        assert out["splunkbaseApps"] == proposal

    def test_empty_proposal_drops_existing(self) -> None:
        uc = {
            "id": "1.1.1",
            "app": "X",
            "splunkbaseApps": [{"id": 9, "role": "primary"}],
            "description": "D",
        }
        out = sbm._update_uc_in_place(uc, [])
        assert "splunkbaseApps" not in out

    def test_appends_when_no_app_field(self) -> None:
        uc = {"id": "1.1.1", "title": "T", "description": "D"}
        proposal = [{"id": 1234, "role": "primary"}]
        out = sbm._update_uc_in_place(uc, proposal)
        # No "app" anchor → splunkbaseApps appended at end.
        assert list(out.keys())[-1] == "splunkbaseApps"
        assert out["splunkbaseApps"] == proposal


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    repo = tmp_path
    content = repo / "content"
    cat = content / "cat-01-foo"
    cat.mkdir(parents=True)
    data = repo / "data"
    data.mkdir(parents=True)
    monkeypatch.setattr(sbm, "REPO_ROOT", repo)
    monkeypatch.setattr(sbm, "CONTENT_DIR", content)
    monkeypatch.setattr(sbm, "CATALOG_PATH", data / "splunkbase-catalog.json")
    monkeypatch.setattr(sbm, "OVERRIDES_PATH", data / "splunkbase-catalog-overrides.json")
    return repo


def _write_catalog(repo: pathlib.Path) -> None:
    (repo / "data" / "splunkbase-catalog.json").write_text(
        json.dumps(
            {
                "apps": {
                    "1234": {
                        "name": "TA-cisco-ise",
                        "displayName": "Cisco ISE TA",
                    }
                }
            }
        ),
        encoding="utf-8",
    )


class TestMainCli:
    def test_empty_catalog_warns_but_does_not_fail(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # No catalog file → empty catalog → emit stderr warning, continue.
        # Also no UCs → exit 0 with "no UCs matched the filter".
        rc = sbm.main(["--check"])
        assert rc == 0
        err = capsys.readouterr().err
        assert "data/splunkbase-catalog.json is empty" in err
        assert "no UCs matched the filter" in err

    def test_no_matching_ucs_returns_zero(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        rc = sbm.main(["--check", "--uc", "99.99.99"])
        assert rc == 0
        err = capsys.readouterr().err
        assert "no UCs matched" in err

    def test_check_mode_reports_would_write(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        uc_path.write_text(json.dumps({"id": "1.1.1", "app": "Splunkbase 1234"}), encoding="utf-8")
        rc = sbm.main(["--check"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "would write" in out
        assert "would_write=1" in out
        # Side-effect-free in --check mode: original file untouched.
        original = json.loads(uc_path.read_text())
        assert "splunkbaseApps" not in original

    def test_write_mode_rewrites_file(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        uc_path.write_text(json.dumps({"id": "1.1.1", "app": "Splunkbase 1234"}), encoding="utf-8")
        rc = sbm.main(["--write"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "wrote" in out
        assert "rewrote=1" in out
        new_uc = json.loads(uc_path.read_text())
        assert new_uc["splunkbaseApps"][0]["id"] == 1234
        assert new_uc["splunkbaseApps"][0]["role"] == "primary"
        assert new_uc["splunkbaseApps"][0]["requiresSmeReview"] is True

    def test_check_mode_quiet_suppresses_would_write_line(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        uc_path.write_text(json.dumps({"id": "1.1.1", "app": "Splunkbase 1234"}), encoding="utf-8")
        rc = sbm.main(["--check", "--quiet"])
        assert rc == 0
        out = capsys.readouterr().out
        # "would write " line suppressed in --check --quiet mode; summary kept.
        assert "would write " not in out
        assert "would_write=1" in out

    def test_write_mode_quiet_suppresses_per_uc_lines(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        uc_path.write_text(json.dumps({"id": "1.1.1", "app": "Splunkbase 1234"}), encoding="utf-8")
        rc = sbm.main(["--write", "--quiet"])
        assert rc == 0
        out = capsys.readouterr().out
        # Per-UC "wrote <path>" line suppressed (no file path printed),
        # only the final summary is emitted.
        assert "UC-1.1.1.json" not in out
        assert "rewrote=1" in out

    def test_skipped_human_signed_counted(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        # Existing splunkbaseApps with at least one signed-off entry.
        uc_path.write_text(
            json.dumps(
                {
                    "id": "1.1.1",
                    "app": "Splunkbase 1234",
                    "splunkbaseApps": [{"id": 9, "name": "Foo", "requiresSmeReview": False}],
                }
            ),
            encoding="utf-8",
        )
        rc = sbm.main(["--check"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "skipped_human_signed=1" in out

    def test_no_catalog_match_counted(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Catalog has 1234; UC mentions 9999 → no match.
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        uc_path.write_text(json.dumps({"id": "1.1.1", "app": "Splunkbase 9999"}), encoding="utf-8")
        rc = sbm.main(["--check"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "no_catalog_match=1" in out

    def test_no_change_skipped_without_write(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Existing splunkbaseApps[] matches the proposal exactly →
        # nothing to do.  All entries marked requiresSmeReview so the
        # human-signed short-circuit doesn't fire.
        _write_catalog(isolated_repo)
        uc_path = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        cat = json.loads((isolated_repo / "data" / "splunkbase-catalog.json").read_text())["apps"]
        proposal = sbm._build_proposal({"app": "Splunkbase 1234"}, cat)
        uc_path.write_text(
            json.dumps({"id": "1.1.1", "app": "Splunkbase 1234", "splunkbaseApps": proposal}),
            encoding="utf-8",
        )
        rc = sbm.main(["--check"])
        assert rc == 0
        out = capsys.readouterr().out
        # No per-UC "would write" line is emitted because arrays already match,
        # but the summary still counts the proposed entry (proposed_total is
        # incremented before the _arrays_equal short-circuit).
        assert "would write " not in out
        assert "would_write=1" in out

    def test_uc_parse_error_logged_and_continued(
        self,
        isolated_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_catalog(isolated_repo)
        bad = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json"
        bad.write_text("not valid {", encoding="utf-8")
        good = isolated_repo / "content" / "cat-01-foo" / "UC-1.1.2.json"
        good.write_text(json.dumps({"id": "1.1.2", "app": "Splunkbase 1234"}), encoding="utf-8")
        rc = sbm.main(["--check"])
        assert rc == 0
        captured = capsys.readouterr()
        # The bad file generates a parse-error line on stderr.
        assert "UC-1.1.1.json" in captured.err
        # Final summary still printed.
        assert "scanned=2" in captured.out

    def test_help_lists_check_write_uc_cat_quiet(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as excinfo:
            sbm.main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        for flag in ("--check", "--write", "--uc", "--cat", "--quiet"):
            assert flag in out

    def test_main_module_entry_callable(self) -> None:
        # The `if __name__ == "__main__":` block at the bottom of the
        # module raises SystemExit(main()); we just confirm the symbol
        # is importable and callable from tests.
        assert callable(sbm.main)
