"""Fabric resolver: explicit facts become edges, unknowns stay in the report."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.fabric.resolve import invariant_errors, resolve


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _registries(root: Path) -> None:
    _write(
        root / "sourcetypes.json",
        {
            "entries": [
                {
                    "id": "cisco-ios",
                    "canonical": "cisco:ios",
                    "aliases": [],
                    "usageCount": 2,
                    "vendorProduct": "cisco",
                    "addon": "1352",
                    "cimDatasets": ["network-traffic"],
                }
            ]
        },
    )
    _write(
        root / "vendor-products.json",
        {
            "entries": [
                {
                    "id": "cisco",
                    "vendor": "Cisco",
                    "product": "Cisco",
                    "kind": "equipment",
                    "aliases": ["Cisco IOS"],
                    "models": [],
                    "usageCount": 1,
                }
            ]
        },
    )
    _write(
        root / "addons.json",
        {
            "entries": [
                {
                    "id": "1352",
                    "splunkbaseId": 1352,
                    "name": "Splunk Add-on for Cisco",
                    "folderName": "Splunk_TA_cisco",
                    "aliases": ["TA-cisco_ios"],
                    "inSplunkbaseCatalog": True,
                    "usageCount": 1,
                }
            ]
        },
    )
    _write(
        root / "cim.json",
        {
            "datasets": [
                {
                    "id": "network-traffic",
                    "model": "Network_Traffic",
                    "dataset": "All_Traffic",
                    "usageCount": 1,
                }
            ],
            "fields": [
                {
                    "id": "network-traffic-bytes",
                    "name": "bytes",
                    "dataset": "network-traffic",
                    "usageCount": 1,
                }
            ],
        },
    )
    _write(
        root / "industries.json",
        {"entries": [{"id": "energy", "name": "Energy and Utilities", "aliases": [], "usageCount": 2}]},
    )
    _write(
        root / "business-outcomes.json",
        {"entries": [{"id": "reduce_downtime", "label": "Reduce downtime", "phrases": [], "usageCount": 1}]},
    )
    _write(
        root / "business-areas.json",
        {"entries": [{"id": "network_operations", "label": "Network operations", "phrases": [], "usageCount": 1}]},
    )
    _write(
        root / "personas.json",
        {"entries": [{"id": "network_engineer", "label": "Network engineer", "phrases": [], "usageCount": 1}]},
    )


def test_explicit_facts_link_and_unknowns_do_not(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(
        content / "cat-05-network" / "UC-5.1.1.json",
        {
            "id": "5.1.1",
            "title": "Interface Up/Down",
            "spl": 'index=network sourcetype="cisco:ios"',
            "dataSources": "`sourcetype=not-a-real-sourcetype`",
            "app": "`TA-cisco_ios` (Splunkbase 1352)",
            "equipment": ["cisco", "not-a-vendor"],
            "cimModels": ["Network_Traffic"],
            "requiredFields": ["bytes", "made_up_field"],
            "industry": "Energy & Utilities",
            "prerequisiteUseCases": ["5.9.9"],
            "compliance": [
                {"regulation": "gdpr", "version": "2016/679", "clause": "Art.5", "obligationRef": "gdpr@2016/679#Art.5"}
            ],
        },
    )
    _write(
        content / "cat-05-network" / "UC-5.1.2.json",
        {"id": "5.1.2", "title": "Second", "spl": "sourcetype=cisco:ios"},
    )
    fabric = resolve(content=content, registries=registries)
    edges = {(row[0], row[1], row[2], row[3]) for row in fabric.relationships}
    assert ("5.1.1", "uses", "cisco-ios", "authored") in edges
    assert ("5.1.1", "runsOn", "cisco", "authored") in edges
    assert ("5.1.1", "inIndustry", "energy", "authored") in edges
    assert ("5.1.1", "requiresField", "network-traffic-bytes", "authored") in edges
    assert ("5.1.1", "covers", "gdpr-2016-679-art-5", "authored") in edges
    assert not any(row[2] == "not-a-real-sourcetype" for row in fabric.relationships)
    assert not any(row[1] == "requires" and row[2] == "5.9.9" for row in fabric.relationships)
    assert fabric.report["unresolvedCounts"]["sourcetype"] >= 1
    assert fabric.report["unresolvedCounts"]["vendorProduct"] >= 1
    assert fabric.rates["ucCount"] == 2
    assert invariant_errors(fabric, registries) == []


def test_enrichment_lists_add_seller_edges(tmp_path: Path) -> None:
    registries = tmp_path / "registries"
    content = tmp_path / "content"
    _registries(registries)
    _write(
        content / "cat-05-network" / "UC-5.1.2.json",
        {
            "id": "5.1.2",
            "title": "VLAN changes",
            "businessOutcomes": ["reduce_downtime"],
            "businessAreas": ["network_operations"],
            "personas": ["network_engineer"],
            "enrichment": {
                "businessOutcomes": [
                    {
                        "id": "reduce_downtime",
                        "source": "inferred",
                        "confidence": 0.8,
                        "evidence": "VLAN changes",
                        "model": "phrase-list",
                        "version": "1",
                    }
                ],
                "businessAreas": [
                    {
                        "id": "network_operations",
                        "source": "authored",
                        "confidence": 1,
                        "evidence": "VLAN changes",
                        "model": "phrase-list",
                        "version": "1",
                    }
                ],
                "personas": [
                    {
                        "id": "network_engineer",
                        "source": "inferred",
                        "confidence": 0.6,
                        "evidence": "VLAN changes",
                        "model": "phrase-list",
                        "version": "1",
                    }
                ],
            },
        },
    )
    fabric = resolve(content=content, registries=registries)
    edges = {(row[0], row[1], row[2], row[3], row[4]) for row in fabric.relationships}
    assert ("5.1.2", "servesOutcome", "reduce_downtime", "inferred", 0.8) in edges
    assert ("5.1.2", "inArea", "network_operations", "authored", 1.0) in edges
    assert ("5.1.2", "forPersona", "network_engineer", "inferred", 0.6) in edges
    assert invariant_errors(fabric, registries) == []


def test_real_catalogue_counts_match_files_and_registries(tmp_path: Path) -> None:
    fabric = resolve()
    errors = invariant_errors(fabric)
    assert errors == []
    assert fabric.rates["sourcetypeRate"] == 1.0
    assert fabric.rates["ucCount"] == sum(1 for _ in Path("content").glob("cat-*/UC-*.json"))
    from splunk_uc.fabric.publish import write_parquet

    assert write_parquet(fabric, tmp_path)
    import pyarrow.parquet as pq

    entities = pq.read_table(tmp_path / "entities.parquet")
    relationships = pq.read_table(tmp_path / "relationships.parquet")
    assert entities.num_rows == len(fabric.entities)
    assert relationships.num_rows == len(fabric.relationships)
