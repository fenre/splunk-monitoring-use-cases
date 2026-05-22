"""Tests for the tools defined in ``splunk_uc_mcp.tools.compliance``.

Covers the original :func:`find_compliance_gap` plus the story-layer
pair added in v1.6.x — :func:`get_clause_coverage` and
:func:`list_uncovered_clauses`.
"""

from __future__ import annotations

from typing import Any

import pytest
from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.compliance import (
    FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
    FIND_COMPLIANCE_GAP_SCHEMA,
    GET_CLAUSE_COVERAGE_OUTPUT_SCHEMA,
    GET_CLAUSE_COVERAGE_SCHEMA,
    LIST_UNCOVERED_CLAUSES_OUTPUT_SCHEMA,
    LIST_UNCOVERED_CLAUSES_SCHEMA,
    find_compliance_gap,
    get_clause_coverage,
    list_uncovered_clauses,
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


# =====================================================================
# get_clause_coverage
# =====================================================================


class TestGetClauseCoverageSchemas:
    def test_input_schema_shape(self) -> None:
        s = GET_CLAUSE_COVERAGE_SCHEMA
        assert set(s["required"]) == {"regulation_id", "clause"}
        assert s["additionalProperties"] is False
        # Clause must allow the characters that appear in real labels.
        pat = s["properties"]["clause"]["pattern"]
        assert "§" in pat  # HIPAA sections
        assert "(" in pat  # HIPAA subparagraphs
        assert "/" in pat  # ISO clauses

    def test_output_schema_shape(self) -> None:
        s = GET_CLAUSE_COVERAGE_OUTPUT_SCHEMA
        assert "regulationId" in s["required"]
        assert "clause" in s["required"]
        assert "clauseId" in s["required"]
        assert "coverageState" in s["required"]
        enum = s["properties"]["coverageState"]["enum"]
        assert "covered-full" in enum
        assert "uncovered" in enum


class TestGetClauseCoverageLive:
    """Run against the real clauses index shipped under ``api/v1``."""

    def test_gdpr_art5_is_fully_covered(self, live_catalog: Catalog) -> None:
        r = get_clause_coverage(
            catalog=live_catalog, regulation_id="gdpr", clause="Art.5"
        )
        assert r["regulationId"] == "gdpr"
        assert r["clause"] == "Art.5"
        assert r["clauseId"].startswith("gdpr@")
        assert r["coverageState"] == "covered-full"
        assert r["coveringUcCount"] >= 1
        assert isinstance(r["coveringUcs"], list)
        assert all(isinstance(u, str) and u for u in r["coveringUcs"])
        # Deep link is relative and URL-encoded so it works regardless
        # of site deploy prefix.
        assert r["deepLink"].startswith("clause-navigator.html#clause=")

    def test_explicit_version_round_trips(
        self, live_catalog: Catalog
    ) -> None:
        r = get_clause_coverage(
            catalog=live_catalog,
            regulation_id="gdpr",
            clause="Art.5",
            version="2016/679",
        )
        assert r["version"] == "2016/679"

    def test_unknown_clause_raises(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_clause_coverage(
                catalog=live_catalog,
                regulation_id="gdpr",
                clause="Art.999",
            )

    def test_unknown_version_raises(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_clause_coverage(
                catalog=live_catalog,
                regulation_id="gdpr",
                clause="Art.5",
                version="9999/1",
            )

    def test_uncovered_clause_reports_empty_ucs(
        self, live_catalog: Catalog
    ) -> None:
        # Pick a clause the clauses index still marks uncovered — hard-coding
        # a label drifts when catalogue coverage changes.
        worklist = list_uncovered_clauses(
            catalog=live_catalog,
            regulations=["*"],
            limit=1,
        )
        entries = worklist["entries"]
        assert entries, "live catalogue should list at least one uncovered clause"
        row = entries[0]
        kwargs: dict[str, Any] = {
            "catalog": live_catalog,
            "regulation_id": row["regulationId"],
            "clause": row["clause"],
        }
        ver = row.get("version")
        if ver is not None:
            kwargs["version"] = ver
        r = get_clause_coverage(**kwargs)
        assert r["coverageState"] == "uncovered"
        assert r["coveringUcs"] == []
        assert r["coveringUcCount"] == 0


class TestGetClauseCoverageValidation:
    @pytest.mark.parametrize(
        "bad_id",
        ["GDPR", "gdpr ", " gdpr", "../evil", "gdpr;drop", "gdpr\x00"],
    )
    def test_rejects_bad_regulation_id(
        self, live_catalog: Catalog, bad_id: str
    ) -> None:
        with pytest.raises(ValueError):
            get_clause_coverage(
                catalog=live_catalog,
                regulation_id=bad_id,
                clause="Art.5",
            )

    @pytest.mark.parametrize(
        "bad_clause",
        [
            "",
            "   ",
            "Art.5; DROP TABLE users;",
            "Art\x005",
            "a" * 65,  # > CLAUSE_MAX_LENGTH
        ],
    )
    def test_rejects_bad_clause(
        self, live_catalog: Catalog, bad_clause: str
    ) -> None:
        with pytest.raises(ValueError):
            get_clause_coverage(
                catalog=live_catalog,
                regulation_id="gdpr",
                clause=bad_clause,
            )

    def test_rejects_non_string_version(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError):
            get_clause_coverage(
                catalog=live_catalog,
                regulation_id="gdpr",
                clause="Art.5",
                version=2016,  # type: ignore[arg-type]
            )


# =====================================================================
# list_uncovered_clauses
# =====================================================================


class TestListUncoveredClausesSchemas:
    def test_input_schema_shape(self) -> None:
        s = LIST_UNCOVERED_CLAUSES_SCHEMA
        assert "regulations" in s["required"]
        assert s["additionalProperties"] is False
        # Wildcard support is explicit in the pattern.
        item = s["properties"]["regulations"]["items"]
        assert item["pattern"].startswith("^(\\*|")

    def test_output_schema_shape(self) -> None:
        s = LIST_UNCOVERED_CLAUSES_OUTPUT_SCHEMA
        assert "count" in s["required"]
        assert "entries" in s["required"]
        assert "summary" in s["required"]


class TestListUncoveredClausesLive:
    def test_wildcard_returns_uncovered_sorted_by_priority(
        self, live_catalog: Catalog
    ) -> None:
        r = list_uncovered_clauses(
            catalog=live_catalog, regulations=["*"], limit=10
        )
        assert r["summary"]["totalUncoveredInScope"] > 0
        # Every entry is strictly uncovered.
        assert all(
            e["coverageState"] == "uncovered" for e in r["entries"]
        )
        # Sorted by descending priority weight.
        weights = [
            (e.get("priorityWeight") or 0.0) for e in r["entries"]
        ]
        assert weights == sorted(weights, reverse=True)

    def test_limit_is_honoured(self, live_catalog: Catalog) -> None:
        r = list_uncovered_clauses(
            catalog=live_catalog, regulations=["*"], limit=3
        )
        assert r["count"] <= 3
        assert len(r["entries"]) <= 3

    def test_truncation_flag_when_more_exist(
        self, live_catalog: Catalog
    ) -> None:
        r_small = list_uncovered_clauses(
            catalog=live_catalog, regulations=["*"], limit=1
        )
        # The live catalogue has >1 uncovered clauses; so
        # truncated must be True.
        if r_small["summary"]["totalUncoveredInScope"] > 1:
            assert r_small["summary"]["truncated"] is True

    def test_per_regulation_scope(self, live_catalog: Catalog) -> None:
        r = list_uncovered_clauses(
            catalog=live_catalog, regulations=["ccpa"]
        )
        assert all(e["regulationId"] == "ccpa" for e in r["entries"])

    def test_tier_filter(self, live_catalog: Catalog) -> None:
        r = list_uncovered_clauses(
            catalog=live_catalog, regulations=["*"], tier=2, limit=20
        )
        assert all(e.get("tier") == 2 for e in r["entries"])

    def test_unknown_regulation_is_reported(
        self, live_catalog: Catalog
    ) -> None:
        r = list_uncovered_clauses(
            catalog=live_catalog,
            regulations=["gdpr", "does-not-exist"],
        )
        assert "does-not-exist" in r["summary"]["regulationsNotFound"]

    def test_deep_link_is_url_encoded(
        self, live_catalog: Catalog
    ) -> None:
        r = list_uncovered_clauses(
            catalog=live_catalog, regulations=["*"], limit=5
        )
        for e in r["entries"]:
            assert e["deepLink"].startswith(
                "clause-navigator.html#clause="
            )
            # The clauseId portion must never contain a raw ``#`` or
            # ``@`` — those are reserved in hashes and would break the
            # client-side parser.
            fragment = e["deepLink"].split("#clause=", 1)[1]
            assert "@" not in fragment
            assert "#" not in fragment


class TestListUncoveredClausesValidation:
    def test_rejects_empty_list(self, live_catalog: Catalog) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            list_uncovered_clauses(
                catalog=live_catalog, regulations=[]
            )

    def test_rejects_too_many_regulations(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="at most"):
            list_uncovered_clauses(
                catalog=live_catalog,
                regulations=[f"r{i}" for i in range(21)],
            )

    @pytest.mark.parametrize(
        "bad", ["GDPR", "gdpr ", "../../etc", "gdpr;rm"],
    )
    def test_rejects_bad_slug(
        self, live_catalog: Catalog, bad: str
    ) -> None:
        with pytest.raises(ValueError):
            list_uncovered_clauses(
                catalog=live_catalog, regulations=[bad]
            )

    @pytest.mark.parametrize("bad_tier", [0, 4, -1, 99])
    def test_rejects_bad_tier(
        self, live_catalog: Catalog, bad_tier: int
    ) -> None:
        with pytest.raises(ValueError):
            list_uncovered_clauses(
                catalog=live_catalog,
                regulations=["*"],
                tier=bad_tier,
            )

    @pytest.mark.parametrize("bad_limit", [0, -5, 501, 10_000])
    def test_rejects_bad_limit(
        self, live_catalog: Catalog, bad_limit: int
    ) -> None:
        with pytest.raises(ValueError):
            list_uncovered_clauses(
                catalog=live_catalog,
                regulations=["*"],
                limit=bad_limit,
            )

    def test_rejects_non_boolean_common_flag(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError):
            list_uncovered_clauses(
                catalog=live_catalog,
                regulations=["*"],
                include_common_only="yes",  # type: ignore[arg-type]
            )


# =====================================================================
# Private-helper coverage closure
# =====================================================================


class TestEquipmentOverlayHelper:
    """Pin the four partial branches inside ``_equipment_overlay`` /
    ``_project_clause_entry`` that the broader fixture-driven suites do
    not naturally exercise.

    Without these tests:

    * branch 239->237 — the False arm of ``if clause:`` inside the
      ``clauseMappings`` loop (a mapping with a missing or empty
      ``clause`` field that the loop must skip silently).
    * branch 687->695 — the False arm of ``if clause_id:`` in
      ``_project_clause_entry``; ``deep_link`` stays ``None`` and the
      caller falls through without emitting a ``deepLink`` key.
    * branch 711->713 — the False arm of ``if endpoint:``; the
      ``clauseEndpoint`` key is omitted for entries with no endpoint.
    * branch 713->718 — the False arm of ``if deep_link:`` (same
      condition as 687 surfacing at the second emission site).
    """

    def test_clauseless_mapping_is_skipped(self) -> None:
        # Imports the private helper directly so the test stays
        # focused on the loop's branch matrix without dragging the
        # whole ``find_compliance_gap`` request shape into the fixture.
        from splunk_uc_mcp.tools.compliance import _equipment_overlay

        equipment_doc: dict[str, Any] = {
            "id": "azure",
            "regulations": [
                {
                    "regulationId": "gdpr",
                    "clauseMappings": [
                        {"clause": "Art.5"},
                        {"clause": ""},  # branch 239->237 (falsy clause)
                        {},  # also falsy via .get default
                        {"clause": "Art.32"},
                    ],
                }
            ],
        }
        gap_entry = {"commonClausesUncovered": ["Art.5", "Art.17", "Art.32"]}
        out = _equipment_overlay(equipment_doc, "gdpr", gap_entry)
        # The two non-empty clauses are accepted; the two falsy
        # mappings are silently skipped by the ``if clause:`` guard.
        assert out["clausesCoveredByEquipment"] == ["Art.32", "Art.5"]
        assert out["uncoveredClausesStillUncovered"] == ["Art.17"]

    def test_legacy_endpoint_fallback_when_regulation_id_missing(
        self,
    ) -> None:
        # Adjacent contract: when ``regulationId`` is missing on the
        # equipment regulation, the helper must derive it from
        # ``regulationEndpoint``. Pinning here so the fallback parser
        # does not silently regress.
        from splunk_uc_mcp.tools.compliance import _equipment_overlay

        equipment_doc: dict[str, Any] = {
            "id": "azure",
            "regulations": [
                {
                    "regulationEndpoint": (
                        "/api/v1/compliance/regulations/gdpr@2016-679.json"
                    ),
                    "clauseMappings": [{"clause": "Art.5"}],
                }
            ],
        }
        gap_entry = {"commonClausesUncovered": ["Art.5"]}
        out = _equipment_overlay(equipment_doc, "gdpr", gap_entry)
        assert out["clausesCoveredByEquipment"] == ["Art.5"]

    def test_project_entry_omits_deeplink_when_clause_id_missing(
        self,
    ) -> None:
        # Closes branches 687->695 (no clauseId means no deep_link)
        # AND 713->718 (deep_link is None, so the second emission site
        # is skipped). The returned payload must still be valid and
        # must NOT contain ``deepLink``.
        from splunk_uc_mcp.tools.compliance import _project_clause_entry

        entry = {
            "regulationId": "gdpr",
            "regulationShortName": "GDPR",
            "clause": "Art.5",
            # clauseId omitted on purpose
            "coverageState": "covered-full",
            "coveringUcs": ["UC-22.5.1"],
            "coveringUcCount": 1,
        }
        out = _project_clause_entry(entry)
        assert out["clause"] == "Art.5"
        assert out["coverageState"] == "covered-full"
        assert "deepLink" not in out
        # ``clauseId`` was None so the None-stripping pass should
        # remove it from the response payload entirely.
        assert "clauseId" not in out

    def test_project_entry_omits_endpoint_when_missing(self) -> None:
        # Closes branch 711->713 — when ``endpoint`` is missing the
        # ``clauseEndpoint`` key must NOT appear in the response.
        # We deliberately keep ``clauseId`` populated so the deep_link
        # branch still emits, isolating the endpoint-only False arm.
        from splunk_uc_mcp.tools.compliance import _project_clause_entry

        entry = {
            "regulationId": "gdpr",
            "regulationShortName": "GDPR",
            "clause": "Art.5",
            "clauseId": "gdpr@2016/679#Art.5",
            # endpoint omitted on purpose
            "coverageState": "covered-full",
            "coveringUcs": ["UC-22.5.1"],
            "coveringUcCount": 1,
        }
        out = _project_clause_entry(entry)
        assert "clauseEndpoint" not in out
        assert out["deepLink"].startswith("clause-navigator.html#clause=")
