"""Tests for ``splunk_uc.audits.starter_packs``."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import starter_packs as sp

REPO = Path(__file__).resolve().parents[3]


def _uc(uc_id: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": uc_id,
        "title": f"UC {uc_id}",
        "status": "verified",
        "spl": "index=os sourcetype=linux_secure sshd failed",
        "dataSources": "sourcetype=linux_secure",
        "equipment": ["linux"],
        "splunkbaseApps": [
            {"id": 833, "name": "Splunk Add-on for Unix and Linux", "role": "primary"}
        ],
        "prerequisiteUseCases": [],
    }
    payload.update(extra)
    return payload


def _pack(pid: str, goal: str, pair: str | None, ucs: list[str], **extra: Any) -> dict[str, Any]:
    pack: dict[str, Any] = {
        "id": pid,
        "title": f"Pack {pid}",
        "description": "A test pack that exercises the starter-pack audit contract end to end.",
        "goal": goal,
        "status": "draft",
        "pairId": pair,
        "equipment": ["linux"],
        "requiredData": {
            "splunkbaseApps": [{"id": 833, "displayName": "Splunk Add-on for Unix and Linux"}],
            "sourcetypes": ["linux_secure"],
            "indexes": [],
            "notes": "Enable the secure log monitor.",
        },
        "industrySources": [{"url": "https://example.com/list", "control": "Example control"}],
        "steps": [{"ucId": u, "order": n} for n, u in enumerate(ucs, 1)],
        "nextPacks": [],
    }
    pack.update(extra)
    return pack


CATALOG = {"833": {"displayName": "Splunk Add-on for Unix and Linux"}}
EQUIPMENT = {"linux", "windows", "cisco_thousandeyes"}


@pytest.fixture(autouse=True)
def _fixed_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sp, "uc_tier", lambda path, sidecar: sidecar.get("_tier", "gold"))


def _run(packs: dict[str, dict[str, Any]], ucs: dict[str, dict[str, Any]]) -> list[sp.Finding]:
    return sp.audit_packs(
        {pid: (Path(f"{pid}.json"), p) for pid, p in packs.items()},
        {f"UC-{u['id']}": (Path(f"UC-{u['id']}.json"), u) for u in ucs.values()},
        catalog_apps=CATALOG,
        equipment_ids=EQUIPMENT,
        aliases=sp.alias_map([["xmlwineventlog", "wineventlog"]]),
    )


def _codes(findings: list[sp.Finding], level: str = "error") -> set[str]:
    return {f.code for f in findings if f.level == level}


def _base() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    ucs = {u: _uc(u) for u in ("1.1.1", "1.1.2", "1.1.3", "1.1.4")}
    packs = {
        "lin-sec": _pack("lin-sec", "security", "lin-ops", ["UC-1.1.1", "UC-1.1.2"]),
        "lin-ops": _pack("lin-ops", "operations", "lin-sec", ["UC-1.1.3", "UC-1.1.4"]),
    }
    return packs, ucs


def test_clean_pair_passes() -> None:
    packs, ucs = _base()
    assert _run(packs, ucs) == []


def test_missing_goal_is_schema_error() -> None:
    packs, ucs = _base()
    del packs["lin-sec"]["goal"]
    assert "schema" in _codes(_run(packs, ucs))


def test_unknown_goal_is_schema_error() -> None:
    packs, ucs = _base()
    packs["lin-sec"]["goal"] = "compliance"
    assert "schema" in _codes(_run(packs, ucs))


def test_unknown_uc() -> None:
    packs, ucs = _base()
    packs["lin-sec"]["steps"].append({"ucId": "UC-9.9.9", "order": 3})
    assert "unknown-uc" in _codes(_run(packs, ucs))


def test_pair_overlap() -> None:
    packs, ucs = _base()
    packs["lin-ops"]["steps"][0]["ucId"] = "UC-1.1.1"
    assert "pair-overlap" in _codes(_run(packs, ucs))


def test_pair_same_goal_and_reciprocity() -> None:
    packs, ucs = _base()
    packs["lin-ops"]["goal"] = "security"
    assert "pair-same-goal" in _codes(_run(packs, ucs))
    packs, ucs = _base()
    packs["lin-ops"]["pairId"] = None
    assert "pair-not-reciprocal" in _codes(_run(packs, ucs))


def test_prereq_order_violation() -> None:
    packs, ucs = _base()
    ucs["1.1.1"]["prerequisiteUseCases"] = ["UC-1.1.2"]
    assert "prereq-order" in _codes(_run(packs, ucs))


def test_prereq_in_pair_is_fine_outside_is_warning() -> None:
    packs, ucs = _base()
    ucs["1.1.1"]["prerequisiteUseCases"] = ["UC-1.1.3"]
    assert _run(packs, ucs) == []
    ucs["1.1.1"]["prerequisiteUseCases"] = ["UC-7.7.7"]
    assert "prereq-outside" in _codes(_run(packs, ucs), "warning")


def test_data_not_covered() -> None:
    packs, ucs = _base()
    ucs["1.1.2"]["spl"] = "index=os sourcetype=vmstat"
    ucs["1.1.2"]["dataSources"] = "vmstat.sh"
    assert "data-coverage" in _codes(_run(packs, ucs))


def test_internal_index_counts_as_coverage() -> None:
    packs, ucs = _base()
    ucs["1.1.2"]["spl"] = 'index=_audit action="edit_user"'
    ucs["1.1.2"]["dataSources"] = "_audit"
    packs["lin-sec"]["requiredData"]["indexes"] = ["_audit"]
    assert "data-coverage" not in _codes(_run(packs, ucs))


def test_alias_normalisation_counts_as_coverage() -> None:
    packs, ucs = _base()
    ucs["1.1.2"]["spl"] = "index=wineventlog sourcetype=WinEventLog EventCode=4728"
    packs["lin-sec"]["requiredData"]["sourcetypes"] = ["linux_secure", "XmlWinEventLog"]
    assert "data-coverage" not in _codes(_run(packs, ucs))


def test_equipment_and_app_coverage() -> None:
    packs, ucs = _base()
    ucs["1.1.2"]["equipment"] = ["windows"]
    assert "equipment-coverage" in _codes(_run(packs, ucs))
    packs, ucs = _base()
    ucs["1.1.2"]["splunkbaseApps"] = [{"id": 742, "name": "Windows", "role": "data-source"}]
    assert "app-coverage" in _codes(_run(packs, ucs))


def test_next_packs_unknown_and_self() -> None:
    packs, ucs = _base()
    packs["lin-sec"]["nextPacks"] = ["lin-sec", "nope"]
    codes = _codes(_run(packs, ucs))
    assert {"next-self", "next-unknown"} <= codes


def test_mutual_next_packs_allowed() -> None:
    packs, ucs = _base()
    packs["lin-sec"]["nextPacks"] = ["lin-ops"]
    packs["lin-ops"]["nextPacks"] = ["lin-sec"]
    assert _run(packs, ucs) == []


def test_step_order_and_duplicates() -> None:
    packs, ucs = _base()
    packs["lin-sec"]["steps"][1]["order"] = 5
    assert "step-order" in _codes(_run(packs, ucs))
    packs, ucs = _base()
    packs["lin-sec"]["steps"].append({"ucId": "UC-1.1.1", "order": 3})
    assert "duplicate-step" in _codes(_run(packs, ucs))


def test_unknown_app_and_equipment() -> None:
    packs, ucs = _base()
    packs["lin-sec"]["requiredData"]["splunkbaseApps"].append(
        {"id": 999999, "displayName": "Ghost"}
    )
    packs["lin-sec"]["equipment"].append("toaster")
    codes = _codes(_run(packs, ucs))
    assert {"unknown-app", "unknown-equipment"} <= codes


def test_quality_warnings_block_publish_only() -> None:
    packs, ucs = _base()
    ucs["1.1.1"]["status"] = "draft"
    ucs["1.1.2"]["_tier"] = "bronze"
    ucs["1.1.2"]["compliance"] = [{"requires_sme_review": True}]
    findings = _run(packs, ucs)
    assert _codes(findings) == set()
    assert {"uc-not-verified", "uc-depth", "uc-sme-review"} <= _codes(findings, "warning")
    packs["lin-sec"]["status"] = "published"
    assert "published-with-warnings" in _codes(_run(packs, ucs))


def test_published_pack_rejects_cat25() -> None:
    packs, ucs = _base()
    ucs["25.1.1"] = _uc("25.1.1")
    packs["lin-sec"]["status"] = "published"
    packs["lin-sec"]["steps"].append({"ucId": "UC-25.1.1", "order": 3})
    assert "published-cat25" in _codes(_run(packs, ucs))


def test_id_must_match_file_name() -> None:
    packs, ucs = _base()
    renamed = copy.deepcopy(packs["lin-sec"])
    renamed["id"] = "other"
    packs["lin-sec"] = renamed
    assert "id-mismatch" in _codes(_run(packs, ucs))


def test_alias_groups_reject_duplicates() -> None:
    findings = sp.audit_alias_groups([["a", "b"], ["b", "c"]])
    assert [f.code for f in findings] == ["alias-duplicate"]


def test_repository_packs_have_no_errors() -> None:
    packs, findings = sp.run_audit()
    assert len(packs) >= 10
    errors = [f.render() for f in findings if f.level == "error"]
    assert errors == []
    goals = {p["goal"] for _path, p in packs.values()}
    assert goals == {"security", "operations"}
