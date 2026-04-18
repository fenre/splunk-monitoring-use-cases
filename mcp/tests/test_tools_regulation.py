"""Tests for ``splunk_uc_mcp.tools.regulation``."""

from __future__ import annotations

import pytest

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.regulation import (
    GET_REGULATION_OUTPUT_SCHEMA,
    GET_REGULATION_SCHEMA,
    LIST_REGULATIONS_OUTPUT_SCHEMA,
    LIST_REGULATIONS_SCHEMA,
    get_regulation,
    list_regulations,
)


class TestListRegulationsSchemas:
    def test_input_schema(self) -> None:
        s = LIST_REGULATIONS_SCHEMA
        for key in ("tier", "jurisdiction", "tag"):
            assert key in s["properties"]
        assert s["additionalProperties"] is False

    def test_output_schema(self) -> None:
        s = LIST_REGULATIONS_OUTPUT_SCHEMA
        assert "regulations" in s["properties"]
        assert "count" in s["properties"]
        item_schema = s["properties"]["regulations"]["items"]
        for key in ("id", "name"):
            assert key in item_schema["required"]


class TestListRegulationsLive:
    def test_all(self, live_catalog: Catalog) -> None:
        r = list_regulations(catalog=live_catalog)
        assert r["count"] >= 30
        ids = {reg["id"] for reg in r["regulations"]}
        for known in ("gdpr", "hipaa-security", "pci-dss"):
            assert known in ids, f"expected {known} in regulation list"

    def test_tier_filter(self, live_catalog: Catalog) -> None:
        r = list_regulations(catalog=live_catalog, tier=1)
        assert r["count"] >= 1
        for reg in r["regulations"]:
            assert reg["tier"] == 1

    def test_jurisdiction_filter_case_insensitive(
        self, live_catalog: Catalog
    ) -> None:
        upper = list_regulations(catalog=live_catalog, jurisdiction="EU")
        lower = list_regulations(catalog=live_catalog, jurisdiction="eu")
        assert upper["count"] == lower["count"] >= 1
        for reg in upper["regulations"]:
            assert any(j.upper() == "EU" for j in reg.get("jurisdiction", []))

    def test_tag_filter(self, live_catalog: Catalog) -> None:
        r = list_regulations(catalog=live_catalog, tag="privacy")
        # May be 0 if no regulation carries the exact tag, but must not error.
        for reg in r["regulations"]:
            assert "privacy" in reg.get("tags", [])

    def test_combined_filters(self, live_catalog: Catalog) -> None:
        r = list_regulations(catalog=live_catalog, tier=1, jurisdiction="EU")
        for reg in r["regulations"]:
            assert reg["tier"] == 1
            assert any(j.upper() == "EU" for j in reg.get("jurisdiction", []))

    def test_unknown_jurisdiction_returns_empty(
        self, live_catalog: Catalog
    ) -> None:
        r = list_regulations(catalog=live_catalog, jurisdiction="MARS")
        assert r["count"] == 0


class TestListRegulationsValidation:
    @pytest.mark.parametrize("bad", [0, -1, 4, 100])
    def test_rejects_out_of_range_tier(
        self, live_catalog: Catalog, bad: int
    ) -> None:
        with pytest.raises(ValueError, match="tier"):
            list_regulations(catalog=live_catalog, tier=bad)

    @pytest.mark.parametrize("bad", ["1", 10.5, True])
    def test_rejects_wrong_type_tier(
        self, live_catalog: Catalog, bad: object
    ) -> None:
        with pytest.raises(ValueError, match="tier"):
            list_regulations(catalog=live_catalog, tier=bad)  # type: ignore[arg-type]

    def test_rejects_oversize_jurisdiction(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="jurisdiction"):
            list_regulations(
                catalog=live_catalog, jurisdiction="A" * 17
            )

    def test_rejects_oversize_tag(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="tag"):
            list_regulations(catalog=live_catalog, tag="A" * 49)


class TestListRegulationsSynthetic:
    def test_synthetic_single_reg(self, synthetic_catalog: Catalog) -> None:
        r = list_regulations(catalog=synthetic_catalog)
        assert r["count"] == 1
        reg = r["regulations"][0]
        assert reg["id"] == "gdpr"
        assert reg["tier"] == 1
        assert "EU" in reg["jurisdiction"]

    def test_synthetic_tier_mismatch(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = list_regulations(catalog=synthetic_catalog, tier=2)
        assert r["count"] == 0


class TestGetRegulationSchemas:
    def test_input_schema(self) -> None:
        s = GET_REGULATION_SCHEMA
        assert "regulation_id" in s["required"]
        assert s["additionalProperties"] is False

    def test_output_schema(self) -> None:
        s = GET_REGULATION_OUTPUT_SCHEMA
        for key in ("id", "name", "version"):
            assert key in s["properties"]


class TestGetRegulationLive:
    def test_default_returns_base_and_versions(
        self, live_catalog: Catalog
    ) -> None:
        r = get_regulation(catalog=live_catalog, regulation_id="gdpr")
        assert r["id"] == "gdpr"
        assert r["name"]
        assert isinstance(r.get("availableVersions"), list)
        assert len(r["availableVersions"]) >= 1

    def test_version_in_display_form(self, live_catalog: Catalog) -> None:
        """Display form uses slashes (``2016/679``); tool converts to dashes."""

        r = get_regulation(
            catalog=live_catalog, regulation_id="gdpr", version="2016/679"
        )
        assert "version" in r

    def test_version_in_dash_form(self, live_catalog: Catalog) -> None:
        r = get_regulation(
            catalog=live_catalog, regulation_id="gdpr", version="2016-679"
        )
        assert "version" in r

    def test_unknown_regulation_raises(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_regulation(
                catalog=live_catalog, regulation_id="nonexistent-xyz"
            )

    def test_unknown_version_raises_with_hint(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(CatalogNotFoundError, match="available"):
            get_regulation(
                catalog=live_catalog,
                regulation_id="gdpr",
                version="1999-00",
            )

    def test_response_strips_meta(self, live_catalog: Catalog) -> None:
        r = get_regulation(catalog=live_catalog, regulation_id="gdpr")
        assert "apiVersion" not in r
        assert "generatedAt" not in r
        assert "_meta" not in r


class TestGetRegulationValidation:
    @pytest.mark.parametrize(
        "bad",
        ["GDPR", "gdpr/..", "", "gdpr 2016", "gdpr@2016", "../etc"],
    )
    def test_rejects_bad_id(self, live_catalog: Catalog, bad: str) -> None:
        with pytest.raises(ValueError, match="regulation_id"):
            get_regulation(catalog=live_catalog, regulation_id=bad)

    @pytest.mark.parametrize(
        "bad_version",
        [
            "../../etc",
            "2016\x00-679",
            "2016;rm",
            ".hidden",
            "",
        ],
    )
    def test_rejects_bad_version(
        self, live_catalog: Catalog, bad_version: str
    ) -> None:
        with pytest.raises(ValueError, match="version"):
            get_regulation(
                catalog=live_catalog,
                regulation_id="gdpr",
                version=bad_version,
            )

    def test_accepts_slash_version(self, live_catalog: Catalog) -> None:
        """Slashes are allowed in the display form."""

        r = get_regulation(
            catalog=live_catalog, regulation_id="gdpr", version="2016/679"
        )
        assert r["id"] == "gdpr"


class TestGetRegulationSynthetic:
    def test_default(self, synthetic_catalog: Catalog) -> None:
        r = get_regulation(catalog=synthetic_catalog, regulation_id="gdpr")
        assert r["id"] == "gdpr"
        assert r["availableVersions"] == ["2016/679"]

    def test_versioned(self, synthetic_catalog: Catalog) -> None:
        r = get_regulation(
            catalog=synthetic_catalog,
            regulation_id="gdpr",
            version="2016/679",
        )
        assert r["id"] == "gdpr"
        assert "version" in r
