"""Tests for ``splunk_uc.generators.sarif_emit``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.generators import sarif_emit as se

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "sarif"


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    return tmp_path / "sarif"


def test_load_audit_report_findings_shape() -> None:
    report = se.load_audit_report(FIXTURES / "spl-references.json", audit_name="spl-references")
    assert report.name == "spl-references"
    assert len(report.findings) == 2
    assert report.findings[0].kind == "unknown-command"
    assert report.findings[0].severity.upper() == "HIGH"


def test_load_audit_report_prerequisites_shape() -> None:
    report = se.load_audit_report(FIXTURES / "prerequisites.json", audit_name="prerequisites")
    assert len(report.findings) == 3  # 1 error + 1 warning + cycle
    kinds = {f.kind for f in report.findings}
    assert "unknown-prereq" in kinds
    assert "wave-monotonicity" in kinds
    assert "cycle" in kinds


def test_load_audit_report_violations_shape() -> None:
    report = se.load_audit_report(FIXTURES / "content-quality.json", audit_name="content-quality")
    assert len(report.findings) == 2
    assert all(f.file.startswith("content/") for f in report.findings)


def test_load_audit_report_missing_file_returns_empty() -> None:
    report = se.load_audit_report(FIXTURES / "does-not-exist.json", audit_name="empty")
    assert report.findings == []


def test_level_mapping_info_warn_error() -> None:
    assert se._sarif_level("info", include_info=False) is None
    assert se._sarif_level("info", include_info=True) == "note"
    assert se._sarif_level("warn", include_info=False) == "warning"
    assert se._sarif_level("HIGH", include_info=False) == "error"
    assert se._sarif_level("fail", include_info=False) == "error"


def test_audit_to_sarif_results_rule_registration() -> None:
    report = se.load_audit_report(FIXTURES / "spl-references.json", audit_name="spl-references")
    results, rules = se.audit_to_sarif_results(report)
    rule_ids = {r.rule_id for r in rules}
    assert all(r.rule_id in rule_ids for r in results)
    assert "splunk-uc:spl-references:unknown-command" in rule_ids


def test_audit_to_sarif_results_excludes_info_by_default() -> None:
    report = se.AuditReport(
        name="t",
        version="1.0.0",
        findings=[
            se.AuditFinding(kind="a", message="info msg", severity="info"),
            se.AuditFinding(kind="b", message="warn msg", severity="warn"),
        ],
    )
    results, _ = se.audit_to_sarif_results(report)
    assert len(results) == 1
    assert results[0].level == "warning"


def test_audit_to_sarif_results_location_uri_formation() -> None:
    report = se.load_audit_report(FIXTURES / "spl-references.json", audit_name="spl-references")
    results, _ = se.audit_to_sarif_results(report)
    assert results[0].artifact_uri == "content/cat-05-network/UC-5.2.35.json"
    assert results[0].start_line >= 1


def test_build_sarif_log_schema_version_pinning() -> None:
    report = se.load_audit_report(FIXTURES / "content-quality.json", audit_name="content-quality")
    results, rules = se.audit_to_sarif_results(report)
    run = se.build_sarif_run("content-quality", "8.6.4", results, rules)
    log = se.build_sarif_log([run])
    assert log["$schema"] == se.SARIF_SCHEMA
    assert log["version"] == "2.1.0"
    assert log["runs"][0]["tool"]["driver"]["name"] == se.TOOL_NAME


def test_emit_sarif_writes_combined_and_per_audit(tmp_out: Path) -> None:
    reports = {
        "spl-references": FIXTURES / "spl-references.json",
        "prerequisites": FIXTURES / "prerequisites.json",
    }
    se.emit_sarif(reports, tmp_out)
    assert (tmp_out / "catalogue.sarif").is_file()
    assert (tmp_out / "spl-references.sarif").is_file()
    assert (tmp_out / "prerequisites.sarif").is_file()
    combined = json.loads((tmp_out / "catalogue.sarif").read_text(encoding="utf-8"))
    assert len(combined["runs"]) == 2


def test_emit_sarif_deterministic_byte_identical(tmp_out: Path) -> None:
    reports = {"spl-references": FIXTURES / "spl-references.json"}
    se.emit_sarif(reports, tmp_out)
    first = (tmp_out / "catalogue.sarif").read_bytes()
    se.emit_sarif(reports, tmp_out)
    second = (tmp_out / "catalogue.sarif").read_bytes()
    assert first == second


def test_emit_sarif_empty_report_handling(tmp_out: Path) -> None:
    empty = tmp_out.parent / "empty.json"
    empty.write_text("{}", encoding="utf-8")
    se.emit_sarif({"empty": empty}, tmp_out)
    payload = json.loads((tmp_out / "catalogue.sarif").read_text(encoding="utf-8"))
    assert payload["runs"][0]["results"] == []


def test_main_audit_filter(tmp_out: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        se,
        "DEFAULT_AUDITS_DIR",
        FIXTURES,
    )
    rc = se.main(
        [
            "--out",
            str(tmp_out),
            "--audits-dir",
            str(FIXTURES),
            "--audit",
            "spl-references",
            "--report",
            f"spl-references={FIXTURES / 'spl-references.json'}",
        ]
    )
    assert rc == 0
    combined = json.loads((tmp_out / "catalogue.sarif").read_text(encoding="utf-8"))
    assert len(combined["runs"]) == 1
    assert combined["runs"][0]["results"]


def test_main_check_mode(tmp_out: Path) -> None:
    reports = {"spl-references": FIXTURES / "spl-references.json"}
    se.emit_sarif(reports, tmp_out)
    rc = se.main(["--check", "--out", str(tmp_out), "--report", f"spl-references={FIXTURES / 'spl-references.json'}"])
    assert rc == 0


def test_main_check_mode_detects_drift(tmp_out: Path) -> None:
    reports = {"spl-references": FIXTURES / "spl-references.json"}
    se.emit_sarif(reports, tmp_out)
    (tmp_out / "catalogue.sarif").write_text("{}\n", encoding="utf-8")
    rc = se.main(["--check", "--out", str(tmp_out), "--report", f"spl-references={FIXTURES / 'spl-references.json'}"])
    assert rc == 1


def test_main_limit_flag(tmp_out: Path) -> None:
    rc = se.main(
        [
            "--out",
            str(tmp_out),
            "--limit",
            "1",
            "--report",
            f"spl-references={FIXTURES / 'spl-references.json'}",
            "--report",
            f"prerequisites={FIXTURES / 'prerequisites.json'}",
        ]
    )
    assert rc == 0
    per = json.loads((tmp_out / "prerequisites.sarif").read_text(encoding="utf-8"))
    assert len(per["runs"][0]["results"]) == 1


def test_rule_id_convention() -> None:
    rid = se._rule_id("spl-grammar", "stats span", rule_prefix="splunk-uc")
    assert rid == "splunk-uc:spl-grammar:stats-span"
