#!/usr/bin/env python3
"""Generate signed evidence manifests for UC sidecars and evidence-pack JSON.

Phase C-2 — signed evidence packs (Catalog Parallel Execution Atlas).

Produces deterministic, content-addressable manifests under
``dist/evidence/<uc-id>/manifest.json`` and optional pack-level artefacts
under ``dist/evidence-packs/``. Signatures are applied externally (Sigstore
via ``.github/workflows/sign-evidence.yml``, GPG via ``--gpg``) so PR CI
stays byte-deterministic with ``signature.state="unsigned"``.

Usage
-----
    PYTHONPATH=src python3 -m splunk_uc generate-evidence-signatures
    PYTHONPATH=src python3 -m splunk_uc generate-evidence-signatures --check
    PYTHONPATH=src python3 -m splunk_uc generate-evidence-signatures --all --gpg
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import iter_uc_sidecars

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = ROOT / "dist" / "evidence"
PACKS_OUT_DIR = ROOT / "dist" / "evidence-packs"
API_PACKS_DIR = ROOT / "api" / "v1" / "evidence-packs"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()

SCHEMA_VERSION = "1.0.0"
HASH_ALGORITHM = "sha256"
SIGSTORE_ALGORITHM = "sigstore-cosign-bundle-v0.3"
GPG_ALGORITHM = "openpgp-detached-sig-v1"

CANONICAL_MANIFEST_FIELDS = (
    "ucId",
    "evidence",
    "evidenceSigning",
    "complianceFingerprint",
)


def canonical_dump(obj: Any) -> str:
    """RFC 8785-compatible subset: sorted keys, no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compliance_fingerprint(compliance: list[Any]) -> str:
    """Stable hash over compliance[] entries relevant to evidence."""
    rows: list[dict[str, str]] = []
    for entry in compliance:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "regulation": str(entry.get("regulation", "")),
                "version": str(entry.get("version", "")),
                "clause": str(entry.get("clause", "")),
                "mode": str(entry.get("mode", "")),
                "assurance": str(entry.get("assurance", "")),
                "evidenceArtifact": str(entry.get("evidenceArtifact", "")),
            }
        )
    rows.sort(key=lambda r: (r["regulation"], r["version"], r["clause"], r["mode"]))
    return sha256_hex(canonical_dump(rows))


def signing_method(payload: dict[str, Any]) -> str:
    signing = payload.get("evidenceSigning")
    if isinstance(signing, dict):
        method = signing.get("method")
        if isinstance(method, str) and method:
            return method
    return "none"


def build_unsigned_signature_block(method: str) -> dict[str, Any]:
    return {
        "state": "unsigned",
        "method": method,
        "reason": "development iteration; sign-evidence workflow promotes to signed",
    }


def build_uc_manifest(uc_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    evidence = payload.get("evidence")
    evidence_text = evidence if isinstance(evidence, str) else ""
    signing_meta = payload.get("evidenceSigning")
    if not isinstance(signing_meta, dict):
        signing_meta = None
    compliance = payload.get("compliance")
    if not isinstance(compliance, list):
        compliance = []

    canonical_body = {
        "ucId": uc_id,
        "evidence": evidence_text,
        "evidenceSigning": signing_meta,
        "complianceFingerprint": compliance_fingerprint(compliance),
    }
    content_hash = sha256_hex(canonical_dump(canonical_body))
    method = signing_method(payload)

    manifest: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "hashAlgorithm": HASH_ALGORITHM,
        "ucId": uc_id,
        "contentHash": content_hash,
        "evidence": evidence_text,
        "complianceFingerprint": canonical_body["complianceFingerprint"],
        "signature": build_unsigned_signature_block(method),
    }
    if signing_meta is not None:
        manifest["evidenceSigning"] = signing_meta
    return manifest


def collect_uc_manifests() -> dict[str, dict[str, Any]]:
    """Return ``{uc_id: manifest}`` for every sidecar with evidence metadata."""
    out: dict[str, dict[str, Any]] = {}
    for _path, payload in iter_uc_sidecars():
        uc_id = payload.get("id")
        if not isinstance(uc_id, str) or not uc_id:
            continue
        has_evidence = isinstance(payload.get("evidence"), str) and payload.get("evidence")
        has_signing = isinstance(payload.get("evidenceSigning"), dict)
        if not has_evidence and not has_signing:
            continue
        out[uc_id] = build_uc_manifest(uc_id, payload)
    return out


def collect_pack_sources() -> list[tuple[str, Path]]:
    """Return ``(regulation_id, path)`` for machine-readable evidence packs."""
    if not API_PACKS_DIR.is_dir():
        return []
    packs: list[tuple[str, Path]] = []
    for path in sorted(API_PACKS_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        packs.append((path.stem, path))
    return packs


def build_pack_descriptor(regulation_id: str, source: Path) -> dict[str, Any]:
    raw = source.read_bytes()
    content_hash = hashlib.sha256(raw).hexdigest()
    try:
        rel = source.relative_to(ROOT).as_posix()
    except ValueError:
        rel = source.as_posix()
    return {
        "schemaVersion": SCHEMA_VERSION,
        "hashAlgorithm": HASH_ALGORITHM,
        "regulationId": regulation_id,
        "sourcePath": rel,
        "contentHash": content_hash,
        "signature": {
            "state": "unsigned",
            "method": "sigstore",
            "reason": "development iteration; sign-evidence workflow promotes to signed",
        },
    }


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object at {path}")
    return data


def sign_gpg_detached(target: Path, key_id: str | None = None) -> Path | None:
    """Create a detached OpenPGP signature beside *target*. Returns sig path or None."""
    if shutil.which("gpg") is None:
        return None
    sig_path = target.with_suffix(target.suffix + ".sig")
    cmd = ["gpg", "--batch", "--yes", "--armor", "--detach-sign", "-o", str(sig_path), str(target)]
    if key_id:
        cmd = [
            "gpg",
            "--batch",
            "--yes",
            "--local-user",
            key_id,
            "--armor",
            "--detach-sign",
            "-o",
            str(sig_path),
            str(target),
        ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return sig_path if sig_path.exists() else None


def stamp_pack_sigstore(regulation_id: str, bundle_filename: str, *, run_id: str = "", commit: str = "") -> None:
    """Promote a pack descriptor to ``signature.state=signed`` (Sigstore)."""
    desc_path = PACKS_OUT_DIR / f"{regulation_id}.descriptor.json"
    if not desc_path.exists():
        return
    descriptor = read_json(desc_path)
    descriptor["signature"] = {
        "state": "signed",
        "method": "sigstore",
        "signatureAlgorithm": SIGSTORE_ALGORITHM,
        "bundlePath": bundle_filename,
        "runId": run_id or None,
        "commit": commit or None,
    }
    # Drop null optional fields for stable JSON.
    descriptor["signature"] = {k: v for k, v in descriptor["signature"].items() if v is not None}
    write_json(desc_path, descriptor)


def apply_gpg_signature(manifest: dict[str, Any], manifest_path: Path, key_id: str | None) -> None:
    sig_path = sign_gpg_detached(manifest_path, key_id=key_id)
    if sig_path is None:
        return
    manifest["signature"] = {
        "state": "signed",
        "method": "gpg",
        "signatureAlgorithm": GPG_ALGORITHM,
        "sigPath": sig_path.name,
        "signer": key_id or "default-key",
    }
    write_json(manifest_path, manifest)


def generate_all(*, gpg: bool = False, gpg_key: str | None = None, packs: bool = True) -> int:
    manifests = collect_uc_manifests()
    written = 0
    for uc_id, manifest in sorted(manifests.items()):
        out_dir = EVIDENCE_DIR / f"UC-{uc_id}"
        out_path = out_dir / "manifest.json"
        write_json(out_path, manifest)
        if gpg and manifest.get("signature", {}).get("method") in {"gpg", "rfc3161-tsa", "sigstore"}:
            method = signing_method({"evidenceSigning": manifest.get("evidenceSigning")})
            if method == "gpg" or gpg:
                apply_gpg_signature(manifest, out_path, gpg_key)
        written += 1

    pack_count = 0
    if packs:
        for regulation_id, source in collect_pack_sources():
            descriptor = build_pack_descriptor(regulation_id, source)
            dest = PACKS_OUT_DIR / f"{regulation_id}.json"
            shutil.copy2(source, dest)
            write_json(PACKS_OUT_DIR / f"{regulation_id}.descriptor.json", descriptor)
            if gpg:
                apply_gpg_signature(descriptor, PACKS_OUT_DIR / f"{regulation_id}.descriptor.json", gpg_key)
            pack_count += 1

    print(
        f"Wrote {written} UC evidence manifest(s) under {EVIDENCE_DIR.relative_to(ROOT)}/ "
        f"and {pack_count} evidence-pack descriptor(s) under {PACKS_OUT_DIR.relative_to(ROOT)}/."
    )
    return 0


def check_drift(*, gpg: bool = False) -> int:
    """Recompute manifests and fail on byte drift."""
    errors: list[str] = []
    expected = collect_uc_manifests()
    if EVIDENCE_DIR.is_dir():
        for uc_id, manifest in sorted(expected.items()):
            path = EVIDENCE_DIR / f"UC-{uc_id}" / "manifest.json"
            if not path.exists():
                errors.append(f"missing manifest for UC-{uc_id} at {_rel(path)}")
                continue
            on_disk = read_json(path)
            if on_disk.get("contentHash") != manifest.get("contentHash"):
                errors.append(f"contentHash drift for UC-{uc_id}")
            for key in ("schemaVersion", "ucId", "complianceFingerprint"):
                if on_disk.get(key) != manifest.get(key):
                    errors.append(f"{key} drift for UC-{uc_id}")
    else:
        print(
            f"WARN: {_rel(EVIDENCE_DIR)}/ absent — skipping UC manifest drift check.",
            file=sys.stderr,
        )

    for regulation_id, source in collect_pack_sources():
        descriptor = build_pack_descriptor(regulation_id, source)
        desc_path = PACKS_OUT_DIR / f"{regulation_id}.descriptor.json"
        pack_path = PACKS_OUT_DIR / f"{regulation_id}.json"
        if not desc_path.exists() or not pack_path.exists():
            continue
        on_disk = read_json(desc_path)
        if on_disk.get("contentHash") != descriptor.get("contentHash"):
            errors.append(f"pack contentHash drift for {regulation_id}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print("PASS: evidence signature manifests are current.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic evidence manifests and optional GPG signatures."
    )
    parser.add_argument("--check", action="store_true", help="Fail when on-disk manifests drift.")
    parser.add_argument("--all", action="store_true", help="Generate manifests for all eligible UCs.")
    parser.add_argument(
        "--gpg",
        action="store_true",
        help="Apply detached GPG signatures (requires gpg and a local key).",
    )
    parser.add_argument("--gpg-key", default=None, help="GPG key id for --gpg signing.")
    parser.add_argument(
        "--no-packs",
        action="store_true",
        help="Skip api/v1/evidence-packs/* descriptor generation.",
    )
    args = parser.parse_args(argv)

    if args.check:
        return check_drift(gpg=args.gpg)

    if not args.all and not args.gpg:
        parser.error("Specify --all to write manifests, or --check to verify drift.")

    return generate_all(gpg=args.gpg, gpg_key=args.gpg_key, packs=not args.no_packs)


if __name__ == "__main__":
    sys.exit(main())
