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


class TestGetUcSchemaCacheBranches:
    """Pin the two remaining branches in ``_get_uc_schema``: the cache-hit
    short-circuit and the OSError/JSONDecodeError fall-through when the
    schema file exists but is malformed."""

    def setup_method(self):
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False

    def teardown_method(self):
        parse_content._UC_SCHEMA = None
        parse_content._UC_SCHEMA_LOADED = False

    def test_second_call_returns_cached_value(self, tmp_path):
        """Line 77: ``if _UC_SCHEMA_LOADED: return _UC_SCHEMA`` — second
        call hits the cache and never re-reads the file."""
        schema = {"type": "object", "properties": {}}
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "uc.schema.json").write_text(
            json.dumps(schema), encoding="utf-8"
        )
        first = parse_content._get_uc_schema(tmp_path)
        assert first == schema
        # Mutate the on-disk file — cache should win.
        (schemas_dir / "uc.schema.json").write_text(
            "this is not json anymore", encoding="utf-8"
        )
        second = parse_content._get_uc_schema(tmp_path)
        assert second == schema  # cached; not re-read

    def test_malformed_schema_returns_none(self, tmp_path, capsys):
        """Lines 88-89: ``except (OSError, json.JSONDecodeError)``
        — schema file exists but is unreadable / not JSON."""
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "uc.schema.json").write_text(
            '{"unbalanced": broken', encoding="utf-8"  # invalid JSON
        )
        result = parse_content._get_uc_schema(tmp_path)
        assert result is None
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "could not load UC schema" in captured.err


class TestComputeQualityRefBranches:
    """Pin line 847 (``ref_count = 0`` else arm) and branch [800, 802]
    (``isinstance(md_text, str)`` false arm) in ``_compute_quality``.

    Both fire only at Gold-tier evaluation time, which requires every
    bronze + silver field plus ``z`` and ``em`` to be present. Build a
    minimal Gold-eligible UC and flip the two fields the targeted
    branches inspect."""

    def _gold_uc(self) -> dict:
        """Return a UC that satisfies bronze + silver + gold field
        requirements except where individual tests perturb it."""
        return {
            # Bronze (9 fields)
            "i": "1.1.1",
            "n": "Sample",
            "c": "high",
            "f": "intermediate",
            "q": "index=foo | stats count",
            "v": "Value",
            "d": "datasources",
            "t": "splunk_app",
            "m": "implementation",
            # Silver (6 fields)
            "mtype": ["Availability"],
            "md": "## Step 1\n## Step 2\n## Step 3\n## Step 4\n"
            + "x" * 600,
            "refs": "[A](https://example.com)],[B](https://example.org)]",
            "e": "splunk-enterprise",
            "ge": "Plain-language explanation goes here",
            "wv": "walk",
            # Gold (2 extras)
            "z": "Single value panel",
            "em": "splunk-enterprise:9.x",
        }

    def test_refs_as_list_falls_back_to_zero_count(self):
        """Line 847: ``else: ref_count = 0`` when ``refs`` is not a
        string. Pass a list — the gold check then complains about
        missing references but exercises the else arm."""
        uc = self._gold_uc()
        uc["refs"] = ["not", "a", "string"]
        # _present treats non-empty list as present, so silver + gold
        # field-presence checks still pass; only the per-string parse
        # in the gold branch hits the else arm.
        tier, depth, gaps = parse_content._compute_quality(uc)
        # The fallback ref_count=0 means gold demotes to silver with a
        # "add at least 2 references" gap.
        assert any("references" in g.lower() for g in gaps)
        # Tier is silver (gold check failed on refs even though field
        # is present).
        assert tier in {"silver", "bronze"}
        assert depth >= 25

    def test_md_as_non_string_skips_section_count_block(self):
        """Branch [800, 802]: ``if isinstance(md_text, str)`` false arm.
        ``md`` set to a non-string truthy value (e.g. a list) means
        ``md_text = uc.get("md") or ""`` returns the list itself, and
        the section-count block is skipped without crashing.

        Both the silver-downgrade and gold sub-block are also gated on
        ``isinstance(md_text, str)``, so when md is non-string the
        function returns a tier reflecting only the field-presence
        signals — no gaps about sections, length, or refs."""
        uc = self._gold_uc()
        uc["md"] = ["not", "a", "string"]  # truthy non-string
        tier, depth, gaps = parse_content._compute_quality(uc)
        # Function ran cleanly (no TypeError on .search() against a
        # list). With every field present, the silver/gold sub-blocks
        # are skipped because they all gate on isinstance(md, str).
        assert tier in {"gold", "silver", "bronze"}
        assert depth >= 25
        # Critically: no "sections" gap because the section-count
        # block was skipped; no TypeError raised either.
        assert not any("sections" in g.lower() for g in gaps)


class TestCanonicalUcCmpRowsEmpty:
    """Pin branch [671, 675]: ``if cmp_rows:`` false arm — every entry
    in ``compliance`` is invalid (missing reg/version/clause), so
    ``cmp_rows`` stays empty and ``uc["cmp"]`` is never assigned."""

    def test_compliance_with_only_invalid_entries_skips_cmp_assignment(self):
        canonical = {
            "id": "1.1.1",
            "title": "Sample",
            "criticality": "high",
            "difficulty": "beginner",
            "value": "x",
            "spl": "index=foo",
            "compliance": [
                {"regulation": "gdpr"},  # missing version + clause
                {"regulation": "pci", "version": "4.0"},  # missing clause
                "not-a-dict",  # wrong shape, skipped earlier
            ],
        }
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert "cmp" not in uc

    def test_compliance_with_one_valid_entry_assigns_cmp(self):
        """Symmetry test — confirm the true arm of [671, 675] still
        works so the previous test's negative is meaningful."""
        canonical = {
            "id": "1.1.1",
            "title": "Sample",
            "compliance": [
                {"regulation": "GDPR", "version": "2016/679", "clause": "Art. 32"}
            ],
        }
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert uc.get("cmp") and len(uc["cmp"]) == 1
        assert uc["cmp"][0]["r"] == "GDPR"
