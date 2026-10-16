"""Pilot sampling, phrase grades, and surgical enrichment inserts."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.audits.enrichment import audit_tree
from splunk_uc.fabric.enrich import (
    PHRASE_GRADE,
    _Catalog,
    assign_uc,
    grade_assignment,
    insert_enrichment,
    pilot_paths,
)

REPO = Path(__file__).resolve().parents[3]


def test_every_registry_phrase_has_a_grade() -> None:
    catalog = _Catalog(REPO / "registries")
    missing = []
    for field, rows in catalog.phrases.items():
        for phrase, _entity_id in rows:
            if phrase.casefold() not in PHRASE_GRADE[field]:
                missing.append(f"{field}:{phrase}")
    assert missing == []


def test_pilot_is_seeded_and_covers_every_category() -> None:
    first = pilot_paths()
    second = pilot_paths()
    assert [path.as_posix() for path in first] == [path.as_posix() for path in second]
    assert len(first) == 300
    counts: dict[str, int] = {}
    for path in first:
        counts[path.parent.name] = counts.get(path.parent.name, 0) + 1
    assert len(counts) == 25
    assert all(count >= 8 for count in counts.values())
    assert any(name.startswith("cat-18-") for name in counts)
    assert any(name.startswith("cat-25-") for name in counts)


def test_field_names_and_scripts_are_not_sourcetypes() -> None:
    catalog = _Catalog(REPO / "registries")
    uc = json.loads((REPO / "content/cat-01-server-compute/UC-1.1.4.json").read_text(encoding="utf-8"))
    payload = assign_uc(uc, catalog, "strict-1")
    assert "iostat" in payload["sourcetypes"]
    assert "device" not in payload["sourcetypes"]
    assert "iostat-sh" not in payload["sourcetypes"]
    row = next(item for item in payload["enrichment"]["sourcetypes"] if item["id"] == "iostat")
    assert grade_assignment(uc, "sourcetypes", row, catalog) == "correct"
    assert "iostat.sh" not in row["evidence"]


def test_insert_keeps_the_original_bytes() -> None:
    source = REPO / "content" / "cat-05-network-infrastructure" / "UC-5.1.10.json"
    original = source.read_text(encoding="utf-8")
    payload = {
        "sourcetypes": ["cisco-ios"],
        "enrichment": {
            "sourcetypes": [
                {
                    "id": "cisco-ios",
                    "source": "authored",
                    "confidence": 1,
                    "evidence": "`sourcetype=cisco:ios`",
                    "model": "explicit-sourcetype",
                    "version": "strict-1",
                }
            ]
        },
    }
    updated = insert_enrichment(original, payload)
    assert updated.startswith(original.rstrip()[:-1].rstrip())
    parsed = json.loads(updated)
    assert parsed["title"] == json.loads(original)["title"]
    assert parsed["spl"] == json.loads(original)["spl"]
    assert parsed["sourcetypes"] == ["cisco-ios"]


def test_loose_owner_copy_is_wrong_and_strict_omits_it(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    _tiny_registries(registries)
    catalog = _Catalog(registries)
    uc = {
        "id": "22.35.1",
        "title": "Audit-log continuity",
        "owner": "CISO",
        "description": "Detects an indexing gap in the audit trail.",
        "value": "The control shows an indexing gap.",
        "industry": "Healthcare",
    }
    loose = assign_uc(uc, catalog, "loose-1")
    assert "auditor" in loose["personas"]
    copied = next(row for row in loose["enrichment"]["personas"] if row["id"] == "auditor")
    assert grade_assignment(uc, "personas", copied, catalog) == "wrong"
    strict = assign_uc(uc, catalog, "strict-1")
    assert "personas" not in strict
    assert strict["industries"] == ["healthcare"]


def test_prose_sourcetype_fails_the_grade_and_strict_keeps_the_explicit_one(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    _tiny_registries(registries)
    catalog = _Catalog(registries)
    uc = {
        "id": "9.1.1",
        "title": "Brute-Force Login Detection",
        "description": "Windows Security Event Log shows failed logons. Operators sometimes nickname the feed not-a-real-sourcetype.",
        "value": "Account takeover risk falls when the failures are visible.",
        "dataSources": "Windows Security Event Log",
        "spl": 'index=wineventlog sourcetype="WinEventLog:Security"',
        "equipment": ["windows"],
        "app": "Splunk Add-on for Microsoft Windows",
    }
    loose = assign_uc(uc, catalog, "loose-1")
    strict = assign_uc(uc, catalog, "strict-1")
    assert strict["sourcetypes"] == ["wineventlog-security"]
    assert grade_assignment(uc, "sourcetypes", strict["enrichment"]["sourcetypes"][0], catalog) == "correct"
    prose = next(row for row in loose["enrichment"]["sourcetypes"] if row["id"] == "not-real")
    assert grade_assignment(uc, "sourcetypes", prose, catalog) == "wrong"


def test_written_sidecar_passes_the_audit(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content" / "cat-09"
    _tiny_registries(registries)
    catalog = _Catalog(registries)
    uc = {
        "id": "9.1.1",
        "title": "Brute-Force Login Detection",
        "description": "Failed logons on Windows Security.",
        "value": "Account takeover risk falls.",
        "spl": 'index=wineventlog sourcetype="WinEventLog:Security"',
        "app": "Windows",
        "equipment": ["windows"],
    }
    text = json.dumps(uc, indent=2) + "\n"
    path = content / "UC-9.1.1.json"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    payload = assign_uc(uc, catalog, "strict-1")
    path.write_text(insert_enrichment(text, payload), encoding="utf-8")
    assert audit_tree(content.parent, registries) == []


def _tiny_registries(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "business-outcomes.json").write_text(
        json.dumps({"entries": [{"id": "faster_incident_response", "label": "Faster", "phrases": ["incident response", "triage"]}]}),
        encoding="utf-8",
    )
    (root / "business-areas.json").write_text(
        json.dumps({"entries": [{"id": "security_operations", "label": "Security", "phrases": ["security operations", "compliance"]}]}),
        encoding="utf-8",
    )
    (root / "personas.json").write_text(
        json.dumps({"entries": [{"id": "auditor", "label": "Auditor", "phrases": ["auditor"]}]}),
        encoding="utf-8",
    )
    (root / "industries.json").write_text(
        json.dumps({"entries": [{"id": "healthcare", "name": "Healthcare", "aliases": []}]}),
        encoding="utf-8",
    )
    (root / "sourcetypes.json").write_text(
        json.dumps(
            {
                "entries": [
                    {"id": "wineventlog-security", "canonical": "WinEventLog:Security", "aliases": ["wineventlog:security"]},
                    {"id": "not-real", "canonical": "not-a-real-sourcetype", "aliases": []},
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "vendor-products.json").write_text(
        json.dumps({"entries": [{"id": "windows", "product": "Windows", "vendor": "Microsoft", "aliases": ["WinEventLog"]}]}),
        encoding="utf-8",
    )
