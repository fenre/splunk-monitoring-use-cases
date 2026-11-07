"""Tests for ``audit-equipment-app-map`` (equipment picker Phase 2)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from splunk_uc.audits import equipment_app_map as audit

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def one_linux_sidecar(monkeypatch: pytest.MonkeyPatch) -> None:
    """The corroboration index walks UC-1.1.1 (Linux, app 833) only."""
    path = next(REPO.glob("content/cat-01-*/UC-1.1.1.json"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: iter([(path, payload)]))


def _minimal_entry(**overrides: Any) -> dict[str, Any]:
    base = {
        "apps": [
            {
                "id": "833",
                "displayName": "Splunk Add-on for Unix and Linux",
                "role": "primary",
                "premium": False,
            }
        ]
    }
    base.update(overrides)
    return base


def _good_document() -> dict[str, Any]:
    return {
        "$schema": "../schemas/equipment-app-map.schema.json",
        "version": "1.0.0",
        "generatedAt": "2026-09-08T00:00:00Z",
        "entries": {
            "linux": _minimal_entry(),
        },
    }


def test_validate_schema_rejects_missing_version(tmp_path: Path) -> None:
    bad = {"generatedAt": "2026-09-08T00:00:00Z", "entries": {"linux": _minimal_entry()}}
    errors = audit._validate_schema(bad)
    assert any("version" in err for err in errors)


def test_audit_map_unknown_slug() -> None:
    document = _good_document()
    document["entries"]["not-a-real-slug"] = _minimal_entry()
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=audit.build_corroboration_index(),
    )
    assert any("unknown equipment slug" in err for err in errors)


def test_audit_map_rejects_non_equipment_kind() -> None:
    document = _good_document()
    document["entries"] = {
        "splunk": {
            "apps": [
                {
                    "id": "1621",
                    "displayName": "Splunk Common Information Model (CIM)",
                    "role": "primary",
                    "premium": False,
                }
            ]
        }
    }
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=Counter({("splunk", "1621"): 1}),
    )
    assert any("kind=equipment" in err for err in errors)


def test_audit_map_requires_apps_or_dsa() -> None:
    document = _good_document()
    document["entries"]["linux"] = {}
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=audit.build_corroboration_index(),
    )
    assert any("requires at least one app or dsaSourceId" in err for err in errors)


def test_audit_map_unknown_splunkbase_id() -> None:
    document = _good_document()
    document["entries"]["linux"]["apps"] = [
        {
            "id": "999999",
            "displayName": "Definitely Not Real",
            "role": "primary",
            "premium": False,
        }
    ]
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=Counter({("linux", "999999"): 1}),
    )
    assert any("not in catalog" in err for err in errors)


def test_audit_map_display_name_mismatch() -> None:
    document = _good_document()
    document["entries"]["linux"]["apps"][0]["displayName"] = "Wrong Name"
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=audit.build_corroboration_index(),
    )
    assert any("displayName" in err and "!=" in err for err in errors)


def test_audit_map_unknown_dsa_source_id() -> None:
    document = {
        "version": "1.0.0",
        "generatedAt": "2026-09-08T00:00:00Z",
        "entries": {"asterisk": {"dsaSourceIds": ["definitely_not_real"]}},
    }
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=Counter(),
    )
    assert any("unknown dsaSourceId" in err for err in errors)


def test_audit_map_zero_uc_corroboration_fails() -> None:
    document = _good_document()
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=Counter(),
    )
    assert any("zero UC support" in err for err in errors)


def test_ingest_only_entry_skips_corroboration() -> None:
    document = {
        "version": "1.0.0",
        "generatedAt": "2026-09-08T00:00:00Z",
        "entries": {"github": {"dsaSourceIds": ["dsa_it_cicd"]}},
    }
    errors = audit.audit_map(
        document,
        catalog=audit._load_catalog(),
        equipment_kinds=audit._load_equipment_slugs(),
        dsa_ids=audit._load_dsa_source_ids(),
        corroboration=Counter(),
    )
    assert errors == []


def test_build_corroboration_index_finds_linux_ta() -> None:
    counts = audit.build_corroboration_index()
    assert counts[("linux", "833")] == 1


def test_main_check_exits_nonzero_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bad_path = tmp_path / "equipment-app-map.json"
    bad_path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "generatedAt": "2026-09-08T00:00:00Z",
                "entries": {"linux": {}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "MAP_PATH", bad_path)
    assert audit.main(["--check"]) == 1


def test_main_passes_for_good_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    good_path = tmp_path / "equipment-app-map.json"
    document = _good_document()
    good_path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    monkeypatch.setattr(audit, "MAP_PATH", good_path)
    with patch.object(audit, "build_corroboration_index", return_value=Counter({("linux", "833"): 3})):
        assert audit.main(["--check"]) == 0
