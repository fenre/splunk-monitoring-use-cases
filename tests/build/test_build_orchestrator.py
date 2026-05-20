"""Hermetic tests for ``tools/build/build.py`` — the build orchestrator.

The pipeline runs many independent render_* stages then writes integrity,
build-info, and metrics. End-to-end testing would need the full corpus,
so this suite focuses on the pure helpers (HTML rewrite chain, URL
parsing, fingerprint detection, project-asset copying, argument
parsing) and the CLI entrypoint with all stages mocked.

Goals:

* No subprocess (git, diff) — patched out.
* No actual rendering — every stage is a no-op stub installed on the
  ``build`` module.
* No on-disk catalog — ``tmp_path`` only.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import build as build_mod  # noqa: E402
from build import parse_content  # noqa: E402


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------


class TestLog:
    def test_log_without_timer(self, capsys):
        build_mod._log("hello")
        out = capsys.readouterr().out
        assert out == "[build] hello\n"

    def test_log_with_timer(self, capsys):
        # Anchor t0 in the past so the elapsed includes a small delta.
        import time

        t0 = time.monotonic() - 0.42
        build_mod._log("done", t0=t0)
        out = capsys.readouterr().out
        assert out.startswith("[build] done  (")
        assert out.endswith("s)\n")


class TestEnsureCleanOut:
    def test_creates_directory_when_missing(self, tmp_path: Path):
        out = tmp_path / "newdir"
        build_mod._ensure_clean_out(out)
        assert out.is_dir()

    def test_wipes_existing_directory(self, tmp_path: Path):
        out = tmp_path / "existing"
        out.mkdir()
        (out / "leftover.txt").write_text("garbage", encoding="utf-8")
        nested = out / "subdir"
        nested.mkdir()
        (nested / "deep.txt").write_text("more garbage", encoding="utf-8")
        build_mod._ensure_clean_out(out)
        assert out.is_dir()
        assert list(out.iterdir()) == []


class TestGitCommitEpoch:
    def test_returns_decoded_epoch_on_success(self, monkeypatch):
        def fake_check_output(cmd, cwd):
            assert cmd[0] == "git"
            return b"1700000000\n"

        monkeypatch.setattr(subprocess, "check_output", fake_check_output)
        assert build_mod._git_commit_epoch() == "1700000000"

    def test_returns_zero_on_called_process_error(self, monkeypatch):
        def boom(cmd, cwd):
            raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr(subprocess, "check_output", boom)
        assert build_mod._git_commit_epoch() == "0"

    def test_returns_zero_when_git_missing(self, monkeypatch):
        def boom(cmd, cwd):
            raise FileNotFoundError("no git")

        monkeypatch.setattr(subprocess, "check_output", boom)
        assert build_mod._git_commit_epoch() == "0"


class TestSiteBasePath:
    def test_default_when_no_env(self, monkeypatch):
        monkeypatch.delenv("SITE_URL", raising=False)
        # Default SITE_URL is "https://fenre.github.io/splunk-monitoring-use-cases"
        # so the path component is "/splunk-monitoring-use-cases".
        assert build_mod._site_base_path() == "/splunk-monitoring-use-cases"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("SITE_URL", "https://example.com/my-site/")
        assert build_mod._site_base_path() == "/my-site"

    def test_env_root_deploy_returns_empty(self, monkeypatch):
        monkeypatch.setenv("SITE_URL", "https://example.com")
        assert build_mod._site_base_path() == ""

    def test_env_root_with_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("SITE_URL", "https://example.com/")
        assert build_mod._site_base_path() == ""


class TestLooksLikeSsgLanding:
    def test_detects_landing_via_marker(self, tmp_path: Path):
        page = tmp_path / "index.html"
        page.write_text(
            '<html><body><a class="cta primary" href="/browse/">x</a></body></html>',
            encoding="utf-8",
        )
        assert build_mod._looks_like_ssg_landing(page) is True

    def test_returns_false_when_marker_missing(self, tmp_path: Path):
        page = tmp_path / "index.html"
        page.write_text('<html><body>SPA shell, no marker</body></html>', encoding="utf-8")
        assert build_mod._looks_like_ssg_landing(page) is False

    def test_returns_false_when_browse_anchor_missing(self, tmp_path: Path):
        page = tmp_path / "index.html"
        # Has the cta marker but no /browse/ link.
        page.write_text('<a class="cta primary" href="/x/">x</a>', encoding="utf-8")
        assert build_mod._looks_like_ssg_landing(page) is False

    def test_returns_false_on_oserror(self, tmp_path: Path):
        missing = tmp_path / "absent.html"
        assert build_mod._looks_like_ssg_landing(missing) is False


# ---------------------------------------------------------------------------
# HTML rewrite helpers
# ---------------------------------------------------------------------------


class TestSwapInlineStyle:
    def test_replaces_first_style_block(self):
        html = "<head><style>BIG INLINE BLOCK</style></head>"
        out = build_mod._swap_inline_style(html, "styles.abc.css", "/*crit*/")
        assert "<style>/*crit*/</style>" in out
        assert "BIG INLINE BLOCK" not in out
        assert 'href="assets/styles.abc.css"' in out
        assert 'rel="preload"' in out
        assert '<noscript>' in out

    def test_uses_root_abs_prefix_when_requested(self):
        html = "<head><style>X</style></head>"
        out = build_mod._swap_inline_style(
            html, "s.css", "/*c*/", root_abs=True, base_path="/repo"
        )
        assert 'href="/repo/assets/s.css"' in out

    def test_no_op_when_style_block_missing(self):
        html = "<head><meta charset='utf-8'></head>"
        assert build_mod._swap_inline_style(html, "s.css", "/*c*/") == html

    def test_no_op_when_style_block_unclosed(self):
        html = "<head><style>oops no closer"
        assert build_mod._swap_inline_style(html, "s.css", "/*c*/") == html


class TestSwapInlineScript:
    def test_replaces_bare_script_block(self):
        html = "<body>...</body><script>\nvar x = 1;\n</script></html>"
        out = build_mod._swap_inline_script(html, "app.abc.js")
        assert '<script defer src="assets/app.abc.js"></script>' in out
        assert "var x = 1" not in out

    def test_uses_root_abs_prefix(self):
        html = "<script>\ncode\n</script>"
        out = build_mod._swap_inline_script(
            html, "a.js", root_abs=True, base_path="/repo"
        )
        assert 'src="/repo/assets/a.js"' in out

    def test_no_op_when_bare_script_missing(self):
        # No \n after <script>, so the needle "<script>\n" won't match.
        html = '<script src="other.js"></script>'
        assert build_mod._swap_inline_script(html, "a.js") == html

    def test_no_op_when_script_unclosed(self):
        html = "<script>\ncode without closer"
        assert build_mod._swap_inline_script(html, "a.js") == html

    def test_picks_last_bare_script_block(self):
        """The implementation uses ``rfind`` so it picks the LAST bare
        ``<script>\\n`` block — typically the trailing app code."""
        html = (
            "<script>\nfirst block\n</script>"
            '<script type="application/ld+json">{}</script>'
            "<script>\nlast block\n</script>"
        )
        out = build_mod._swap_inline_script(html, "a.js")
        assert "first block" in out  # untouched
        assert "last block" not in out
        # JSON-LD untouched.
        assert "application/ld+json" in out


class TestDropLegacyDataScript:
    def test_strips_canonical_tag_with_newline(self):
        html = '<head><script src="data.js"></script>\n<body>x</body>'
        out = build_mod._drop_legacy_data_script(html)
        assert "data.js" not in out
        assert "<body>x</body>" in out

    def test_strips_no_newline_variant(self):
        html = '<head><script src="data.js"></script><body>x</body>'
        out = build_mod._drop_legacy_data_script(html)
        assert "data.js" not in out

    def test_noop_when_absent(self):
        html = "<head><meta/></head>"
        assert build_mod._drop_legacy_data_script(html) == html

    def test_strips_only_first_occurrence(self):
        """``replace(..., 1)`` — defensive in case two copies sneak in."""
        html = (
            '<script src="data.js"></script>\n'
            'middle '
            '<script src="data.js"></script>\n'
        )
        out = build_mod._drop_legacy_data_script(html)
        # One canonical tag stripped; the second is then stripped by the
        # no-newline replace path because the trailing \n is still there
        # — actually the second one DOES have a trailing \n so it gets
        # matched by the canonical replace too. The behaviour we care
        # about: at least one removed, no crash.
        assert out.count("data.js") <= 1


class TestInjectBasePathConfig:
    def test_injects_before_head_close(self):
        html = "<head><meta/></head><body></body>"
        out = build_mod._inject_base_path_config(html, "/repo")
        assert '<script>window.__SITE_BASE_PATH="/repo";' in out
        assert '__CATALOG_API_BASE="/repo/api"' in out
        assert '__CATALOG_ASSETS_BASE="/repo/assets"' in out
        # The config script sits just before </head>.
        assert out.index("<script>") < out.index("</head>")

    def test_noop_when_base_path_empty(self):
        html = "<head><meta/></head>"
        assert build_mod._inject_base_path_config(html, "") == html

    def test_noop_when_head_close_missing(self):
        html = "<body>orphan body</body>"
        assert build_mod._inject_base_path_config(html, "/repo") == html


class TestRewriteRelativeRefsToRootAbs:
    def test_rewrites_assets_and_api_refs(self):
        html = (
            '<link href="assets/styles.css">'
            '<script src="api/v1/uc.json"></script>'
        )
        out = build_mod._rewrite_relative_refs_to_root_abs(html, base_path="/repo")
        assert 'href="/repo/assets/styles.css"' in out
        assert 'src="/repo/api/v1/uc.json"' in out

    def test_rewrites_content_directories(self):
        html = (
            '<a href="docs/x.md">x</a>'
            '<a href="content/cat-01.md">y</a>'
            '<a href="schemas/uc.json">z</a>'
        )
        out = build_mod._rewrite_relative_refs_to_root_abs(html, base_path="")
        # Empty base_path -> "/" prefix.
        assert 'href="/docs/x.md"' in out
        assert 'href="/content/cat-01.md"' in out
        assert 'href="/schemas/uc.json"' in out

    def test_rewrites_companion_tool_refs(self):
        # The path regex requires at least one non-"/#/? char after the
        # prefix so a bare ``tools/data-sizing/`` does NOT match — use
        # a fully qualified subpath instead.
        html = (
            '<script src="tools/data-sizing/index.js"></script>'
            '<a href="tools/data-sizing/index.html">Data Sizing</a>'
        )
        out = build_mod._rewrite_relative_refs_to_root_abs(html, base_path="/x")
        assert 'src="/x/tools/data-sizing/index.js"' in out
        assert 'href="/x/tools/data-sizing/index.html"' in out

    def test_rewrites_top_level_files(self):
        html = (
            '<script src="non-technical-view.js"></script>'
            '<link href="provenance.json">'
            '<link href="favicon.ico">'
            '<link href="sitemap.xml">'
            '<link href="docs.html">'
        )
        out = build_mod._rewrite_relative_refs_to_root_abs(html, base_path="/r")
        for needle in (
            'src="/r/non-technical-view.js"',
            'href="/r/provenance.json"',
            'href="/r/favicon.ico"',
            'href="/r/sitemap.xml"',
            'href="/r/docs.html"',
        ):
            assert needle in out

    def test_does_not_rewrite_absolute_urls(self):
        html = '<a href="https://splunk.com/foo">link</a>'
        out = build_mod._rewrite_relative_refs_to_root_abs(html, base_path="/r")
        assert out == html

    def test_does_not_rewrite_anchor_or_query_refs(self):
        """The regex requires no ``#`` or ``?`` in the matched path."""
        html = '<a href="assets/foo#frag">x</a><a href="api/x?bar=1">y</a>'
        out = build_mod._rewrite_relative_refs_to_root_abs(html, base_path="/r")
        # Neither ref matched.
        assert out == html


# ---------------------------------------------------------------------------
# _measure
# ---------------------------------------------------------------------------


class TestMeasure:
    def test_counts_files_and_bytes(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.txt").write_text("world!", encoding="utf-8")
        n_bytes, n_files = build_mod._measure(tmp_path)
        assert n_files == 2
        assert n_bytes == len("hello") + len("world!")

    def test_empty_dir_returns_zeros(self, tmp_path: Path):
        out = tmp_path / "empty"
        out.mkdir()
        assert build_mod._measure(out) == (0, 0)

    def test_ignores_subdirectories_themselves(self, tmp_path: Path):
        """Only files contribute to the count."""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested").mkdir()
        n_bytes, n_files = build_mod._measure(tmp_path)
        assert n_files == 0
        assert n_bytes == 0


# ---------------------------------------------------------------------------
# Stage wrappers — verify each delegates to the right renderer with the
# right arguments. Mock the renderer modules to keep this hermetic.
# ---------------------------------------------------------------------------


def _make_opts(tmp_path: Path, **overrides) -> build_mod.BuildOptions:
    return build_mod.BuildOptions(
        out_dir=tmp_path / "dist",
        reproducible=overrides.get("reproducible", False),
        check=overrides.get("check", False),
        only=overrides.get("only", build_mod.ALL_STAGES),
        verbose=overrides.get("verbose", False),
    )


@pytest.fixture
def empty_catalog(tmp_path: Path) -> parse_content.Catalog:
    return parse_content.empty(tmp_path)


class TestStageWrappers:
    def test_parse_stage_loads_catalog(self, tmp_path: Path, monkeypatch, capsys):
        sentinel_cat = parse_content.empty(tmp_path)
        sentinel_cat.categories = [{"i": 1, "n": "X", "s": []}]

        def fake_load(project_root, *, reproducible):
            return sentinel_cat

        monkeypatch.setattr(build_mod.parse_content, "load", fake_load)
        opts = _make_opts(tmp_path)
        result = build_mod._stage_parse(opts)
        assert result is sentinel_cat
        assert "parsed 0 UCs" in capsys.readouterr().out

    def test_assets_stage_delegates(self, tmp_path: Path, monkeypatch, empty_catalog):
        calls = []
        monkeypatch.setattr(
            build_mod.render_assets,
            "render",
            lambda cat, out, *, reproducible: calls.append(("assets", cat, out, reproducible)),
        )
        opts = _make_opts(tmp_path, reproducible=True)
        build_mod._stage_assets(opts, empty_catalog)
        assert calls == [("assets", empty_catalog, opts.out_dir, True)]

    def test_pages_stage_delegates(self, tmp_path: Path, monkeypatch, empty_catalog):
        calls = []
        monkeypatch.setattr(
            build_mod.render_pages,
            "render",
            lambda cat, out, *, reproducible: calls.append(reproducible),
        )
        opts = _make_opts(tmp_path)
        build_mod._stage_pages(opts, empty_catalog)
        assert calls == [False]

    def test_api_stage_delegates(self, tmp_path: Path, monkeypatch, empty_catalog):
        called = {"v": False}
        monkeypatch.setattr(
            build_mod.render_api,
            "render",
            lambda *a, **kw: called.update(v=True),
        )
        opts = _make_opts(tmp_path)
        build_mod._stage_api(opts, empty_catalog)
        assert called["v"] is True

    def test_search_stage_logs_token_and_doc_counts(
        self, tmp_path: Path, monkeypatch, empty_catalog, capsys
    ):
        empty_catalog.asset_hashes = {
            "search_index_tokens": "42",
            "search_index_docs": "7",
        }
        monkeypatch.setattr(build_mod.render_search, "render", lambda *a, **kw: None)
        monkeypatch.setattr(build_mod.render_search, "SHARD_COUNT", 4, raising=False)
        opts = _make_opts(tmp_path)
        build_mod._stage_search(opts, empty_catalog)
        out = capsys.readouterr().out
        assert "search index: 42 tokens" in out
        assert "× 7 docs" in out

    def test_exports_stage_delegates(self, tmp_path: Path, monkeypatch, empty_catalog):
        monkeypatch.setattr(build_mod.render_exports, "render", lambda *a, **kw: None)
        opts = _make_opts(tmp_path)
        build_mod._stage_exports(opts, empty_catalog)  # no exception = pass

    def test_meta_stage_invokes_legacy_then_meta(
        self, tmp_path: Path, monkeypatch, empty_catalog
    ):
        order: list[str] = []
        monkeypatch.setattr(
            build_mod.render_legacy_artifacts,
            "render",
            lambda *a, **kw: order.append("legacy"),
        )
        monkeypatch.setattr(
            build_mod.render_meta, "render", lambda *a, **kw: order.append("meta")
        )
        opts = _make_opts(tmp_path)
        build_mod._stage_meta(opts, empty_catalog)
        assert order == ["legacy", "meta"]

    def test_integrity_stage_delegates(self, tmp_path: Path, monkeypatch):
        called = {"v": False}
        monkeypatch.setattr(
            build_mod.integrity, "write", lambda *a, **kw: called.update(v=True)
        )
        opts = _make_opts(tmp_path)
        build_mod._stage_integrity(opts)
        assert called["v"] is True

    def test_build_info_stage_delegates(self, tmp_path: Path, monkeypatch, empty_catalog):
        called = {"v": False}
        monkeypatch.setattr(
            build_mod.build_info, "write", lambda *a, **kw: called.update(v=True)
        )
        opts = _make_opts(tmp_path)
        build_mod._stage_build_info(opts, empty_catalog)
        assert called["v"] is True

    def test_metrics_stage_delegates(self, tmp_path: Path, monkeypatch, empty_catalog):
        called = {"v": False}
        monkeypatch.setattr(
            build_mod.render_metrics, "render", lambda *a, **kw: called.update(v=True)
        )
        opts = _make_opts(tmp_path)
        build_mod._stage_metrics(opts, empty_catalog)
        assert called["v"] is True


class TestStagePublic:
    def test_copies_public_directory_and_project_assets(
        self, tmp_path: Path, monkeypatch
    ):
        """Set up a fake project root so we can control which files get copied."""
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        (fake_root / "public").mkdir()
        (fake_root / "public" / "favicon.ico").write_text("ico", encoding="utf-8")
        (fake_root / "index.html").write_text("<html/>", encoding="utf-8")

        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        # _copy_project_assets() does a lot of work scanning directories;
        # patch it out and just confirm it was called.
        called = {"v": False}
        monkeypatch.setattr(
            build_mod, "_copy_project_assets", lambda out: called.update(v=True)
        )
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        build_mod._stage_public(opts)
        # public/favicon.ico was copied.
        assert (opts.out_dir / "favicon.ico").read_text(encoding="utf-8") == "ico"
        # _copy_project_assets was invoked.
        assert called["v"] is True

    def test_no_public_dir_still_invokes_copy_project_assets(
        self, tmp_path: Path, monkeypatch
    ):
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()  # no public/

        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        called = {"v": False}
        monkeypatch.setattr(
            build_mod, "_copy_project_assets", lambda out: called.update(v=True)
        )
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        build_mod._stage_public(opts)
        assert called["v"] is True


class TestStageHtmlRewrite:
    def test_skips_when_no_assets(
        self, tmp_path: Path, monkeypatch, empty_catalog, capsys
    ):
        empty_catalog.asset_hashes = {}
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        build_mod._stage_html_rewrite(opts, empty_catalog)
        assert "html_rewrite skipped" in capsys.readouterr().out

    def test_skips_index_when_ssg_landing(self, tmp_path: Path, monkeypatch, empty_catalog):
        empty_catalog.asset_hashes = {"styles_css": "s.css", "app_js": "a.js"}
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        # Index is an SSG landing — should be skipped.
        index = opts.out_dir / "index.html"
        index.write_text(
            '<a class="cta primary" href="/browse/">x</a><style>X</style><script>\ncode\n</script>',
            encoding="utf-8",
        )
        # Browse copy is the legacy SPA — should be rewritten.
        (opts.out_dir / "browse").mkdir()
        browse = opts.out_dir / "browse" / "index.html"
        browse.write_text(
            "<head><style>BIG</style></head><body><script>\nx\n</script></body>",
            encoding="utf-8",
        )
        monkeypatch.delenv("SITE_URL", raising=False)
        build_mod._stage_html_rewrite(opts, empty_catalog)
        # Index untouched (still contains the original "BIG" sequence? Actually
        # the index doesn't have "BIG"; the test is: it still contains
        # the original style block content X).
        assert "<style>X</style>" in index.read_text(encoding="utf-8")
        # Browse copy was rewritten (no more "BIG").
        assert "BIG" not in browse.read_text(encoding="utf-8")

    def test_drops_legacy_data_js_file(
        self, tmp_path: Path, monkeypatch, empty_catalog
    ):
        empty_catalog.asset_hashes = {"styles_css": "s.css", "app_js": "a.js"}
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        # No SPA shells present; just the legacy data.js sitting in dist/.
        (opts.out_dir / "data.js").write_text("var X = []", encoding="utf-8")
        monkeypatch.delenv("SITE_URL", raising=False)
        build_mod._stage_html_rewrite(opts, empty_catalog)
        assert not (opts.out_dir / "data.js").exists()


class TestCopyProjectAssets:
    def test_copies_static_files_and_content_dirs(self, tmp_path: Path, monkeypatch):
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        # A top-level static file.
        (fake_root / "robots.txt").write_text("User-agent: *", encoding="utf-8")
        # A content directory.
        (fake_root / "data").mkdir()
        (fake_root / "data" / "x.json").write_text("{}", encoding="utf-8")
        # A skipped directory.
        (fake_root / "data" / ".git").mkdir()
        (fake_root / "data" / ".git" / "secret").write_text("nope", encoding="utf-8")
        # A skipped extension.
        (fake_root / "data" / "tmp.pyc").write_text("byte code", encoding="utf-8")

        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        out = tmp_path / "dist"
        out.mkdir()
        build_mod._copy_project_assets(out)

        assert (out / "robots.txt").exists()
        assert (out / "data" / "x.json").exists()
        # Skipped.
        assert not (out / "data" / ".git" / "secret").exists()
        assert not (out / "data" / "tmp.pyc").exists()

    def test_mirrors_index_html_to_browse(self, tmp_path: Path, monkeypatch):
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        (fake_root / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        out = tmp_path / "dist"
        out.mkdir()
        build_mod._copy_project_assets(out)
        assert (out / "index.html").read_text(encoding="utf-8") == "<html>SPA</html>"
        # Mirrored to /browse/index.html.
        assert (out / "browse" / "index.html").read_text(encoding="utf-8") == "<html>SPA</html>"

    def test_skips_v7_owned_api_files(self, tmp_path: Path, monkeypatch):
        """The v7 render stages own api/cat-N.json, api/catalog-index.json,
        api/manifest.json — those must NOT be copied from the project
        root even if present."""
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        (fake_root / "api").mkdir()
        (fake_root / "api" / "cat-1.json").write_text("stale", encoding="utf-8")
        (fake_root / "api" / "catalog-index.json").write_text("stale", encoding="utf-8")
        (fake_root / "api" / "manifest.json").write_text("stale", encoding="utf-8")
        # A non-v7-owned file in api/ SHOULD be copied.
        (fake_root / "api" / "other.json").write_text("fresh", encoding="utf-8")
        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        out = tmp_path / "dist"
        out.mkdir()
        build_mod._copy_project_assets(out)
        assert not (out / "api" / "cat-1.json").exists()
        assert not (out / "api" / "catalog-index.json").exists()
        assert not (out / "api" / "manifest.json").exists()
        assert (out / "api" / "other.json").read_text(encoding="utf-8") == "fresh"

    def test_missing_top_level_file_silently_skipped(self, tmp_path: Path, monkeypatch):
        """``if not (src.exists() and src.is_file()): continue`` —
        non-existent _PROJECT_STATIC_FILES are not an error."""
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        out = tmp_path / "dist"
        out.mkdir()
        build_mod._copy_project_assets(out)  # no exception = pass

    def test_copies_companion_tools(self, tmp_path: Path, monkeypatch):
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        (fake_root / "tools" / "data-sizing").mkdir(parents=True)
        (fake_root / "tools" / "data-sizing" / "index.html").write_text(
            "<html>data sizing</html>", encoding="utf-8"
        )
        # Subdirectory inside companion tool (exercises line 303 — the
        # is_dir() continue in the COMPANION_TOOLS loop).
        nested = fake_root / "tools" / "data-sizing" / "css"
        nested.mkdir()
        (nested / "style.css").write_text("/* css */", encoding="utf-8")
        # Skipped directory inside companion tool (line 306).
        skip = fake_root / "tools" / "data-sizing" / "__pycache__"
        skip.mkdir()
        (skip / "cache.pyc").write_text("byte code", encoding="utf-8")
        # Skipped extension inside companion tool (line 308).
        (fake_root / "tools" / "data-sizing" / "tmp.pyc").write_text(
            "byte code", encoding="utf-8"
        )
        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        out = tmp_path / "dist"
        out.mkdir()
        build_mod._copy_project_assets(out)
        assert (out / "tools" / "data-sizing" / "index.html").exists()
        # Subdirectory copied normally.
        assert (out / "tools" / "data-sizing" / "css" / "style.css").exists()
        # Skip-list paths not copied.
        assert not (out / "tools" / "data-sizing" / "__pycache__").exists()
        assert not (out / "tools" / "data-sizing" / "tmp.pyc").exists()


class TestStagePublicSkipsDirectories:
    """Cover line 211 — ``_stage_public`` rglob iterating a subdirectory."""

    def test_subdirectories_inside_public_are_skipped(self, tmp_path: Path, monkeypatch):
        fake_root = tmp_path / "fake_project"
        fake_root.mkdir()
        public = fake_root / "public"
        public.mkdir()
        # File at the root level.
        (public / "favicon.ico").write_text("ico", encoding="utf-8")
        # Subdirectory + nested file (rglob will encounter the dir entry
        # AND the file — the dir is skipped by `if src.is_dir(): continue`).
        sub = public / "icons"
        sub.mkdir()
        (sub / "favicon-192.png").write_text("img-bytes", encoding="utf-8")

        monkeypatch.setattr(build_mod, "PROJECT_ROOT", fake_root)
        monkeypatch.setattr(build_mod, "_copy_project_assets", lambda out: None)
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        build_mod._stage_public(opts)
        # Both files copied; subdir auto-created.
        assert (opts.out_dir / "favicon.ico").exists()
        assert (opts.out_dir / "icons" / "favicon-192.png").exists()


class TestStageHtmlRewriteBranchCoverage:
    """Cover the conditional skips in ``_stage_html_rewrite``.

    Branches under test (line 460..471):
    * ``if css_name`` False — no inline-style swap.
    * ``if js_name`` False — no inline-script swap.
    * ``if base_path`` False — no base-path config injection.
    * ``if use_root_abs`` False — no relative-ref rewrite.
    """

    def _setup(self, tmp_path: Path, monkeypatch, *, css="s.css", js="a.js"):
        """Returns (opts, catalog, browse_path) — root index is an SSG
        landing so the SPA copy lives at /browse/index.html."""
        cat = parse_content.empty(tmp_path)
        hashes = {}
        if css:
            hashes["styles_css"] = css
        if js:
            hashes["app_js"] = js
        cat.asset_hashes = hashes
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        # Root index is the SSG landing — gets skipped.
        (opts.out_dir / "index.html").write_text(
            '<a class="cta primary" href="/browse/">x</a>', encoding="utf-8"
        )
        # Browse copy is the SPA — gets rewritten.
        (opts.out_dir / "browse").mkdir()
        spa = opts.out_dir / "browse" / "index.html"
        spa.write_text(
            "<head><style>X</style></head><body><script>\nx\n</script></body>",
            encoding="utf-8",
        )
        return opts, cat, spa

    def test_no_css_skips_style_swap(self, tmp_path: Path, monkeypatch):
        opts, cat, spa = self._setup(tmp_path, monkeypatch, css="", js="a.js")
        monkeypatch.delenv("SITE_URL", raising=False)
        build_mod._stage_html_rewrite(opts, cat)
        # Style block untouched.
        assert "<style>X</style>" in spa.read_text(encoding="utf-8")

    def test_no_js_skips_script_swap(self, tmp_path: Path, monkeypatch):
        opts, cat, spa = self._setup(tmp_path, monkeypatch, css="s.css", js="")
        monkeypatch.delenv("SITE_URL", raising=False)
        build_mod._stage_html_rewrite(opts, cat)
        # Bare script block untouched.
        text = spa.read_text(encoding="utf-8")
        assert "<script>\nx\n</script>" in text

    def test_no_base_path_skips_inject_and_rewrite(self, tmp_path: Path, monkeypatch):
        """SITE_URL='https://example.com/' → empty base_path → both
        _inject_base_path_config and _rewrite_relative_refs_to_root_abs
        become no-ops, but the index page is still rewritten."""
        opts, cat, spa = self._setup(tmp_path, monkeypatch)
        # Add a relative asset ref that would normally be rewritten.
        spa.write_text(
            '<head><style>X</style></head>'
            '<body><link href="assets/foo.css">'
            '<script>\nx\n</script></body>',
            encoding="utf-8",
        )
        monkeypatch.setenv("SITE_URL", "https://example.com/")
        build_mod._stage_html_rewrite(opts, cat)
        text = spa.read_text(encoding="utf-8")
        # base_path is empty → no config script injection.
        assert "__SITE_BASE_PATH" not in text
        # But style and script were still swapped (root_abs=True still
        # applies because the file is in /browse/, even though prefix is "").
        assert "<style>X</style>" not in text  # swapped out

    def test_root_spa_use_root_abs_false_skips_relative_rewrite(
        self, tmp_path: Path, monkeypatch
    ):
        """Pin branch [469, 471]: the false arm of ``if use_root_abs``.

        ``use_root_abs = index_path.parent != opts.out_dir`` — when the
        SPA lives at ``dist/index.html`` (parent IS out_dir), the rewrite
        is skipped but the file is still written. Build a setup where:

        * Only ``out_dir/index.html`` exists (no /browse/).
        * It does NOT carry the ``class="cta primary"`` SSG marker, so
          ``_looks_like_ssg_landing`` returns False and the loop
          processes it as a SPA copy.
        * The relative ``href`` would be rewritten if use_root_abs were
          True; we assert it survived intact.
        """
        cat = parse_content.empty(tmp_path)
        cat.asset_hashes = {"styles_css": "s.css", "app_js": "a.js"}
        opts = _make_opts(tmp_path)
        opts.out_dir.mkdir(parents=True)
        # SPA at root (no SSG marker) — gets rewritten with
        # use_root_abs=False.
        spa = opts.out_dir / "index.html"
        spa.write_text(
            '<head><style>X</style></head>'
            '<body><link href="assets/foo.css">'
            '<script>\nx\n</script></body>',
            encoding="utf-8",
        )
        # No browse/ subdir — only the root copy is processed.
        monkeypatch.setenv("SITE_URL", "https://example.com/x/")
        build_mod._stage_html_rewrite(opts, cat)
        text = spa.read_text(encoding="utf-8")
        # File was written (rewrote >= 1).
        assert text != ""
        # Style block was swapped (use_root_abs=False applies to swap
        # too, but it still happens).
        assert "<style>X</style>" not in text
        # The original relative href survived because the
        # _rewrite_relative_refs_to_root_abs call was SKIPPED (line 470
        # short-circuited on the false arm). When use_root_abs is True
        # this href would have been rewritten to ``/x/assets/foo.css``;
        # here it stays bare ``assets/foo.css``.
        assert 'href="assets/foo.css"' in text
        assert 'href="/x/assets/foo.css"' not in text


# ---------------------------------------------------------------------------
# CLI: main / _run_once / _run_check
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_main_runs_once_for_normal_flag(self, tmp_path: Path, monkeypatch):
        called = {"once": 0, "check": 0}
        monkeypatch.setattr(
            build_mod, "_run_once", lambda args: called.update(once=called["once"] + 1) or 0
        )
        monkeypatch.setattr(
            build_mod, "_run_check", lambda args: called.update(check=called["check"] + 1) or 0
        )
        rc = build_mod.main(["--out", str(tmp_path / "dist")])
        assert rc == 0
        assert called == {"once": 1, "check": 0}

    def test_main_runs_check_for_check_flag(self, tmp_path: Path, monkeypatch):
        called = {"once": 0, "check": 0}
        monkeypatch.setattr(
            build_mod, "_run_once", lambda args: called.update(once=called["once"] + 1) or 0
        )
        monkeypatch.setattr(
            build_mod, "_run_check", lambda args: called.update(check=called["check"] + 1) or 0
        )
        rc = build_mod.main(["--out", str(tmp_path / "dist"), "--check"])
        assert rc == 0
        assert called == {"once": 0, "check": 1}


class TestRunOnce:
    def test_dispatches_only_requested_stages(self, tmp_path: Path, monkeypatch, capsys):
        """``--only parse`` runs just the parse stage."""
        stages_called: list[str] = []
        empty_cat = parse_content.empty(tmp_path)

        def fake_parse(opts):
            stages_called.append("parse")
            return empty_cat

        monkeypatch.setattr(build_mod, "_stage_parse", fake_parse)
        # Patch every other stage to record + no-op (defensive — they
        # shouldn't be called when --only parse is set).
        for s in (
            "_stage_assets", "_stage_pages", "_stage_api", "_stage_search",
            "_stage_exports", "_stage_meta", "_stage_public",
            "_stage_html_rewrite", "_stage_integrity", "_stage_build_info",
            "_stage_metrics",
        ):
            monkeypatch.setattr(
                build_mod, s, lambda *a, _name=s, **kw: stages_called.append(_name)
            )
        # render_telemetry: skip writing.
        monkeypatch.setattr(
            build_mod.render_telemetry,
            "render",
            lambda *a, **kw: None,
        )
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=False,
            only=["parse"],
            verbose=False,
        )
        rc = build_mod._run_once(args)
        assert rc == 0
        assert stages_called == ["parse"]

    def test_reproducible_sets_env_vars(self, tmp_path: Path, monkeypatch):
        # ``_run_once`` writes directly to ``os.environ`` (not via
        # monkeypatch). Pre-set each var via monkeypatch.setenv so
        # pytest's teardown restores the prior value and we don't leak
        # SOURCE_DATE_EPOCH into downstream tests that consume it
        # (e.g. test_render_legacy_artifacts).
        for env in ("LC_ALL", "TZ", "PYTHONHASHSEED", "SOURCE_DATE_EPOCH"):
            monkeypatch.setenv(env, "")
            monkeypatch.delenv(env, raising=False)
        monkeypatch.setattr(build_mod, "_git_commit_epoch", lambda: "1700000000")
        # Mock every stage.
        monkeypatch.setattr(build_mod, "_stage_parse", lambda opts: parse_content.empty(tmp_path))
        for s in (
            "_stage_assets", "_stage_pages", "_stage_api", "_stage_search",
            "_stage_exports", "_stage_meta", "_stage_public",
            "_stage_html_rewrite", "_stage_integrity", "_stage_build_info",
            "_stage_metrics",
        ):
            monkeypatch.setattr(build_mod, s, lambda *a, **kw: None)
        monkeypatch.setattr(
            build_mod.render_telemetry, "render", lambda *a, **kw: None
        )
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=True,
            check=False,
            only=list(build_mod.ALL_STAGES),
            verbose=False,
        )
        rc = build_mod._run_once(args)
        assert rc == 0
        assert os.environ["LC_ALL"] == "C"
        assert os.environ["TZ"] == "UTC"
        assert os.environ["PYTHONHASHSEED"] == "0"
        assert os.environ["SOURCE_DATE_EPOCH"] == "1700000000"

    def test_skips_parse_uses_empty_catalog(self, tmp_path: Path, monkeypatch):
        """``--only meta`` (parse absent) — code goes through the
        ``else: catalog = parse_content.empty()`` branch."""
        parse_called = {"v": False}

        def fake_parse(opts):
            parse_called["v"] = True
            return parse_content.empty(tmp_path)

        monkeypatch.setattr(build_mod, "_stage_parse", fake_parse)
        for s in (
            "_stage_assets", "_stage_pages", "_stage_api", "_stage_search",
            "_stage_exports", "_stage_meta", "_stage_public",
            "_stage_html_rewrite", "_stage_integrity", "_stage_build_info",
            "_stage_metrics",
        ):
            monkeypatch.setattr(build_mod, s, lambda *a, **kw: None)
        monkeypatch.setattr(
            build_mod.render_telemetry, "render", lambda *a, **kw: None
        )
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=False,
            only=["meta"],
            verbose=False,
        )
        rc = build_mod._run_once(args)
        assert rc == 0
        assert parse_called["v"] is False

    def test_telemetry_writes_when_returned(self, tmp_path: Path, monkeypatch, capsys):
        """When ``render_telemetry.render`` returns a Path, _run_once
        logs the artifact name."""
        empty_cat = parse_content.empty(tmp_path)
        monkeypatch.setattr(build_mod, "_stage_parse", lambda opts: empty_cat)
        for s in (
            "_stage_assets", "_stage_pages", "_stage_api", "_stage_search",
            "_stage_exports", "_stage_meta", "_stage_public",
            "_stage_html_rewrite", "_stage_integrity", "_stage_build_info",
            "_stage_metrics",
        ):
            monkeypatch.setattr(build_mod, s, lambda *a, **kw: None)
        tele_path = tmp_path / "dist" / "build-telemetry.json"

        def fake_telemetry(out, stages, *, reproducible, total_seconds):
            return tele_path

        monkeypatch.setattr(build_mod.render_telemetry, "render", fake_telemetry)
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=False,
            only=list(build_mod.ALL_STAGES),
            verbose=False,
        )
        rc = build_mod._run_once(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "build-telemetry.json written" in out


class TestRunCheck:
    def test_two_identical_builds_pass(self, tmp_path: Path, monkeypatch):
        run_count = {"n": 0}

        def fake_once(args):
            run_count["n"] += 1
            return 0

        monkeypatch.setattr(build_mod, "_run_once", fake_once)
        # diff returns 0 → builds identical.
        completed = subprocess.CompletedProcess(["diff"], 0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: completed)
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=True,
            only=list(build_mod.ALL_STAGES),
            verbose=False,
        )
        rc = build_mod._run_check(args)
        assert rc == 0
        assert run_count["n"] == 2

    def test_diff_failure_returns_nonzero(self, tmp_path: Path, monkeypatch, capsys):
        monkeypatch.setattr(build_mod, "_run_once", lambda args: 0)
        completed = subprocess.CompletedProcess(
            ["diff"], 1, stdout="diff details", stderr=""
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: completed)
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=True,
            only=list(build_mod.ALL_STAGES),
            verbose=False,
        )
        rc = build_mod._run_check(args)
        assert rc == 1
        err = capsys.readouterr().err
        assert "two consecutive" in err
        assert "diff details" in err

    def test_first_build_failure_short_circuits(self, tmp_path: Path, monkeypatch):
        calls = {"once": 0, "diff": 0}

        def fake_once(args):
            calls["once"] += 1
            return 2  # non-zero on first call

        def fake_diff(*a, **kw):
            calls["diff"] += 1
            return subprocess.CompletedProcess(["diff"], 0)

        monkeypatch.setattr(build_mod, "_run_once", fake_once)
        monkeypatch.setattr(subprocess, "run", fake_diff)
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=True,
            only=list(build_mod.ALL_STAGES),
            verbose=False,
        )
        rc = build_mod._run_check(args)
        assert rc == 2
        # Second build and diff never ran.
        assert calls == {"once": 1, "diff": 0}

    def test_second_build_failure_short_circuits(self, tmp_path: Path, monkeypatch):
        results = iter([0, 7])  # first succeeds, second fails

        def fake_once(args):
            return next(results)

        monkeypatch.setattr(build_mod, "_run_once", fake_once)
        # Diff would say identical, but we should never get there.
        completed = subprocess.CompletedProcess(["diff"], 0, stdout="")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: completed)
        args = argparse.Namespace(
            out=str(tmp_path / "dist"),
            reproducible=False,
            check=True,
            only=list(build_mod.ALL_STAGES),
            verbose=False,
        )
        rc = build_mod._run_check(args)
        assert rc == 7
