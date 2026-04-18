"""Tests for ``splunk_uc_mcp.tools.compliance.find_compliance_gap``."""

from __future__ import annotations

import pytest

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.compliance import (
    FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
    FIND_COMPLIANCE_GAP_SCHEMA,
    find_compliance_gap,
)


class TestFindComplianceGapSchemas:
    def test_input_schema(self) -> None:
        s = FIND_COMPLIANCE_GAP_SCHEMA
        assert "regulations" in s["required"]
        assert "equipment_id" in s["properties"]
        assert s["additionalProperties"] is False
        assert s["properties"]["regulations"]["minItems"] == 1
        assert s["properties"]["regulations"]["maxItems"] == 20

    def test_output_schema(self) -> None:
        s = FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA
        assert "entries" in s["properties"]
        assert "summary" in s["properties"]


class TestFindComplianceGapLive:
    """Tests against the real ``api/v1/compliance/gaps.json``."""

    def test_single_reg_with_uncovered(self, live_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=live_catalog, regulations=["gdpr"]
        )
        assert r["summary"]["regulationsResolved"] == 1
        assert r["summary"]["regulationsNotFound"] == []
        entry = r["entries"][0]
        assert entry["regulationId"] == "gdpr"
        assert isinstance(entry.get("commonClausesUncovered"), list)

    def test_multiple_regs(self, live_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=live_catalog,
            regulations=["gdpr", "hipaa-security", "pci-dss"],
        )
        assert r["summary"]["regulationsResolved"] == 3
        assert len(r["entries"]) == 3

    def test_partial_match(self, live_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=live_catalog,
            regulations=["gdpr", "does-not-exist"],
        )
        assert r["summary"]["regulationsResolved"] == 1
        assert r["summary"]["regulationsNotFound"] == ["does-not-exist"]
        assert len(r["entries"]) == 1

    def test_all_unknown(self, live_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=live_catalog, regulations=["nope-one", "nope-two"]
        )
        assert r["summary"]["regulationsResolved"] == 0
        assert set(r["summary"]["regulationsNotFound"]) == {
            "nope-one",
            "nope-two",
        }
        assert r["entries"] == []
        assert r["summary"]["totalUncoveredClauses"] == 0

    def test_total_uncovered_is_sum(self, live_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=live_catalog,
            regulations=["gdpr", "hipaa-security"],
        )
        total = sum(
            len(e.get("commonClausesUncovered", []))
            for e in r["entries"]
        )
        assert r["summary"]["totalUncoveredClauses"] == total

    def test_equipment_overlay(self, live_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=live_catalog,
            regulations=["gdpr"],
            equipment_id="azure",
        )
        assert r["summary"]["equipmentId"] == "azure"
        entry = r["entries"][0]
        overlay = entry["equipmentOverlay"]
        assert overlay["equipmentId"] == "azure"
        assert "clausesCoveredByEquipment" in overlay
        assert "uncoveredClausesStillUncovered" in overlay
        residual = set(overlay["uncoveredClausesStillUncovered"])
        uncovered = set(entry["commonClausesUncovered"])
        # Residual is a subset of the uncovered set.
        assert residual.issubset(uncovered)

    def test_equipment_overlay_unknown_raises(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(CatalogNotFoundError):
            find_compliance_gap(
                catalog=live_catalog,
                regulations=["gdpr"],
                equipment_id="nonexistent_xyz",
            )


class TestFindComplianceGapValidation:
    def test_rejects_empty_list(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="at least one"):
            find_compliance_gap(catalog=live_catalog, regulations=[])

    def test_rejects_string_instead_of_list(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="regulations"):
            find_compliance_gap(
                catalog=live_catalog, regulations="gdpr"  # type: ignore[arg-type]
            )

    def test_rejects_dict_instead_of_list(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="regulations"):
            find_compliance_gap(
                catalog=live_catalog, regulations={"gdpr": 1}  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "bad",
        [
            ["GDPR"],
            ["gdpr", "bad Id"],
            ["../etc/passwd"],
            ["gdpr;rm -rf"],
            ["gdpr\x00"],
        ],
    )
    def test_rejects_bad_slugs(
        self, live_catalog: Catalog, bad: list[str]
    ) -> None:
        with pytest.raises(ValueError):
            find_compliance_gap(catalog=live_catalog, regulations=bad)

    def test_rejects_non_string_slug(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError):
            find_compliance_gap(
                catalog=live_catalog, regulations=[42]  # type: ignore[list-item]
            )

    def test_rejects_bad_equipment_id(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="equipment_id"):
            find_compliance_gap(
                catalog=live_catalog,
                regulations=["gdpr"],
                equipment_id="Azure",
            )

    def test_rejects_oversize_regulations_list(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="at most"):
            find_compliance_gap(
                catalog=live_catalog,
                regulations=[f"fake-{i}" for i in range(21)],
            )


class TestFindComplianceGapSynthetic:
    def test_single_reg(self, synthetic_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=synthetic_catalog, regulations=["gdpr"]
        )
        assert r["summary"]["regulationsResolved"] == 1
        assert r["summary"]["totalUncoveredClauses"] == 2
        entry = r["entries"][0]
        assert entry["regulationId"] == "gdpr"
        assert entry["commonClausesUncovered"] == ["Art.17", "Art.32"]

    def test_equipment_overlay_covers_clause(
        self, synthetic_catalog: Catalog
    ) -> None:
        """Synthetic azure covers Art.5; gap is Art.17 + Art.32; residual = both."""

        r = find_compliance_gap(
            catalog=synthetic_catalog,
            regulations=["gdpr"],
            equipment_id="azure",
        )
        overlay = r["entries"][0]["equipmentOverlay"]
        assert overlay["clausesCoveredByEquipment"] == ["Art.5"]
        # Art.5 is not in the uncovered set, so residual == uncovered.
        assert overlay["uncoveredClausesStillUncovered"] == [
            "Art.17",
            "Art.32",
        ]

    def test_unknown_regulation(self, synthetic_catalog: Catalog) -> None:
        r = find_compliance_gap(
            catalog=synthetic_catalog, regulations=["nope"]
        )
        assert r["summary"]["regulationsResolved"] == 0
        assert r["summary"]["regulationsNotFound"] == ["nope"]
