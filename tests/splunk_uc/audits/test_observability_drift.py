"""Tests for audit-observability-drift."""

from __future__ import annotations

import splunk_uc.audits.observability_drift as od


def test_validate_quality_distribution_sum() -> None:
    issues = od.validate_quality(
        {
            "byCategoryCriticality": {
                "01": {
                    "high": {
                        "gold": 1,
                        "silver": 0,
                        "bronze": 0,
                        "none": 0,
                        "total": 1,
                        "distribution": {"gold": 50.0, "silver": 0.0, "bronze": 0.0, "none": 0.0},
                    }
                }
            },
            "bronzeHeavyCategories": [],
        }
    )
    assert any(i.code == "quality-distribution" for i in issues)


def test_validate_coverage_percentage_bounds() -> None:
    issues = od.validate_coverage(
        {
            "dimensions": ["compliance"],
            "perDimension": {"compliance": {"count": 1, "percentage": 150.0}},
            "matrixCounts": {"01": {"compliance": 1}},
            "matrixPercentages": {"01": {"compliance": 150.0}},
        }
    )
    assert any(i.code == "coverage-pct-range" for i in issues)
