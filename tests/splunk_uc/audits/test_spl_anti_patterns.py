"""Tests for ``splunk_uc.audits.spl_anti_patterns``."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from itertools import pairwise
from pathlib import Path

import pytest

from splunk_uc.audits import spl_anti_patterns as sap

REPO = Path(__file__).resolve().parents[3]
PATTERNS_PATH = REPO / "data" / "spl-anti-patterns.json"


@pytest.fixture
def patterns() -> list[sap.AntiPattern]:
    return sap.load_anti_patterns(PATTERNS_PATH)


@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    """Tiny content/ tree with one clean UC and one offender."""
    cat = tmp_path / "cat-99-fixture"
    cat.mkdir()
    clean = {
        "id": "99.1.1",
        "title": "Clean UC",
        "spl": 'index=os sourcetype=cpu host=*\n| stats avg(pctIdle) as avg_idle by host\n| where avg_idle < 10',
    }
    offender = {
        "id": "99.1.2",
        "title": "Offender UC",
        "spl": 'index=main sourcetype=foo | stats count by host | join host [search index=assets | stats count by host]',
        "detailedImplementation": (
            "Example block:\n\n```spl\n| makeresults count=1\n| eval x=random()\n```\n"
        ),
    }
    (cat / "UC-99.1.1.json").write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
    (cat / "UC-99.1.2.json").write_text(json.dumps(offender, indent=2) + "\n", encoding="utf-8")
    return tmp_path


def test_data_file_loads(patterns: list[sap.AntiPattern]) -> None:
    assert len(patterns) >= 12
    assert patterns[0].id.startswith("ANTIPAT-")


def test_every_regex_pattern_compiles(patterns: list[sap.AntiPattern]) -> None:
    for p in patterns:
        if p.pattern_kind == "regex" and p.pattern:
            assert p._compiled is not None


def test_scan_spl_finds_known_offenders(patterns: list[sap.AntiPattern]) -> None:
    spl = 'index=x sourcetype=y | join host [search index=z | stats count] | makeresults count=1'
    matches = sap.scan_spl(spl, patterns)
    ids = {m.entry_id for m in matches}
    assert "ANTIPAT-001" in ids
    assert "ANTIPAT-002" in ids
    assert "ANTIPAT-010" in ids


def test_scan_uc_ignores_non_spl_fields(mini_corpus: Path, patterns: list[sap.AntiPattern]) -> None:
    path = mini_corpus / "cat-99-fixture" / "UC-99.1.1.json"
    matches = sap.scan_uc(path, patterns)
    assert all(m.entry_id != "ANTIPAT-002" for m in matches)


def test_evaluate_corpus_reads_only_sidecars(mini_corpus: Path, patterns_path: Path = PATTERNS_PATH) -> None:
    noise = mini_corpus / "cat-99-fixture" / "README.md"
    noise.write_text("| join host\n", encoding="utf-8")
    report = sap.evaluate_corpus(mini_corpus, patterns_path)
    assert report["summary"]["total_ucs_scanned"] == 2
    assert report["summary"]["total_matches"] >= 1


def test_severity_filter_in_main(mini_corpus: Path) -> None:
    rc = sap.main(
        [
            "--content",
            str(mini_corpus),
            "--check",
            "--severity",
            "high",
            "--include-pattern",
            "ANTIPAT-001",
        ]
    )
    assert rc == 1


def test_check_exit_zero_when_under_limit(mini_corpus: Path) -> None:
    rc = sap.main(
        [
            "--content",
            str(mini_corpus),
            "--check",
            "--severity",
            "high",
            "--limit",
            "999",
        ]
    )
    assert rc == 0


def test_include_pattern_filter(mini_corpus: Path) -> None:
    report = sap.evaluate_corpus(mini_corpus, PATTERNS_PATH)
    all_ids = {m["entry_id"] for m in report["matches"]}
    assert "ANTIPAT-001" in all_ids
    rc = sap.main(
        [
            "--content",
            str(mini_corpus),
            "--check",
            "--severity",
            "low",
            "--include-pattern",
            "ANTIPAT-002",
            "--limit",
            "0",
        ]
    )
    assert rc == 1


def test_exclude_pattern_suppresses_matches(mini_corpus: Path) -> None:
    rc = sap.main(
        [
            "--content",
            str(mini_corpus),
            "--check",
            "--severity",
            "high",
            "--exclude-pattern",
            "ANTIPAT-001",
            "--exclude-pattern",
            "ANTIPAT-002",
            "--exclude-pattern",
            "ANTIPAT-003",
            "--exclude-pattern",
            "ANTIPAT-005",
            "--exclude-pattern",
            "ANTIPAT-010",
            "--limit",
            "0",
        ]
    )
    assert rc == 0


def test_sorted_output_is_deterministic(mini_corpus: Path) -> None:
    first = sap.evaluate_corpus(mini_corpus, PATTERNS_PATH)
    second = sap.evaluate_corpus(mini_corpus, PATTERNS_PATH)
    assert first["matches"] == second["matches"]
    matches = first["matches"]
    if len(matches) >= 2:
        sev_rank = sap._SEV_RANK
        for a, b in pairwise(matches):
            assert sev_rank.get(a["severity"], 0) >= sev_rank.get(b["severity"], 0) or (
                a["uc_id"] <= b["uc_id"]
            )


def test_out_writes_json_and_markdown(mini_corpus: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "audits"
    rc = sap.main(["--content", str(mini_corpus), "--out", str(out_dir)])
    assert rc == 0
    json_path = out_dir / "spl-anti-patterns.json"
    md_path = out_dir / "spl-anti-patterns.md"
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    sap._validate_schema(payload, sap._OUTPUT_SCHEMA, "test-output")
    assert "Top offenders" in md_path.read_text(encoding="utf-8")


def test_cli_synthetic_offender_fails_check(mini_corpus: Path) -> None:
    """CI gate contract: a known high-severity offender fails --check at limit=0."""
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "splunk_uc",
            "audit-spl-anti-patterns",
            "--content",
            str(mini_corpus),
            "--check",
            "--severity",
            "high",
            "--limit",
            "0",
        ],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "ANTIPAT-001" in proc.stderr or "join" in proc.stderr.lower()


def test_output_json_has_summary_fields(mini_corpus: Path) -> None:
    report = sap.evaluate_corpus(mini_corpus, PATTERNS_PATH)
    summary = report["summary"]
    for key in ("total_ucs_scanned", "total_matches", "by_severity", "by_pattern", "top_offenders"):
        assert key in summary


def _waiver_file(tmp_path: Path, corpus: Path, uc_id: str, rules: list[dict], spl: str | None = None) -> Path:
    if spl is None:
        spl = json.loads((corpus / "cat-99-fixture" / f"UC-{uc_id}.json").read_text(encoding="utf-8"))["spl"]
    entry = {"uc_id": uc_id, "spl_sha256": hashlib.sha256(spl.encode("utf-8")).hexdigest(), "rules": rules}
    path = tmp_path / "waivers.json"
    path.write_text(json.dumps({"waivers": [entry]}) + "\n", encoding="utf-8")
    return path


def test_waiver_removes_match_from_check(mini_corpus: Path, tmp_path: Path) -> None:
    args = ["--content", str(mini_corpus), "--check", "--include-pattern", "ANTIPAT-001"]
    assert sap.main(args) == 1
    waivers = _waiver_file(tmp_path, mini_corpus, "99.1.2", [{"entry_id": "ANTIPAT-001", "count": 1}])
    assert sap.main([*args, "--waivers", str(waivers)]) == 0


def test_waiver_is_stale_once_spl_changes(mini_corpus: Path, tmp_path: Path) -> None:
    waivers = _waiver_file(
        tmp_path, mini_corpus, "99.1.2", [{"entry_id": "ANTIPAT-001", "count": 1}], spl="index=other | join x [search y]"
    )
    rc = sap.main(["--content", str(mini_corpus), "--check", "--limit", "999", "--waivers", str(waivers)])
    assert rc == 1


def test_waiver_is_stale_when_rule_stops_matching(mini_corpus: Path, tmp_path: Path) -> None:
    waivers = _waiver_file(tmp_path, mini_corpus, "99.1.1", [{"entry_id": "ANTIPAT-001", "count": 1}])
    rc = sap.main(["--content", str(mini_corpus), "--check", "--limit", "999", "--waivers", str(waivers)])
    assert rc == 1


def test_escu_waiver_file_only_shrinks() -> None:
    """59 UCs / 65 matches from verbatim ESCU searches (#161). The numbers may go down, never up."""
    payload = json.loads(sap.DEFAULT_WAIVERS_PATH.read_text(encoding="utf-8"))
    assert len(payload["waivers"]) <= 59
    assert sum(int(r.get("count", 1)) for w in payload["waivers"] for r in w["rules"]) <= 65
