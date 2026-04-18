"""Tests for ``splunk_uc_mcp.tools.equipment`` (list_equipment + get_equipment)."""

from __future__ import annotations

import pytest

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.equipment import (
    GET_EQUIPMENT_OUTPUT_SCHEMA,
    GET_EQUIPMENT_SCHEMA,
    LIST_EQUIPMENT_OUTPUT_SCHEMA,
    LIST_EQUIPMENT_SCHEMA,
    get_equipment,
    list_equipment,
)


class TestListEquipmentSchemas:
    def test_input_schema(self) -> None:
        s = LIST_EQUIPMENT_SCHEMA
        for key in ("regulation_id", "min_use_case_count"):
            assert key in s["properties"]
        assert s["additionalProperties"] is False

    def test_output_schema(self) -> None:
        s = LIST_EQUIPMENT_OUTPUT_SCHEMA
        assert "equipment" in s["properties"]
        assert "count" in s["properties"]
        item = s["properties"]["equipment"]["items"]
        for key in ("id", "label", "useCaseCount"):
            assert key in item["required"]


class TestListEquipmentLive:
    def test_all(self, live_catalog: Catalog) -> None:
        r = list_equipment(catalog=live_catalog)
        assert r["count"] >= 50
        ids = {e["id"] for e in r["equipment"]}
        for slug in ("linux", "windows", "aws", "azure"):
            assert slug in ids, f"expected {slug} in equipment list"

    def test_min_uc_filter(self, live_catalog: Catalog) -> None:
        threshold = 50
        r = list_equipment(
            catalog=live_catalog, min_use_case_count=threshold
        )
        for e in r["equipment"]:
            assert e["useCaseCount"] >= threshold

    def test_min_uc_zero_is_no_filter(self, live_catalog: Catalog) -> None:
        bare = list_equipment(catalog=live_catalog)
        zero = list_equipment(catalog=live_catalog, min_use_case_count=0)
        assert bare["count"] == zero["count"]

    def test_regulation_filter_keeps_compliance_equipment(
        self, live_catalog: Catalog
    ) -> None:
        r = list_equipment(catalog=live_catalog, regulation_id="gdpr")
        assert r["count"] >= 1
        for e in r["equipment"]:
            assert "gdpr" in e.get("regulationIds", [])

    def test_regulation_filter_unknown(self, live_catalog: Catalog) -> None:
        r = list_equipment(
            catalog=live_catalog, regulation_id="nonexistent-xyz"
        )
        assert r["count"] == 0


class TestListEquipmentValidation:
    @pytest.mark.parametrize(
        "bad", ["GDPR", "gdpr space", "../other", "gdpr;rm", ""]
    )
    def test_rejects_bad_regulation_id(
        self, live_catalog: Catalog, bad: str
    ) -> None:
        with pytest.raises(ValueError, match="regulation_id"):
            list_equipment(catalog=live_catalog, regulation_id=bad)

    def test_rejects_negative_min_count(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="min_use_case_count"):
            list_equipment(catalog=live_catalog, min_use_case_count=-1)

    def test_rejects_non_int_min_count(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="min_use_case_count"):
            list_equipment(
                catalog=live_catalog, min_use_case_count="5"  # type: ignore[arg-type]
            )

    def test_rejects_bool_min_count(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="min_use_case_count"):
            list_equipment(
                catalog=live_catalog, min_use_case_count=True  # type: ignore[arg-type]
            )


class TestListEquipmentSynthetic:
    def test_synthetic_all(self, synthetic_catalog: Catalog) -> None:
        r = list_equipment(catalog=synthetic_catalog)
        assert r["count"] == 2
        ids = {e["id"] for e in r["equipment"]}
        assert ids == {"azure", "linux"}

    def test_synthetic_regulation_filter(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = list_equipment(catalog=synthetic_catalog, regulation_id="gdpr")
        assert r["count"] == 2

    def test_synthetic_min_count_filter(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = list_equipment(catalog=synthetic_catalog, min_use_case_count=2)
        assert r["count"] == 1
        assert r["equipment"][0]["id"] == "linux"


class TestGetEquipmentSchemas:
    def test_input_schema(self) -> None:
        s = GET_EQUIPMENT_SCHEMA
        assert "equipment_id" in s["required"]
        assert s["additionalProperties"] is False

    def test_output_schema(self) -> None:
        s = GET_EQUIPMENT_OUTPUT_SCHEMA
        for key in ("id", "label", "useCaseCount"):
            assert key in s["properties"]


class TestGetEquipmentLive:
    def test_fetch_azure(self, live_catalog: Catalog) -> None:
        r = get_equipment(catalog=live_catalog, equipment_id="azure")
        assert r["id"] == "azure"
        assert r["label"]
        assert r["useCaseCount"] >= 1
        assert isinstance(r.get("regulationIds"), list)
        assert isinstance(r.get("useCasesByCategory"), list)
        for entry in r["useCasesByCategory"]:
            assert "useCaseIds" in entry
            assert "useCaseCount" in entry

    def test_fetch_linux(self, live_catalog: Catalog) -> None:
        r = get_equipment(catalog=live_catalog, equipment_id="linux")
        assert r["id"] == "linux"
        assert r["useCaseCount"] >= 100

    def test_strips_meta(self, live_catalog: Catalog) -> None:
        r = get_equipment(catalog=live_catalog, equipment_id="azure")
        assert "apiVersion" not in r
        assert "generatedAt" not in r
        assert "catalogueVersion" not in r

    def test_unknown_equipment_raises(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_equipment(catalog=live_catalog, equipment_id="nonexistent_xyz")


class TestGetEquipmentValidation:
    @pytest.mark.parametrize(
        "bad",
        [
            "Azure",
            "azure-cloud",
            "azure;ls",
            "azure ",
            "",
            "../azure",
            "_azure",
        ],
    )
    def test_rejects_invalid_slug(
        self, live_catalog: Catalog, bad: str
    ) -> None:
        with pytest.raises(ValueError, match="equipment_id"):
            get_equipment(catalog=live_catalog, equipment_id=bad)


class TestGetEquipmentSynthetic:
    def test_synthetic_azure(self, synthetic_catalog: Catalog) -> None:
        r = get_equipment(catalog=synthetic_catalog, equipment_id="azure")
        assert r["id"] == "azure"
        assert r["useCaseCount"] == 1
        assert r["regulationIds"] == ["gdpr"]
        assert len(r["regulations"]) == 1
        assert r["regulations"][0]["regulationId"] == "gdpr"
