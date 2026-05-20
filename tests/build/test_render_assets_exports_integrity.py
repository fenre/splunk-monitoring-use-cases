"""Hermetic tests for three small ``tools/build`` modules with no
existing dedicated test file.

Modules covered:

* ``tools/build/render_assets.py`` — CSS / JS bundlers, copy-tree
* ``tools/build/render_exports.py`` — bulk catalog CSV emitter
* ``tools/build/integrity.py``      — SHA-256 + Merkle-root manifest

All tests construct minimal ``Catalog`` instances and tiny on-disk
fixtures in ``tmp_path``; no real catalog data is loaded.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from build import integrity, render_assets, render_exports
from build.parse_content import Catalog


def _empty_catalog(tmp_path: Path, **overrides) -> Catalog:
    """Construct an in-memory Catalog with sane defaults for tests."""
    kwargs = dict(
        project_root=tmp_path,
        categories=[],
        cat_meta={},
        cat_groups={},
        equipment=[],
        regulations={},
        recently_added=[],
        facets={},
    )
    kwargs.update(overrides)
    return Catalog(**kwargs)


# ---------------------------------------------------------------------------
# render_assets.py
# ---------------------------------------------------------------------------


class TestRenderAssets:
    """``render_assets.render()`` and its bundlers."""

    def test_render_short_circuits_when_src_directory_missing(
        self, tmp_path: Path
    ) -> None:
        """If ``catalog.project_root/src`` doesn't exist the renderer
        returns silently without touching ``out_dir/assets``. Pins line
        49 of ``render_assets.py``."""
        out_dir = tmp_path / "dist"
        cat = _empty_catalog(tmp_path)
        render_assets.render(cat, out_dir, reproducible=True)
        # The assets directory is always pre-created (line 45) but no
        # bundles or asset_hashes entries are emitted.
        assert (out_dir / "assets").is_dir()
        assert cat.asset_hashes == {}
        assert cat.critical_css == ""

    def test_bundle_css_returns_empty_when_styles_dir_missing(
        self, tmp_path: Path
    ) -> None:
        """``_bundle_css`` on a non-existent directory returns empty
        triple (covers line 78)."""
        assert render_assets._bundle_css(tmp_path / "missing", tmp_path) == (
            "",
            "",
            "",
        )

    def test_bundle_css_returns_empty_when_no_css_files(
        self, tmp_path: Path
    ) -> None:
        """``_bundle_css`` on a directory with no ``*.css`` returns
        empty triple (covers line 81)."""
        styles = tmp_path / "styles"
        styles.mkdir()
        (styles / "README.md").write_text("not css", encoding="utf-8")
        assert render_assets._bundle_css(styles, tmp_path) == ("", "", "")

    def test_bundle_css_concatenates_and_fingerprints(self, tmp_path: Path) -> None:
        """Multiple CSS files are concatenated in filename order, the
        resulting bundle is hashed, and the critical subset is captured
        from files matching ``CRITICAL_CSS_PREFIXES``. Covers lines
        85-98."""
        styles = tmp_path / "styles"
        styles.mkdir()
        (styles / "01-tokens.css").write_text(":root{--c:red}", encoding="utf-8")
        (styles / "02-base.css").write_text("body{margin:0}", encoding="utf-8")
        (styles / "10-pages.css").write_text(".page{display:block}", encoding="utf-8")

        assets = tmp_path / "assets"
        assets.mkdir()
        full_hash, name, critical = render_assets._bundle_css(styles, assets)

        # Filename = styles.<10char>.css
        assert name.startswith("styles.")
        assert name.endswith(".css")
        assert len(name) == len("styles.") + render_assets.HASH_LEN + len(".css")
        # Hash matches the concatenated bytes
        expected = b":root{--c:red}body{margin:0}.page{display:block}"
        assert full_hash == hashlib.sha256(expected).hexdigest()
        # Critical is only the 01-/02- files
        assert critical == ":root{--c:red}body{margin:0}"
        # File was actually written
        assert (assets / name).read_bytes() == expected

    def test_bundle_js_returns_empty_when_scripts_dir_missing(
        self, tmp_path: Path
    ) -> None:
        """``_bundle_js`` on a non-existent directory returns empty
        pair (covers line 104)."""
        assert render_assets._bundle_js(tmp_path / "missing", tmp_path) == ("", "")

    def test_bundle_js_returns_empty_when_no_js_files(self, tmp_path: Path) -> None:
        """``_bundle_js`` on a directory with no ``*.js`` returns empty
        pair (covers line 107)."""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "README.md").write_text("not js", encoding="utf-8")
        assert render_assets._bundle_js(scripts, tmp_path) == ("", "")

    def test_bundle_js_concatenates_and_fingerprints(self, tmp_path: Path) -> None:
        """Multiple JS files are concatenated in filename order and
        the bundle is hashed. Covers lines 109-114."""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "00-loader.js").write_text(
            "var x=1;", encoding="utf-8"
        )
        (scripts / "01-app.js").write_text("var y=2;", encoding="utf-8")

        assets = tmp_path / "assets"
        assets.mkdir()
        full_hash, name = render_assets._bundle_js(scripts, assets)
        expected = b"var x=1;var y=2;"
        assert full_hash == hashlib.sha256(expected).hexdigest()
        assert name.startswith("app.") and name.endswith(".js")
        assert (assets / name).read_bytes() == expected

    def test_copy_tree_verbatim_skips_missing_source(self, tmp_path: Path) -> None:
        """``_copy_tree_verbatim`` on a non-existent source is a no-op
        (covers line 119)."""
        dst = tmp_path / "dst"
        render_assets._copy_tree_verbatim(tmp_path / "missing", dst)
        assert not dst.exists()

    def test_copy_tree_verbatim_preserves_subdirs_and_skips_dirs(
        self, tmp_path: Path
    ) -> None:
        """Subdirectories are recreated under ``dst`` and only files
        are copied; non-file entries (directories themselves) are
        skipped via the ``if not path.is_file(): continue`` guard
        (line 122)."""
        src = tmp_path / "src"
        sub = src / "nested"
        sub.mkdir(parents=True)
        (src / "top.txt").write_text("top", encoding="utf-8")
        (sub / "deep.txt").write_text("deep", encoding="utf-8")

        dst = tmp_path / "dst"
        render_assets._copy_tree_verbatim(src, dst)
        assert (dst / "top.txt").read_text(encoding="utf-8") == "top"
        assert (dst / "nested" / "deep.txt").read_text(encoding="utf-8") == "deep"

    def test_render_skips_recording_when_bundlers_return_empty(
        self, tmp_path: Path
    ) -> None:
        """When ``src/`` exists but contains no styles/ or scripts/
        subdirs, ``_bundle_css`` and ``_bundle_js`` both return empty,
        and ``render()`` must skip the ``if css_name:`` and
        ``if js_name:`` blocks so no spurious entries appear on
        ``catalog.asset_hashes``. Covers the false arms of branches
        52→57 and 58→62 in ``render_assets.py``."""
        (tmp_path / "src").mkdir()
        # Intentionally do NOT create styles/ or scripts/ subdirs.

        out_dir = tmp_path / "dist"
        cat = _empty_catalog(tmp_path)
        render_assets.render(cat, out_dir, reproducible=True)

        # Neither bundle path was recorded.
        assert "styles_css" not in cat.asset_hashes
        assert "app_js" not in cat.asset_hashes
        assert cat.critical_css == ""
        # The assets/ output directory was still created (line 45) but
        # no css/js bundles were emitted.
        emitted = sorted(p.name for p in (out_dir / "assets").iterdir())
        assert not any(b.startswith("styles.") for b in emitted)
        assert not any(b.startswith("app.") for b in emitted)

    def test_render_end_to_end_writes_bundles_and_updates_catalog(
        self, tmp_path: Path
    ) -> None:
        """``render()`` orchestrates css + js + img + fonts copy and
        stashes asset hashes on the catalog (covers lines 47-63 of
        ``render_assets.py``)."""
        # Build a tiny src/ tree
        src = tmp_path / "src"
        (src / "styles").mkdir(parents=True)
        (src / "scripts").mkdir(parents=True)
        (src / "img").mkdir(parents=True)
        (src / "fonts").mkdir(parents=True)
        (src / "styles" / "01-tokens.css").write_text("a{}", encoding="utf-8")
        (src / "styles" / "10-misc.css").write_text("b{}", encoding="utf-8")
        (src / "scripts" / "app.js").write_text("var z=3;", encoding="utf-8")
        (src / "img" / "logo.svg").write_text("<svg/>", encoding="utf-8")
        (src / "fonts" / "inter.woff2").write_bytes(b"\x00\x01")

        out_dir = tmp_path / "dist"
        cat = _empty_catalog(tmp_path)
        render_assets.render(cat, out_dir, reproducible=True)

        # Hashes recorded
        assert "styles_css" in cat.asset_hashes
        assert "styles_css_sha256" in cat.asset_hashes
        assert "app_js" in cat.asset_hashes
        assert "app_js_sha256" in cat.asset_hashes
        # Critical CSS is only the 01- file
        assert cat.critical_css == "a{}"
        # Bundles + verbatim copies all landed
        bundles = sorted(p.name for p in (out_dir / "assets").iterdir())
        assert any(b.startswith("styles.") for b in bundles)
        assert any(b.startswith("app.") for b in bundles)
        assert (out_dir / "assets" / "img" / "logo.svg").exists()
        assert (out_dir / "assets" / "fonts" / "inter.woff2").exists()


# ---------------------------------------------------------------------------
# render_exports.py
# ---------------------------------------------------------------------------


class TestRenderExports:
    """``render_exports.render()`` and ``_write_catalog_csv``."""

    def _catalog_with_ucs(self, tmp_path: Path) -> Catalog:
        return _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "Network",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "Routing",
                            "u": [
                                {
                                    "i": "1.1.2",
                                    "n": "BGP flapping",
                                    "c": "high",
                                    "d": "medium",
                                    "mtype": "real-time",
                                    "pillar": "observability",
                                    "regs": ["NIST", "SOC2"],
                                    "a": "Splunk_TA_cisco_ios",
                                },
                                {
                                    "i": "1.1.1",
                                    "n": "OSPF neighbour down",
                                },
                                # No id → skipped by line 69
                                {"n": "headless UC"},
                            ],
                        }
                    ],
                }
            ],
        )

    def test_render_emits_catalog_csv(self, tmp_path: Path) -> None:
        """``dialect='unix'`` quotes every field, so the header line is
        ``"uc_id","title",…`` and each cell carries surrounding quotes
        (covers lines 39-92 of render_exports.py)."""
        cat = self._catalog_with_ucs(tmp_path)
        out_dir = tmp_path / "dist"
        render_exports.render(cat, out_dir, reproducible=False)
        csv_path = out_dir / "exports" / "catalog.csv"
        assert csv_path.exists()

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        # Header + 2 UC rows (the headless UC is dropped by line 69).
        assert len(lines) == 3
        assert lines[0].startswith('"uc_id","title","category_id"')
        # Non-reproducible run preserves catalog order: 1.1.2 first.
        assert (
            '"UC-1.1.2","BGP flapping","1","Network","1.1","Routing","high","medium"'
            in lines[1]
        )
        # Regulations are joined with commas (the field is quoted by
        # dialect=unix so the comma inside is fine).
        assert '"NIST,SOC2"' in lines[1]

    def test_reproducible_mode_sorts_rows_lexically(self, tmp_path: Path) -> None:
        """When ``reproducible=True`` the row list is sorted before
        being written so two runs yield byte-identical output (covers
        line 89)."""
        cat = self._catalog_with_ucs(tmp_path)
        out_dir = tmp_path / "dist"
        render_exports.render(cat, out_dir, reproducible=True)
        lines = (out_dir / "exports" / "catalog.csv").read_text(encoding="utf-8").splitlines()
        # After sort, UC-1.1.1 (the row with that prefix) comes before
        # UC-1.1.2.
        assert lines[1].startswith('"UC-1.1.1","OSPF neighbour down","1","Network","1.1","Routing"')
        assert lines[2].startswith('"UC-1.1.2","BGP flapping","1","Network","1.1","Routing"')

    def test_render_empty_catalog_writes_header_only(self, tmp_path: Path) -> None:
        cat = _empty_catalog(tmp_path)
        out_dir = tmp_path / "dist"
        render_exports.render(cat, out_dir, reproducible=True)
        text = (out_dir / "exports" / "catalog.csv").read_text(encoding="utf-8")
        assert text.startswith('"uc_id","title","category_id"')
        # Only the header line.
        assert text.count("\n") == 1


# ---------------------------------------------------------------------------
# integrity.py
# ---------------------------------------------------------------------------


class TestIntegrity:
    """``integrity.write()`` + ``_sha256_file`` + ``_merkle_root``."""

    def test_sha256_file_streams_correct_digest_for_small_file(
        self, tmp_path: Path
    ) -> None:
        p = tmp_path / "small.bin"
        p.write_bytes(b"hello world")
        assert (
            integrity._sha256_file(p)
            == hashlib.sha256(b"hello world").hexdigest()
        )

    def test_sha256_file_handles_multi_chunk_payload(self, tmp_path: Path) -> None:
        """Files larger than the 64 KiB read window iterate the
        ``iter(lambda: f.read(64 * 1024), b'')`` loop more than once
        (covers the loop body on line 68 with realistic input)."""
        p = tmp_path / "big.bin"
        # ~200 KiB so the streamer reads >1 chunk
        data = (b"abc" * 70_000)
        p.write_bytes(data)
        assert integrity._sha256_file(p) == hashlib.sha256(data).hexdigest()

    def test_merkle_root_empty_returns_sha256_of_empty_string(self) -> None:
        """Covers line 80-81: empty digest iterable returns
        ``sha256(b'')``."""
        assert (
            integrity._merkle_root(iter([]))
            == hashlib.sha256(b"").hexdigest()
        )

    def test_merkle_root_sorted_concatenation_is_stable(self) -> None:
        """The two digests are sorted lexically before concat-hashing,
        so input order doesn't affect the root (covers line 79)."""
        a = hashlib.sha256(b"alpha").hexdigest()
        b = hashlib.sha256(b"beta").hexdigest()
        # Forward + reverse orderings agree
        root_forward = integrity._merkle_root([a, b])
        root_reverse = integrity._merkle_root([b, a])
        assert root_forward == root_reverse
        # Manually compute the expected root
        h = hashlib.sha256()
        for d in sorted([a, b]):
            h.update(bytes.fromhex(d))
        assert root_forward == h.hexdigest()

    def test_write_emits_manifest_with_correct_shape_and_skips_self(
        self, tmp_path: Path
    ) -> None:
        """End-to-end: ``write()`` walks ``out_dir``, hashes every
        file, omits its own ``integrity.json`` from the listing, and
        emits a schema-shaped payload sorted by path."""
        out = tmp_path / "dist"
        out.mkdir()
        (out / "a.txt").write_text("alpha", encoding="utf-8")
        (out / "nested").mkdir()
        (out / "nested" / "b.txt").write_text("beta", encoding="utf-8")
        # Pre-existing integrity.json — must be skipped during walk.
        (out / "integrity.json").write_text(
            "this will be overwritten", encoding="utf-8"
        )

        result_path = integrity.write(out, reproducible=True)
        assert result_path == out / "integrity.json"

        payload = json.loads(result_path.read_text(encoding="utf-8"))
        assert payload["$schema"] == "/schemas/v2/integrity.schema.json"
        assert payload["version"] == "2.0.0"
        assert payload["algorithm"] == "sha256"
        assert payload["fileCount"] == 2  # a.txt + nested/b.txt, NOT integrity.json
        paths = [entry["path"] for entry in payload["files"]]
        # Lexically sorted (line 32: sorted(out_dir.rglob('*')))
        assert paths == ["a.txt", "nested/b.txt"]
        # Hashes match expectations
        assert (
            payload["files"][0]["sha256"]
            == hashlib.sha256(b"alpha").hexdigest()
        )
        assert payload["files"][0]["size"] == len(b"alpha")
        # Merkle root is sha256(sorted concat of file digests)
        digests = sorted(entry["sha256"] for entry in payload["files"])
        h = hashlib.sha256()
        for d in digests:
            h.update(bytes.fromhex(d))
        assert payload["merkleRoot"] == h.hexdigest()

    def test_write_skips_non_file_paths(self, tmp_path: Path) -> None:
        """``rglob('*')`` returns directories too; the manifest must
        skip them via the ``if not path.is_file(): continue`` guard
        (line 33)."""
        out = tmp_path / "dist"
        out.mkdir()
        (out / "subdir").mkdir()  # directory only — must be skipped
        (out / "subdir" / "leaf.txt").write_text("leaf", encoding="utf-8")
        integrity.write(out, reproducible=True)
        payload = json.loads((out / "integrity.json").read_text(encoding="utf-8"))
        paths = [entry["path"] for entry in payload["files"]]
        assert paths == ["subdir/leaf.txt"]

    def test_write_on_empty_directory_returns_empty_root(self, tmp_path: Path) -> None:
        """Empty directory → empty file list → merkle root is the
        SHA-256 of an empty byte string."""
        out = tmp_path / "dist"
        out.mkdir()
        integrity.write(out, reproducible=True)
        payload = json.loads((out / "integrity.json").read_text(encoding="utf-8"))
        assert payload["fileCount"] == 0
        assert payload["files"] == []
        assert payload["merkleRoot"] == hashlib.sha256(b"").hexdigest()
