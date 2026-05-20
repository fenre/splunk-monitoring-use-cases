"""Hermetic tests for ``tools/build/render_legacy_artifacts.py``.

Covers the pure helpers, the catalog dict builder, the
``_last_modified_iso`` reproducible/non-reproducible branches, the
``_atomic_write`` happy path and failure cleanup, the
``_write_llms_artefacts`` global-shim save/restore behaviour, and the
``render()`` orchestration with a mocked ``_enrichment`` module.
"""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pytest

from build import render_legacy_artifacts as rla
from build.parse_content import Catalog


def _empty_catalog(tmp_path: Path, **overrides) -> Catalog:
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
# _read_version
# ---------------------------------------------------------------------------


class TestReadVersion:
    def test_returns_version_file_content_stripped(self, monkeypatch, tmp_path: Path):
        """When VERSION exists, its trimmed content is returned. We
        monkeypatch ``__file__`` so the helper looks in our temp tree."""
        # The helper resolves repo_root via __file__.parent.parent.parent,
        # so simulate a 3-deep layout under tmp_path.
        fake_module = tmp_path / "tools" / "build" / "render_legacy_artifacts.py"
        fake_module.parent.mkdir(parents=True)
        fake_module.touch()
        (tmp_path / "VERSION").write_text("  9.4.2\n", encoding="utf-8")
        monkeypatch.setattr(rla, "__file__", str(fake_module))
        assert rla._read_version() == "9.4.2"

    def test_returns_zero_zero_zero_when_version_missing(
        self, monkeypatch, tmp_path: Path
    ):
        """A missing VERSION returns the documented fallback (line
        279)."""
        fake_module = tmp_path / "tools" / "build" / "render_legacy_artifacts.py"
        fake_module.parent.mkdir(parents=True)
        fake_module.touch()
        # Do not write VERSION.
        monkeypatch.setattr(rla, "__file__", str(fake_module))
        assert rla._read_version() == "0.0.0"

    def test_returns_fallback_when_version_file_is_blank(
        self, monkeypatch, tmp_path: Path
    ):
        """A VERSION that contains only whitespace strips to '' and
        falls through to the ``or "0.0.0"`` fallback on line 278."""
        fake_module = tmp_path / "tools" / "build" / "render_legacy_artifacts.py"
        fake_module.parent.mkdir(parents=True)
        fake_module.touch()
        (tmp_path / "VERSION").write_text("   \n", encoding="utf-8")
        monkeypatch.setattr(rla, "__file__", str(fake_module))
        assert rla._read_version() == "0.0.0"


# ---------------------------------------------------------------------------
# _generated_at_iso + _last_modified_iso
# ---------------------------------------------------------------------------


class TestTimestamps:
    def test_generated_at_iso_returns_utc_iso_with_z_suffix(self):
        import re
        out = rla._generated_at_iso()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", out), out

    def test_last_modified_iso_non_reproducible_uses_wall_clock(self):
        """Covers line 306."""
        import re
        out = rla._last_modified_iso(reproducible=False)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", out), out

    def test_last_modified_iso_reproducible_no_epoch_returns_unix_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """When SOURCE_DATE_EPOCH is unset, reproducible builds anchor
        to 1970-01-01 (covers lines 307-313)."""
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        assert rla._last_modified_iso(reproducible=True) == "1970-01-01T00:00:00Z"

    def test_last_modified_iso_reproducible_zero_epoch_returns_unix_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
        assert rla._last_modified_iso(reproducible=True) == "1970-01-01T00:00:00Z"

    def test_last_modified_iso_reproducible_invalid_epoch_returns_unix_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Non-numeric SOURCE_DATE_EPOCH triggers the
        ``except (TypeError, ValueError)`` arm on line 311."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")
        assert rla._last_modified_iso(reproducible=True) == "1970-01-01T00:00:00Z"

    def test_last_modified_iso_reproducible_positive_epoch_returns_that_iso(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """SOURCE_DATE_EPOCH=1700000000 → '2023-11-14T22:13:20Z'.
        Covers the happy path on lines 314-319."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        assert (
            rla._last_modified_iso(reproducible=True)
            == "2023-11-14T22:13:20Z"
        )


# ---------------------------------------------------------------------------
# _atomic_write
# ---------------------------------------------------------------------------


class TestAtomicWrite:
    def test_writes_content_via_tempfile_rename(self, tmp_path: Path):
        target = tmp_path / "out" / "file.txt"
        rla._atomic_write(target, "hello world\n")
        assert target.read_text(encoding="utf-8") == "hello world\n"
        # The parent dir was auto-created (line 330).
        assert target.parent.is_dir()
        # No leftover tempfiles in the target dir.
        assert sorted(p.name for p in target.parent.iterdir()) == ["file.txt"]

    def test_failure_cleans_up_tempfile(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """When ``os.replace`` raises, the temp file MUST be unlinked
        and the exception re-raised (covers lines 338-343)."""
        target = tmp_path / "out" / "file.txt"
        target.parent.mkdir()

        original_replace = os.replace

        def boom(src, dst):
            raise RuntimeError("simulated rename failure")

        monkeypatch.setattr(os, "replace", boom)
        with pytest.raises(RuntimeError, match="simulated rename failure"):
            rla._atomic_write(target, "content")
        # Restore so other tests aren't affected (handled by monkeypatch),
        # then verify no tempfile leaked.
        monkeypatch.setattr(os, "replace", original_replace)
        leftovers = list(target.parent.iterdir())
        assert leftovers == [], f"leaked tempfiles: {leftovers}"

    def test_failure_cleanup_handles_already_gone_tempfile(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """If the rename failure happens AFTER something else has
        already removed the tempfile, the ``except OSError: pass`` on
        line 341 swallows the second failure so the original
        exception still propagates."""
        target = tmp_path / "out" / "file.txt"
        target.parent.mkdir()

        # Make replace raise AND make unlink raise so we exercise the
        # nested-OSError path on line 341.
        def boom_replace(src, dst):
            raise RuntimeError("primary failure")

        def boom_unlink(p):
            raise OSError("secondary failure")

        monkeypatch.setattr(os, "replace", boom_replace)
        monkeypatch.setattr(os, "unlink", boom_unlink)
        with pytest.raises(RuntimeError, match="primary failure"):
            rla._atomic_write(target, "content")


# ---------------------------------------------------------------------------
# _build_catalog_dict
# ---------------------------------------------------------------------------


class TestBuildCatalogDict:
    def test_returns_documented_top_level_keys(self):
        out = rla._build_catalog_dict(
            data=[{"i": 1, "n": "Network"}],
            cat_meta={"1": {"icon": "fa-net"}},
            cat_groups={"infra": [1, 2]},
            equipment=[{"id": "cisco_ios"}],
            roadmap={"crawl": []},
            version="9.4.2",
            last_modified="1970-01-01T00:00:00Z",
        )
        assert out["version"] == "9.4.2"
        assert out["lastModified"] == "1970-01-01T00:00:00Z"
        assert out["DATA"][0]["n"] == "Network"
        assert out["CAT_META"]["1"]["icon"] == "fa-net"
        assert out["CAT_GROUPS"]["infra"] == [1, 2]
        assert out["EQUIPMENT"][0]["id"] == "cisco_ios"
        assert out["implementationRoadmap"]["crawl"] == []
        assert out["_readme"] == rla._CATALOG_README
        # Field map carries every key documented in docs/catalog-schema.md
        for k in ("i", "n", "c", "f", "v", "ge", "t", "d", "q", "qs", "m"):
            assert k in out["_field_map"]
        # Schema URL is the published GitHub Pages base + relative path
        assert out["_schema_url"].endswith("/docs/catalog-schema.md")
        assert out["_agents_url"].endswith("/AGENTS.md")
        assert out["_ai_policy_url"].endswith("/ai.txt")


# ---------------------------------------------------------------------------
# _write_llms_artefacts — global-shim save/restore
# ---------------------------------------------------------------------------


class _FakeEnrichment:
    """Drop-in replacement for the heavy ``build.enrichment`` module
    with the four globals/calls used by ``_write_llms_artefacts``."""

    def __init__(self):
        self.calls: list[tuple[str, tuple, dict]] = []
        self._original_state: dict[str, object] = {}

    def write_llms_txt(self, data, cat_meta, files, total_uc):
        self.calls.append(("write_llms_txt", (data, cat_meta, files, total_uc), {}))
        # Mimic the real writer: emit a small llms.txt at OUTPUT_LLMS_TXT
        Path(self.OUTPUT_LLMS_TXT).write_text(
            "fake llms.txt\n", encoding="utf-8"
        )

    def write_llms_full_txt(self, data, cat_meta, files, total_uc):
        self.calls.append(("write_llms_full_txt", (data, cat_meta, files, total_uc), {}))
        Path(self.OUTPUT_LLMS_FULL_TXT).write_text(
            "fake llms-full.txt\n", encoding="utf-8"
        )


class TestWriteLlmsArtefacts:
    def test_save_restore_round_trip_with_preexisting_globals(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """When the enrichment module already has the three OUTPUT_*
        globals defined, ``_write_llms_artefacts`` overwrites them,
        runs the writers, then restores the originals on the way out
        (covers lines 240-261)."""
        fake = _FakeEnrichment()
        fake.OUTPUT_LLMS_TXT = "original-llms-path"
        fake.OUTPUT_LLM_TXT = "original-llm-path"
        fake.OUTPUT_LLMS_FULL_TXT = "original-llms-full-path"
        monkeypatch.setattr(rla, "_enrichment", fake)

        rla._write_llms_artefacts(
            tmp_path, data=[], cat_meta={}, files=[], total_uc=0
        )
        # llms.txt + llms-full.txt landed
        assert (tmp_path / "llms.txt").read_text(encoding="utf-8") == "fake llms.txt\n"
        assert (tmp_path / "llms-full.txt").read_text(encoding="utf-8") == "fake llms-full.txt\n"
        # llm.txt is a copy of llms.txt (line 253)
        assert (tmp_path / "llm.txt").read_text(encoding="utf-8") == "fake llms.txt\n"
        # Both writers were invoked exactly once
        names = [c[0] for c in fake.calls]
        assert names == ["write_llms_txt", "write_llms_full_txt"]
        # Globals were restored to their pre-shim values (line 261)
        assert fake.OUTPUT_LLMS_TXT == "original-llms-path"
        assert fake.OUTPUT_LLM_TXT == "original-llm-path"
        assert fake.OUTPUT_LLMS_FULL_TXT == "original-llms-full-path"

    def test_globals_absent_before_shim_are_deleted_after(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """When the enrichment module does NOT pre-define an
        OUTPUT_* attribute (``getattr`` returns None on line 241), the
        shim must delete the attribute on the way out rather than
        leaving a leftover (covers lines 257-259)."""
        fake = _FakeEnrichment()
        monkeypatch.setattr(rla, "_enrichment", fake)
        assert not hasattr(fake, "OUTPUT_LLMS_TXT")
        rla._write_llms_artefacts(
            tmp_path, data=[], cat_meta={}, files=[], total_uc=0
        )
        # Attribute was set during the shim then removed in the finally.
        assert not hasattr(fake, "OUTPUT_LLMS_TXT")
        assert not hasattr(fake, "OUTPUT_LLM_TXT")
        assert not hasattr(fake, "OUTPUT_LLMS_FULL_TXT")

    def test_finally_skips_missing_attribute_in_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """If the writer itself removes one of the OUTPUT_* globals
        mid-call, the cleanup loop must skip the ``delattr`` instead
        of raising. Covers the false arm of the ``if hasattr(...)``
        guard on line 258."""

        class _SelfDeletingEnrichment:
            def write_llms_txt(self, *a, **k):
                # Pretend the writer removed the global it was given.
                del self.OUTPUT_LLMS_TXT

            def write_llms_full_txt(self, *a, **k):
                pass

        fake = _SelfDeletingEnrichment()
        monkeypatch.setattr(rla, "_enrichment", fake)
        # Should NOT raise even though the cleanup finds the attribute
        # already gone.
        rla._write_llms_artefacts(
            tmp_path, data=[], cat_meta={}, files=[], total_uc=0
        )
        assert not hasattr(fake, "OUTPUT_LLMS_TXT")

    def test_llm_copy_is_skipped_when_writer_does_not_emit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """If the writer fails to produce ``llms.txt`` for some
        reason, the ``shutil.copy2`` shouldn't fire (covers the false
        arm of ``if llms_path.exists():`` on line 252)."""

        class _NoOpEnrichment:
            def write_llms_txt(self, *a, **k):  # no-op — emits nothing
                pass

            def write_llms_full_txt(self, *a, **k):
                Path(self.OUTPUT_LLMS_FULL_TXT).write_text("ok", encoding="utf-8")

        fake = _NoOpEnrichment()
        monkeypatch.setattr(rla, "_enrichment", fake)
        rla._write_llms_artefacts(
            tmp_path, data=[], cat_meta={}, files=[], total_uc=0
        )
        assert not (tmp_path / "llms.txt").exists()
        assert not (tmp_path / "llm.txt").exists()
        assert (tmp_path / "llms-full.txt").read_text(encoding="utf-8") == "ok"


# ---------------------------------------------------------------------------
# render() end-to-end with a mocked enrichment module
# ---------------------------------------------------------------------------


class TestRender:
    def test_render_writes_all_five_artefacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """End-to-end smoke: ``render()`` emits ``catalog.json``,
        ``data.js``, ``llms.txt``, ``llm.txt``, and ``llms-full.txt``
        under ``out_dir``, with the correct top-level catalog shape
        and a populated ``DATA`` block."""

        class _StubEnrichment:
            SITE_BASE_URL = "https://example.test"

            def __init__(self):
                self.calls = []

            def compute_implementation_roadmap(self, data):
                self.calls.append(("compute_implementation_roadmap", data))
                return {"crawl": [], "walk": [], "run": []}

            def write_data_js(self, data, cat_meta, path, recently_added, roadmap):
                self.calls.append(("write_data_js", path))
                Path(path).write_text(
                    "window.DATA = []; window.CAT_META = {};", encoding="utf-8"
                )

            def write_llms_txt(self, data, cat_meta, files, total_uc):
                Path(self.OUTPUT_LLMS_TXT).write_text("llms\n", encoding="utf-8")

            def write_llms_full_txt(self, data, cat_meta, files, total_uc):
                Path(self.OUTPUT_LLMS_FULL_TXT).write_text(
                    "full\n", encoding="utf-8"
                )

        stub = _StubEnrichment()
        # ``render_legacy_artifacts`` references both
        # ``SITE_BASE_URL`` (set at import time) and ``_enrichment``
        # (the module reference). Patch both for hermetic test.
        monkeypatch.setattr(rla, "_enrichment", stub)
        monkeypatch.setattr(rla, "SITE_BASE_URL", stub.SITE_BASE_URL)

        cat = _empty_catalog(
            tmp_path,
            categories=[
                {"i": 1, "n": "Network", "s": [{"i": "1.1", "u": [{"i": "1.1.1"}]}]},
            ],
            cat_meta={"1": {"icon": "fa-net"}},
        )
        out_dir = tmp_path / "dist"
        rla.render(cat, out_dir, reproducible=True)

        # All five files landed
        for name in ("catalog.json", "data.js", "llms.txt", "llm.txt", "llms-full.txt"):
            assert (out_dir / name).exists(), f"missing {name}"

        # catalog.json is valid JSON with the documented shape
        catalog = json.loads((out_dir / "catalog.json").read_text(encoding="utf-8"))
        assert catalog["DATA"][0]["i"] == 1
        assert catalog["CAT_META"]["1"]["icon"] == "fa-net"
        assert catalog["lastModified"] == "1970-01-01T00:00:00Z"
        # Stub enrichment computed the roadmap exactly once.
        assert any(c[0] == "compute_implementation_roadmap" for c in stub.calls)
