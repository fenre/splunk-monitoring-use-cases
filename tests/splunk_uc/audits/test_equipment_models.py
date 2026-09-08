"""Unit tests for ``splunk_uc.audits.equipment_models``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import equipment_models as em
from splunk_uc.audits import _uc_walk


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tools" / "data-sizing").mkdir(parents=True)
    (repo / "content" / "cat-01-test").mkdir(parents=True)

    mapping = """window.EQUIPMENT_GROUPS = [
  { name: 'Test', ids: ['paloalto', 'missing_from_registry'] },
];
window.DSA_EQUIPMENT_MAP = {};
"""
    (repo / "tools" / "data-sizing" / "mapping.js").write_text(mapping, encoding="utf-8")

    monkeypatch.setattr(em, "REPO_ROOT", repo)
    monkeypatch.setattr(em, "MAPPING_JS", repo / "tools" / "data-sizing" / "mapping.js")
    monkeypatch.setattr(_uc_walk, "REPO", repo)
    monkeypatch.setattr(_uc_walk, "CONTENT", repo / "content")

    registry = [
        {
            "id": "paloalto",
            "tas": ["Palo Alto"],
            "kind": "equipment",
            "vendor": "Palo Alto Networks",
            "models": [{"id": "pan_firewall", "label": "Firewall", "tas": ["PAN-OS"]}],
        },
        {
            "id": "splunk_es",
            "tas": ["Splunk ES"],
            "kind": "splunk-platform",
            "vendor": "Splunk",
        },
    ]

    def _fake_load_registry() -> tuple[set[str], set[str], list[dict[str, object]]]:
        equipment_ids = {entry["id"] for entry in registry}
        compounds = {"paloalto_pan_firewall"}
        return equipment_ids, compounds, registry

    monkeypatch.setattr(em, "_load_registry", _fake_load_registry)
    return repo


def _write_sidecar(repo: Path, payload: dict[str, object]) -> None:
    path = repo / "content" / "cat-01-test" / "UC-1.1.1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_parse_equipment_group_ids_reads_mapping_js() -> None:
    text = """window.EQUIPMENT_GROUPS = [
  { name: 'A', ids: ['linux','windows'] },
  { name: 'B', ids: ['paloalto'] },
];
window.DSA_EQUIPMENT_MAP = { "linux": [] };
"""
    assert em.parse_equipment_group_ids(text) == {"linux", "windows", "paloalto"}


def test_audit_registry_flags_missing_group_membership() -> None:
    entries = [
        {"id": "paloalto", "kind": "equipment", "vendor": "Palo Alto Networks"},
        {"id": "zeek", "kind": "equipment", "vendor": "Zeek Project"},
    ]
    findings = em.audit_registry(entries, {"paloalto"})
    kinds = {f.kind for f in findings}
    assert "equipment-missing-from-groups" in kinds


def test_audit_registry_flags_vendor_spelling_drift() -> None:
    entries = [
        {"id": "a", "kind": "equipment", "vendor": "Palo Alto Networks"},
        {"id": "b", "kind": "equipment", "vendor": "Palo  Alto Networks"},
    ]
    findings = em.audit_registry(entries, {"a", "b"})
    assert any(f.kind == "vendor-spelling-inconsistent" for f in findings)


def test_audit_sidecars_flags_unresolved_slug_and_unknown_model(
    fake_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_uc_walk, "REPO", fake_repo)
    monkeypatch.setattr(_uc_walk, "CONTENT", fake_repo / "content")
    _write_sidecar(
        fake_repo,
        {
            "id": "1.1.1",
            "equipment": ["palo-alto", "not_registered"],
            "equipmentModels": ["paloalto_pan_firewall", "paloalto_missing_model", "snmp_generic"],
        },
    )
    equipment_ids, compounds, _entries = em._load_registry()
    findings = em.audit_sidecars(equipment_ids, compounds)
    kinds = {f.kind for f in findings}
    assert "unresolved-equipment-slug" in kinds
    assert "unknown-equipment-model" in kinds
    assert "generic-suffix-model" in kinds
    assert not any("palo-alto" in f.message for f in findings if f.kind == "unresolved-equipment-slug")


def test_main_check_exits_nonzero_on_findings(fake_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_uc_walk, "REPO", fake_repo)
    monkeypatch.setattr(_uc_walk, "CONTENT", fake_repo / "content")
    _write_sidecar(fake_repo, {"id": "1.1.1", "equipment": ["not_registered"]})
    assert em.main(["--check"]) == 1


def test_main_passes_when_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [{"id": "paloalto", "kind": "equipment", "vendor": "Palo Alto Networks"}]

    def _clean_registry() -> tuple[set[str], set[str], list[dict[str, object]]]:
        return {"paloalto"}, set(), entries

    monkeypatch.setattr(em, "_load_registry", _clean_registry)
    monkeypatch.setattr(em, "audit_sidecars", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(em, "parse_equipment_group_ids", lambda _text: {"paloalto"})

    class _MappingPath:
        def read_text(self, encoding: str = "utf-8") -> str:
            return "window.EQUIPMENT_GROUPS = [];\nwindow.DSA_EQUIPMENT_MAP = {};"

    monkeypatch.setattr(em, "MAPPING_JS", _MappingPath())
    assert em.main(["--check"]) == 0
