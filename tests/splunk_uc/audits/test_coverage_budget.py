"""Unit tests for `src/splunk_uc/audits/coverage_budget.py`.

This pins the CI ratchet itself — the foundation of the P16
test-coverage burndown. Every contract surface is exercised:

- `_classify` (tier-1 includes / tier-1 excludes / tier-2 includes /
  tier-3 fallthrough)
- `_short_record` (the 4-key reshape over a coverage.py record)
- `_load_coverage_report` (missing-file ``SystemExit(2)`` with stderr;
  path normalisation to repo-root-relative posix; the
  ``ValueError``-fallback when a file lives outside REPO_ROOT)
- `_git_head` (subprocess happy path + Exception → "unknown")
- `_read_version` (VERSION file present / missing)
- `build_baseline` (tier partitioning, totals rollup, ``$schema`` key,
  sorted dicts, captured_at format, git_head wired)
- `check` (missing-baseline → 2; clean → 0; regression beyond
  tolerance → 1; disappeared-file → warning-only; new tier-1/2 file
  below floor → 1; mixed regression + warning paths; the
  ``percent_covered - tolerance`` boundary; tier-2-only files)
- `main` (`--print-baseline` happy path; default flow into ``check``;
  ``argv=None`` fall-through to ``sys.argv``; ``--help`` exits 0;
  the ``__main__`` block)

All tests are hermetic — `tmp_path` for coverage JSON and baseline
fixtures, `monkeypatch` for subprocess / VERSION / REPO_ROOT
rewiring where needed.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

import pytest

from splunk_uc.audits import coverage_budget as cb

# -------------------------------------------------------------- fixtures


_SENTINEL: Any = object()


class WriteReport(Protocol):
    """Factory for a synthetic coverage.py JSON report file."""

    def __call__(
        self,
        files: dict[str, dict[str, Any]],
        *,
        totals: dict[str, Any] | None = ...,
    ) -> Path: ...


class WriteBaseline(Protocol):
    """Factory for a synthetic baseline JSON file."""

    def __call__(self, payload: dict[str, Any]) -> Path: ...


@pytest.fixture
def write_report(tmp_path: Path) -> WriteReport:
    """Write a coverage.py-shaped report under ``tmp_path`` and return its path."""

    counter = {"n": 0}

    def _make(
        files: dict[str, dict[str, Any]],
        *,
        totals: Any = _SENTINEL,
    ) -> Path:
        counter["n"] += 1
        body: dict[str, Any] = {"files": files}
        if totals is not _SENTINEL:
            body["totals"] = totals
        else:
            body["totals"] = {
                "covered_lines": 100,
                "num_statements": 200,
                "percent_covered": 50.0,
                "missing_lines": 100,
            }
        path = tmp_path / f"report-{counter['n']}.json"
        path.write_text(json.dumps(body), encoding="utf-8")
        return path

    return _make


@pytest.fixture
def write_baseline(tmp_path: Path) -> WriteBaseline:
    """Write a baseline JSON under ``tmp_path`` and return its path."""

    counter = {"n": 0}

    def _make(payload: dict[str, Any]) -> Path:
        counter["n"] += 1
        path = tmp_path / f"baseline-{counter['n']}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    return _make


def _summary(
    percent: float, *, covered: int = 0, statements: int = 100, missing: int = 0
) -> dict[str, Any]:
    return {
        "summary": {
            "covered_lines": covered if covered else int(percent),
            "num_statements": statements,
            "percent_covered": percent,
            "missing_lines": missing if missing else (statements - int(percent)),
        }
    }


# ----------------------------------------------------------- module-level


def test_module_repo_root_resolves_three_parents_up() -> None:
    """REPO_ROOT must walk three parents up per ADR-0009.

    coverage_budget.py -> audits/ -> splunk_uc/ -> src/ -> repo
    """
    expected = Path(cb.__file__).resolve().parents[3]
    assert cb.REPO_ROOT == expected


def test_module_tier_1_includes_matches_tools_build() -> None:
    """Tier-1 must accept ``tools/build/foo.py`` paths."""
    assert any(p.match("tools/build/foo.py") for p in cb.TIER_1_INCLUDES)


def test_module_tier_1_excludes_filters_generators_and_migrations() -> None:
    """Generators and migrators inside tools/build are exempt."""
    assert any(p.match("tools/build/generate_x.py") for p in cb.TIER_1_EXCLUDES)
    assert any(p.match("tools/build/migrate_x.py") for p in cb.TIER_1_EXCLUDES)


def test_module_tier_2_includes_six_patterns() -> None:
    """Tier-2 must accept the six documented include patterns."""
    assert len(cb.TIER_2_INCLUDES) == 6


def test_module_tier_3_documented_exempt_lists_known_shapes() -> None:
    """Tier-3 documented exempt set covers the six known prefixes."""
    samples = [
        "scripts/uplift_x.py",
        "scripts/migrate_x.py",
        "scripts/_helper.py",
        "scripts/backfill_x.py",
        "scripts/enrich_x.py",
        "scripts/generate_x.py",
        "scripts/ingest/x.py",
        "scripts/ingest_x.py",
    ]
    for s in samples:
        assert any(p.match(s) for p in cb.TIER_3_DOCUMENTED_EXEMPT), s


# ------------------------------------------------------------- _classify


def test_classify_tier1_tools_build_python_file() -> None:
    assert cb._classify("tools/build/build.py") == "tier1"


def test_classify_tier1_excluded_when_generator_under_tools_build() -> None:
    assert cb._classify("tools/build/generate_catalog.py") == "tier3"


def test_classify_tier1_excluded_when_migrator_under_tools_build() -> None:
    assert cb._classify("tools/build/migrate_legacy.py") == "tier3"


def test_classify_tier2_audit_under_scripts() -> None:
    assert cb._classify("scripts/audit_foo.py") == "tier2"


def test_classify_tier2_equipment_lib_under_scripts() -> None:
    assert cb._classify("scripts/equipment_lib.py") == "tier2"


def test_classify_tier2_build_es_and_build_ta() -> None:
    assert cb._classify("scripts/build_es.py") == "tier2"
    assert cb._classify("scripts/build_ta.py") == "tier2"


def test_classify_tier2_under_splunk_uc_audits() -> None:
    assert cb._classify("src/splunk_uc/audits/anything.py") == "tier2"


def test_classify_tier2_under_splunk_uc_generators() -> None:
    assert cb._classify("src/splunk_uc/generators/anything.py") == "tier2"


def test_classify_tier3_fallthrough_for_arbitrary_paths() -> None:
    assert cb._classify("docs/whatever.md") == "tier3"
    assert cb._classify("scripts/random_helper.py") == "tier3"


def test_classify_tier1_wins_over_tier2_priority() -> None:
    """Tier-1 includes are checked first.

    A path matching tier-1 should never fall through to tier-2 even
    if some other pattern would (none currently do).
    """
    assert cb._classify("tools/build/x.py") == "tier1"


# -------------------------------------------------------- _short_record


def test_short_record_reshapes_summary_to_four_keys() -> None:
    info = {
        "summary": {
            "covered_lines": 10,
            "num_statements": 50,
            "percent_covered": 20.123456,
            "missing_lines": 40,
            "extra_ignored_field": "noise",
        }
    }
    rec = cb._short_record(info)
    assert rec == {
        "covered_lines": 10,
        "num_statements": 50,
        "percent_covered": 20.12,  # rounded to 2dp
        "missing_lines": 40,
    }


def test_short_record_rounds_half_up_at_two_dp() -> None:
    """``round`` is banker's rounding in Python; the contract is "2dp"."""
    info = {
        "summary": {
            "covered_lines": 0,
            "num_statements": 0,
            "percent_covered": 99.999,
            "missing_lines": 0,
        }
    }
    rec = cb._short_record(info)
    assert rec["percent_covered"] == 100.0


# ---------------------------------------------------- _load_coverage_report


def test_load_coverage_report_missing_file_exits_2_and_emits_stderr(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "absent.json"
    with pytest.raises(SystemExit) as exc:
        cb._load_coverage_report(missing)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "coverage report not found" in err
    assert str(missing) in err
    assert "::error::" in err


def test_load_coverage_report_normalises_absolute_paths_to_repo_relative(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Absolute paths inside REPO_ROOT are normalised to relative posix."""
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    # The fake-root must actually contain the file so resolve+relative_to works.
    src = fake_root / "src"
    src.mkdir()
    target = src / "foo.py"
    target.write_text("x", encoding="utf-8")

    report = write_report({str(target): _summary(75.0)})
    out = cb._load_coverage_report(report)
    assert "src/foo.py" in out["files"]
    assert "totals" in out


def test_load_coverage_report_keeps_paths_outside_repo_root_as_is(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ValueError on ``relative_to`` falls back to ``Path.as_posix``."""
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    # Path outside fake_root → relative_to() raises ValueError.
    outside = tmp_path / "elsewhere" / "bar.py"

    report = write_report({str(outside): _summary(33.0)})
    out = cb._load_coverage_report(report)
    # The fallback uses Path.as_posix() on the raw path.
    assert str(outside.as_posix()) in out["files"]


def test_load_coverage_report_returns_empty_files_when_absent_key(
    tmp_path: Path,
) -> None:
    """Missing ``files`` key in the report defaults to {}."""
    p = tmp_path / "empty.json"
    p.write_text("{}", encoding="utf-8")
    out = cb._load_coverage_report(p)
    assert out == {"files": {}, "totals": {}}


# ---------------------------------------------------------------- _git_head


def test_git_head_returns_subprocess_output_stripped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_check_output(*args: Any, **kwargs: Any) -> str:
        return "abc123\n"

    monkeypatch.setattr(cb.subprocess, "check_output", fake_check_output)
    assert cb._git_head() == "abc123"


def test_git_head_returns_unknown_on_subprocess_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_check_output(*args: Any, **kwargs: Any) -> str:
        raise subprocess.CalledProcessError(returncode=128, cmd=["git"])

    monkeypatch.setattr(cb.subprocess, "check_output", fake_check_output)
    assert cb._git_head() == "unknown"


def test_git_head_returns_unknown_on_filenotfound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``git`` binary missing also triggers the unknown fallback."""

    def fake_check_output(*args: Any, **kwargs: Any) -> str:
        raise FileNotFoundError

    monkeypatch.setattr(cb.subprocess, "check_output", fake_check_output)
    assert cb._git_head() == "unknown"


# -------------------------------------------------------------- _read_version


def test_read_version_returns_version_file_contents_stripped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    (fake_root / "VERSION").write_text("9.99.99\n", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    assert cb._read_version() == "9.99.99"


def test_read_version_returns_unknown_when_file_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    assert cb._read_version() == "unknown"


# --------------------------------------------------------------- build_baseline


def test_build_baseline_partitions_files_by_tier(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    # Put files inside fake_root so the normaliser picks them up.
    (fake_root / "tools" / "build").mkdir(parents=True)
    t1 = fake_root / "tools" / "build" / "core.py"
    t1.write_text("x", encoding="utf-8")
    (fake_root / "scripts").mkdir(parents=True)
    t2 = fake_root / "scripts" / "audit_foo.py"
    t2.write_text("x", encoding="utf-8")
    t3 = fake_root / "scripts" / "uplift_legacy.py"
    t3.write_text("x", encoding="utf-8")

    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "deadbeef")
    (fake_root / "VERSION").write_text("9.1.0\n", encoding="utf-8")

    report = write_report(
        {
            str(t1): _summary(85.0),
            str(t2): _summary(50.0),
            str(t3): _summary(0.0),
        },
        totals={
            "covered_lines": 10,
            "num_statements": 20,
            "percent_covered": 50.0,
            "missing_lines": 10,
        },
    )
    baseline = cb.build_baseline(report)
    assert baseline["$schema"] == "../../schemas/coverage-baseline.schema.json"
    assert baseline["version"] == "9.1.0"
    assert baseline["git_head"] == "deadbeef"
    assert baseline["totals"]["percent_covered"] == 50.0
    assert "tools/build/core.py" in baseline["tier_1_modules"]
    assert "scripts/audit_foo.py" in baseline["tier_2_modules"]
    assert "scripts/uplift_legacy.py" in baseline["tier_3_exempt"]


def test_build_baseline_emits_iso_8601_utc_captured_at(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "head")
    report = write_report({})
    baseline = cb.build_baseline(report)
    captured = baseline["captured_at"]
    # YYYY-MM-DDTHH:MM:SSZ
    assert len(captured) == 20
    assert captured.endswith("Z")
    assert "T" in captured


def test_build_baseline_sorts_per_tier_module_dicts(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    (fake_root / "tools" / "build").mkdir(parents=True)
    (fake_root / "tools" / "build" / "z.py").write_text("x", encoding="utf-8")
    (fake_root / "tools" / "build" / "a.py").write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "head")
    report = write_report(
        {
            str(fake_root / "tools" / "build" / "z.py"): _summary(50.0),
            str(fake_root / "tools" / "build" / "a.py"): _summary(60.0),
        }
    )
    baseline = cb.build_baseline(report)
    keys = list(baseline["tier_1_modules"].keys())
    assert keys == ["tools/build/a.py", "tools/build/z.py"]


def test_build_baseline_iterates_past_unrecognised_classify_value(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Pin the 'no case matched' loop-continue branch in ``build_baseline``.

    The ``match _classify(fn): ...`` statement's three explicit cases
    are exhaustive against the real ``_classify`` return values
    (``tier1`` / ``tier2`` / ``tier3``). The branch
    ``case "tier3" → continue loop`` is therefore unreachable in
    practice. We monkey-patch ``_classify`` to return an
    unrecognised value so coverage.py picks up the fall-through
    arc, then iterate to the next file.
    """
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "head")
    monkeypatch.setattr(cb, "_classify", lambda path: "unknown_tier")

    report = write_report(
        {
            "scripts/anything_a.py": _summary(0.0),
            "scripts/anything_b.py": _summary(0.0),
        }
    )
    baseline = cb.build_baseline(report)
    # Neither file is in any tier bucket because _classify returned junk.
    assert baseline["tier_1_modules"] == {}
    assert baseline["tier_2_modules"] == {}
    assert baseline["tier_3_exempt"] == []


def test_build_baseline_iterates_past_tier3_to_subsequent_files(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Pin the loop-back branch when a tier-3 file is followed by more files.

    Coverage.py marks the ``case "tier3": tier3_seen.add(fn)`` branch
    as partially covered unless the for-loop continues past it — i.e.
    a tier-3 file must appear *before* the last file in the iteration.
    """
    fake_root = tmp_path / "fakerepo"
    (fake_root / "scripts").mkdir(parents=True)
    (fake_root / "tools" / "build").mkdir(parents=True)
    tier3 = fake_root / "scripts" / "uplift_legacy.py"
    tier3.write_text("x", encoding="utf-8")
    tier1 = fake_root / "tools" / "build" / "core.py"
    tier1.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "head")

    # Tier-3 file FIRST, then tier-1; the iteration must continue.
    report = write_report(
        {
            str(tier3): _summary(0.0),
            str(tier1): _summary(50.0),
        }
    )
    baseline = cb.build_baseline(report)
    assert "scripts/uplift_legacy.py" in baseline["tier_3_exempt"]
    assert "tools/build/core.py" in baseline["tier_1_modules"]


def test_build_baseline_with_no_totals_defaults_to_zeroes(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "head")
    # Pass totals={} so the .get(..., 0) fallbacks fire on every key.
    report = write_report({}, totals={})
    baseline = cb.build_baseline(report)
    assert baseline["totals"] == {
        "covered_lines": 0,
        "num_statements": 0,
        "percent_covered": 0.0,
        "missing_lines": 0,
    }


# ----------------------------------------------------------------- check()


def test_check_missing_baseline_returns_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = cb.check(
        baseline_path=tmp_path / "absent.json",
        report_path=tmp_path / "rpt.json",
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "baseline not found" in err
    assert "::error::" in err


def test_check_clean_when_all_files_match_baseline(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {"scripts/audit_x.py": {"percent_covered": 50.0}},
        }
    )
    report = write_report(
        {
            "tools/build/x.py": _summary(80.0),
            "scripts/audit_x.py": _summary(50.0),
        }
    )
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK: every tier-1 / tier-2 file is within 1.00pp" in out


def test_check_clean_when_delta_within_tolerance_boundary(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
) -> None:
    """delta exactly equal to -tolerance is NOT a failure."""
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {},
        }
    )
    report = write_report({"tools/build/x.py": _summary(79.0)})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 0


def test_check_fails_when_regression_beyond_tolerance(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {},
        }
    )
    report = write_report({"tools/build/x.py": _summary(70.0)})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "Coverage budget regressions:" in out
    assert "tools/build/x.py" in out
    assert "tier-1" in out
    assert "::error::" in out


def test_check_warns_but_does_not_fail_when_file_disappears(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {"scripts/audit_x.py": {"percent_covered": 50.0}},
        }
    )
    # Neither file present in the fresh report.
    report = write_report({})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Coverage budget warnings:" in out
    assert "disappeared" in out
    assert "tools/build/x.py" in out
    assert "scripts/audit_x.py" in out


def test_check_fails_when_new_tier1_file_below_floor(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Normalise paths via REPO_ROOT-rewired environment.
    fake_root = tmp_path / "fakerepo"
    (fake_root / "tools" / "build").mkdir(parents=True)
    new_file = fake_root / "tools" / "build" / "newfile.py"
    new_file.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)

    baseline = write_baseline({"tier_1_modules": {}, "tier_2_modules": {}})
    report = write_report({str(new_file): _summary(10.0)})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 1


def test_check_fails_when_new_tier2_file_below_floor(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    (fake_root / "scripts").mkdir(parents=True)
    new_file = fake_root / "scripts" / "audit_newone.py"
    new_file.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)

    baseline = write_baseline({"tier_1_modules": {}, "tier_2_modules": {}})
    report = write_report({str(new_file): _summary(5.0)})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 1


def test_check_passes_when_new_tier1_file_at_floor(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A new file exactly at the floor is acceptable (not below)."""
    fake_root = tmp_path / "fakerepo"
    (fake_root / "tools" / "build").mkdir(parents=True)
    new_file = fake_root / "tools" / "build" / "at_floor.py"
    new_file.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)

    baseline = write_baseline({"tier_1_modules": {}, "tier_2_modules": {}})
    report = write_report({str(new_file): _summary(60.0)})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 0


def test_check_does_not_double_count_files_in_baseline_as_new(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Files already in the baseline must not trigger the new-file floor."""
    fake_root = tmp_path / "fakerepo"
    (fake_root / "tools" / "build").mkdir(parents=True)
    in_baseline = fake_root / "tools" / "build" / "kept.py"
    in_baseline.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)

    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/kept.py": {"percent_covered": 5.0}},
            "tier_2_modules": {},
        }
    )
    report = write_report({str(in_baseline): _summary(5.0)})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    # No regression, no new-file floor breach → clean.
    assert rc == 0


def test_check_distinguishes_tier1_and_tier2_in_failure_label(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Failure messages must carry the correct tier label."""
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {"scripts/audit_x.py": {"percent_covered": 50.0}},
        }
    )
    report = write_report(
        {
            "tools/build/x.py": _summary(70.0),
            "scripts/audit_x.py": _summary(40.0),
        }
    )
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "tier-1" in out
    assert "tier-2" in out


def test_check_warnings_printed_even_when_no_failures(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The warnings block prints unconditionally; failures block only on rc=1."""
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {},
        }
    )
    report = write_report({})  # disappeared
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Coverage budget warnings:" in out
    assert "OK:" in out


def test_check_handles_missing_tier_modules_key_in_baseline(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
) -> None:
    """A baseline without ``tier_X_modules`` keys must default to {}."""
    baseline = write_baseline({})
    report = write_report({})
    rc = cb.check(
        baseline_path=baseline,
        report_path=report,
        tolerance=1.0,
        tier1_floor=60.0,
        tier2_floor=40.0,
    )
    assert rc == 0


# ------------------------------------------------------------------- main()


def test_main_print_baseline_writes_json_to_stdout(
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cb, "_git_head", lambda: "abc")
    report = write_report({}, totals={"percent_covered": 42.0})
    rc = cb.main(["--print-baseline", "--report", str(report)])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["git_head"] == "abc"
    assert data["totals"]["percent_covered"] == 42.0


def test_main_default_flow_dispatches_to_check(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
) -> None:
    baseline = write_baseline({"tier_1_modules": {}, "tier_2_modules": {}})
    report = write_report({})
    rc = cb.main(
        [
            "--baseline",
            str(baseline),
            "--report",
            str(report),
        ]
    )
    assert rc == 0


def test_main_default_flow_returns_nonzero_on_failure(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
) -> None:
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {},
        }
    )
    report = write_report({"tools/build/x.py": _summary(50.0)})
    rc = cb.main(["--baseline", str(baseline), "--report", str(report)])
    assert rc == 1


def test_main_argv_none_falls_through_to_sys_argv(
    monkeypatch: pytest.MonkeyPatch,
    write_baseline: WriteBaseline,
    write_report: WriteReport,
) -> None:
    baseline = write_baseline({"tier_1_modules": {}, "tier_2_modules": {}})
    report = write_report({})
    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--baseline", str(baseline), "--report", str(report)],
    )
    rc = cb.main(None)
    assert rc == 0


def test_main_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as exc:
        cb.main(["--help"])
    assert exc.value.code == 0


def test_main_with_custom_tolerance(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
) -> None:
    """A wider tolerance must absorb a previously-failing regression."""
    baseline = write_baseline(
        {
            "tier_1_modules": {"tools/build/x.py": {"percent_covered": 80.0}},
            "tier_2_modules": {},
        }
    )
    report = write_report({"tools/build/x.py": _summary(70.0)})
    rc = cb.main(
        [
            "--baseline",
            str(baseline),
            "--report",
            str(report),
            "--tolerance",
            "15.0",
        ]
    )
    assert rc == 0


def test_main_with_custom_tier1_floor(
    write_baseline: WriteBaseline,
    write_report: WriteReport,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Lowering the tier-1 floor must let a new low-coverage file pass."""
    fake_root = tmp_path / "fakerepo"
    (fake_root / "tools" / "build").mkdir(parents=True)
    new_file = fake_root / "tools" / "build" / "new.py"
    new_file.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cb, "REPO_ROOT", fake_root)

    baseline = write_baseline({"tier_1_modules": {}, "tier_2_modules": {}})
    report = write_report({str(new_file): _summary(15.0)})
    rc = cb.main(
        [
            "--baseline",
            str(baseline),
            "--report",
            str(report),
            "--tier1-floor",
            "10.0",
        ]
    )
    assert rc == 0


# -------------------------------------------------------- _build_arg_parser


def test_build_arg_parser_defaults() -> None:
    parser = cb._build_arg_parser()
    args = parser.parse_args([])
    assert args.tolerance == pytest.approx(1.0)
    assert args.tier1_floor == pytest.approx(60.0)
    assert args.tier2_floor == pytest.approx(40.0)
    assert args.print_baseline is False
    # default baseline path lives under data/baselines/ in the repo.
    assert "coverage-v9.1.0.json" in str(args.baseline)
    assert "/tmp/coverage.json" in str(args.report)


def test_build_arg_parser_doc_extraction_when_doc_present() -> None:
    parser = cb._build_arg_parser()
    # description should pull the first paragraph of the module docstring.
    assert parser.description is not None
    assert "Coverage budget auditor" in parser.description


# ----------------------------------------------------------- __main__ block


def test_dunder_main_block_exists() -> None:
    """The module's ``if __name__ == "__main__"`` entry point exists.

    We don't execute via ``runpy`` (the module is already imported,
    which produces a RuntimeWarning) — instead we assert the source
    contains the expected entry-point shape.
    """
    src = pathlib.Path(cb.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "raise SystemExit(main())" in src
