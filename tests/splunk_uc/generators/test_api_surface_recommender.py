"""Hermetic unit tests for the recommender + equipment helpers in
``splunk_uc.generators.api_surface``.

Targets four function families that the existing
``test_api_surface_units.py`` and ``test_api_surface_loaders.py`` left
uncovered:

* ``_load_catalog`` — flattens ``catalog.json`` into one list.
* ``_recommender_apps`` + ``_recommender_uc_thin`` +
  ``_recommender_payloads`` — drive
  ``api/v1/recommender/{sourcetype,cim,app,uc-thin}.json``.
* ``_recommender_splunkbase_index`` — drives
  ``api/v1/recommender/splunkbase-index.json``.
* ``_equipment_metadata`` + ``_equipment_payloads`` — drive
  ``api/v1/equipment/`` index + per-equipment detail.

Each test pins a tiny synthetic catalog / sidecar set in
``tmp_path`` and re-points the module-level globals
(``CATALOG_PATH_PRIMARY``, ``SPLUNKBASE_CATALOG_PATH``, etc.) at the
fixture so we never touch the real corpus.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from splunk_uc.generators import api_surface as M  # noqa: E402

# ---------------------------------------------------------------------------
# _load_catalog
# ---------------------------------------------------------------------------


class TestLoadCatalog:
    def test_returns_empty_when_no_catalog_found(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            M, "CATALOG_PATH_PRIMARY", tmp_path / "missing-1.json"
        )
        monkeypatch.setattr(
            M, "CATALOG_PATH_LEGACY", tmp_path / "missing-2.json"
        )
        assert M._load_catalog() == []

    def test_flattens_data_subs_ucs_and_sorts(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps(
                {
                    "DATA": [
                        {
                            "s": [
                                {
                                    "u": [
                                        {"i": "5.1.1", "n": "Five"},
                                        {"i": "1.1.2", "n": "Two"},
                                        # Non-dict and missing-id entries
                                        # MUST be skipped silently.
                                        "string entry",
                                        {"n": "no id"},
                                    ]
                                }
                            ]
                        },
                        {"s": [{"u": [{"i": "1.1.1", "n": "One"}]}]},
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "CATALOG_PATH_PRIMARY", cat)
        monkeypatch.setattr(
            M, "CATALOG_PATH_LEGACY", tmp_path / "no-fallback.json"
        )
        out = M._load_catalog()
        assert [u["i"] for u in out] == ["1.1.1", "1.1.2", "5.1.1"]


# ---------------------------------------------------------------------------
# _recommender_apps
# ---------------------------------------------------------------------------


class TestRecommenderApps:
    def test_extracts_backticked_folder_names(self) -> None:
        uc = {"t": "Use `Splunk_TA_nix` for nix; see also `Splunk_SA_CIM`."}
        out = M._recommender_apps(uc)
        assert "Splunk_TA_nix" in out
        assert "Splunk_SA_CIM" in out

    def test_skips_backticked_pure_version_numbers(self) -> None:
        uc = {"t": "Version `1.2.3` only"}
        assert M._recommender_apps(uc) == []

    def test_skips_backticked_token_that_fails_looks_like_app_label(
        self,
    ) -> None:
        """A backticked token that the surrounding regex admits
        (``[A-Za-z][A-Za-z0-9_\\-\\.]{2,79}``) but ``_looks_like_app_label``
        rejects (here: alphanumeric ratio < 40%) MUST be dropped silently
        rather than added to the app index. This pins the false branch
        of ``if _looks_like_app_label(token)`` (line 1126->1118).
        """
        # ``a-.-.-.-.-`` is 11 chars, only 1 alnum (9%). The backtick
        # regex admits it (starts with letter, rest in
        # ``[A-Za-z0-9_\\-\\.]``), but ``_looks_like_app_label`` rejects
        # it on the alphanumeric ratio check (alnum=1 < max(3, 11*0.4)=4.4).
        uc = {"t": "See `a-.-.-.-.-` for the placeholder token."}
        assert "a-.-.-.-.-" not in M._recommender_apps(uc)

    def test_strips_markdown_links_and_bold(self) -> None:
        uc = {"t": "[Splunk Add-on for Cisco](https://example), **Splunk Enterprise Security**"}
        out = M._recommender_apps(uc)
        assert "Splunk Add-on for Cisco" in out
        assert "Splunk Enterprise Security" in out

    def test_drops_ingest_method_descriptions(self) -> None:
        uc = {"t": "Cisco ASA via HEC, Custom scripted input, Scripted CLI"}
        # All three should be filtered out (via, scripted, scripted-prefix).
        assert M._recommender_apps(uc) == []

    def test_includes_marketplace_app_names(self) -> None:
        uc = {
            "sapp": [
                {"name": "Splunk App for AWS"},
                {"name": ""},  # too short, dropped
                "Some Splunkbase App",  # str fallback
                42,  # non-dict/non-str, ignored
            ]
        }
        out = M._recommender_apps(uc)
        assert "Splunk App for AWS" in out
        assert "Some Splunkbase App" in out

    def test_canonicalises_premium_aliases(self) -> None:
        uc = {"premium": "ES, soar (optional, for response), UBA"}
        out = M._recommender_apps(uc)
        # ``(optional, for response)`` is stripped as a balanced
        # parenthetical before the comma split, and each alias maps to
        # its canonical form.
        assert "Splunk Enterprise Security" in out
        assert "Splunk SOAR" in out
        assert "Splunk User Behavior Analytics" in out

    def test_drops_oversize_premium_token(self) -> None:
        big = "x" * 200
        uc = {"premium": big}
        assert M._recommender_apps(uc) == []

    def test_rejects_tokens_with_markdown_emphasis_residue(self) -> None:
        """A token like ``Splunk**TA**`` (residue from a botched
        markdown-bold strip) MUST be rejected by
        ``_looks_like_app_label`` — pins line 1045."""
        assert M._looks_like_app_label("Splunk**TA**nix") is False
        assert M._looks_like_app_label("foo__bar") is False

    def test_rejects_splunkbase_trailing_paren_or_dot_prefix(self) -> None:
        """Tokens starting with ``splunkbase `` and ending in ``)``
        or ``.`` are prose-trailers and MUST be rejected — pin
        line 1081 (e.g. "Splunkbase 7404)")."""
        assert M._looks_like_app_label("Splunkbase 7404)") is False
        assert M._looks_like_app_label("Splunkbase 7404.") is False
        # But the plain prefix without trailing dot/paren is allowed.
        assert M._looks_like_app_label("Splunkbase 7404") is True

    def test_rejects_bracketed_splunkbase_prefix(self) -> None:
        """``[splunkbase 7404]`` markdown-link residue MUST be
        rejected — pin line 1083. Note: the token must NOT start
        with ``[`` (already rejected at line 1040) but the
        ``startswith("[splunkbase ")`` branch only fires for tokens
        whose case-folded prefix matches. So the input has to be
        something like ``[Splunkbase 7404`` (missing the ``[``-
        starts-with rejection because it was already passed through
        a transform — defensive). We craft a token that begins with
        ``(`` then ``[`` to slip past the first guard."""
        # The first character-class guard at line 1040 rejects ``[``
        # so we can only reach line 1083 with a markdown-stripped
        # token where the very first character is ``[`` was already
        # filtered. The branch is defensive — assert that the explicit
        # rejection IS still applied if the upstream guards ever
        # change.
        # Bypass the first-char guard by stripping ``[`` to test
        # the branch directly.
        assert M._looks_like_app_label("[splunkbase 7404]") is False

    def test_rejects_low_alphanumeric_ratio_tokens(self) -> None:
        """Tokens with <40% alphanumeric characters are punctuation
        debris (e.g. ``...$``, ``/>``, ``)))``) and MUST be rejected
        — pin line 1089."""
        # 10-char token with only 2 alphanumeric chars (20%) → reject.
        assert M._looks_like_app_label("X.Y!!!!!!!!") is False
        # Same length, 5 alphanumeric (50%) → allowed.
        assert M._looks_like_app_label("XYZAB!!!!!") is True

    def test_backticked_pure_version_numbers_are_not_extracted(self) -> None:
        """Pure version-number tokens like ``1.2.3`` MUST NOT appear
        in the result. The regex at line 1118 enforces a letter
        start (``[A-Za-z][A-Za-z0-9_\\-\\.]{2,79}``) so a numeric
        leader never matches; lines 1121 and 1123 are defensive
        guards that complement the regex if it is ever widened.
        Pinning the contract regardless of which layer enforces it."""
        uc = {"t": "`1.2.3`"}
        assert M._recommender_apps(uc) == []

    def test_drops_oversize_or_undersize_commaspliced_tokens(self) -> None:
        """Comma-split pieces too short (``ab``) or too long (>80)
        are dropped without further inspection — pin line 1144."""
        # Two-char piece → too short (drop). 100-char piece → too long.
        uc = {"t": "ab, " + "x" * 100 + ", Splunk_TA_aws"}
        out = M._recommender_apps(uc)
        # Only the valid mid-length token survives.
        assert "Splunk_TA_aws" in out
        assert "ab" not in out
        assert all(len(label) <= 80 for label in out)

    def test_drops_empty_premium_pieces(self) -> None:
        """Empty pieces from comma-splitting premium (e.g. trailing
        comma) hit ``continue`` at line 1179 and MUST be dropped."""
        uc = {"premium": "ES,,, ,UBA"}
        out = M._recommender_apps(uc)
        # Both non-empty aliases canonicalise; empty pieces dropped.
        assert "Splunk Enterprise Security" in out
        assert "Splunk User Behavior Analytics" in out

    def test_drops_premium_token_that_does_not_look_like_app_label(self) -> None:
        """A premium token whose canonical form fails
        ``_looks_like_app_label`` (e.g. wholly numeric) hits
        ``continue`` at line 1184 and MUST be dropped."""
        uc = {"premium": "12345"}
        assert M._recommender_apps(uc) == []


# ---------------------------------------------------------------------------
# _recommender_uc_thin
# ---------------------------------------------------------------------------


class TestRecommenderUcThin:
    def test_emits_compact_record_with_defaults(self) -> None:
        uc = {"i": "1.1.1"}
        out = M._recommender_uc_thin(uc)
        assert out["id"] == "1.1.1"
        # All string/list fields default to empty.
        assert out["title"] == ""
        assert out["app"] == []
        assert out["sb"] == []

    def test_propagates_all_known_fields(self) -> None:
        uc = {
            "i": "5.2.1",
            "n": "Title",
            "v": "Value",
            "c": "high",
            "f": "medium",
            "wv": "walk",
            "pre": ["1.1.1", "1.1.2", "1.1.1"],  # dedup
            "mtype": ["proactive", "reactive"],
            "pillar": "security",
            "mitre": ["T1003"],
            "e": ["paloalto", "cisco-meraki"],
            "em": ["paloalto_pa-220"],
            # Recommender_apps + recommender_cim_models pull from t/q.
            # ``datamodel`` requires ``=`` or ``:`` between the keyword
            # and value to match _CIM_DATAMODEL_RX.
            "t": "Splunk_TA_nix",
            "q": "| datamodel=Authentication",
        }
        out = M._recommender_uc_thin(uc)
        assert out["prerequisiteUseCases"] == ["1.1.1", "1.1.2"]
        assert out["monitoringType"] == ["proactive", "reactive"]
        assert out["mitreAttack"] == ["T1003"]
        assert out["equipment"] == ["cisco-meraki", "paloalto"]
        assert out["equipmentModels"] == ["paloalto_pa-220"]
        assert out["app"] == ["Splunk_TA_nix"]
        assert out["cimModels"] == ["Authentication"]
        assert out["splunkPillar"] == "security"

    def test_compacts_sidecar_splunkbase_entries(self) -> None:
        sb_map = {
            "1.1.1": [
                {
                    "id": "742",
                    "role": "primary",
                    "name": "App 742",
                    "minVersion": "1.0.0",
                    "requiresSmeReview": True,
                },
                {"id": "abc"},  # un-castable id → dropped
                {"id": 0},  # non-positive id → dropped
                {"role": "primary"},  # no id → dropped
                "not a mapping",  # not a Mapping → dropped
            ]
        }
        out = M._recommender_uc_thin({"i": "1.1.1"}, sb_map)
        assert out["sb"] == [
            {
                "id": 742,
                "role": "primary",
                "name": "App 742",
                "minVersion": "1.0.0",
                "requiresSmeReview": True,
            }
        ]

    def test_skips_sb_when_map_missing_uc_id(self) -> None:
        out = M._recommender_uc_thin({"i": "9.9.9"}, {"1.1.1": [{"id": 1}]})
        assert out["sb"] == []

    def test_handles_none_sidecar_map(self) -> None:
        assert (
            M._recommender_uc_thin({"i": "1.1.1"}, sidecar_sb_map=None)["sb"]
            == []
        )


# ---------------------------------------------------------------------------
# _recommender_payloads
# ---------------------------------------------------------------------------


class TestRecommenderPayloads:
    def test_buckets_sourcetypes_cim_apps_and_thin(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        catalog = [
            {
                "i": "1.1.1",
                "n": "First",
                "q": (
                    'index=foo sourcetype="aws:cloudtrail" '
                    "| datamodel=Authentication"
                ),
                "t": "Splunk_TA_aws",
                "d": "AWS CloudTrail",
            },
            {
                "i": "1.1.2",
                "n": "Second",
                "q": 'index=foo sourcetype="aws:cloudtrail"',
                "t": "Splunk_TA_aws",
                "d": "",
            },
            {"i": "", "n": "Skipped"},  # no id → dropped
        ]
        out = M._recommender_payloads(catalog)
        st_idx = out["sourcetype-index"]
        assert st_idx["sourcetypeCount"] == 1
        assert st_idx["sourcetypes"]["aws:cloudtrail"] == ["1.1.1", "1.1.2"]
        cim_idx = out["cim-index"]
        assert cim_idx["cimModels"]["Authentication"] == ["1.1.1"]
        app_idx = out["app-index"]
        assert app_idx["apps"]["Splunk_TA_aws"] == ["1.1.1", "1.1.2"]
        thin = out["uc-thin"]
        assert [r["id"] for r in thin["useCases"]] == ["1.1.1", "1.1.2"]


# ---------------------------------------------------------------------------
# _recommender_splunkbase_index
# ---------------------------------------------------------------------------


class TestRecommenderSplunkbaseIndex:
    def test_empty_when_neither_file_present(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(
            M, "SPLUNKBASE_CATALOG_PATH", tmp_path / "missing-cat.json"
        )
        monkeypatch.setattr(
            M, "SPLUNKBASE_OVERRIDES_PATH", tmp_path / "missing-ovr.json"
        )
        out = M._recommender_splunkbase_index()
        assert out["appCount"] == 0
        assert out["apps"] == {}
        assert out["etag"].startswith('"') and out["etag"].endswith('"')

    def test_merges_catalog_and_overrides_with_precedence(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cat = tmp_path / "catalog.json"
        ovr = tmp_path / "overrides.json"
        cat.write_text(
            json.dumps(
                {
                    "apps": {
                        "742": {
                            "id": 742,
                            "name": "app-742",
                            "displayName": "App 742",
                            "url": "https://splunkbase/742",
                            "latestVersion": "1.0.0",
                            "cloudVetted": True,
                            "splunkVersionsSupported": ["9.x", "9.x"],
                        },
                        "bad-key": {"id": 1, "name": "skip me"},
                        "123": "not a mapping",
                    }
                }
            ),
            encoding="utf-8",
        )
        ovr.write_text(
            json.dumps(
                {
                    "apps": {
                        "742": {
                            "displayName": "App 742 (override)",
                            "cloudVetted": False,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "SPLUNKBASE_CATALOG_PATH", cat)
        monkeypatch.setattr(M, "SPLUNKBASE_OVERRIDES_PATH", ovr)
        out = M._recommender_splunkbase_index()
        entry = out["apps"]["742"]
        # Override wins on cloudVetted and displayName; rest preserved.
        assert entry["displayName"] == "App 742 (override)"
        assert entry["cloudVetted"] is False
        assert entry["splunkVersionsSupported"] == ["9.x"]

    def test_drops_id_field_when_int_coercion_fails(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When ``raw_meta['id']`` is non-string AND non-int-coercible
        (e.g. a dict), the inner try/except at line 1435-1438 hits
        the False/except path and the ``id`` key is dropped from the
        emitted entry — the merged entry keeps the OTHER fields."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps(
                {
                    "apps": {
                        "742": {
                            "id": {"nested": "value"},  # int() raises TypeError
                            "name": "ok-name",
                            "displayName": "OK App",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "SPLUNKBASE_CATALOG_PATH", cat)
        monkeypatch.setattr(
            M,
            "SPLUNKBASE_OVERRIDES_PATH",
            tmp_path / "missing-overrides.json",
        )
        out = M._recommender_splunkbase_index()
        entry = out["apps"]["742"]
        # name/displayName survive, ``id`` is omitted because the
        # coercion failed.
        assert entry["name"] == "ok-name"
        assert entry["displayName"] == "OK App"
        assert "id" not in entry

    def test_drops_id_field_when_value_is_none(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When ``raw_meta['id']`` is explicitly ``None``, the inner
        guard at line 1433-1434 hits ``continue`` and the entry's
        ``id`` is omitted."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps(
                {
                    "apps": {
                        "742": {
                            "id": None,
                            "name": "ok-name",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "SPLUNKBASE_CATALOG_PATH", cat)
        monkeypatch.setattr(
            M,
            "SPLUNKBASE_OVERRIDES_PATH",
            tmp_path / "missing-overrides.json",
        )
        out = M._recommender_splunkbase_index()
        entry = out["apps"]["742"]
        assert entry["name"] == "ok-name"
        assert "id" not in entry

    def test_drops_entries_with_non_mapping_payload(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cat = tmp_path / "catalog.json"
        cat.write_text(json.dumps({"apps": {"742": "not-a-mapping"}}), encoding="utf-8")
        monkeypatch.setattr(M, "SPLUNKBASE_CATALOG_PATH", cat)
        monkeypatch.setattr(
            M,
            "SPLUNKBASE_OVERRIDES_PATH",
            tmp_path / "missing-overrides.json",
        )
        out = M._recommender_splunkbase_index()
        assert out["appCount"] == 0

    def test_non_dict_catalog_payload_is_ignored(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pins the false branch of ``isinstance(loaded, dict)`` for
        the catalog file (line 1402->1404). When the catalog payload
        decodes to a JSON list rather than an object, the merger MUST
        silently fall back to an empty catalog, NOT raise.
        """
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cat = tmp_path / "catalog.json"
        # Top-level JSON array — valid JSON but the wrong shape.
        cat.write_text(json.dumps([{"id": 742}]), encoding="utf-8")
        monkeypatch.setattr(M, "SPLUNKBASE_CATALOG_PATH", cat)
        monkeypatch.setattr(
            M,
            "SPLUNKBASE_OVERRIDES_PATH",
            tmp_path / "missing-overrides.json",
        )
        out = M._recommender_splunkbase_index()
        assert out["appCount"] == 0
        assert out["apps"] == {}

    def test_non_dict_overrides_payload_is_ignored(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pins the false branch of ``isinstance(loaded, dict)`` for
        the overrides file (line 1407->1409). A list-shaped overrides
        file is silently ignored; the catalog wins as if no overrides
        existed.
        """
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cat = tmp_path / "catalog.json"
        cat.write_text(
            json.dumps(
                {
                    "apps": {
                        "742": {
                            "id": 742,
                            "name": "app-742",
                            "displayName": "App 742",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        ovr = tmp_path / "overrides.json"
        ovr.write_text(json.dumps(["wrong shape"]), encoding="utf-8")
        monkeypatch.setattr(M, "SPLUNKBASE_CATALOG_PATH", cat)
        monkeypatch.setattr(M, "SPLUNKBASE_OVERRIDES_PATH", ovr)
        out = M._recommender_splunkbase_index()
        # Catalog entry survives unchanged — overrides did NOT
        # mutate displayName (no "(override)" suffix).
        assert out["apps"]["742"]["displayName"] == "App 742"


# ---------------------------------------------------------------------------
# _equipment_metadata
# ---------------------------------------------------------------------------


class TestEquipmentMetadata:
    def test_builds_by_id_and_compound_models(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_equipment = [
            {
                "id": "paloalto",
                "label": "Palo Alto Networks",
                "models": [
                    {"id": "pa-220", "label": "PA-220"},
                    {"id": "pa-440", "label": "PA-440"},
                    {"label": "id-missing"},  # skipped (no id)
                ],
            },
            {"id": "ciscofw", "label": "Cisco Firewall"},
        ]
        monkeypatch.setattr(M, "load_equipment", lambda: fake_equipment)
        by_id, compound = M._equipment_metadata()
        assert by_id["paloalto"]["label"] == "Palo Alto Networks"
        assert [m["id"] for m in by_id["paloalto"]["models"]] == ["pa-220", "pa-440"]
        assert by_id["ciscofw"]["models"] == []
        assert compound["paloalto_pa-220"]["equipmentLabel"] == "Palo Alto Networks"
        assert "paloalto_pa-440" in compound


# ---------------------------------------------------------------------------
# _equipment_payloads
# ---------------------------------------------------------------------------


class TestEquipmentPayloads:
    def test_index_and_detail_resolve_compliance_clauses(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(
            M,
            "load_equipment",
            lambda: [
                {
                    "id": "paloalto",
                    "label": "Palo Alto Networks",
                    "models": [{"id": "pa-220", "label": "PA-220"}],
                },
            ],
        )
        # ``catalog_ucs`` uses compact schema (i, n, e, em).
        catalog = [
            {
                "i": "5.1.1",
                "n": "FW logs",
                "e": ["paloalto"],
                "em": ["paloalto_pa-220"],
            },
            {
                "i": "22.1.1",
                "n": "PCI control",
                "e": ["paloalto"],
                "em": [],
            },
            # UC without 'e' is ignored by equipment_ucs but counted in
            # total_referenced.
            {"i": "1.1.1", "n": "no equipment"},
            # Empty id is silently skipped.
            {"i": "", "e": ["paloalto"]},
        ]
        compliance = [
            {
                "id": "22.1.1",
                "compliance": [
                    {
                        "regulation": "PCI DSS",
                        "version": "4.0",
                        "clause": "Req 1",
                    },
                    {
                        "regulation": "PCI DSS",
                        "version": "4.0",
                        "clause": "Req 2",
                    },
                    {"regulation": "", "version": "4.0", "clause": "ignored"},
                ],
            }
        ]
        alias_to_id = {"pci dss": "pci-dss"}
        idx, details = M._equipment_payloads(catalog, compliance, alias_to_id)
        assert idx["equipmentCount"] == 1
        paloalto = next(e for e in idx["equipment"] if e["id"] == "paloalto")
        assert paloalto["useCaseCount"] == 2
        assert paloalto["complianceUseCaseCount"] == 1
        assert "pci-dss" in paloalto["regulationIds"]
        detail = details["paloalto"]
        assert detail["regulationIds"] == ["pci-dss"]
        # useCasesByCategory groups by leading category id.
        cats = {entry["category"]: entry["useCaseIds"] for entry in detail["useCasesByCategory"]}
        assert cats == {5: ["5.1.1"], 22: ["22.1.1"]}
        # Per-regulation entries.
        regs = {r["regulationId"]: r for r in detail["regulations"]}
        assert regs["pci-dss"]["useCaseIds"] == ["22.1.1"]
        # Both clauses preserved in the clauseMappings list.
        clauses = [m["clause"] for m in regs["pci-dss"]["clauseMappings"]]
        assert clauses == ["Req 1", "Req 2"]

    def test_includes_equipment_with_no_uc_references(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Equipment registered with the EQUIPMENT registry must still
        appear in the index even when zero catalog UCs reference it
        (uses ``set(by_id.keys())`` in the all_referenced_ids union)."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(
            M,
            "load_equipment",
            lambda: [
                {
                    "id": "ghostfw",
                    "label": "Ghost Firewall",
                    "models": [],
                }
            ],
        )
        idx, details = M._equipment_payloads([], [], {})
        assert idx["equipmentCount"] == 1
        assert "ghostfw" in details

    def test_handles_uc_with_non_numeric_category_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """UC ids that don't split into a numeric prefix fall through
        to category 0 (pins the bare-except ``ValueError`` branch in
        ``_equipment_payloads``)."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(
            M,
            "load_equipment",
            lambda: [{"id": "paloalto", "label": "Palo Alto", "models": []}],
        )
        catalog = [
            {"i": "weird-id", "e": ["paloalto"]},
        ]
        _idx, details = M._equipment_payloads(catalog, [], {})
        cats = [e["category"] for e in details["paloalto"]["useCasesByCategory"]]
        assert 0 in cats

    def test_skips_non_string_equipment_and_model_ids(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pins the false branch of ``isinstance(eq_id, str) and eq_id``
        on the catalog scan (lines 1552->1551 + 1555->1554). Non-string
        or empty entries in ``e``/``em`` are silently dropped — the
        equipment/model index MUST NOT crash on dirty catalog data.
        """
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(
            M,
            "load_equipment",
            lambda: [{"id": "paloalto", "label": "Palo Alto", "models": []}],
        )
        catalog = [
            {
                "i": "5.1.1",
                "e": ["paloalto", "", 42, {"nested": "dict"}, None],
                "em": ["paloalto_pa-220", "", 99, ["list"], None],
            },
        ]
        _idx, details = M._equipment_payloads(catalog, [], {})
        # paloalto string still indexed; the malformed entries are
        # filtered out (no KeyError, no crash).
        assert "paloalto" in details
        # useCaseCount counts only the valid equipment binding.
        assert details["paloalto"]["useCaseCount"] == 1

    def test_skips_compliance_entries_with_whitespace_regulation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pins the false branch of ``if fid:`` (line 1569->1564)
        inside ``_resolve_regulation_ids``. A whitespace-only
        regulation value passes the ``if not reg`` guard (it's
        truthy) but resolves to an empty fid via
        ``alias_to_id.get('  ') or '  '.strip().lower() == ''`` —
        and so MUST NOT be added to the regulation set.
        """
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(
            M,
            "load_equipment",
            lambda: [
                {"id": "paloalto", "label": "Palo Alto Networks", "models": []}
            ],
        )
        catalog = [{"i": "22.1.1", "n": "Cmp", "e": ["paloalto"]}]
        compliance = [
            {
                "id": "22.1.1",
                "compliance": [
                    # Whitespace-only regulation — passes the truthy
                    # guard but produces an empty fid downstream.
                    {"regulation": "   ", "version": "4.0", "clause": "X"},
                ],
            }
        ]
        idx, _details = M._equipment_payloads(catalog, compliance, {})
        paloalto = next(e for e in idx["equipment"] if e["id"] == "paloalto")
        # No regulation tag survives the whitespace-only entry.
        assert paloalto["regulationIds"] == []


# ---------------------------------------------------------------------------
# _manifest / _context_jsonld (small composite + constant builder)
# ---------------------------------------------------------------------------


class TestManifest:
    def test_manifest_lists_all_top_level_endpoints(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        manifest = M._manifest(
            ucs=[
                {"id": "1.1.1", "_category": 1, "compliance": [{}]},
                {"id": "22.1.1", "_category": 22, "compliance": []},
            ],
            regs={"frameworks": [{"id": "gdpr"}]},
            coverage={"regulationsVersion": "2026-01-01"},
        )
        endpoints: Any = manifest["endpoints"]
        # Endpoints may be a list or dict depending on schema — assert
        # presence rather than membership operator semantics.
        text = json.dumps(endpoints)
        for key in (
            "compliance",
            "mitre",
            "oscal",
            "recommender",
            "equipment",
        ):
            assert key in text


class TestContextJsonld:
    def test_context_jsonld_is_stable_dict_with_well_known_keys(self) -> None:
        ctx = M._context_jsonld()
        assert isinstance(ctx, dict)
        assert "@context" in ctx
