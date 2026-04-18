"""Tests for ``splunk_uc_mcp.tools.use_case`` (get_use_case, list_categories)."""

from __future__ import annotations

import pytest

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.use_case import (
    GET_USE_CASE_OUTPUT_SCHEMA,
    GET_USE_CASE_SCHEMA,
    LIST_CATEGORIES_OUTPUT_SCHEMA,
    LIST_CATEGORIES_SCHEMA,
    get_use_case,
    list_categories,
)


class TestGetUseCaseSchemas:
    def test_input_schema_shape(self) -> None:
        s = GET_USE_CASE_SCHEMA
        assert s["properties"]["uc_id"]["type"] == "string"
        assert "uc_id" in s["required"]
        assert s["additionalProperties"] is False

    def test_output_schema_shape(self) -> None:
        s = GET_USE_CASE_OUTPUT_SCHEMA
        for key in ("id", "title", "equipment", "mitreAttack", "compliance"):
            assert key in s["properties"]

    def test_input_schema_pattern_is_valid(self) -> None:
        import re

        pattern = GET_USE_CASE_SCHEMA["properties"]["uc_id"]["pattern"]
        compiled = re.compile(pattern)
        assert compiled.fullmatch("22.1.1") is not None
        assert compiled.fullmatch("1.1.1") is not None
        assert compiled.fullmatch("22.01.1") is None  # no leading zero
        assert compiled.fullmatch("22.1") is None
        assert compiled.fullmatch("22.1.1.1") is None


class TestGetUseCaseLive:
    def test_fetch_compliance_uc(self, live_catalog: Catalog) -> None:
        """cat-22 UCs return the compliance sidecar with full detail."""

        r = get_use_case(catalog=live_catalog, uc_id="22.1.1")
        assert r["id"] == "22.1.1"
        assert r["title"]
        assert isinstance(r.get("compliance"), list)
        assert len(r["compliance"]) >= 1
        entry = r["compliance"][0]
        assert "regulation" in entry
        assert "clause" in entry

    def test_fetch_non_compliance_uc(self, live_catalog: Catalog) -> None:
        """Non-cat-22 UCs fall back to uc-thin; get empty compliance[]."""

        r = get_use_case(catalog=live_catalog, uc_id="1.1.1")
        assert r["id"] == "1.1.1"
        assert r["title"]
        assert r.get("compliance") == []

    def test_unknown_uc_raises_not_found(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_use_case(catalog=live_catalog, uc_id="999.999.999")

    def test_compliance_sidecar_strips_apiVersion(
        self, live_catalog: Catalog
    ) -> None:
        """Sidecars carry apiVersion/_meta; those must not leak to agents."""

        r = get_use_case(catalog=live_catalog, uc_id="22.1.1")
        assert "apiVersion" not in r
        assert "_meta" not in r
        for k in r:
            assert not k.startswith("$")


class TestGetUseCaseValidation:
    @pytest.mark.parametrize(
        "bad_id",
        [
            "22.1",
            "abc",
            "22.1.1.1",
            "../etc/passwd",
            "22.01.1",
            "",
            "22.1.1 ",
            "22.1.a",
            "-1.1.1",
        ],
    )
    def test_rejects_invalid_uc_id(
        self, live_catalog: Catalog, bad_id: str
    ) -> None:
        with pytest.raises(ValueError, match="uc_id"):
            get_use_case(catalog=live_catalog, uc_id=bad_id)

    def test_accepts_zero_segments(self, live_catalog: Catalog) -> None:
        """``0.0.0`` is a valid shape even if the UC itself doesn't exist."""

        with pytest.raises(CatalogNotFoundError):
            get_use_case(catalog=live_catalog, uc_id="0.0.0")


class TestGetUseCaseSynthetic:
    def test_compliance_sidecar_preferred(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = get_use_case(catalog=synthetic_catalog, uc_id="22.1.1")
        assert r["id"] == "22.1.1"
        assert r["compliance"][0]["regulation"] == "GDPR"
        # Sidecar-only field (SPL) must flow through.
        assert "spl" in r
        # Bookkeeping must not leak.
        assert "apiVersion" not in r

    def test_thin_fallback(self, synthetic_catalog: Catalog) -> None:
        r = get_use_case(catalog=synthetic_catalog, uc_id="1.1.1")
        assert r["id"] == "1.1.1"
        assert r["title"] == "Test UC One"
        assert r["compliance"] == []

    def test_unknown_uc_raises(self, synthetic_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_use_case(catalog=synthetic_catalog, uc_id="99.99.99")


class TestListCategoriesSchemas:
    def test_input_schema_is_empty(self) -> None:
        s = LIST_CATEGORIES_SCHEMA
        assert s["type"] == "object"
        assert s.get("properties") in (None, {})
        assert s["additionalProperties"] is False

    def test_output_schema_shape(self) -> None:
        s = LIST_CATEGORIES_OUTPUT_SCHEMA
        assert "categories" in s["properties"]
        assert "count" in s["properties"]
        sub_schema = s["properties"]["categories"]["items"]["properties"]
        assert "id" in sub_schema
        assert "useCaseCount" in sub_schema
        assert "subcategories" in sub_schema


class TestListCategoriesLive:
    def test_categories_present(self, live_catalog: Catalog) -> None:
        r = list_categories(catalog=live_catalog)
        assert r["count"] >= 20
        ids = {c["id"] for c in r["categories"]}
        assert "22" in ids

    def test_category_structure(self, live_catalog: Catalog) -> None:
        r = list_categories(catalog=live_catalog)
        for c in r["categories"]:
            assert "id" in c
            assert "useCaseCount" in c
            assert "subcategories" in c
            assert c["useCaseCount"] >= 1
            for sub in c["subcategories"]:
                assert sub["id"].startswith(f"{c['id']}.")
                assert sub["useCaseCount"] >= 1

    def test_subcategory_counts_sum_to_category(
        self, live_catalog: Catalog
    ) -> None:
        r = list_categories(catalog=live_catalog)
        for c in r["categories"]:
            total = sum(s["useCaseCount"] for s in c["subcategories"])
            assert total == c["useCaseCount"]

    def test_categories_sorted_numerically(
        self, live_catalog: Catalog
    ) -> None:
        r = list_categories(catalog=live_catalog)
        ids = [int(c["id"]) for c in r["categories"]]
        assert ids == sorted(ids)


class TestListCategoriesSynthetic:
    def test_synthetic_tree(self, synthetic_catalog: Catalog) -> None:
        r = list_categories(catalog=synthetic_catalog)
        assert r["count"] == 2
        ids = [c["id"] for c in r["categories"]]
        assert ids == ["1", "22"]

        cat_1 = r["categories"][0]
        assert cat_1["useCaseCount"] == 1
        assert cat_1["subcategories"] == [{"id": "1.1", "useCaseCount": 1}]

        cat_22 = r["categories"][1]
        assert cat_22["useCaseCount"] == 1
        assert cat_22["subcategories"] == [{"id": "22.1", "useCaseCount": 1}]
