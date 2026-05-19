"""Tests for generate-observability-metrics."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

import splunk_uc.audits.observability_drift as od
import splunk_uc.generators.observability_metrics as om

PROM_LINE_RE = od.PROM_LINE_RE


@pytest.fixture()
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    content = tmp_path / "content" / "cat-01-test"
    content.mkdir(parents=True)
    (tmp_path / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    monkeypatch.setattr(om, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(om, "CONTENT_DIR", tmp_path / "content")
    monkeypatch.setattr(om, "VERSION_PATH", tmp_path / "VERSION")
    monkeypatch.setattr(om, "DEFAULT_OUT", tmp_path / "dist" / "observability")
    return tmp_path


def _write_uc(
    repo: Path,
    *,
    cat: str = "01",
    uc_id: str = "1.1.1",
    payload: dict | None = None,
) -> Path:
    cat_dir = repo / "content" / f"cat-{cat}-slug"
    cat_dir.mkdir(parents=True, exist_ok=True)
    stem = f"UC-{uc_id}"
    base = {
        "id": uc_id,
        "title": "Test UC",
        "criticality": "high",
        "difficulty": "beginner",
        "spl": "index=main | stats count",
        "description": "A" * 50,
        "value": "B" * 50,
        "dataSources": "index=main sourcetype=foo",
        "app": "Splunk Core",
        "implementation": "Do the thing carefully.",
    }
    if payload:
        base.update(payload)
    path = cat_dir / f"{stem}.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    return path


class TestFreshness:
    def test_quantiles_and_buckets(self, tmp_repo: Path) -> None:
        p1 = _write_uc(tmp_repo, uc_id="1.1.1")
        p2 = _write_uc(tmp_repo, uc_id="1.1.2")
        ref = date(2026, 6, 1)

        def fake_git(path: Path) -> tuple[str | None, str]:
            if path == p1:
                return "2026-01-01T00:00:00Z", "git"
            if path == p2:
                return "2026-05-01T00:00:00Z", "git"
            return None, "unavailable"

        with patch.object(om, "_git_last_modified", side_effect=fake_git):
            payload = om.build_freshness([p1, p2], reference=ref)

        assert payload["totalUseCases"] == 2
        assert payload["quantiles"]["p50"] == pytest.approx(91.0)
        assert sum(payload["ageBuckets"].values()) == 2
        assert payload["cumulativeOlderThan"]["olderThan90Days"] == 1

    def test_oldest_newest_tie_break_by_uc_id(self, tmp_repo: Path) -> None:
        p1 = _write_uc(tmp_repo, uc_id="1.1.2")
        p2 = _write_uc(tmp_repo, uc_id="1.1.1")
        ref = date(2026, 6, 1)

        def fake_git(_path: Path) -> tuple[str | None, str]:
            return "2026-01-01T00:00:00Z", "git"

        with patch.object(om, "_git_last_modified", side_effect=fake_git):
            payload = om.build_freshness([p1, p2], reference=ref)

        assert payload["oldest"][0]["ucId"] == "1.1.1"
        assert payload["newest"][0]["ucId"] == "1.1.1"

    def test_git_failure_falls_back_to_mtime(self, tmp_repo: Path) -> None:
        path = _write_uc(tmp_repo)
        with patch.object(om, "_git_last_modified", return_value=("2026-03-01T00:00:00Z", "mtime")):
            entry_ts, source = om._git_last_modified(path)
        assert source == "mtime"
        assert entry_ts is not None


class TestQuality:
    def test_tier_classification_bronze(self, tmp_repo: Path) -> None:
        path = _write_uc(tmp_repo, payload={"criticality": "critical"})
        payload = om.build_quality([path])
        block = payload["byCategoryCriticality"]["01"]["critical"]
        assert block["bronze"] == 1
        assert block["total"] == 1
        assert block["distribution"]["bronze"] == pytest.approx(100.0)

    def test_bronze_heavy_category_surfaced(self, tmp_repo: Path) -> None:
        paths = [_write_uc(tmp_repo, uc_id=f"1.1.{i}") for i in range(1, 6)]
        payload = om.build_quality(paths)
        assert "01" in payload["bronzeHeavyCategories"]

    def test_per_category_criticality_rollup(self, tmp_repo: Path) -> None:
        high = _write_uc(tmp_repo, uc_id="1.1.1", payload={"criticality": "high"})
        low = _write_uc(tmp_repo, uc_id="1.1.2", payload={"criticality": "low"})
        payload = om.build_quality([high, low])
        assert "high" in payload["byCategoryCriticality"]["01"]
        assert "low" in payload["byCategoryCriticality"]["01"]


class TestCoverage:
    def test_empty_compliance_not_populated(self, tmp_repo: Path) -> None:
        path = _write_uc(tmp_repo, payload={"compliance": []})
        payload = om.build_coverage([path])
        assert payload["perDimension"]["compliance"]["count"] == 0

    def test_nonempty_compliance_populated(self, tmp_repo: Path) -> None:
        path = _write_uc(
            tmp_repo,
            payload={"compliance": [{"regulation": "GDPR", "version": "2016", "clause": "32"}]},
        )
        payload = om.build_coverage([path])
        assert payload["perDimension"]["compliance"]["count"] == 1

    def test_matrix_shape(self, tmp_repo: Path) -> None:
        path = _write_uc(tmp_repo, payload={"references": [{"title": "Doc"}]})
        payload = om.build_coverage([path])
        assert set(payload["matrixCounts"]["01"]) == set(om.COVERAGE_DIMENSIONS)
        assert payload["matrixPercentages"]["01"]["references"] == pytest.approx(100.0)


class TestPrometheus:
    def test_prom_lines_match_regex(self, tmp_repo: Path) -> None:
        paths = [_write_uc(tmp_repo, uc_id="1.1.1")]
        ref = date(2026, 6, 1)
        with patch.object(om, "_git_last_modified", return_value=("2026-01-01T00:00:00Z", "git")):
            freshness = om.build_freshness(paths, reference=ref)
        quality = om.build_quality(paths)
        coverage = om.build_coverage(paths)
        text = om.render_prometheus(freshness, quality, coverage)
        families_help: set[str] = set()
        families_type: set[str] = set()
        for line in text.splitlines():
            if not line.strip():
                continue
            if line.startswith("# HELP "):
                families_help.add(line.split()[2])
            elif line.startswith("# TYPE "):
                families_type.add(line.split()[2])
            elif not line.startswith("#"):
                assert PROM_LINE_RE.match(line)
        for fam in families_type:
            assert fam in families_help


class TestDeterminism:
    def test_two_runs_byte_identical(self, tmp_repo: Path) -> None:
        path = _write_uc(
            tmp_repo,
            payload={"compliance": [{"regulation": "GDPR", "version": "2016", "clause": "32"}]},
        )
        ref = date(2026, 6, 1)
        with patch.object(om, "_git_last_modified", return_value=("2026-01-01T00:00:00Z", "git")):
            a = om.build_freshness([path], reference=ref)
            b = om.build_freshness([path], reference=ref)
        assert om._canonical_json(a) == om._canonical_json(b)


class TestCLI:
    def test_family_filter_quality_only(self, tmp_repo: Path) -> None:
        _write_uc(tmp_repo)
        out = tmp_repo / "dist" / "observability"
        rc = om.main(["--out", str(out), "--family", "quality", "--reference-date", "2026-06-01"])
        assert rc == 0
        assert (out / "quality.json").is_file()
        assert not (out / "freshness.json").exists()

    def test_check_exit_codes(self, tmp_repo: Path) -> None:
        _write_uc(tmp_repo)
        out = tmp_repo / "dist" / "observability"
        assert om.main(["--out", str(out), "--family", "quality"]) == 0
        assert om.main(["--check", "--out", str(out), "--family", "quality"]) == 0
        (out / "quality.json").write_text("{}\n", encoding="utf-8")
        assert om.main(["--check", "--out", str(out), "--family", "quality"]) == 1


class TestAuditDrift:
    def test_catches_bad_freshness_quantiles(self) -> None:
        issues = od.validate_freshness(
            {
                "totalUseCases": 2,
                "quantiles": {"p25": 10, "p50": 5, "p75": 20, "p95": 30},
                "ageBuckets": {
                    "under90Days": 1,
                    "days90to179": 1,
                    "days180to364": 0,
                    "days365to719": 0,
                    "days720Plus": 0,
                },
                "oldest": [{"ucId": "1.1.1"}],
                "newest": [{"ucId": "1.1.2"}],
            }
        )
        assert any(i.code == "freshness-monotone" for i in issues)

    def test_catches_bad_prometheus_line(self) -> None:
        issues = od.validate_prometheus("not_a_metric\n")
        assert any(i.code == "prom-line" for i in issues)

    def test_audit_directory_ok(self, tmp_repo: Path) -> None:
        _write_uc(tmp_repo)
        out = tmp_repo / "dist" / "observability"
        with patch.object(om, "_git_last_modified", return_value=("2026-01-01T00:00:00Z", "git")):
            om.main(["--out", str(out), "--reference-date", "2026-06-01"])
        assert od.audit_directory(out) == []

    def test_limit_caps_per_category(self, tmp_repo: Path) -> None:
        for i in range(1, 5):
            _write_uc(tmp_repo, uc_id=f"1.1.{i}")
        paths = om._iter_sidecar_paths(limit=2)
        assert len(paths) == 2
