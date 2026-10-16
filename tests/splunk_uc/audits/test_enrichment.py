"""Enrichment contract: registry ids, evidence quotes, and the caps."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from splunk_uc.audits.enrichment import RegistryIndex, audit_tree, main

REPO = Path(__file__).resolve().parents[3]
SCHEMA = REPO / "schemas" / "uc.schema.json"


def _registries(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "business-outcomes.json").write_text(
        json.dumps({"entries": [{"id": "faster_incident_response", "label": "Faster"}]}),
        encoding="utf-8",
    )
    (root / "business-areas.json").write_text(
        json.dumps({"entries": [{"id": "cloud_operations", "label": "Cloud"}]}),
        encoding="utf-8",
    )
    (root / "personas.json").write_text(
        json.dumps({"entries": [{"id": "auditor", "label": "Auditor"}]}),
        encoding="utf-8",
    )
    (root / "industries.json").write_text(
        json.dumps(
            {
                "entries": [
                    {"id": "healthcare", "name": "Healthcare", "aliases": []},
                    {
                        "id": "contact-center-and-cx-operations",
                        "name": "Contact Center and CX Operations",
                        "aliases": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "sourcetypes.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "id": "wineventlog-security",
                        "canonical": "WinEventLog:Security",
                        "aliases": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "vendor-products.json").write_text(
        json.dumps({"entries": [{"id": "aws", "product": "AWS"}]}),
        encoding="utf-8",
    )


def _assignment(entity_id: str, evidence: str, source: str = "authored", confidence: float = 1) -> dict:
    return {
        "id": entity_id,
        "source": source,
        "confidence": confidence,
        "evidence": evidence,
        "model": "test",
        "version": "1",
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_schema_accepts_enrichment_and_rejects_a_fourth_outcome() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["version"] == "1.9.0"
    validator = jsonschema.Draft202012Validator(schema)
    validator.validate(
        {
            "id": "1.1.1",
            "title": "Example use case title",
            "businessOutcomes": ["faster_incident_response"],
            "enrichment": {
                "businessOutcomes": [
                    _assignment("faster_incident_response", "incident response", "inferred", 0.8)
                ],
                "proposedValues": [
                    {"field": "industries", "value": "space mining", "note": "No registry industry."}
                ],
            },
        }
    )
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(
            {
                "id": "1.1.1",
                "title": "Example use case title",
                "businessOutcomes": ["one", "two", "three", "four"],
            }
        )


def test_real_catalogue_has_no_enrichment_breaks() -> None:
    assert audit_tree() == []


def _contains(node: object, quote: str) -> bool:
    if isinstance(node, str):
        return quote in node
    if isinstance(node, dict):
        return any(_contains(value, quote) for value in node.values())
    if isinstance(node, list):
        return any(_contains(value, quote) for value in node)
    return False


def test_contract_quotes_exist_in_the_named_sidecars() -> None:
    quotes = {
        "content/cat-05-network-infrastructure/UC-5.1.10.json": "`sourcetype=cisco:ios`",
        "content/cat-04-cloud-infrastructure/UC-4.1.199.json": "sourcetype=`aws:cloudtrail`",
        "content/cat-10-security-infrastructure/UC-10.12.42.json": 'sourcetype="WinEventLog:Security"',
        "content/cat-21-industry-verticals/UC-21.14.20.json": "Contact Center and CX Operations",
        "content/cat-01-server-compute/UC-1.1.10.json": "service owners",
        "content/cat-09-identity-access-management/UC-9.1.1.json": (
            "Windows Security Event Log (Event ID 4625 — failed logon)"
        ),
        "content/cat-22-regulatory-compliance/UC-22.35.1.json": "CISO",
    }
    for relative, quote in quotes.items():
        payload = json.loads((REPO / relative).read_text(encoding="utf-8"))
        assert _contains(payload, quote)


def test_unknown_id_missing_evidence_and_owner_copy(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(
        content / "cat-22" / "UC-22.35.1.json",
        {
            "id": "22.35.1",
            "title": "Audit-log continuity",
            "owner": "CISO",
            "description": "Detects an indexing gap.",
            "personas": ["auditor"],
            "businessAreas": ["plant_safety"],
            "enrichment": {
                "personas": [_assignment("auditor", "CISO")],
            },
        },
    )
    issues = audit_tree(content, registries)
    assert any("unknown id plant_safety" in issue for issue in issues)
    assert any("owner copied into personas" in issue for issue in issues)
    assert main(["--check", "--content", str(content), "--registries", str(registries)]) == 1
    assert "enrichment:" in capsys.readouterr().err


def test_explicit_sourcetype_passes_and_prose_does_not(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(
        content / "cat-09" / "UC-9.1.1.json",
        {
            "id": "9.1.1",
            "title": "Brute-Force Login Detection",
            "dataSources": "Windows Security Event Log (Event ID 4625 — failed logon)",
            "spl": 'index=wineventlog sourcetype="WinEventLog:Security"',
            "sourcetypes": ["wineventlog-security"],
            "enrichment": {
                "sourcetypes": [
                    _assignment(
                        "wineventlog-security",
                        "Windows Security Event Log (Event ID 4625 — failed logon)",
                    )
                ]
            },
        },
    )
    issues = audit_tree(content, registries)
    assert any("not an explicit sourcetype" in issue for issue in issues)

    fixed = {
        "id": "9.1.1",
        "title": "Brute-Force Login Detection",
        "spl": 'index=wineventlog sourcetype="WinEventLog:Security"',
        "sourcetypes": ["wineventlog-security"],
        "businessOutcomes": ["faster_incident_response"],
        "enrichment": {
            "sourcetypes": [_assignment("wineventlog-security", 'sourcetype="WinEventLog:Security"')],
            "businessOutcomes": [
                _assignment("faster_incident_response", "Brute-Force Login Detection", "inferred", 0.6)
            ],
        },
    }
    _write(content / "cat-09" / "UC-9.1.1.json", fixed)
    assert audit_tree(content, registries) == []


def test_industry_must_match_the_field_and_evidence_must_be_present(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(
        content / "cat-21" / "UC-21.14.20.json",
        {
            "id": "21.14.20",
            "title": "Healthcare HL7 latency",
            "industry": "Contact Center and CX Operations",
            "industries": ["healthcare"],
            "enrichment": {
                "industries": [_assignment("healthcare", "Healthcare")],
                "businessOutcomes": [_assignment("faster_incident_response", "encryption controls are healthy", "inferred", 0.5)],
            },
        },
    )
    issues = audit_tree(content, registries)
    assert any("does not match the industry field" in issue for issue in issues)
    assert any("is not in the id list" in issue for issue in issues)

    _write(
        content / "cat-21" / "UC-21.14.20.json",
        {
            "id": "21.14.20",
            "title": "Healthcare HL7 latency",
            "industry": "Contact Center and CX Operations",
            "value": "Contact Center and CX Operations",
            "industries": ["contact-center-and-cx-operations"],
            "businessOutcomes": ["faster_incident_response"],
            "enrichment": {
                "industries": [
                    _assignment("contact-center-and-cx-operations", "Contact Center and CX Operations")
                ],
                "businessOutcomes": [{"id": "faster_incident_response", "source": "inferred", "confidence": 0.4, "model": "test", "version": "1"}],
            },
        },
    )
    issues = audit_tree(content, registries)
    assert any("missing evidence" in issue for issue in issues)


def test_cap_and_absent_quote(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(
        content / "cat-22" / "UC-22.1.21.json",
        {
            "id": "22.1.21",
            "title": "GDPR Encryption at Rest Audit Evidence",
            "businessOutcomes": ["faster_incident_response", "faster_incident_response", "nope", "also"],
            "enrichment": {
                "businessOutcomes": [
                    _assignment("faster_incident_response", "encryption controls are healthy", "inferred", 0.4)
                ]
            },
        },
    )
    issues = audit_tree(content, registries)
    assert any("the cap is 3" in issue for issue in issues)
    assert any("unknown id" in issue for issue in issues)
    assert any("does not appear in the use case" in issue for issue in issues)


def test_clean_tree_prints_ok(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(content / "cat-01" / "UC-1.1.1.json", {"id": "1.1.1", "title": "Nothing enriched"})
    assert main(["--content", str(content), "--registries", str(registries)]) == 0
    assert "enrichment: OK" in capsys.readouterr().out


def test_registry_index_loads_the_committed_files() -> None:
    index = RegistryIndex(REPO / "registries")
    assert "cisco-ios" in index.ids["sourcetypes"]
    assert "WinEventLog:Security" in index.sourcetype_spellings["wineventlog-security"]
    assert index.industry_by_norm["contact center and cx operations"] == "contact-center-and-cx-operations"
