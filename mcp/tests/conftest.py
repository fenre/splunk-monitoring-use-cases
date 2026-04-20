"""Shared pytest fixtures for the MCP server test suite.

The catalogue is huge (6,424 UCs, ~855 KB index), so we intentionally use
the *live* ``api/v1`` tree shipped in this repository whenever the test
is concerned with real-world shapes. That keeps the tests honest and
avoids drift between fixtures and reality — the CI drift guard
(``scripts/audit_mcp_tool_schemas.py``) runs against the same data.

For edge-case tests that require a missing or malformed endpoint, the
``synthetic_catalog_root`` fixture builds a tiny fake ``api/v1`` tree on
disk. The fixture mirrors the real schema exactly (same top-level
keys, same per-item keys) so tests cannot succeed against a shape that
production would reject.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from splunk_uc_mcp.catalog import Catalog


LOG = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Root of this git checkout (parent of ``mcp/``)."""

    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "api" / "v1" / "manifest.json").is_file():
            return candidate
    pytest.fail(
        "Could not locate repo root — expected api/v1/manifest.json above the test dir"
    )


@pytest.fixture(scope="session")
def live_catalog(repo_root: Path) -> Iterator[Catalog]:
    """A :class:`Catalog` bound to the real repository tree.

    Use this whenever a test simply wants to call a tool against the
    genuine API surface. Session-scoped so every test reuses the same
    LRU-warmed loader.
    """

    with Catalog(catalog_root=repo_root) as cat:
        yield cat


@pytest.fixture
def synthetic_catalog_root(tmp_path: Path) -> Path:
    """Build a minimal ``api/v1`` tree that mirrors production shapes.

    Includes just enough UCs, regulations, equipment, and a gap file
    for edge-case tests. Each JSON document uses the same top-level
    keys that the real generator emits so the tools cannot accidentally
    assume a synthetic-only shape.
    """

    v1 = tmp_path / "api" / "v1"
    (v1 / "recommender").mkdir(parents=True)
    (v1 / "compliance" / "ucs").mkdir(parents=True)
    (v1 / "compliance" / "regulations").mkdir(parents=True)
    (v1 / "equipment").mkdir(parents=True)

    (v1 / "manifest.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "catalogueVersion": "0.0.0-test",
                "generatedAt": "2026-04-16T00:00:00Z",
                "endpoints": {},
                "counts": {"useCases": 2},
                "status": "test",
            },
            indent=2,
        )
    )

    (v1 / "recommender" / "uc-thin.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "catalogueVersion": "0.0.0-test",
                "generatedAt": "2026-04-16T00:00:00Z",
                "useCaseCount": 2,
                "useCases": [
                    {
                        "id": "1.1.1",
                        "title": "Test UC One",
                        "value": "Detect baseline linux anomalies",
                        "criticality": "low",
                        "difficulty": "easy",
                        "wave": "crawl",
                        "prerequisiteUseCases": [],
                        "splunkPillar": "security",
                        "monitoringType": ["detection"],
                        "app": ["splunk_ta_linux"],
                        "equipment": ["linux"],
                        "equipmentModels": [],
                        "mitreAttack": [],
                        "cimModels": ["Authentication"],
                    },
                    {
                        "id": "22.1.1",
                        "title": "GDPR PII access detection",
                        "value": "Spot anomalous PII access patterns",
                        "criticality": "high",
                        "difficulty": "medium",
                        "wave": "walk",
                        "prerequisiteUseCases": ["UC-1.1.1"],
                        "splunkPillar": "compliance",
                        "monitoringType": ["detection"],
                        "app": ["splunk_ta_nix"],
                        "equipment": ["linux", "azure"],
                        "equipmentModels": ["azure:vm"],
                        "mitreAttack": ["T1078"],
                        "cimModels": ["Authentication"],
                    },
                ],
            }
        )
    )

    (v1 / "compliance" / "ucs" / "index.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "generatedAt": "2026-04-16T00:00:00Z",
                "count": 1,
                "items": [
                    {
                        "id": "22.1.1",
                        "title": "GDPR PII access detection",
                        "category": "Regulatory & Compliance",
                        "controlFamily": "GDPR",
                        "criticality": "high",
                        "difficulty": "medium",
                        "equipment": ["linux", "azure"],
                        "equipmentModels": ["azure:vm"],
                        "hasControlTest": True,
                        "mitreAttack": ["T1078"],
                        "monitoringType": ["detection"],
                        "owner": "privacy",
                        "regulationIds": ["gdpr@2016/679"],
                    }
                ],
            }
        )
    )

    (v1 / "compliance" / "ucs" / "22.1.1.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "id": "22.1.1",
                "title": "GDPR PII access detection",
                "value": "Spot anomalous PII access patterns",
                "wave": "walk",
                "prerequisiteUseCases": ["UC-1.1.1"],
                "equipment": ["linux", "azure"],
                "mitreAttack": ["T1078"],
                "compliance": [
                    {
                        "regulation": "GDPR",
                        "regulationId": "gdpr",
                        "version": "2016/679",
                        "clause": "Art.5",
                        "mode": "detect",
                        "assurance": "primary",
                        "assurance_rationale": "Test rationale",
                    }
                ],
                "spl": "index=azure | stats count by user",
            }
        )
    )

    (v1 / "compliance" / "regulations" / "index.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "schemaVersion": 1,
                "frameworkCount": 1,
                "frameworks": [
                    {
                        "id": "gdpr",
                        "name": "General Data Protection Regulation",
                        "shortName": "GDPR",
                        "tier": 1,
                        "jurisdiction": ["EU"],
                        "tags": ["privacy"],
                        "versions": ["2016/679"],
                        "endpoint": "/api/v1/compliance/regulations/gdpr.json",
                    }
                ],
            }
        )
    )

    (v1 / "compliance" / "regulations" / "gdpr.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "generatedAt": "2026-04-16T00:00:00Z",
                "id": "gdpr",
                "name": "General Data Protection Regulation",
                "shortName": "GDPR",
                "tier": 1,
                "jurisdiction": ["EU"],
                "tags": ["privacy"],
                "version": "base",
            }
        )
    )

    (v1 / "compliance" / "regulations" / "gdpr@2016-679.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "generatedAt": "2026-04-16T00:00:00Z",
                "id": "gdpr",
                "name": "General Data Protection Regulation",
                "shortName": "GDPR",
                "tier": 1,
                "jurisdiction": ["EU"],
                "tags": ["privacy"],
                "version": {"label": "2016/679", "status": "current"},
            }
        )
    )

    (v1 / "compliance" / "gaps.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "generatedAt": "2026-04-16T00:00:00Z",
                "entries": [
                    {
                        "regulationId": "gdpr",
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "tier": 1,
                        "commonClausesTotal": 10,
                        "commonClausesCovered": 6,
                        "commonClausesUncovered": ["Art.17", "Art.32"],
                        "commonClausesUncoveredCount": 2,
                        "priorityWeightedUncovered": 2.5,
                        "regulationEndpoint": (
                            "/api/v1/compliance/regulations/gdpr.json"
                        ),
                    }
                ],
                "summary": {"totalRegulations": 1, "totalUncoveredClauses": 2},
            }
        )
    )

    (v1 / "equipment" / "index.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "catalogueVersion": "0.0.0-test",
                "generatedAt": "2026-04-16T00:00:00Z",
                "description": "Test equipment index",
                "equipmentCount": 2,
                "modelCount": 1,
                "useCasesWithEquipmentTotal": 2,
                "equipment": [
                    {
                        "id": "azure",
                        "label": "Microsoft Azure",
                        "useCaseCount": 1,
                        "complianceUseCaseCount": 1,
                        "regulationIds": ["gdpr"],
                        "models": [{"id": "azure_vm", "label": "Azure VM"}],
                        "endpoint": "/api/v1/equipment/azure.json",
                    },
                    {
                        "id": "linux",
                        "label": "Linux",
                        "useCaseCount": 2,
                        "complianceUseCaseCount": 1,
                        "regulationIds": ["gdpr"],
                        "models": [],
                        "endpoint": "/api/v1/equipment/linux.json",
                    },
                ],
            }
        )
    )

    (v1 / "equipment" / "azure.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "catalogueVersion": "0.0.0-test",
                "generatedAt": "2026-04-16T00:00:00Z",
                "id": "azure",
                "label": "Microsoft Azure",
                "useCaseCount": 1,
                "complianceUseCaseCount": 1,
                "models": [
                    {
                        "id": "azure_vm",
                        "label": "Azure VM",
                        "modelId": "vm",
                        "useCaseCount": 1,
                        "useCaseIds": ["22.1.1"],
                    }
                ],
                "useCaseIds": ["22.1.1"],
                "useCasesByCategory": [
                    {
                        "category": 22,
                        "useCaseCount": 1,
                        "useCaseIds": ["22.1.1"],
                    }
                ],
                "indexEndpoint": "/api/v1/equipment/index.json",
                "regulationIds": ["gdpr"],
                "regulations": [
                    {
                        "regulationId": "gdpr",
                        "regulationEndpoint": (
                            "/api/v1/compliance/regulations/gdpr@2016-679.json"
                        ),
                        "useCaseCount": 1,
                        "useCaseIds": ["22.1.1"],
                        "clauseMappings": [
                            {
                                "clause": "Art.5",
                                "useCaseId": "22.1.1",
                                "version": "2016/679",
                            }
                        ],
                    }
                ],
            }
        )
    )

    (v1 / "equipment" / "linux.json").write_text(
        json.dumps(
            {
                "apiVersion": "v1",
                "catalogueVersion": "0.0.0-test",
                "generatedAt": "2026-04-16T00:00:00Z",
                "id": "linux",
                "label": "Linux",
                "useCaseCount": 2,
                "complianceUseCaseCount": 1,
                "models": [],
                "useCaseIds": ["1.1.1", "22.1.1"],
                "useCasesByCategory": [
                    {
                        "category": 1,
                        "useCaseCount": 1,
                        "useCaseIds": ["1.1.1"],
                    },
                    {
                        "category": 22,
                        "useCaseCount": 1,
                        "useCaseIds": ["22.1.1"],
                    },
                ],
                "indexEndpoint": "/api/v1/equipment/index.json",
                "regulationIds": ["gdpr"],
                "regulations": [
                    {
                        "regulationId": "gdpr",
                        "regulationEndpoint": (
                            "/api/v1/compliance/regulations/gdpr@2016-679.json"
                        ),
                        "useCaseCount": 1,
                        "useCaseIds": ["22.1.1"],
                        "clauseMappings": [
                            {
                                "clause": "Art.5",
                                "useCaseId": "22.1.1",
                                "version": "2016/679",
                            }
                        ],
                    }
                ],
            }
        )
    )

    return tmp_path


@pytest.fixture
def synthetic_catalog(synthetic_catalog_root: Path) -> Iterator[Catalog]:
    """Catalog pointed at the synthetic tree."""

    with Catalog(catalog_root=synthetic_catalog_root) as cat:
        yield cat


@pytest.fixture(autouse=True)
def _isolate_default_catalog_cache() -> Iterator[None]:
    """Clear the ``default_catalog()`` LRU cache between tests.

    Ensures that one test's catalogue state doesn't bleed into another
    (e.g. a synthetic-root test followed by a real-root test). Older
    builds of the catalog module exposed the cache as
    ``default_catalog``; the guard keeps the fixture resilient if the
    helper is renamed or removed.
    """

    from splunk_uc_mcp import catalog as catalog_module

    cache = getattr(catalog_module, "default_catalog", None)
    if cache is not None and hasattr(cache, "cache_clear"):
        cache.cache_clear()
    yield
    cache = getattr(catalog_module, "default_catalog", None)
    if cache is not None and hasattr(cache, "cache_clear"):
        cache.cache_clear()


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove env vars that influence Catalog defaults."""

    for var in ("SPLUNK_UC_CATALOG_ROOT", "SPLUNK_UC_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
