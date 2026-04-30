"""Tests for tools/build/integrity.py — SHA-256 manifest and merkle root."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build.integrity import _merkle_root, _sha256_file, write  # noqa: E402

SHA256_EMPTY = hashlib.sha256(b"").hexdigest()


class TestSha256File:
    def test_empty_file_matches_known_digest(self, tmp_path: Path):
        p = tmp_path / "empty.bin"
        p.write_bytes(b"")
        assert _sha256_file(p) == SHA256_EMPTY

    def test_known_content_matches_hashlib(self, tmp_path: Path):
        data = b"The quick brown fox"
        p = tmp_path / "fox.txt"
        p.write_bytes(data)
        assert _sha256_file(p) == hashlib.sha256(data).hexdigest()


class TestMerkleRoot:
    def test_empty_inputs_hashes_empty_bytestring(self):
        assert _merkle_root([]) == SHA256_EMPTY
        assert _merkle_root(iter(())) == SHA256_EMPTY

    def test_single_digest(self):
        d = hashlib.sha256(b"a").hexdigest()
        h = hashlib.sha256()
        h.update(bytes.fromhex(d))
        assert _merkle_root([d]) == h.hexdigest()

    def test_order_independent(self):
        a = hashlib.sha256(b"a").hexdigest()
        b = hashlib.sha256(b"b").hexdigest()
        assert _merkle_root([a, b]) == _merkle_root([b, a])


class TestWriteIntegrityManifest:
    def test_manifest_json_structure_and_roundtrip(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.txt").write_bytes(b"\x00\xff")

        out = write(tmp_path)

        assert out == tmp_path / "integrity.json"
        assert out.is_file()

        raw = json.loads(out.read_text(encoding="utf-8"))
        assert raw["$schema"] == "/schemas/v2/integrity.schema.json"
        assert raw["version"] == "2.0.0"
        assert raw["algorithm"] == "sha256"
        assert isinstance(raw["merkleRoot"], str) and len(raw["merkleRoot"]) == 64
        assert raw["fileCount"] == 2
        assert isinstance(raw["files"], list) and len(raw["files"]) == 2

        by_path = {f["path"]: f for f in raw["files"]}
        assert "a.txt" in by_path and "sub/b.txt" in by_path
        for f in raw["files"]:
            assert set(f.keys()) == {"path", "sha256", "size"}
            assert len(f["sha256"]) == 64
            assert f["sha256"] == _sha256_file(tmp_path / f["path"])
            assert f["size"] == (tmp_path / f["path"]).stat().st_size

        roots = [f["sha256"] for f in raw["files"]]
        assert raw["merkleRoot"] == _merkle_root(roots)

    def test_integrity_json_excluded_from_file_list(self, tmp_path: Path):
        (tmp_path / "only.txt").write_text("x", encoding="utf-8")
        write(tmp_path)
        raw = json.loads((tmp_path / "integrity.json").read_text(encoding="utf-8"))
        paths = {f["path"] for f in raw["files"]}
        assert "integrity.json" not in paths
