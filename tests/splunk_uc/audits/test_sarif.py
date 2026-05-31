"""Tests for ``splunk_uc.audits.sarif``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import sarif as sarif_audit

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "sarif"


def test_validate_known_good_sarif() -> None:
    path = FIXTURES / "valid-catalogue.sarif"
    errors = sarif_audit.validate_sarif_file(path)
    assert errors == []


def test_detect_orphan_rule_id() -> None:
    path = FIXTURES / "broken-orphan-rule.sarif"
    errors = sarif_audit.validate_sarif_file(path)
    assert any("orphan ruleId" in err for err in errors)


def test_detect_bad_level() -> None:
    payload = json.loads((FIXTURES / "valid-catalogue.sarif").read_text(encoding="utf-8"))
    payload["runs"][0]["results"][0]["level"] = "critical"
    errors = sarif_audit.validate_sarif_payload(payload)
    assert any("invalid level" in err for err in errors)


def test_detect_bad_schema() -> None:
    payload = json.loads((FIXTURES / "valid-catalogue.sarif").read_text(encoding="utf-8"))
    payload["$schema"] = "https://example.com/not-sarif.json"
    errors = sarif_audit.validate_sarif_payload(payload)
    assert any("$schema must be" in err for err in errors)


def test_detect_bad_version() -> None:
    payload = json.loads((FIXTURES / "valid-catalogue.sarif").read_text(encoding="utf-8"))
    payload["version"] = "2.0.0"
    errors = sarif_audit.validate_sarif_payload(payload)
    assert any("version must be" in err for err in errors)


def test_detect_unparseable_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.sarif"
    bad.write_text("{ not json", encoding="utf-8")
    errors = sarif_audit.validate_sarif_file(bad)
    assert any("invalid JSON" in err for err in errors)


def test_main_check_exit_codes(tmp_path: Path) -> None:
    good = FIXTURES / "valid-catalogue.sarif"
    assert sarif_audit.main(["--check", "--sarif", str(good)]) == 0

    missing = tmp_path / "missing.sarif"
    assert sarif_audit.main(["--check", "--sarif", str(missing)]) == 1

    broken = FIXTURES / "broken-orphan-rule.sarif"
    assert sarif_audit.main(["--check", "--sarif", str(broken)]) == 1
