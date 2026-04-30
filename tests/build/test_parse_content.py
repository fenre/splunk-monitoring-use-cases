"""Tests for tools/build/parse_content.py — schema validation and content loading."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import parse_content  # noqa: E402


class TestGetUcSchema:
    def test_loads_schema_from_repo(self):
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False
        schema = parse_content._get_uc_schema(REPO_ROOT)
        assert schema is not None
        assert schema.get("type") == "object"
        assert "properties" in schema
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False

    def test_returns_none_for_missing_schema(self, tmp_path):
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False
        result = parse_content._get_uc_schema(tmp_path)
        assert result is None
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False


class TestValidateUcJson:
    @pytest.fixture(autouse=True)
    def _load_schema(self):
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False
        self.schema = parse_content._get_uc_schema(REPO_ROOT)
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False
        if self.schema is None:
            pytest.skip("jsonschema not available or schema file missing")

    def test_valid_uc_passes(self):
        uc = {
            "id": "99.1.1",
            "title": "Test Use Case",
            "criticality": "high",
            "difficulty": "beginner",
            "monitoringType": ["Availability"],
            "splunkPillar": "Security",
            "value": "Test value for this use case that explains why it matters.",
            "description": "Test description of what this use case detects or monitors.",
            "app": "test_app",
            "dataSources": "index=main sourcetype=test:log",
            "spl": "index=main sourcetype=test:log | stats count",
            "implementation": "Install the TA and configure the input.",
            "visualization": "Single value panel",
            "cimModels": ["Endpoint"],
            "references": [{"url": "https://example.com", "title": "Example"}],
        }
        errors = parse_content._validate_uc_json(uc, Path("test.json"), self.schema)
        assert errors == []

    def test_missing_required_field(self):
        uc = {"title": "Missing ID"}
        errors = parse_content._validate_uc_json(uc, Path("test.json"), self.schema)
        assert len(errors) > 0
        assert any("id" in e for e in errors)

    def test_invalid_criticality(self):
        uc = {
            "id": "99.1.1",
            "title": "Test",
            "criticality": "INVALID_VALUE",
        }
        errors = parse_content._validate_uc_json(uc, Path("test.json"), self.schema)
        assert len(errors) > 0
        assert any("criticality" in e for e in errors)

    def test_invalid_monitoring_type(self):
        uc = {
            "id": "99.1.1",
            "title": "Test",
            "monitoringType": ["Wireless"],
        }
        errors = parse_content._validate_uc_json(uc, Path("test.json"), self.schema)
        assert len(errors) > 0
        assert any("monitoringType" in e for e in errors)


class TestCatalogLoad:
    def test_load_returns_catalog(self):
        cat = parse_content.load(REPO_ROOT, reproducible=True)
        assert isinstance(cat, parse_content.Catalog)
        assert len(cat.categories) > 0

    def test_catalog_has_categories(self):
        cat = parse_content.load(REPO_ROOT, reproducible=True)
        assert len(cat.categories) >= 20

    def test_catalog_uc_count(self):
        cat = parse_content.load(REPO_ROOT, reproducible=True)
        total_ucs = 0
        for c in cat.categories:
            for sub in c.get("s", []):
                total_ucs += len(sub.get("u", []))
        assert total_ucs >= 7000

    def test_loader_kind(self):
        kind = parse_content.loader_kind()
        assert kind == "content"
