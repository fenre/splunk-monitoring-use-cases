"""Tests for ``splunk_uc_mcp.tools.starter_packs``."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.starter_packs import (
    GET_STARTER_PACK_OUTPUT_SCHEMA,
    LIST_STARTER_PACKS_OUTPUT_SCHEMA,
    PLAN_ROLLOUT_OUTPUT_SCHEMA,
    PLAN_ROLLOUT_SCHEMA,
    get_starter_pack,
    list_starter_packs,
    plan_rollout,
)

_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "starter-plan-parity.json"


@pytest.fixture
def pack_catalog(tmp_path: Path) -> Iterator[Catalog]:
    """A tiny api/v1 tree whose starter-packs index is the parity fixture's."""

    index: dict[str, Any] = json.loads(_FIXTURE.read_text(encoding="utf-8"))["index"]
    v1 = tmp_path / "api" / "v1"
    (v1 / "starter-packs").mkdir(parents=True)
    (v1 / "manifest.json").write_text(json.dumps({"apiVersion": "v1", "endpoints": {}}))
    packs = []
    for p in index["packs"]:
        pack = {
            "description": "",
            "pairId": None,
            "equipment": [],
            "requiredData": {"splunkbaseApps": [], "sourcetypes": [], "indexes": [], "notes": ""},
            "nextPacks": [],
            "curationNotes": ["internal"],
            **p,
        }
        pack["stepCount"] = len(pack["steps"])
        pack["readiness"] = {
            "publishable": pack["status"] == "published",
            "warnings": [],
            "errors": [],
        }
        packs.append(pack)
        (v1 / "starter-packs" / f"{pack['id']}.json").write_text(
            json.dumps({"apiVersion": "v1", "pack": pack})
        )
    (v1 / "starter-packs" / "index.json").write_text(
        json.dumps(
            {"apiVersion": "v1", "sourcetypeAliases": index["sourcetypeAliases"], "packs": packs}
        )
    )
    with Catalog(catalog_root=tmp_path) as cat:
        yield cat


class TestListStarterPacks:
    def test_published_only_by_default(self, pack_catalog: Catalog) -> None:
        r = list_starter_packs(catalog=pack_catalog)
        jsonschema.validate(r, LIST_STARTER_PACKS_OUTPUT_SCHEMA)
        assert all(p["status"] == "published" for p in r["packs"])
        assert "lin-sec" not in {p["id"] for p in r["packs"]}
        assert r["count"] == len(r["packs"])

    def test_include_drafts_and_goal(self, pack_catalog: Catalog) -> None:
        r = list_starter_packs(catalog=pack_catalog, goal="security", include_drafts=True)
        ids = [p["id"] for p in r["packs"]]
        assert "lin-sec" in ids
        assert "win-ops" not in ids
        assert ids == sorted(ids)

    def test_equipment_filter_accepts_compound_ids(self, pack_catalog: Catalog) -> None:
        r = list_starter_packs(
            catalog=pack_catalog, equipment_id="windows_server_2022", include_drafts=True
        )
        assert {p["id"] for p in r["packs"]} == {"win-ops", "win-sec"}

    @pytest.mark.parametrize(
        "kwargs",
        [{"goal": "fun"}, {"equipment_id": "../etc"}, {"include_drafts": "yes"}],
    )
    def test_rejects_bad_input(self, pack_catalog: Catalog, kwargs: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            list_starter_packs(catalog=pack_catalog, **kwargs)


class TestGetStarterPack:
    def test_published_pack(self, pack_catalog: Catalog) -> None:
        r = get_starter_pack(catalog=pack_catalog, pack_id="win-sec")
        jsonschema.validate(r, GET_STARTER_PACK_OUTPUT_SCHEMA)
        assert r["id"] == "win-sec"
        assert "curationNotes" not in r

    def test_draft_hidden_unless_requested(self, pack_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError, match="include_drafts"):
            get_starter_pack(catalog=pack_catalog, pack_id="lin-sec")
        assert (
            get_starter_pack(catalog=pack_catalog, pack_id="lin-sec", include_drafts=True)["status"]
            == "draft"
        )

    def test_rejects_traversal(self, pack_catalog: Catalog) -> None:
        with pytest.raises(ValueError):
            get_starter_pack(catalog=pack_catalog, pack_id="../manifest")


class TestPlanRollout:
    def test_schema_requires_goal(self) -> None:
        assert PLAN_ROLLOUT_SCHEMA["required"] == ["goal"]
        assert PLAN_ROLLOUT_SCHEMA["additionalProperties"] is False

    def test_plan_from_sourcetypes(self, pack_catalog: Catalog) -> None:
        r = plan_rollout(
            catalog=pack_catalog, goal="security", sourcetypes=["WinEventLog:Security"]
        )
        jsonschema.validate(r, PLAN_ROLLOUT_OUTPUT_SCHEMA)
        assert r["steps"] and r["steps"][0]["packId"] == "win-sec"
        assert all(s["packId"] != "lin-sec" for s in r["steps"])
        assert "parsed" not in r

    def test_paste_is_parsed_and_merged(self, pack_catalog: Catalog) -> None:
        r = plan_rollout(
            catalog=pack_catalog,
            goal="security",
            paste="index\tsourcetype\tcount\n_audit\taudittrail\t5\n",
            sourcetypes=["WinEventLog"],
        )
        jsonschema.validate(r, PLAN_ROLLOUT_OUTPUT_SCHEMA)
        assert r["parsed"] == {"sourcetypes": ["audittrail"], "indexes": ["_audit"]}
        assert {p["id"] for p in r["packs"]} >= {"win-sec", "plat-sec"}

    def test_max_steps_and_empty(self, pack_catalog: Catalog) -> None:
        r = plan_rollout(
            catalog=pack_catalog, goal="security", sourcetypes=["WinEventLog"], max_steps=1
        )
        assert len(r["steps"]) == 1
        empty = plan_rollout(catalog=pack_catalog, goal="operations")
        assert empty["steps"] == [] and empty["emptyReason"] == "no-input"

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"goal": "x"},
            {"goal": "security", "level": "guru"},
            {"goal": "security", "max_steps": 11},
            {"goal": "security", "max_steps": True},
            {"goal": "security", "sourcetypes": "wineventlog"},
            {"goal": "security", "sourcetypes": ["x" * 201]},
            {"goal": "security", "paste": "x" * 200_001},
        ],
    )
    def test_rejects_bad_input(self, pack_catalog: Catalog, kwargs: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            plan_rollout(catalog=pack_catalog, **kwargs)


class TestLiveTree:
    """Run against the generated api/v1/starter-packs tree when present."""

    def test_live_drafts(self, live_catalog: Catalog, repo_root: Path) -> None:
        if not (repo_root / "api" / "v1" / "starter-packs" / "index.json").is_file():
            pytest.skip("api/v1/starter-packs not generated")
        r = list_starter_packs(catalog=live_catalog, include_drafts=True)
        jsonschema.validate(r, LIST_STARTER_PACKS_OUTPUT_SCHEMA)
        assert r["count"] >= 10
        plan = plan_rollout(
            catalog=live_catalog,
            goal="operations",
            sourcetypes=["splunkd"],
            indexes=["_internal"],
            include_drafts=True,
        )
        jsonschema.validate(plan, PLAN_ROLLOUT_OUTPUT_SCHEMA)
        assert plan["steps"] and plan["steps"][0]["packId"] == "splunk-platform-ops"
