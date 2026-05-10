"""Unit tests for ``scripts/generate_stewardship_digest.py``.

Repo-overhaul plan §P8 step 4 (2026-05-09): the digest is the
release-over-release stewardship report. The tests pin the contract
across six dimensions:

* Pure helpers (``_parse_iso_date``, ``_semver_key``, ``_snapshot_counts``,
  ``_quality_tiers``, ``_coverage_block``, ``_leader_block``,
  ``_delta_dict``, ``_top_movers``, ``_coverage_shifts``,
  ``_parse_audit_warnings``).
* ``_previous_snapshot`` selects the highest-versioned snapshot
  strictly less than ``current_version`` and ignores ``index.json``,
  malformed JSON, and snapshots equal to or above the current
  version.
* ``_stale_use_cases`` partitions sidecars into stale vs. fresh
  against a configurable threshold, sorts ``topStale`` by
  ``-ageDays, +id``, and treats missing ``lastReviewed`` as
  max-stale so curators see them first.
* ``build_digest`` end-to-end against synthetic fixtures emits a
  payload that validates against
  ``schemas/v2/stewardship-digest.schema.json``, including the
  ``previous is None`` first-release-ever path.
* Reproducibility: two invocations of ``main()`` against fixed
  inputs produce byte-identical ``stewardship-digest.json`` and
  ``stewardship-digest.md``.
* CLI exit codes: missing metrics → 2, malformed audit-warning → 2,
  invalid stale threshold → 2, valid invocation → 0.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
SCHEMA_PATH = REPO_ROOT / "schemas" / "v2" / "stewardship-digest.schema.json"

# Tests import the implementation module directly so monkeypatched module-level
# state propagates through the closure cleanly. The shim at
# scripts/generate_stewardship_digest.py would only re-export the public API
# at import time, which would not pick up later patches against helpers like
# ``_walk_sidecars`` or ``_previous_snapshot``.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import splunk_uc.generators.stewardship_digest as gsd  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture builders.
# ---------------------------------------------------------------------------


def _metrics(version: str, **overrides: Any) -> dict[str, Any]:
    """Return a minimal-but-valid metrics.json dict, overridable per test."""
    base: dict[str, Any] = {
        "$schema": "/schemas/v2/metrics.schema.json",
        "schema_version": "1.0.0",
        "catalogueVersion": version,
        "generatedAt": "2026-05-09T00:00:00+00:00",
        "build": {"platform": "test", "python": "3.14.4", "reproducible": False},
        "counts": {
            "useCases": 100,
            "categories": 5,
            "subcategories": 12,
            "regulations": 3,
            "equipment": 7,
        },
        "quality": {
            "tierCounts": {"gold": 10, "silver": 5, "bronze": 80, "none": 5},
            "tierPercentages": {"gold": 10.0, "silver": 5.0, "bronze": 80.0, "none": 5.0},
            "depthScore": {
                "count": 100,
                "min": 1,
                "max": 100,
                "mean": 50.0,
                "p50": 50,
                "p90": 90,
                "p99": 99,
            },
            "grandmaExplanation": {
                "count": 100,
                "min": 30,
                "max": 200,
                "mean": 100.0,
                "p50": 100,
                "p90": 150,
                "p99": 180,
            },
        },
        "coverage": {
            "compliance": {"count": 20, "percentage": 20.0},
            "mitreAttack": {"count": 30, "percentage": 30.0},
            "cimModels": {"count": 70, "percentage": 70.0},
            "equipment": {"count": 80, "percentage": 80.0},
            "escuDetections": {"count": 25, "percentage": 25.0},
            "escuRiskBased": {"count": 20, "percentage": 20.0},
            "prerequisites": {"count": 5, "percentage": 5.0},
        },
        "distributions": {
            "criticality": {"high": 50, "medium": 30, "low": 20},
            "difficulty": {"easy": 40, "medium": 40, "hard": 20},
            "wave": {"crawl": 60, "walk": 30, "run": 10},
        },
        "ucsByCategory": {"1": 50, "2": 30, "3": 20},
        "leaders": {
            "regulations": [
                {"regulation": "GDPR", "count": 10},
                {"regulation": "PCI DSS", "count": 8},
            ],
            "mitreAttack": [{"technique": "T1078", "count": 5}],
            "cimModels": [{"model": "Authentication", "count": 12}],
            "equipment": [{"equipment": "switch", "count": 7}],
        },
    }
    base.update(overrides)
    return base


def _sidecar(uc_id: str, last_reviewed: str | None, status: str = "verified") -> dict[str, Any]:
    return {
        "id": uc_id,
        "title": f"UC {uc_id}",
        "lastReviewed": last_reviewed,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Pure helpers.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2026-05-09", _dt.date(2026, 5, 9)),
        ("1999-12-31", _dt.date(1999, 12, 31)),
        ("not-a-date", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_iso_date(raw, expected):
    assert gsd._parse_iso_date(raw) == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("8.0.0", (8, 0, 0)),
        ("9.10.5", (9, 10, 5)),
        ("8.0.0-rc1", (8, 0, 0)),
        ("8.0.0+build123", (8, 0, 0)),
        ("8.0.0-rc1+build123", (8, 0, 0)),
        ("garbage", (0,)),
    ],
)
def test_semver_key_strips_suffixes(version, expected):
    assert gsd._semver_key(version) == expected


def test_snapshot_counts_extracts_only_count_fields():
    out = gsd._snapshot_counts(_metrics("8.0.0"))
    assert out == {
        "version": "8.0.0",
        "useCases": 100,
        "categories": 5,
        "subcategories": 12,
        "regulations": 3,
        "equipment": 7,
    }


def test_snapshot_counts_defaults_missing_fields_to_zero():
    out = gsd._snapshot_counts({"catalogueVersion": "8.0.0", "counts": {}})
    assert out == {
        "version": "8.0.0",
        "useCases": 0,
        "categories": 0,
        "subcategories": 0,
        "regulations": 0,
        "equipment": 0,
    }


def test_quality_tiers_returns_all_four_tiers():
    out = gsd._quality_tiers(_metrics("8.0.0"))
    assert out == {"gold": 10, "silver": 5, "bronze": 80, "none": 5}


def test_quality_tiers_fills_missing_tiers_with_zero():
    out = gsd._quality_tiers({"quality": {"tierCounts": {"gold": 1}}})
    assert out == {"gold": 1, "silver": 0, "bronze": 0, "none": 0}


def test_coverage_block_returns_all_axes():
    out = gsd._coverage_block(_metrics("8.0.0"))
    assert set(out) == set(gsd.COVERAGE_AXES)
    assert out["compliance"] == {"count": 20, "percentage": 20.0}
    assert out["prerequisites"] == {"count": 5, "percentage": 5.0}


def test_leader_block_flattens_to_name_count_dict():
    out = gsd._leader_block(_metrics("8.0.0"))
    assert out["regulations"] == {"GDPR": 10, "PCI DSS": 8}
    assert out["mitreAttack"] == {"T1078": 5}
    assert out["cimModels"] == {"Authentication": 12}
    assert out["equipment"] == {"switch": 7}


def test_leader_block_skips_entries_without_name():
    metrics = _metrics("8.0.0")
    metrics["leaders"]["regulations"] = [{"count": 5}]
    out = gsd._leader_block(metrics)
    assert out["regulations"] == {}


def test_delta_dict_handles_missing_keys_in_either_side():
    cur = {"a": 5, "b": 3}
    prev = {"a": 2, "c": 4}
    out = gsd._delta_dict(cur, prev)
    assert out == {"a": 3, "b": 3, "c": -4}


def test_delta_dict_returns_zeros_when_inputs_match():
    out = gsd._delta_dict({"a": 5}, {"a": 5})
    assert out == {"a": 0}


def test_top_movers_drops_zero_deltas():
    cur = {"A": 10, "B": 5, "C": 3}
    prev = {"A": 10, "B": 4, "C": 5}
    out = gsd._top_movers(cur, prev)
    names = [e["name"] for e in out]
    assert "A" not in names
    assert names == ["C", "B"]


def test_top_movers_sorted_by_abs_delta_then_name():
    cur = {"A": 10, "B": 5, "C": 7}
    prev = {"A": 5, "B": 3, "C": 4}
    out = gsd._top_movers(cur, prev)
    assert [(e["name"], e["delta"]) for e in out] == [("A", 5), ("C", 3), ("B", 2)]


def test_top_movers_respects_limit():
    cur = {chr(ord("A") + i): i + 10 for i in range(15)}
    prev = {chr(ord("A") + i): 0 for i in range(15)}
    out = gsd._top_movers(cur, prev, limit=5)
    assert len(out) == 5


def test_top_movers_handles_alphabetic_tiebreak_for_equal_abs_deltas():
    cur = {"A": 5, "B": 5, "C": 5}
    prev = {"A": 0, "B": 0, "C": 0}
    out = gsd._top_movers(cur, prev)
    assert [e["name"] for e in out] == ["A", "B", "C"]


def test_coverage_shifts_no_previous_emits_zero_delta():
    cur = {"compliance": {"count": 20, "percentage": 20.0}}
    out = gsd._coverage_shifts(cur, None)
    assert out["compliance"]["currentCount"] == 20
    assert out["compliance"]["delta"] == 0
    assert "previousCount" not in out["compliance"]


def test_coverage_shifts_with_previous_includes_percentage_delta():
    cur = {"compliance": {"count": 30, "percentage": 30.0}}
    prev = {"compliance": {"count": 25, "percentage": 25.0}}
    out = gsd._coverage_shifts(cur, prev)
    assert out["compliance"]["delta"] == 5
    assert out["compliance"]["previousCount"] == 25
    assert out["compliance"]["percentageDelta"] == 5.0


def test_parse_audit_warnings_extracts_warn_lines_only():
    stderr = (
        "INFO : starting\n"
        "WARN : drift detected on field A\n"
        "ERROR : exit\n"
        "WARN : drift detected on field B\n"
        "WARN :  \n"
        "WARN: missing colon-space prefix\n"
    )
    out = gsd._parse_audit_warnings(stderr, "audit_x")
    assert [w["message"] for w in out] == [
        "drift detected on field A",
        "drift detected on field B",
    ]
    assert all(w["audit"] == "audit_x" and w["severity"] == "warn" for w in out)


# ---------------------------------------------------------------------------
# _previous_snapshot.
# ---------------------------------------------------------------------------


def test_previous_snapshot_returns_none_when_history_empty(tmp_path: Path):
    history = tmp_path / "metrics-history"
    history.mkdir()
    assert gsd._previous_snapshot(history, "8.0.0") is None


def test_previous_snapshot_picks_highest_strictly_below_current(tmp_path: Path):
    history = tmp_path / "metrics-history"
    history.mkdir()
    for ver in ("7.4.0", "7.4.2", "8.0.0"):
        (history / f"{ver}.json").write_text(json.dumps(_metrics(ver)), encoding="utf-8")
    out = gsd._previous_snapshot(history, "8.0.0")
    assert out is not None
    assert out["catalogueVersion"] == "7.4.2"


def test_previous_snapshot_ignores_index_json(tmp_path: Path):
    history = tmp_path / "metrics-history"
    history.mkdir()
    (history / "7.4.2.json").write_text(json.dumps(_metrics("7.4.2")), encoding="utf-8")
    (history / "index.json").write_text(json.dumps({"snapshots": []}), encoding="utf-8")
    out = gsd._previous_snapshot(history, "8.0.0")
    assert out is not None
    assert out["catalogueVersion"] == "7.4.2"


def test_previous_snapshot_ignores_malformed_files(tmp_path: Path):
    history = tmp_path / "metrics-history"
    history.mkdir()
    (history / "7.4.2.json").write_text("{not json", encoding="utf-8")
    (history / "7.3.0.json").write_text(json.dumps(_metrics("7.3.0")), encoding="utf-8")
    out = gsd._previous_snapshot(history, "8.0.0")
    assert out is not None
    assert out["catalogueVersion"] == "7.3.0"


def test_previous_snapshot_returns_none_when_only_equal_or_above_current(tmp_path: Path):
    history = tmp_path / "metrics-history"
    history.mkdir()
    (history / "8.0.0.json").write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    (history / "9.0.0.json").write_text(json.dumps(_metrics("9.0.0")), encoding="utf-8")
    assert gsd._previous_snapshot(history, "8.0.0") is None


# ---------------------------------------------------------------------------
# Stale UC detection.
# ---------------------------------------------------------------------------


def test_stale_use_cases_partitions_against_threshold():
    ref = _dt.date(2026, 5, 9)
    sidecars = [
        _sidecar("1.1.1", "2025-09-01"),     # 250 days → stale @ 180
        _sidecar("1.1.2", "2026-04-01"),     # 38 days → fresh
        _sidecar("1.1.3", "2024-01-01"),     # 859 days → stale
    ]
    out = gsd._stale_use_cases(sidecars, reference=ref, threshold_days=180)
    assert out["count"] == 2
    ids = [u["id"] for u in out["topStale"]]
    assert ids == ["1.1.3", "1.1.1"]
    assert out["byCategory"] == {"1": 2}


def test_stale_use_cases_treats_missing_lastReviewed_as_max_stale():
    ref = _dt.date(2026, 5, 9)
    sidecars = [
        _sidecar("2.1.1", None),
        _sidecar("2.1.2", "2026-05-01"),
    ]
    out = gsd._stale_use_cases(sidecars, reference=ref, threshold_days=30)
    assert out["count"] == 1
    assert out["topStale"][0]["id"] == "2.1.1"
    assert out["topStale"][0]["lastReviewed"] is None


def test_stale_use_cases_caps_topStale_at_20():
    ref = _dt.date(2026, 5, 9)
    sidecars = [
        _sidecar(f"3.1.{i}", "2024-01-01") for i in range(1, 31)
    ]
    out = gsd._stale_use_cases(sidecars, reference=ref, threshold_days=180)
    assert out["count"] == 30
    assert len(out["topStale"]) == gsd.TOP_STALE_LIMIT


def test_stale_use_cases_normalises_unknown_status():
    ref = _dt.date(2026, 5, 9)
    sidecars = [_sidecar("4.1.1", "2024-01-01", status="experimental")]
    out = gsd._stale_use_cases(sidecars, reference=ref, threshold_days=30)
    assert out["topStale"][0]["status"] == "unknown"


def test_stale_use_cases_handles_unparseable_date_as_missing():
    ref = _dt.date(2026, 5, 9)
    sidecars = [_sidecar("5.1.1", "garbage")]
    out = gsd._stale_use_cases(sidecars, reference=ref, threshold_days=30)
    assert out["count"] == 1
    assert out["topStale"][0]["lastReviewed"] == "garbage"


def test_stale_use_cases_skips_sidecars_without_id():
    ref = _dt.date(2026, 5, 9)
    sidecars = [
        {"title": "no-id", "lastReviewed": None},
        _sidecar("6.1.1", None),
    ]
    out = gsd._stale_use_cases(sidecars, reference=ref, threshold_days=30)
    assert out["count"] == 1
    assert out["topStale"][0]["id"] == "6.1.1"


# ---------------------------------------------------------------------------
# build_digest end-to-end + schema gate.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(schema: dict[str, Any], digest: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(schema).validate(digest)


def test_build_digest_first_release_validates(schema):
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=[],
        audit_warnings=[],
        reference_date=_dt.date(2026, 5, 9),
    )
    _validate(schema, digest)
    assert digest["previous"] is None
    assert digest["deltas"]["useCases"] == 0
    assert digest["topMovers"]["regulations"] == []


def test_build_digest_with_prior_release_emits_signed_deltas(schema):
    cur = _metrics("8.0.0")
    prev = _metrics(
        "7.4.2",
        counts={
            "useCases": 90,
            "categories": 5,
            "subcategories": 11,
            "regulations": 3,
            "equipment": 7,
        },
        leaders={
            "regulations": [{"regulation": "GDPR", "count": 5}],
            "mitreAttack": [],
            "cimModels": [],
            "equipment": [],
        },
    )
    digest = gsd.build_digest(
        metrics=cur,
        previous=prev,
        sidecars=[],
        audit_warnings=[],
        reference_date=_dt.date(2026, 5, 9),
    )
    _validate(schema, digest)
    assert digest["deltas"]["useCases"] == 10
    assert digest["deltas"]["subcategories"] == 1
    movers = digest["topMovers"]["regulations"]
    assert any(m["name"] == "GDPR" and m["delta"] == 5 for m in movers)


def test_build_digest_includes_audit_warnings(schema):
    warnings = [
        {"audit": "audit_roadmap_consistency", "severity": "warn", "message": "drift"},
    ]
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=[],
        audit_warnings=warnings,
        reference_date=_dt.date(2026, 5, 9),
    )
    _validate(schema, digest)
    assert digest["auditWarnings"] == warnings


def test_build_digest_walks_synthetic_sidecars(schema):
    sidecars = [_sidecar(f"1.1.{i}", "2024-01-01") for i in range(1, 11)]
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=sidecars,
        audit_warnings=[],
        reference_date=_dt.date(2026, 5, 9),
        stale_threshold_days=30,
    )
    _validate(schema, digest)
    assert digest["staleUseCases"]["count"] == 10
    assert digest["staleUseCases"]["thresholdDays"] == 30


# ---------------------------------------------------------------------------
# Reproducibility.
# ---------------------------------------------------------------------------


def test_main_byte_identical_across_two_runs(tmp_path: Path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    out_dir_a = tmp_path / "out_a"
    out_dir_b = tmp_path / "out_b"

    args = [
        "--metrics", str(metrics_path),
        "--history-dir", str(history_dir),
        "--content-dir", str(content_dir),
        "--reference-date", "2026-05-09",
    ]
    rc_a = gsd.main([*args, "--out", str(out_dir_a)])
    rc_b = gsd.main([*args, "--out", str(out_dir_b)])
    assert rc_a == 0
    assert rc_b == 0

    json_a = (out_dir_a / "stewardship-digest.json").read_bytes()
    json_b = (out_dir_b / "stewardship-digest.json").read_bytes()
    assert json_a == json_b

    md_a = (out_dir_a / "stewardship-digest.md").read_bytes()
    md_b = (out_dir_b / "stewardship-digest.md").read_bytes()
    assert md_a == md_b


def test_main_emitted_json_validates_against_schema(tmp_path: Path, schema):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    out_dir = tmp_path / "out"

    args = [
        "--metrics", str(metrics_path),
        "--history-dir", str(history_dir),
        "--content-dir", str(content_dir),
        "--out", str(out_dir),
        "--reference-date", "2026-05-09",
    ]
    assert gsd.main(args) == 0
    digest = json.loads((out_dir / "stewardship-digest.json").read_text(encoding="utf-8"))
    _validate(schema, digest)


# ---------------------------------------------------------------------------
# CLI exit codes.
# ---------------------------------------------------------------------------


def test_main_returns_2_when_metrics_missing(tmp_path: Path):
    rc = gsd.main(
        [
            "--metrics", str(tmp_path / "nope.json"),
            "--history-dir", str(tmp_path),
            "--content-dir", str(tmp_path),
            "--out", str(tmp_path / "out"),
            "--reference-date", "2026-05-09",
        ]
    )
    assert rc == 2


def test_main_returns_2_when_audit_warning_malformed(tmp_path: Path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    rc = gsd.main(
        [
            "--metrics", str(metrics_path),
            "--history-dir", str(tmp_path / "history"),
            "--content-dir", str(tmp_path / "content"),
            "--out", str(tmp_path / "out"),
            "--reference-date", "2026-05-09",
            "--audit-warning", "no-equals-sign",
        ]
    )
    assert rc == 2


def test_main_returns_2_when_audit_warning_empty_message(tmp_path: Path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    rc = gsd.main(
        [
            "--metrics", str(metrics_path),
            "--history-dir", str(tmp_path / "history"),
            "--content-dir", str(tmp_path / "content"),
            "--out", str(tmp_path / "out"),
            "--reference-date", "2026-05-09",
            "--audit-warning", "audit_x=",
        ]
    )
    assert rc == 2


def test_main_returns_2_when_threshold_invalid(tmp_path: Path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    rc = gsd.main(
        [
            "--metrics", str(metrics_path),
            "--history-dir", str(tmp_path / "history"),
            "--content-dir", str(tmp_path / "content"),
            "--out", str(tmp_path / "out"),
            "--reference-date", "2026-05-09",
            "--stale-threshold-days", "0",
        ]
    )
    assert rc == 2


def test_main_returns_2_when_reference_date_invalid(tmp_path: Path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    rc = gsd.main(
        [
            "--metrics", str(metrics_path),
            "--history-dir", str(tmp_path / "history"),
            "--content-dir", str(tmp_path / "content"),
            "--out", str(tmp_path / "out"),
            "--reference-date", "not-a-date",
        ]
    )
    assert rc == 2


def test_main_accepts_audit_warning_and_includes_it(tmp_path: Path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_metrics("8.0.0")), encoding="utf-8")
    out_dir = tmp_path / "out"
    rc = gsd.main(
        [
            "--metrics", str(metrics_path),
            "--history-dir", str(tmp_path / "history"),
            "--content-dir", str(tmp_path / "content"),
            "--out", str(out_dir),
            "--reference-date", "2026-05-09",
            "--audit-warning", "audit_x=drift detected",
            "--audit-warning", "audit_y=other warning",
        ]
    )
    assert rc == 0
    digest = json.loads((out_dir / "stewardship-digest.json").read_text(encoding="utf-8"))
    audits = sorted(w["audit"] for w in digest["auditWarnings"])
    assert audits == ["audit_x", "audit_y"]


# ---------------------------------------------------------------------------
# Markdown rendering smoke.
# ---------------------------------------------------------------------------


def test_markdown_starts_with_digest_heading():
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=[],
        audit_warnings=[],
        reference_date=_dt.date(2026, 5, 9),
    )
    md = gsd.render_markdown(digest)
    assert md.startswith("# Stewardship Digest\n")
    assert "## Catalogue counts" in md
    assert "## Quality tier mix" in md
    assert "## Coverage shifts" in md
    assert "## Stale use cases" in md


def test_markdown_lists_audit_warnings_section_when_present():
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=[],
        audit_warnings=[{"audit": "x", "severity": "warn", "message": "hi"}],
        reference_date=_dt.date(2026, 5, 9),
    )
    md = gsd.render_markdown(digest)
    assert "## Open audit warnings" in md
    assert "**x** (warn): hi" in md


def test_markdown_omits_audit_warnings_section_when_empty():
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=[],
        audit_warnings=[],
        reference_date=_dt.date(2026, 5, 9),
    )
    md = gsd.render_markdown(digest)
    assert "## Open audit warnings" not in md


# ---------------------------------------------------------------------------
# Schema sanity.
# ---------------------------------------------------------------------------


def test_schema_is_valid_draft_2020_12(schema):
    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_top_level_keys_match_payload_keys():
    expected = {
        "$schema",
        "schema_version",
        "generatedAt",
        "referenceDate",
        "current",
        "previous",
        "deltas",
        "qualityShifts",
        "coverageShifts",
        "topMovers",
        "auditWarnings",
        "staleUseCases",
    }
    digest = gsd.build_digest(
        metrics=_metrics("8.0.0"),
        previous=None,
        sidecars=[],
        audit_warnings=[],
        reference_date=_dt.date(2026, 5, 9),
    )
    assert set(digest.keys()) == expected
