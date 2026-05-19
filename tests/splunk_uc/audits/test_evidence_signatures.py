"""Unit tests for ``splunk_uc.audits.evidence_signatures``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import evidence_signatures as A
from splunk_uc.generators.sign_evidence import build_uc_manifest

_REPO = Path(__file__).resolve().parents[3]
_FIXTURES = _REPO / "tests" / "fixtures" / "evidence-signatures"


def test_recompute_uc_content_hash_matches_fixture() -> None:
    manifest = json.loads((_FIXTURES / "uc-22.2.32" / "manifest.json").read_text(encoding="utf-8"))
    assert A.recompute_uc_content_hash(manifest) == manifest["contentHash"]


def test_audit_fixtures_pass() -> None:
    assert A.audit_fixtures(_FIXTURES) == []


def test_audit_fixtures_detect_tampered() -> None:
    errors = A.audit_fixtures(_FIXTURES)
    assert not any("tampered" in e for e in errors)


def test_main_check_passes_hermetic(capsys: pytest.CaptureFixture[str]) -> None:
    rc = A.main(["--check", "--fixtures-dir", str(_FIXTURES)])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out


def test_audit_uc_manifest_detects_bad_hash(tmp_path: Path) -> None:
    manifest = json.loads((_FIXTURES / "uc-22.2.32" / "manifest.json").read_text(encoding="utf-8"))
    manifest["contentHash"] = "deadbeef"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    errors = A.audit_uc_manifest(path, {})
    assert any("contentHash mismatch" in e for e in errors)


def test_audit_tree_warns_when_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "no-evidence"
    errors, warnings = A.audit_tree(missing, verify_signature=False)
    assert errors == []
    assert any("absent" in w for w in warnings)


def test_verify_gpg_missing_sig() -> None:
    errors = A.verify_gpg_detached(_FIXTURES / "uc-22.2.32" / "manifest.json", _FIXTURES / "missing.sig")
    assert errors
    assert any("missing GPG" in e or "gpg not installed" in e for e in errors)
