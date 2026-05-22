"""Unit-level coverage for ``tools/audits/asset_drift.py``.

``asset_drift`` enforces the v7-transition contract documented in the
module docstring: the inline ``<style>`` / ``<script>`` blocks inside
``index.html`` must stay byte-identical (modulo blank-line cosmetics)
to the concatenated ``src/styles/*.css`` and ``src/scripts/*.js``
bundles. Without this audit a contributor can edit the inline blocks
but forget to update ``src/`` (or vice versa), causing
``dist/index.html`` to silently diverge from the local-dev experience.

The audit is wired into CI; before this commit it had zero unit
tests (``Module tools.audits.asset_drift was never imported``).

What this suite locks
---------------------

* ``_read_inline_blocks`` parses the FIRST ``<style>`` block and the
  LAST bare ``<script>\\n...\\n</script>`` block (covers absence of
  either tag, missing closing tag, no needle match at all).
* ``_bundle`` returns empty string when the directory does not
  exist, joins sorted-by-name file contents with single ``\\n``
  separators, strips trailing newlines from each file, and ignores
  non-file children (e.g. nested directories).
* ``_normalise`` drops blank lines and right-strips remaining lines.
* ``_diff`` produces unified-diff output with the documented
  ``index.html (inline)`` / ``src/ (bundled)`` labels, and is
  truncated to ``max_lines`` chunks.
* ``main`` returns ``0`` with a banner when ``index.html`` is
  missing (graceful no-op).
* ``main`` returns ``0`` with the OK banner when inline blocks and
  bundles match.
* ``main`` returns ``1`` and prints a per-asset FAIL line when CSS
  drifts, JS drifts, or both drift; the ``--verbose`` flag swaps the
  one-liner for a diff hunk and additionally prints per-asset size
  lines.
* ``main`` with ``--fix`` rewrites the inline blocks from the
  bundles and returns ``0``.
* ``_write_back`` handles three placement modes: both CSS and JS
  needles present, only CSS present, only JS present, neither
  present (no-op).
* The ``if __name__ == "__main__":`` guard is exercised by a
  subprocess smoke check against the real repo's ``index.html``.

Run
---

``pytest tests/build/test_tools_audits_asset_drift.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_asset_drift.py \
    --cov=tools.audits.asset_drift --cov-branch``
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pytest

import tools.audits.asset_drift as asset_drift


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_html(
    path: Path,
    *,
    css: str | None = "/*css*/",
    js: str | None = "// js",
) -> None:
    """Write an index.html-shaped fixture under ``path``.

    Pass ``css=None`` / ``js=None`` to omit the corresponding block
    entirely. We always wrap blocks in the exact tag shape
    ``_read_inline_blocks`` expects (``<style>...</style>`` and
    ``<script>\\n...\\n</script>``).
    """

    parts: list[str] = ["<!doctype html><html><head>"]
    if css is not None:
        parts.append(f"<style>{css}</style>")
    parts.append("</head><body>")
    if js is not None:
        # The needle the parser greps for includes the trailing
        # newline after ``<script>``.
        parts.append(f"<script>\n{js}\n</script>")
    parts.append("</body></html>")
    path.write_text("".join(parts), encoding="utf-8")


def _write_bundle(
    directory: Path,
    files: Iterable[tuple[str, str]],
) -> None:
    """Drop the named files under ``directory`` with the given content."""

    directory.mkdir(parents=True, exist_ok=True)
    for name, content in files:
        (directory / name).write_text(content, encoding="utf-8")


@pytest.fixture
def isolated_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Redirect ``INDEX_PATH``/``STYLES_DIR``/``SCRIPTS_DIR`` to
    ``tmp_path`` so every test runs against a fresh synthetic tree.
    """

    monkeypatch.setattr(
        asset_drift, "PROJECT_ROOT", tmp_path
    )
    monkeypatch.setattr(
        asset_drift, "INDEX_PATH", tmp_path / "index.html"
    )
    monkeypatch.setattr(
        asset_drift, "STYLES_DIR", tmp_path / "src" / "styles"
    )
    monkeypatch.setattr(
        asset_drift, "SCRIPTS_DIR", tmp_path / "src" / "scripts"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# _read_inline_blocks
# ---------------------------------------------------------------------------


class TestReadInlineBlocks:
    def test_parses_both_blocks(self) -> None:
        """Happy path: ``<style>X</style>...<script>\\n Y \\n</script>``
        yields the inner CSS and JS.

        The ``<script>`` parser captures everything between
        ``<script>\\n`` and ``</script>`` so the trailing ``\\n``
        before the close tag is part of the JS body — that's the
        documented contract."""

        html = (
            "<html><head><style>body{color:red}</style></head>"
            "<body><script>\nconsole.log('x')\n</script></body></html>"
        )
        css, js = asset_drift._read_inline_blocks(html)
        assert css == "body{color:red}"
        assert js == "console.log('x')\n"

    def test_missing_style_block_returns_empty_css(self) -> None:
        """``<style>`` absent -> first ``find()`` returns -1 ->
        empty string for CSS. JS body includes the trailing
        newline before ``</script>``."""

        html = "<html><script>\njs\n</script></html>"
        css, js = asset_drift._read_inline_blocks(html)
        assert css == ""
        assert js == "js\n"

    def test_missing_script_block_returns_empty_js(self) -> None:
        """No ``<script>\\n`` needle -> empty string for JS, and the
        function returns early without touching ``js_end``."""

        html = "<html><style>x</style></html>"
        css, js = asset_drift._read_inline_blocks(html)
        assert css == "x"
        assert js == ""

    def test_missing_closing_style_returns_empty_css(self) -> None:
        """Open ``<style>`` tag without ``</style>`` -> ``css_end == -1``
        -> empty CSS (covers the ``and css_end != -1`` arm)."""

        html = "<html><style>oops"
        css, _js = asset_drift._read_inline_blocks(html)
        assert css == ""

    def test_missing_closing_script_returns_empty_js(self) -> None:
        """Open ``<script>\\n`` without ``</script>`` -> ``js_end == -1``
        -> empty JS (covers the ``if js_end != -1 else ""`` arm)."""

        html = "<html><style>x</style><script>\nincomplete"
        _css, js = asset_drift._read_inline_blocks(html)
        assert js == ""

    def test_first_style_block_wins(self) -> None:
        """The function uses ``find()`` (returns FIRST match) for
        the ``<style>`` block."""

        html = (
            "<style>FIRST</style>"
            "<style>SECOND</style>"
        )
        css, _ = asset_drift._read_inline_blocks(html)
        assert css == "FIRST"

    def test_last_script_block_wins(self) -> None:
        """The function uses ``rfind()`` (returns LAST match) for the
        ``<script>\\n`` block, so the audit ignores e.g. inline
        analytics snippets that appear earlier in the document.

        Trailing ``\\n`` before ``</script>`` is part of the body
        per the documented contract."""

        html = (
            "<script>\nFIRST\n</script>"
            "<style>x</style>"
            "<script>\nLAST\n</script>"
        )
        _, js = asset_drift._read_inline_blocks(html)
        assert js == "LAST\n"


# ---------------------------------------------------------------------------
# _bundle
# ---------------------------------------------------------------------------


class TestBundle:
    def test_missing_directory_returns_empty_string(
        self,
        tmp_path: Path,
    ) -> None:
        """If the source directory doesn't exist the bundle is the
        empty string (covers the ``not directory.exists()`` branch)."""

        result = asset_drift._bundle(tmp_path / "missing", ".css")
        assert result == ""

    def test_concatenates_sorted_files_with_newline(
        self,
        tmp_path: Path,
    ) -> None:
        """Files are joined in sorted-by-name order with a single
        ``\\n`` separator (no leading or trailing newline)."""

        _write_bundle(
            tmp_path,
            [
                ("b.css", "B"),
                ("a.css", "A"),
                ("c.css", "C"),
            ],
        )
        assert asset_drift._bundle(tmp_path, ".css") == "A\nB\nC"

    def test_strips_trailing_newline_from_each_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Each file's trailing newline is rstripped before
        concatenation — otherwise the joined string would carry
        double newlines that don't appear in the inline block."""

        _write_bundle(
            tmp_path,
            [("a.css", "A\n"), ("b.css", "B\n\n")],
        )
        # rstrip("\n") strips ALL trailing newlines from each file.
        assert asset_drift._bundle(tmp_path, ".css") == "A\nB"

    def test_ignores_non_files(self, tmp_path: Path) -> None:
        """A nested directory named ``something.css`` (or anything
        else that ``is_file()`` rejects) is skipped."""

        (tmp_path / "real.css").write_text("X", encoding="utf-8")
        (tmp_path / "fake.css").mkdir()  # directory with .css suffix
        assert asset_drift._bundle(tmp_path, ".css") == "X"

    def test_only_matching_suffix_collected(
        self, tmp_path: Path
    ) -> None:
        """Files without the requested suffix are not picked up
        by the ``glob(f"*{suffix}")``."""

        _write_bundle(
            tmp_path,
            [("a.css", "A"), ("b.js", "B")],
        )
        assert asset_drift._bundle(tmp_path, ".css") == "A"
        assert asset_drift._bundle(tmp_path, ".js") == "B"

    def test_empty_directory_returns_empty_string(
        self, tmp_path: Path
    ) -> None:
        """Directory exists but contains no matching files -> empty
        string (separator-only join over an empty iterator)."""

        tmp_path.mkdir(exist_ok=True)
        assert asset_drift._bundle(tmp_path, ".css") == ""


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------


class TestNormalise:
    def test_drops_blank_lines(self) -> None:
        """Blank lines (whitespace-only) are removed."""

        text = "A\n\nB\n   \nC"
        assert asset_drift._normalise(text) == "A\nB\nC"

    def test_rstrips_trailing_whitespace(self) -> None:
        """Per-line right-strip removes trailing spaces / tabs."""

        text = "A   \nB\t\t\nC"
        assert asset_drift._normalise(text) == "A\nB\nC"

    def test_preserves_leading_whitespace(self) -> None:
        """Indentation is meaningful for CSS / JS so leading
        whitespace is preserved (only trailing is stripped)."""

        text = "  A\n    B"
        assert asset_drift._normalise(text) == "  A\n    B"

    def test_empty_input_returns_empty_string(self) -> None:
        """The empty string is a fixed point."""

        assert asset_drift._normalise("") == ""

    def test_only_blank_lines_returns_empty_string(self) -> None:
        """Input that is entirely whitespace collapses to ''."""

        assert asset_drift._normalise("\n\n   \n") == ""


# ---------------------------------------------------------------------------
# _diff
# ---------------------------------------------------------------------------


class TestDiff:
    def test_produces_unified_diff_with_labels(self) -> None:
        """The diff is unified and carries the documented labels."""

        result = asset_drift._diff("A\nB", "A\nC", "css")
        assert "css: index.html (inline)" in result
        assert "css: src/ (bundled)" in result
        assert "-B" in result
        assert "+C" in result

    def test_truncated_at_max_lines(self) -> None:
        """The diff is sliced to ``max_lines`` lines."""

        # Two very different blobs produce many diff lines.
        a = "\n".join(f"a{i}" for i in range(20))
        b = "\n".join(f"b{i}" for i in range(20))
        result = asset_drift._diff(a, b, "x", max_lines=5)
        assert len(result.splitlines()) <= 5


# ---------------------------------------------------------------------------
# main — missing index.html
# ---------------------------------------------------------------------------


class TestMainMissingIndex:
    def test_returns_0_with_banner_when_index_absent(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No ``index.html`` in the repo root is a valid state
        (post-cleanup) — the audit returns 0 and prints a banner."""

        rc = asset_drift.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "no index.html" in out


# ---------------------------------------------------------------------------
# main — happy path
# ---------------------------------------------------------------------------


class TestMainHappyPath:
    def test_matching_inline_and_bundles_returns_0(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When the inline blocks match the bundled src/ contents,
        the audit emits the OK banner and exits 0."""

        css_body = "body{color:red}"
        js_body = "console.log('hi')"
        _write_html(
            isolated_repo / "index.html",
            css=css_body,
            js=js_body,
        )
        _write_bundle(
            isolated_repo / "src" / "styles",
            [("a.css", css_body)],
        )
        _write_bundle(
            isolated_repo / "src" / "scripts",
            [("a.js", js_body)],
        )
        rc = asset_drift.main([])
        assert rc == 0
        assert "OK: index.html inline blocks match" in capsys.readouterr().out

    def test_verbose_prints_per_asset_sizes(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``--verbose`` enriches the OK banner with per-asset size
        and match-state lines."""

        css_body = "body{color:red}"
        js_body = "console.log('hi')"
        _write_html(
            isolated_repo / "index.html", css=css_body, js=js_body
        )
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", css_body)]
        )
        _write_bundle(
            isolated_repo / "src" / "scripts", [("a.js", js_body)]
        )
        rc = asset_drift.main(["--verbose"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "inline css=" in out
        assert "inline js=" in out
        assert "match=True" in out

    def test_blank_line_only_drift_passes(
        self,
        isolated_repo: Path,
    ) -> None:
        """Blank-line cosmetics are dropped by ``_normalise`` so a
        bundle whose contents differ ONLY by blank lines still
        matches the inline block."""

        css_body = "body{color:red}\n\np{color:blue}"
        bundle_css = "body{color:red}\np{color:blue}"
        _write_html(isolated_repo / "index.html", css=css_body, js=None)
        # Without the JS block in HTML the inline JS is empty; pair
        # with an empty bundle so the JS-side check passes too.
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", bundle_css)]
        )
        # SCRIPTS_DIR not created -> _bundle returns "" -> match.
        rc = asset_drift.main([])
        assert rc == 0


# ---------------------------------------------------------------------------
# main — drift failures (rc=1)
# ---------------------------------------------------------------------------


class TestMainDrift:
    def test_css_drift_only_returns_1(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Drift on the CSS side alone fails the audit, prints the
        CSS-specific FAIL line, and surfaces the verbose hint."""

        _write_html(
            isolated_repo / "index.html",
            css="body{color:red}",
            js="console.log('x')",
        )
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", "DIFFERENT")]
        )
        _write_bundle(
            isolated_repo / "src" / "scripts",
            [("a.js", "console.log('x')")],
        )
        rc = asset_drift.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL: inline <style> block differs" in out
        # Hint line directs operator to --verbose / --fix.
        assert "run with --verbose to see the diff" in out
        # JS side OK, so its FAIL line MUST NOT appear.
        assert "FAIL: inline <script>" not in out

    def test_js_drift_only_returns_1(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Drift on the JS side alone fails the audit and prints
        only the JS FAIL line."""

        _write_html(
            isolated_repo / "index.html",
            css="body{color:red}",
            js="console.log('x')",
        )
        _write_bundle(
            isolated_repo / "src" / "styles",
            [("a.css", "body{color:red}")],
        )
        _write_bundle(
            isolated_repo / "src" / "scripts", [("a.js", "DIFFERENT")]
        )
        rc = asset_drift.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL: inline <script> block differs" in out
        assert "FAIL: inline <style>" not in out

    def test_both_sides_drift_returns_1_and_lists_both(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When BOTH css and js drift, BOTH FAIL lines appear and
        rc=1."""

        _write_html(
            isolated_repo / "index.html",
            css="body{color:red}",
            js="console.log('x')",
        )
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", "X-DIFF")]
        )
        _write_bundle(
            isolated_repo / "src" / "scripts", [("a.js", "Y-DIFF")]
        )
        rc = asset_drift.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL: inline <style>" in out
        assert "FAIL: inline <script>" in out

    def test_verbose_drift_prints_diff_hunks(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``--verbose`` swaps the one-line hint for a unified diff
        hunk on each drifting side."""

        _write_html(
            isolated_repo / "index.html",
            css="body{color:red}",
            js="console.log('x')",
        )
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", "DIFF-CSS")]
        )
        _write_bundle(
            isolated_repo / "src" / "scripts", [("a.js", "DIFF-JS")]
        )
        rc = asset_drift.main(["--verbose"])
        assert rc == 1
        out = capsys.readouterr().out
        # Per-asset size lines appear under verbose mode.
        assert "match=False" in out
        # Diff labels show up because we route through _diff.
        assert "css: index.html (inline)" in out
        assert "js: index.html (inline)" in out
        # The terse hint must NOT appear in verbose mode.
        assert "run with --verbose" not in out


# ---------------------------------------------------------------------------
# main --fix
# ---------------------------------------------------------------------------


class TestMainFix:
    def test_fix_rewrites_inline_blocks_and_returns_0(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``--fix`` overwrites the inline blocks with the bundle
        contents and returns 0 (used for ad-hoc resync; CI never
        passes --fix)."""

        _write_html(
            isolated_repo / "index.html",
            css="OLD-CSS",
            js="OLD-JS",
        )
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", "NEW-CSS")]
        )
        _write_bundle(
            isolated_repo / "src" / "scripts", [("a.js", "NEW-JS")]
        )
        rc = asset_drift.main(["--fix"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "FIXED: index.html inline blocks rewritten" in out
        rewritten = (isolated_repo / "index.html").read_text(encoding="utf-8")
        # New bundle contents are now embedded.
        assert "NEW-CSS" in rewritten
        assert "NEW-JS" in rewritten
        # Old contents replaced.
        assert "OLD-CSS" not in rewritten
        assert "OLD-JS" not in rewritten

    def test_fix_with_no_style_tag_skips_css_rewrite(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If the index.html has no ``<style>`` tag the CSS rewrite
        is skipped (``css_start == -1`` branch in ``_write_back``)
        but the function still rewrites JS if applicable. The
        invocation reaches ``_write_back`` because the JS side
        drifted."""

        # index.html with only a <script> block, no <style> at all.
        path = isolated_repo / "index.html"
        path.write_text(
            "<html><script>\nOLD-JS\n</script></html>",
            encoding="utf-8",
        )
        # No styles dir -> bundle_css empty -> inline CSS ("") equal
        # to bundle_css ("") -> css_match True; only the JS side
        # drifts so we still reach --fix's _write_back path.
        _write_bundle(
            isolated_repo / "src" / "scripts", [("a.js", "NEW-JS")]
        )
        rc = asset_drift.main(["--fix"])
        assert rc == 0
        rewritten = path.read_text(encoding="utf-8")
        assert "NEW-JS" in rewritten
        assert "<style>" not in rewritten

    def test_fix_with_no_script_tag_skips_js_rewrite(
        self,
        isolated_repo: Path,
    ) -> None:
        """If the index.html has no ``<script>\\n`` needle the JS
        rewrite is skipped (``js_start == -1`` branch)."""

        path = isolated_repo / "index.html"
        path.write_text(
            "<html><style>OLD-CSS</style></html>",
            encoding="utf-8",
        )
        _write_bundle(
            isolated_repo / "src" / "styles", [("a.css", "NEW-CSS")]
        )
        rc = asset_drift.main(["--fix"])
        assert rc == 0
        rewritten = path.read_text(encoding="utf-8")
        assert "NEW-CSS" in rewritten
        assert "<script>" not in rewritten


# ---------------------------------------------------------------------------
# _write_back — directly exercise edge cases
# ---------------------------------------------------------------------------


class TestWriteBackDirect:
    def test_no_style_no_script_returns_0_and_writes_html_unchanged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When neither block is present the function writes the
        original HTML back unchanged and prints the FIXED banner.

        This branch isn't reachable from --fix in normal use because
        the audit would have already returned 0 ("nothing to fix"),
        but the function is exposed and other tooling could call it
        directly — we lock the documented contract."""

        path = isolated_repo / "index.html"
        path.write_text(
            "<html><body>nothing</body></html>", encoding="utf-8"
        )
        rc = asset_drift._write_back(
            path.read_text(encoding="utf-8"),
            "NEW-CSS",
            "NEW-JS",
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "FIXED:" in out
        # Neither bundle ended up in the file because no tag was
        # found.
        assert "NEW-CSS" not in path.read_text(encoding="utf-8")
        assert "NEW-JS" not in path.read_text(encoding="utf-8")

    def test_orphan_open_style_tag_skips_css_rewrite(
        self,
        isolated_repo: Path,
    ) -> None:
        """Open ``<style>`` without ``</style>`` -> ``css_end == -1``
        -> CSS rewrite skipped (covers the ``css_start != -1 and
        css_end != -1`` AND-arm)."""

        path = isolated_repo / "index.html"
        path.write_text(
            "<html><style>broken<script>\nOLD-JS\n</script></html>",
            encoding="utf-8",
        )
        rc = asset_drift._write_back(
            path.read_text(encoding="utf-8"),
            "NEW-CSS",
            "NEW-JS",
        )
        assert rc == 0
        result = path.read_text(encoding="utf-8")
        assert "NEW-JS" in result
        # CSS rewrite was skipped because no </style>.
        assert "NEW-CSS" not in result

    def test_orphan_open_script_tag_skips_js_rewrite(
        self,
        isolated_repo: Path,
    ) -> None:
        """Open ``<script>\\n`` without ``</script>`` -> ``js_end == -1``
        -> JS rewrite skipped."""

        path = isolated_repo / "index.html"
        path.write_text(
            "<html><style>OLD-CSS</style><script>\nincomplete",
            encoding="utf-8",
        )
        rc = asset_drift._write_back(
            path.read_text(encoding="utf-8"),
            "NEW-CSS",
            "NEW-JS",
        )
        assert rc == 0
        result = path.read_text(encoding="utf-8")
        assert "NEW-CSS" in result
        # JS rewrite was skipped because no </script>.
        assert "NEW-JS" not in result


# ---------------------------------------------------------------------------
# Module entrypoint guard — subprocess smoke against real repo
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_against_real_repo(self) -> None:
        """Invoke ``python -m tools.audits.asset_drift`` against the
        real repo. We accept any documented rc (0, 1) — the audit
        will return 2 only on invocation error, which must NEVER
        happen in a healthy checkout. The subprocess inherits no
        coverage instrumentation so this test exists purely to pin
        the CLI contract advertised in the docstring."""

        repo_root = Path(asset_drift.__file__).resolve().parents[2]
        if not (repo_root / "index.html").exists():
            pytest.skip("repo lacks index.html (post-v7 cleanup)")
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.asset_drift"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1), (
            f"unexpected rc={result.returncode} "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "[asset_drift]" in result.stdout
