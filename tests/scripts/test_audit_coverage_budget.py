"""Unit tests for ``python3 -m splunk_uc audit-coverage-budget``.

The auditor classifies files into three tiers (tier-1, tier-2,
tier-3) and ratchets per-file coverage against a committed baseline.
A regression beyond a configurable tolerance fails CI; a brand-new
file under tier-1 / tier-2 must clear its tier floor.

These tests cover:

* ``_classify`` correctness across realistic paths from each tier.
* ``build_baseline`` round-trips a coverage.py JSON report into the
  baseline JSON schema (and its ``--print-baseline`` form sorts files
  deterministically so committed diffs stay reviewable).
* ``check`` returns 0 when the report is at or above the baseline,
  1 when any file regresses beyond tolerance, and 1 when a new
  tier-1/tier-2 file lands below its floor.
* The committed v9.1.0 baseline validates against
  ``schemas/coverage-baseline.schema.json``.

The auditor never executes pytest itself — it consumes a
coverage.py JSON report. Every test here builds a synthetic report
in-memory or on a tmp_path so the suite stays hermetic and fast.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# P6 (scripts taxonomy, 2026-05-09): the audit body now lives at
# src/splunk_uc/audits/coverage_budget.py with a thin shim at the
# original scripts/ path. The test does not monkeypatch any module
# state but loading the implementation module directly keeps the
# import surface aligned with the rest of the migrated suite. The
# legacy spec-loader path is preserved as a fallback for an unpacked
# sdist that lost the src/ tree.
try:
    import splunk_uc.audits.coverage_budget as audit
except ImportError:
    _spec = importlib.util.spec_from_file_location(
        "audit_coverage_budget",
        REPO_ROOT / "scripts" / "audit_coverage_budget.py",
    )
    assert _spec is not None and _spec.loader is not None
    audit = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(audit)


def _make_report(per_file: dict[str, tuple[int, int]]) -> dict[str, Any]:
    """Build a minimal coverage.py-shaped JSON report.

    ``per_file`` is ``{path: (covered_lines, num_statements)}``;
    everything else (totals, executed_lines, missing_lines) is
    derived deterministically.
    """
    files: dict[str, Any] = {}
    total_cov = 0
    total_stmt = 0
    for path, (cov, stmt) in per_file.items():
        missing = stmt - cov
        pct = (cov / stmt * 100) if stmt else 0.0
        files[path] = {
            "summary": {
                "covered_lines": cov,
                "num_statements": stmt,
                "percent_covered": pct,
                "missing_lines": missing,
            }
        }
        total_cov += cov
        total_stmt += stmt
    pct = (total_cov / total_stmt * 100) if total_stmt else 0.0
    return {
        "files": files,
        "totals": {
            "covered_lines": total_cov,
            "num_statements": total_stmt,
            "percent_covered": pct,
            "missing_lines": total_stmt - total_cov,
        },
    }


# ---------------------------------------------------------------------------
# _classify
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path, expected",
    [
        # Tier 1 (build pipeline core)
        ("tools/build/build.py", "tier1"),
        ("tools/build/__init__.py", "tier1"),
        ("tools/build/enrichment.py", "tier1"),
        ("tools/build/render_legacy_artifacts.py", "tier1"),
        # Tier 1 excludes (one-shot generators inside tools/build/)
        ("tools/build/migrate_legacy.py", "tier3"),
        ("tools/build/generate_phase4_5.py", "tier3"),
        # Tier 2 (audit CLIs + named exceptions). These strings are
        # *path-shaped test fixtures* fed into the classifier — not real
        # invocations — because the classifier matches on
        # ``scripts/audit_*.py`` / ``src/splunk_uc/audits/*.py`` patterns
        # to bucket coverage-report file paths.
        ("scripts/audit_uc_structure.py", "tier2"),
        ("scripts/audit_action_pins.py", "tier2"),
        ("scripts/audit_compliance_mappings.py", "tier2"),
        ("scripts/equipment_lib.py", "tier2"),
        ("scripts/build_es.py", "tier2"),
        ("scripts/build_ta.py", "tier2"),
        # Tier 3 (one-shot helpers — always exempt)
        ("scripts/uplift_iso27001_tier_bcd.py", "tier3"),
        ("python3 -m splunk_uc migrate-compliance-phase4", "tier3"),
        ("scripts/_draft_uc_18_1_15.py", "tier3"),
        ("scripts/backfill_cim_models.py", "tier3"),
        ("scripts/enrich_di_gold.py", "tier3"),
        # ``generate-md-from-json`` was retired on 2026-05-18 (F21 close);
        # this row is retained as a path-shape fixture so the classifier
        # logic is exercised, not as a live invocation.
        ("python3 -m splunk_uc generate-md-from-json", "tier3"),
        # P6 Tier 2 batch 5: generate_recommender_app.py is now a shim;
        # the implementation moved to src/splunk_uc/generators/recommender_app.py.
        ("python3 -m splunk_uc generate-recommender-app", "tier3"),
        ("python3 -m splunk_uc ingest-all", "tier3"),
        ("scripts/ingest/source_a.py", "tier3"),
        # Anything outside the included paths is tier-3
        ("mcp/src/splunk_uc_mcp/server.py", "tier3"),
        ("tests/build/test_foo.py", "tier3"),
    ],
)
def test_classify_assigns_correct_tier(path: str, expected: str) -> None:
    assert audit._classify(path) == expected, f"path {path!r} should be classified as {expected!r}"


# ---------------------------------------------------------------------------
# build_baseline
# ---------------------------------------------------------------------------


def test_build_baseline_partitions_by_tier(tmp_path: Path) -> None:
    """build_baseline must route every input file into exactly one tier bucket."""
    report = _make_report(
        {
            "tools/build/build.py": (50, 100),
            "tools/build/migrate_x.py": (0, 30),  # tier-1 exclude → tier-3
            "scripts/audit_uc_ids.py": (10, 100),
            "scripts/uplift_x.py": (0, 50),  # tier-3
        }
    )
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))

    out = audit.build_baseline(rp)
    assert "tools/build/build.py" in out["tier_1_modules"]
    assert "tools/build/migrate_x.py" not in out["tier_1_modules"]
    assert "tools/build/migrate_x.py" in out["tier_3_exempt"]
    assert "scripts/audit_uc_ids.py" in out["tier_2_modules"]
    assert "scripts/audit_uc_ids.py" not in out["tier_1_modules"]
    assert "scripts/uplift_x.py" in out["tier_3_exempt"]
    # Per-file record shape
    rec = out["tier_1_modules"]["tools/build/build.py"]
    assert rec.keys() == {
        "covered_lines",
        "num_statements",
        "percent_covered",
        "missing_lines",
    }


def test_build_baseline_sorts_deterministically(tmp_path: Path) -> None:
    """The committed baseline must diff cleanly from one capture to the next.

    Sorted dicts mean a contributor running --print-baseline gets the same
    serialisation regardless of pytest discovery order.
    """
    report = _make_report(
        {
            "tools/build/zeta.py": (1, 1),
            "tools/build/alpha.py": (1, 1),
            "tools/build/middle.py": (1, 1),
        }
    )
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    out = audit.build_baseline(rp)
    keys = list(out["tier_1_modules"].keys())
    assert keys == sorted(keys), f"tier_1_modules must be lexicographically sorted; got {keys}"


def test_build_baseline_rounds_percentages_to_two_decimals(tmp_path: Path) -> None:
    """Coverage percentages must round to 2 decimals so trivial float jitter doesn't churn diffs."""
    # 1/3 = 33.333... → 33.33
    report = _make_report({"tools/build/build.py": (1, 3)})
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    out = audit.build_baseline(rp)
    pct = out["tier_1_modules"]["tools/build/build.py"]["percent_covered"]
    assert pct == 33.33, f"expected 33.33, got {pct}"


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def _write_baseline(tmp_path: Path, baseline: dict[str, Any]) -> Path:
    p = tmp_path / "baseline.json"
    # The baseline-builder normally inserts a $schema key; tests don't need it.
    p.write_text(json.dumps(baseline))
    return p


def _baseline_with(
    tier1: dict[str, float], tier2: dict[str, float] | None = None
) -> dict[str, Any]:
    return {
        "version": "9.1.0",
        "captured_at": "2026-05-09T00:00:00Z",
        "git_head": "0" * 40,
        "totals": {
            "covered_lines": 0,
            "num_statements": 0,
            "percent_covered": 0.0,
            "missing_lines": 0,
        },
        "tier_1_modules": {
            path: {
                "covered_lines": int(pct),
                "num_statements": 100,
                "percent_covered": pct,
                "missing_lines": 100 - int(pct),
            }
            for path, pct in tier1.items()
        },
        "tier_2_modules": {
            path: {
                "covered_lines": int(pct),
                "num_statements": 100,
                "percent_covered": pct,
                "missing_lines": 100 - int(pct),
            }
            for path, pct in (tier2 or {}).items()
        },
        "tier_3_exempt": [],
    }


def test_check_passes_when_report_matches_baseline(tmp_path: Path) -> None:
    baseline = _baseline_with({"tools/build/build.py": 50.0})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"tools/build/build.py": (50, 100)})
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))

    rc = audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0)
    assert rc == 0


def test_check_passes_when_coverage_improves(tmp_path: Path) -> None:
    """Improvement is silently accepted; the next baseline regen will lock it in."""
    baseline = _baseline_with({"tools/build/build.py": 50.0})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"tools/build/build.py": (75, 100)})
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    assert audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0) == 0


def test_check_passes_within_tolerance(tmp_path: Path) -> None:
    """A small jitter (<=tolerance) is accepted to absorb rounding noise."""
    baseline = _baseline_with({"tools/build/build.py": 50.0})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"tools/build/build.py": (49, 100)})  # 49.0% (Δ -1.0pp)
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    assert audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0) == 0


def test_check_fails_when_tier1_regresses_beyond_tolerance(tmp_path: Path) -> None:
    baseline = _baseline_with({"tools/build/build.py": 50.0})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"tools/build/build.py": (40, 100)})  # 40.0% (Δ -10pp)
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    assert audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0) == 1


def test_check_fails_when_tier2_regresses_beyond_tolerance(tmp_path: Path) -> None:
    baseline = _baseline_with({}, {"scripts/audit_uc_ids.py": 70.0})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"scripts/audit_uc_ids.py": (40, 100)})  # 40.0% (Δ -30pp)
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    assert audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0) == 1


def test_check_fails_when_new_tier1_file_below_floor(tmp_path: Path) -> None:
    """A brand-new tier-1 file that doesn't meet the new-file floor blocks the merge."""
    baseline = _baseline_with({})  # empty baseline — every file is "new"
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"tools/build/new_module.py": (10, 100)})  # 10% < 60% floor
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    assert audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0) == 1


def test_check_passes_when_new_tier1_file_clears_floor(tmp_path: Path) -> None:
    baseline = _baseline_with({})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({"tools/build/new_module.py": (75, 100)})  # 75% > 60% floor
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    assert audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0) == 0


def test_check_warns_when_tier1_file_disappears(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Deleting a tier-1 file is allowed (warned, but not failed).

    A real deletion that actually moves coverage backward will get
    caught by the totals rollup at the next baseline-regen step.
    """
    baseline = _baseline_with({"tools/build/old.py": 80.0})
    bp = _write_baseline(tmp_path, baseline)
    report = _make_report({})  # old.py is gone
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    rc = audit.check(bp, rp, tolerance=1.0, tier1_floor=60.0, tier2_floor=40.0)
    assert rc == 0
    captured = capsys.readouterr()
    assert "disappeared since the baseline" in captured.out


def test_check_returns_2_on_missing_baseline(tmp_path: Path) -> None:
    """Missing baseline is a usage error, not a coverage failure."""
    report = _make_report({"tools/build/build.py": (50, 100)})
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(report))
    rc = audit.check(
        tmp_path / "nonexistent.json",
        rp,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 2


# ---------------------------------------------------------------------------
# Committed baseline ↔ schema
# ---------------------------------------------------------------------------


def test_committed_baseline_validates_against_schema() -> None:
    """The v9.1.0 baseline must always validate against the schema.

    Hand-edits to the baseline JSON have to satisfy the schema; this
    test catches drift in either direction.
    """
    baseline_path = REPO_ROOT / "data" / "baselines" / "coverage-v9.1.0.json"
    schema_path = REPO_ROOT / "schemas" / "coverage-baseline.schema.json"
    assert baseline_path.is_file(), f"baseline missing at {baseline_path}"
    assert schema_path.is_file(), f"schema missing at {schema_path}"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=baseline, schema=schema)


def test_committed_baseline_has_nonempty_tier1_and_tier2() -> None:
    """If the partition stops finding tier-1/tier-2 files something has broken in classification."""
    baseline_path = REPO_ROOT / "data" / "baselines" / "coverage-v9.1.0.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["tier_1_modules"], "tier_1_modules must list at least tools/build/*"
    assert baseline["tier_2_modules"], "tier_2_modules must list at least scripts/audit_*.py"


def test_committed_baseline_version_matches_VERSION() -> None:
    """Drift between the baseline's ``version`` field and the repo VERSION
    means the baseline is stale; a new one should be cut and committed.
    """
    baseline_path = REPO_ROOT / "data" / "baselines" / "coverage-v9.1.0.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    # The baseline filename pins the version; the field inside must agree.
    assert baseline["version"].startswith("9.1"), (
        f"baseline version {baseline['version']!r} does not match the v9.1.x family "
        f"the filename promises. If you cut a new baseline, rename the file too."
    )
