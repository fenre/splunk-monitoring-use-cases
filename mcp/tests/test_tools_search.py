"""Tests for ``splunk_uc_mcp.tools.search.search_use_cases``."""

from __future__ import annotations

import pytest

from splunk_uc_mcp.catalog import Catalog
from splunk_uc_mcp.tools.search import (
    SEARCH_USE_CASES_OUTPUT_SCHEMA,
    SEARCH_USE_CASES_SCHEMA,
    search_use_cases,
)


class TestSearchUseCasesSchemas:
    def test_output_schema_shape(self) -> None:
        s = SEARCH_USE_CASES_OUTPUT_SCHEMA
        assert s["type"] == "object"
        for key in ("count", "totalMatched", "truncated", "useCases"):
            assert key in s["properties"], f"missing property: {key}"

    def test_input_schema_shape(self) -> None:
        s = SEARCH_USE_CASES_SCHEMA
        assert s["type"] == "object"
        for key in (
            "query",
            "category",
            "regulation_id",
            "equipment",
            "mitre_technique",
            "limit",
        ):
            assert key in s["properties"]
        assert s["additionalProperties"] is False

    def test_input_schema_patterns_are_valid_regex(self) -> None:
        import re

        for key in ("category", "regulation_id", "equipment", "mitre_technique"):
            pattern = SEARCH_USE_CASES_SCHEMA["properties"][key]["pattern"]
            re.compile(pattern)

    def test_output_schema_advertises_implementation_ordering(self) -> None:
        """The agent-facing output schema must surface wave + prereq edges."""

        uc_props = SEARCH_USE_CASES_OUTPUT_SCHEMA["properties"]["useCases"][
            "items"
        ]["properties"]
        assert uc_props["wave"]["type"] == "string"
        assert (
            uc_props["prerequisiteUseCases"]["items"]["pattern"].startswith(
                "^UC-"
            )
        )


class TestSearchUseCasesLive:
    """Tests that hit the real catalogue shipped in ``api/v1``."""

    def test_bare_call_returns_everything_capped(
        self, live_catalog: Catalog
    ) -> None:
        r = search_use_cases(catalog=live_catalog, limit=5)
        assert r["count"] == 5
        assert r["totalMatched"] >= 5000  # catalogue ships ~6,424 UCs
        assert r["truncated"] is True
        assert len(r["useCases"]) == 5

    def test_keyword_query_case_insensitive(self, live_catalog: Catalog) -> None:
        r = search_use_cases(catalog=live_catalog, query="GDPR", limit=10)
        assert r["totalMatched"] >= 1
        for uc in r["useCases"]:
            hay = f"{uc.get('title', '')} {uc.get('value', '')}".lower()
            assert "gdpr" in hay

    def test_category_filter_22(self, live_catalog: Catalog) -> None:
        r = search_use_cases(catalog=live_catalog, category="22", limit=20)
        assert r["totalMatched"] >= 20
        for uc in r["useCases"]:
            assert uc["id"].split(".", 1)[0] == "22"

    def test_subcategory_filter(self, live_catalog: Catalog) -> None:
        r = search_use_cases(catalog=live_catalog, category="22.1", limit=20)
        for uc in r["useCases"]:
            assert uc["id"].startswith("22.1.")

    def test_regulation_filter_gdpr(self, live_catalog: Catalog) -> None:
        r = search_use_cases(
            catalog=live_catalog, regulation_id="gdpr", limit=50
        )
        assert r["totalMatched"] >= 1
        assert len(r["useCases"]) > 0
        for uc in r["useCases"]:
            assert uc["id"].startswith("22.")

    def test_equipment_filter(self, live_catalog: Catalog) -> None:
        r = search_use_cases(catalog=live_catalog, equipment="azure", limit=10)
        assert r["totalMatched"] >= 1
        for uc in r["useCases"]:
            assert "azure" in uc.get("equipment", [])

    def test_mitre_filter(self, live_catalog: Catalog) -> None:
        r = search_use_cases(
            catalog=live_catalog, mitre_technique="T1078", limit=10
        )
        for uc in r["useCases"]:
            assert "T1078" in uc.get("mitreAttack", [])

    def test_combined_filters_category_and_equipment(
        self, live_catalog: Catalog
    ) -> None:
        r = search_use_cases(
            catalog=live_catalog,
            category="22",
            equipment="azure",
            limit=10,
        )
        for uc in r["useCases"]:
            assert uc["id"].startswith("22.")
            assert "azure" in uc.get("equipment", [])

    def test_unknown_regulation_returns_zero(
        self, live_catalog: Catalog
    ) -> None:
        r = search_use_cases(
            catalog=live_catalog, regulation_id="nonexistent-xyz"
        )
        assert r["totalMatched"] == 0
        assert r["count"] == 0
        assert r["useCases"] == []

    def test_result_fields_are_slim(self, live_catalog: Catalog) -> None:
        """Project only whitelisted keys — don't leak unaudited fields."""

        r = search_use_cases(catalog=live_catalog, limit=1)
        allowed = {
            "id",
            "title",
            "value",
            "criticality",
            "difficulty",
            "wave",
            "prerequisiteUseCases",
            "splunkPillar",
            "monitoringType",
            "app",
            "equipment",
            "equipmentModels",
            "mitreAttack",
            "cimModels",
        }
        for uc in r["useCases"]:
            assert set(uc).issubset(allowed), (
                f"unexpected fields leaked: {set(uc) - allowed}"
            )


class TestSearchUseCasesValidation:
    def test_rejects_bad_limit_low(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="limit"):
            search_use_cases(catalog=live_catalog, limit=0)

    def test_rejects_bad_limit_high(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="limit"):
            search_use_cases(catalog=live_catalog, limit=10_000)

    def test_rejects_bool_limit(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="limit"):
            search_use_cases(catalog=live_catalog, limit=True)  # type: ignore[arg-type]

    @pytest.mark.parametrize("bad_category", ["abc", "22.", ".22", "22..1", "-1"])
    def test_rejects_invalid_category(
        self, live_catalog: Catalog, bad_category: str
    ) -> None:
        with pytest.raises(ValueError, match="category"):
            search_use_cases(catalog=live_catalog, category=bad_category)

    def test_rejects_uppercase_regulation_id(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="regulation_id"):
            search_use_cases(catalog=live_catalog, regulation_id="GDPR")

    def test_rejects_regulation_id_with_traversal(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="regulation_id"):
            search_use_cases(catalog=live_catalog, regulation_id="../etc/passwd")

    def test_rejects_uppercase_equipment(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="equipment"):
            search_use_cases(catalog=live_catalog, equipment="Azure")

    def test_rejects_lowercase_mitre(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="mitre"):
            search_use_cases(catalog=live_catalog, mitre_technique="t1078")

    def test_rejects_malformed_mitre(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="mitre"):
            search_use_cases(catalog=live_catalog, mitre_technique="T12345")

    @pytest.mark.parametrize("query_len", [201, 1000, 5000])
    def test_rejects_oversize_query(
        self, live_catalog: Catalog, query_len: int
    ) -> None:
        with pytest.raises(ValueError, match="query"):
            search_use_cases(
                catalog=live_catalog, query="a" * query_len
            )

    def test_accepts_max_size_query(self, live_catalog: Catalog) -> None:
        r = search_use_cases(catalog=live_catalog, query="a" * 200, limit=1)
        assert "useCases" in r


class TestSearchUseCasesSynthetic:
    def test_synthetic_keyword_search(self, synthetic_catalog: Catalog) -> None:
        r = search_use_cases(catalog=synthetic_catalog, query="gdpr")
        assert r["totalMatched"] == 1
        assert r["useCases"][0]["id"] == "22.1.1"

    def test_synthetic_regulation_filter(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = search_use_cases(catalog=synthetic_catalog, regulation_id="gdpr")
        assert r["totalMatched"] == 1
        assert r["useCases"][0]["id"] == "22.1.1"

    def test_synthetic_category_filter(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = search_use_cases(catalog=synthetic_catalog, category="22")
        assert r["totalMatched"] == 1
        assert r["useCases"][0]["id"] == "22.1.1"

        r = search_use_cases(catalog=synthetic_catalog, category="1")
        assert r["totalMatched"] == 1
        assert r["useCases"][0]["id"] == "1.1.1"

    def test_synthetic_equipment_filter(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = search_use_cases(catalog=synthetic_catalog, equipment="linux")
        assert r["totalMatched"] == 2

        r = search_use_cases(catalog=synthetic_catalog, equipment="azure")
        assert r["totalMatched"] == 1
        assert r["useCases"][0]["id"] == "22.1.1"

    def test_synthetic_mitre_filter(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = search_use_cases(
            catalog=synthetic_catalog, mitre_technique="T1078"
        )
        assert r["totalMatched"] == 1

    def test_synthetic_combined_filters(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = search_use_cases(
            catalog=synthetic_catalog,
            category="22",
            equipment="linux",
            mitre_technique="T1078",
        )
        assert r["totalMatched"] == 1
        assert r["useCases"][0]["id"] == "22.1.1"

    def test_synthetic_wave_and_prereq_passthrough(
        self, synthetic_catalog: Catalog
    ) -> None:
        """Wave + prereq edges must survive projection into search results.

        The synthetic fixture seeds UC-1.1.1 as a crawl UC with no prereqs
        and UC-22.1.1 as a walk UC depending on UC-1.1.1 — a minimal edge
        that is enough to verify the field flows end-to-end.
        """

        r = search_use_cases(catalog=synthetic_catalog, limit=5)
        by_id = {uc["id"]: uc for uc in r["useCases"]}

        assert by_id["1.1.1"]["wave"] == "crawl"
        assert by_id["1.1.1"]["prerequisiteUseCases"] == []

        assert by_id["22.1.1"]["wave"] == "walk"
        assert by_id["22.1.1"]["prerequisiteUseCases"] == ["UC-1.1.1"]
