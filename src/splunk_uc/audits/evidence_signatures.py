#!/usr/bin/env python3
"""Audit UC evidence manifests and evidence-pack signatures.

Phase C-2 — signed evidence packs verification gate.

Validates:
    * per-UC ``dist/evidence/<uc-id>/manifest.json`` content hashes
    * evidence-pack descriptors under ``dist/evidence-packs/``
    * optional Sigstore bundles via ``gh attestation verify``
    * optional detached GPG ``.sig`` files

Hermetic ``--check`` always validates committed fixtures under
``tests/fixtures/evidence-signatures/`` even when ``dist/evidence/`` is
absent. Missing production manifests emit a WARN and still PASS.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import iter_uc_sidecars
from splunk_uc.generators.sign_evidence import (
    build_pack_descriptor,
    build_uc_manifest,
    canonical_dump,
    sha256_hex,
)

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = ROOT / "dist" / "evidence"
PACKS_DIR = ROOT / "dist" / "evidence-packs"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "evidence-signatures"
REPORT_PATH = ROOT / "reports" / "evidence-signatures-audit.json"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def recompute_uc_content_hash(manifest: dict[str, Any]) -> str:
    body = {
        "ucId": manifest.get("ucId", ""),
        "evidence": manifest.get("evidence", ""),
        "evidenceSigning": manifest.get("evidenceSigning"),
        "complianceFingerprint": manifest.get("complianceFingerprint", ""),
    }
    return sha256_hex(canonical_dump(body))


def sidecar_by_id() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for _path, payload in iter_uc_sidecars():
        uc_id = payload.get("id")
        if isinstance(uc_id, str) and uc_id:
            out[uc_id] = payload
    return out


def audit_uc_manifest(path: Path, sidecars: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{_rel(path)}: invalid JSON ({exc})"]

    uc_id = manifest.get("ucId")
    if not isinstance(uc_id, str) or not uc_id:
        return [f"{_rel(path)}: missing ucId"]

    expected_hash = recompute_uc_content_hash(manifest)
    if manifest.get("contentHash") != expected_hash:
        errors.append(
            f"{_rel(path)}: contentHash mismatch "
            f"(stored={str(manifest.get('contentHash'))[:16]}… "
            f"expected={expected_hash[:16]}…)"
        )

    sidecar = sidecars.get(uc_id)
    if sidecar is not None:
        expected_manifest = build_uc_manifest(uc_id, sidecar)
        for key in ("schemaVersion", "complianceFingerprint"):
            if manifest.get(key) != expected_manifest.get(key):
                errors.append(f"{_rel(path)}: {key} drift vs sidecar UC-{uc_id}")

    errors.extend(_audit_signature_block(manifest, path))
    return errors


def audit_pack_descriptor(desc_path: Path, pack_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        descriptor = json.loads(desc_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{_rel(desc_path)}: invalid JSON ({exc})"]

    regulation_id = descriptor.get("regulationId")
    if not isinstance(regulation_id, str) or not regulation_id:
        return [f"{_rel(desc_path)}: missing regulationId"]

    if not pack_path.exists():
        return [f"{_rel(pack_path)}: missing pack JSON"]

    expected = build_pack_descriptor(regulation_id, pack_path)
    if descriptor.get("contentHash") != expected.get("contentHash"):
        errors.append(f"{_rel(desc_path)}: contentHash mismatch for {regulation_id}")

    errors.extend(_audit_signature_block(descriptor, pack_path))
    return errors


def _audit_signature_block(doc: dict[str, Any], subject_path: Path) -> list[str]:
    errors: list[str] = []
    sig = doc.get("signature")
    if not isinstance(sig, dict):
        return [f"{_rel(subject_path)}: missing signature block"]

    state = sig.get("state")
    method = sig.get("method")
    if state == "unsigned":
        return errors
    if state != "signed":
        errors.append(f"{_rel(subject_path)}: unknown signature.state={state!r}")
        return errors

    if method == "gpg":
        sig_name = sig.get("sigPath")
        if not isinstance(sig_name, str):
            errors.append(f"{_rel(subject_path)}: gpg signature missing sigPath")
            return errors
        sig_path = subject_path.parent / sig_name
        errors.extend(verify_gpg_detached(subject_path, sig_path))
    elif method == "sigstore":
        bundle_name = sig.get("bundlePath")
        if isinstance(bundle_name, str):
            bundle_path = _resolve_bundle_path(bundle_name, subject_path)
            if bundle_path is None:
                errors.append(f"{_rel(subject_path)}: bundlePath={bundle_name!r} not found")
            else:
                errors.extend(verify_sigstore_bundle(subject_path, bundle_path))
    elif method == "rfc3161-tsa":
        if not sig.get("tsaTokenPath"):
            errors.append(f"{_rel(subject_path)}: rfc3161-tsa missing tsaTokenPath")
    return errors


def verify_gpg_detached(subject_path: Path, sig_path: Path) -> list[str]:
    if shutil.which("gpg") is None:
        return [f"gpg not installed; cannot verify {sig_path.name}"]
    if not sig_path.exists():
        return [f"missing GPG signature file {_rel(sig_path)}"]
    try:
        result = subprocess.run(
            ["gpg", "--batch", "--verify", str(sig_path), str(subject_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"gpg verify failed to execute for {sig_path.name}: {exc}"]
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return [f"gpg verify rejected {sig_path.name}: {detail}"]
    return []


def _resolve_bundle_path(bundle_path: str, subject_path: Path) -> Path | None:
    candidates = [
        ROOT / bundle_path,
        subject_path.parent / bundle_path,
        PACKS_DIR / bundle_path,
        EVIDENCE_DIR / bundle_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def verify_sigstore_bundle(subject_path: Path, bundle_path: Path) -> list[str]:
    if shutil.which("gh") is None:
        return ["gh CLI not installed; skipping Sigstore verification"]
    try:
        result = subprocess.run(
            [
                "gh",
                "attestation",
                "verify",
                str(subject_path),
                "--bundle",
                str(bundle_path),
                "--predicate-type",
                "https://slsa.dev/provenance/v1",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"gh attestation verify failed to execute: {exc}"]
    if result.returncode != 0:
        return [f"gh attestation verify rejected bundle: {(result.stderr or '').strip()}"]
    return []


def audit_tree(base: Path, *, verify_signature: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    sidecars = sidecar_by_id()

    if not base.exists():
        warnings.append(f"{_rel(base)}/ absent — no production manifests to audit.")
        return errors, warnings

    for manifest_path in sorted(base.glob("UC-*/manifest.json")):
        manifest_errors = audit_uc_manifest(manifest_path, sidecars)
        if verify_signature:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            sig = manifest.get("signature", {})
            if sig.get("state") == "signed" and sig.get("method") == "sigstore":
                bundle = sig.get("bundlePath")
                if isinstance(bundle, str):
                    bundle_path = _resolve_bundle_path(bundle, manifest_path)
                    if bundle_path:
                        manifest_errors.extend(verify_sigstore_bundle(manifest_path, bundle_path))
        errors.extend(manifest_errors)

    if PACKS_DIR.is_dir():
        for desc_path in sorted(PACKS_DIR.glob("*.descriptor.json")):
            regulation_id = desc_path.name.replace(".descriptor.json", "")
            pack_path = PACKS_DIR / f"{regulation_id}.json"
            errors.extend(audit_pack_descriptor(desc_path, pack_path))

    return errors, warnings


def audit_fixtures(fixtures_dir: Path) -> list[str]:
    """Validate hermetic fixture manifests recompute cleanly."""
    errors: list[str] = []
    manifest_fixture = fixtures_dir / "uc-22.2.32" / "manifest.json"
    if not manifest_fixture.exists():
        return [f"missing fixture {_rel(manifest_fixture)}"]

    manifest = json.loads(manifest_fixture.read_text(encoding="utf-8"))
    expected_hash = recompute_uc_content_hash(manifest)
    if manifest.get("contentHash") != expected_hash:
        errors.append("fixture uc-22.2.32 manifest contentHash mismatch")

    pack_fixture = fixtures_dir / "evidence-packs" / "gdpr.descriptor.json"
    pack_json = fixtures_dir / "evidence-packs" / "gdpr.json"
    if pack_fixture.exists() and pack_json.exists():
        descriptor = json.loads(pack_fixture.read_text(encoding="utf-8"))
        expected = build_pack_descriptor("gdpr", pack_json)
        if descriptor.get("contentHash") != expected.get("contentHash"):
            errors.append("fixture gdpr pack descriptor contentHash mismatch")

    tampered = fixtures_dir / "tampered" / "manifest.json"
    if tampered.exists():
        bad = json.loads(tampered.read_text(encoding="utf-8"))
        if recompute_uc_content_hash(bad) == bad.get("contentHash"):
            errors.append("tampered fixture should fail hash recompute but did not")
    return errors


def write_report(errors: list[str], warnings: list[str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "$comment": "Phase C-2 evidence-signatures audit output.",
        "status": "fail" if errors else "pass",
        "errorCount": len(errors),
        "warningCount": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit evidence manifests and signatures.")
    parser.add_argument("--check", action="store_true", help="CI drift gate (includes fixtures).")
    parser.add_argument(
        "--verify-signature",
        action="store_true",
        help="Run gh attestation verify / gpg verify on signed artefacts.",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=FIXTURES_DIR,
        help="Hermetic fixture root (default: tests/fixtures/evidence-signatures).",
    )
    args = parser.parse_args(argv)

    errors: list[str] = []
    warnings: list[str] = []

    fixture_errors = audit_fixtures(args.fixtures_dir)
    errors.extend(fixture_errors)

    prod_errors, prod_warnings = audit_tree(EVIDENCE_DIR, verify_signature=args.verify_signature)
    errors.extend(prod_errors)
    warnings.extend(prod_warnings)

    write_report(errors, warnings)

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)

    if errors:
        print("FAIL: evidence-signatures audit found issues:", file=sys.stderr)
        for err in errors[:40]:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if warnings:
        print("PASS WITH WARNINGS: evidence-signatures audit OK.")
    else:
        print("PASS: evidence-signatures audit OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
