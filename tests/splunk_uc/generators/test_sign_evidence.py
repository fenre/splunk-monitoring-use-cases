"""Unit tests for ``splunk_uc.generators.sign_evidence``."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from splunk_uc.generators import sign_evidence as M

_REPO = Path(__file__).resolve().parents[3]
_FIXTURES = _REPO / "tests" / "fixtures" / "evidence-signatures"


def test_compliance_fingerprint_is_order_independent() -> None:
    a = [{"regulation": "gdpr", "version": "2016/679", "clause": "Art. 32", "mode": "satisfies", "assurance": "full", "evidenceArtifact": "x"}]
    b = list(reversed(a))
    assert M.compliance_fingerprint(a) == M.compliance_fingerprint(b)


def test_build_uc_manifest_matches_fixture() -> None:
    fixture = json.loads((_FIXTURES / "uc-22.2.32" / "manifest.json").read_text(encoding="utf-8"))
    sidecar = json.loads(
        (_REPO / "content/cat-22-regulatory-compliance/UC-22.2.32.json").read_text(encoding="utf-8")
    )
    built = M.build_uc_manifest("22.2.32", sidecar)
    assert built["contentHash"] == fixture["contentHash"]
    assert built["complianceFingerprint"] == fixture["complianceFingerprint"]


def test_build_pack_descriptor_hash() -> None:
    pack = _FIXTURES / "evidence-packs" / "gdpr.json"
    desc = M.build_pack_descriptor("gdpr", pack)
    on_disk = json.loads((_FIXTURES / "evidence-packs" / "gdpr.descriptor.json").read_text(encoding="utf-8"))
    assert desc["contentHash"] == on_disk["contentHash"]


def test_check_drift_passes_without_dist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(M, "EVIDENCE_DIR", tmp_path / "evidence")
    monkeypatch.setattr(M, "PACKS_OUT_DIR", tmp_path / "packs")
    monkeypatch.setattr(M, "collect_pack_sources", list)
    assert M.check_drift() == 0


def test_check_drift_detects_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sidecar = json.loads(
        (_REPO / "content/cat-22-regulatory-compliance/UC-22.2.32.json").read_text(encoding="utf-8")
    )
    manifest = M.build_uc_manifest("22.2.32", sidecar)
    manifest["contentHash"] = "0" * 64
    out = tmp_path / "evidence" / "UC-22.2.32" / "manifest.json"
    out.parent.mkdir(parents=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(M, "EVIDENCE_DIR", tmp_path / "evidence")
    monkeypatch.setattr(M, "PACKS_OUT_DIR", tmp_path / "packs")
    monkeypatch.setattr(M, "collect_uc_manifests", lambda: {"22.2.32": M.build_uc_manifest("22.2.32", sidecar)})
    assert M.check_drift() == 1


def test_main_requires_all_or_check() -> None:
    with pytest.raises(SystemExit):
        M.main([])


def test_gpg_sign_and_verify_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if shutil.which("gpg") is None:
        pytest.skip("gpg not installed")

    gnupg_home = tmp_path / "gnupg"
    gnupg_home.mkdir()
    env = {"GNUPGHOME": str(gnupg_home)}
    monkeypatch.setenv("GNUPGHOME", str(gnupg_home))
    subprocess.run(
        [
            "gpg",
            "--batch",
            "--passphrase",
            "",
            "--quick-gen-key",
            "Evidence Test <test@example.com>",
            "default",
            "default",
        ],
        check=True,
        capture_output=True,
        env=env,
    )
    fingerprint = subprocess.run(
        ["gpg", "--list-secret-keys", "--with-colons"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout
    key_id = next(line.split(":")[4] for line in fingerprint.splitlines() if line.startswith("sec:"))

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"schemaVersion":"1.0.0"}\n', encoding="utf-8")
    sig = M.sign_gpg_detached(manifest_path, key_id=key_id)
    assert sig is not None and sig.exists()

    verify = subprocess.run(
        ["gpg", "--batch", "--verify", str(sig), str(manifest_path)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert verify.returncode == 0, verify.stderr
