"""tools.build.integrity — emit dist/integrity.json (SHA-256 manifest).

Per docs/architecture.md, every release publishes:

* ``dist/integrity.json``  — SHA-256 of every file in ``dist/`` plus the
                              merkle tree root over those hashes
* ``dist/BUILD-INFO.json`` — build metadata (git SHA, schema versions,
                              UC count, asset hashes, build timestamp)

In CI, the GitHub OIDC identity attests both files via
``actions/attest-build-provenance@v1`` (Sigstore keyless). Consumers
verify with ``gh attestation verify dist/integrity.json --owner <owner>``.

Determinism
-----------
The manifest is sorted by path, uses sort_keys=True, and a fixed JSON
separator. Two ``--reproducible`` builds of the same source SHA produce
byte-identical ``integrity.json``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def write(out_dir: Path, *, reproducible: bool = False) -> Path:
    """Walk ``out_dir`` and emit ``out_dir/integrity.json``."""
    files: list[tuple[str, str, int]] = []
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "integrity.json":
            continue
        rel = path.relative_to(out_dir).as_posix()
        digest = _sha256_file(path)
        size = path.stat().st_size
        files.append((rel, digest, size))

    tree_root = _merkle_root(digest for _, digest, _ in files)

    payload: dict[str, Any] = {
        "$schema": "/schemas/v2/integrity.schema.json",
        "version": "2.0.0",
        "algorithm": "sha256",
        "merkleRoot": tree_root,
        "fileCount": len(files),
        "files": [
            {"path": rel, "sha256": digest, "size": size}
            for rel, digest, size in files
        ],
    }

    out_path = out_dir / "integrity.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def _sha256_file(path: Path) -> str:
    """Stream the file through sha256 in 64 KiB chunks."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _merkle_root(digests):
    """Plain SHA-256 over concatenated leaf digests, sorted lexically.

    Not a full Merkle tree (no log-N proofs), but consumers can verify
    the root by re-hashing the sorted list of file digests.
    """
    items = sorted(digests)
    if not items:
        return hashlib.sha256(b"").hexdigest()
    h = hashlib.sha256()
    for d in items:
        h.update(bytes.fromhex(d))
    return h.hexdigest()
