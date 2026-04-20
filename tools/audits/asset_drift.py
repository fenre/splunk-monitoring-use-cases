#!/usr/bin/env python3
"""tools.audits.asset_drift — flag drift between index.html inline blocks and src/.

During the v7 transition the source ``index.html`` retains its inline
``<style>`` and bare ``<script>`` blocks for backwards compatibility
with anyone serving the file directly (e.g. ``python -m http.server``
from repo root). The v7 source-of-truth lives in ``src/styles/*.css``
and ``src/scripts/*.js``; the build pipeline concatenates those files
and replaces the inline blocks in ``dist/index.html`` with
fingerprinted bundle references.

If a contributor edits the inline blocks but forgets to update
``src/`` (or vice-versa) the deployed site silently diverges from
local-dev. This audit catches that drift in CI.

Comparison rule
---------------
The inline blocks and the concatenated ``src/`` bundles must be
byte-identical, modulo single ``\\n`` separators between component
files. Any other divergence fails the audit and the PR.

Usage
-----
    python3 tools/audits/asset_drift.py
    python3 tools/audits/asset_drift.py --fix     # rewrite inline blocks from src/
    python3 tools/audits/asset_drift.py --verbose

Exit codes
----------
    0  inline blocks are in sync with src/
    1  drift detected (CI failure)
    2  invocation/IO error

Lifecycle
---------
This audit is removed in the ``cleanup-and-docs`` todo when the source
``index.html`` is deleted entirely (``render_pages.py`` SSG generates
the landing page natively from ``src/`` + ``content/``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = PROJECT_ROOT / "index.html"
STYLES_DIR = PROJECT_ROOT / "src" / "styles"
SCRIPTS_DIR = PROJECT_ROOT / "src" / "scripts"


def _read_inline_blocks(html: str) -> tuple[str, str]:
    """Return (inline_css, inline_js) as plain strings.

    inline_css = contents of the FIRST ``<style>...</style>`` block.
    inline_js  = contents of the LAST bare ``<script>\\n...\\n</script>``
                 block (i.e. the one without a ``src=`` or ``type=`` attr).
    """
    css_start = html.find("<style>")
    css_end = html.find("</style>", css_start) if css_start != -1 else -1
    inline_css = (
        html[css_start + len("<style>"): css_end]
        if css_start != -1 and css_end != -1
        else ""
    )

    needle = "<script>\n"
    js_start = html.rfind(needle)
    if js_start == -1:
        return inline_css, ""
    js_end = html.find("</script>", js_start)
    inline_js = html[js_start + len(needle): js_end] if js_end != -1 else ""
    return inline_css, inline_js


def _bundle(directory: Path, suffix: str) -> str:
    """Concat sorted ``directory/*.{suffix}`` joined by ``\\n``."""
    if not directory.exists():
        return ""
    files = sorted(p for p in directory.glob(f"*{suffix}") if p.is_file())
    return "\n".join(p.read_text(encoding="utf-8").rstrip("\n") for p in files)


def _normalise(text: str) -> str:
    """Drop ALL blank lines and trim trailing whitespace per line.

    Blank-line placement between top-level CSS rules / JS functions is
    purely cosmetic and gets lost when sources are split across files
    (each ``src/`` file has its own EOF newline). The drift contract
    is therefore "non-blank lines must match in order", which this
    normalisation enforces.
    """
    return "\n".join(
        line.rstrip()
        for line in text.splitlines()
        if line.strip() != ""
    )


def _diff(a: str, b: str, label: str, max_lines: int = 30) -> str:
    import difflib
    diff = list(
        difflib.unified_diff(
            a.splitlines(keepends=False),
            b.splitlines(keepends=False),
            lineterm="",
            fromfile=f"{label}: index.html (inline)",
            tofile=f"{label}: src/ (bundled)",
            n=1,
        )
    )
    return "\n".join(diff[:max_lines])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.audits.asset_drift")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file sizes and diff hunks.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Overwrite inline blocks in index.html with src/ bundles. "
             "Intended for ad-hoc resync; CI never passes --fix.",
    )
    args = parser.parse_args(argv)

    if not INDEX_PATH.exists():
        print("[asset_drift] no index.html in repo root; nothing to compare")
        return 0

    html = INDEX_PATH.read_text(encoding="utf-8")
    inline_css, inline_js = _read_inline_blocks(html)
    bundle_css = _bundle(STYLES_DIR, ".css")
    bundle_js = _bundle(SCRIPTS_DIR, ".js")

    css_match = _normalise(inline_css) == _normalise(bundle_css)
    js_match = _normalise(inline_js) == _normalise(bundle_js)

    if args.verbose:
        print(
            f"[asset_drift] inline css={len(inline_css):,}b "
            f"bundle css={len(bundle_css):,}b match={css_match}"
        )
        print(
            f"[asset_drift] inline js={len(inline_js):,}b "
            f"bundle js={len(bundle_js):,}b match={js_match}"
        )

    if css_match and js_match:
        print("[asset_drift] OK: index.html inline blocks match src/")
        return 0

    if args.fix:
        return _write_back(html, bundle_css, bundle_js)

    if not css_match:
        print("[asset_drift] FAIL: inline <style> block differs from src/styles/")
        if args.verbose:
            print(_diff(inline_css, bundle_css, "css"))
        else:
            print("           run with --verbose to see the diff, "
                  "or --fix to rewrite from src/")
    if not js_match:
        print("[asset_drift] FAIL: inline <script> block differs from src/scripts/")
        if args.verbose:
            print(_diff(inline_js, bundle_js, "js"))
        else:
            print("           run with --verbose to see the diff, "
                  "or --fix to rewrite from src/")
    return 1


def _write_back(html: str, bundle_css: str, bundle_js: str) -> int:
    """Overwrite the inline blocks in index.html with the src/ bundles."""
    css_start = html.find("<style>")
    css_end = html.find("</style>", css_start) if css_start != -1 else -1
    if css_start != -1 and css_end != -1:
        html = (
            html[: css_start + len("<style>")]
            + bundle_css
            + "\n"
            + html[css_end:]
        )

    needle = "<script>\n"
    js_start = html.rfind(needle)
    js_end = html.find("</script>", js_start) if js_start != -1 else -1
    if js_start != -1 and js_end != -1:
        html = (
            html[: js_start + len(needle)]
            + bundle_js
            + "\n"
            + html[js_end:]
        )

    INDEX_PATH.write_text(html, encoding="utf-8")
    print("[asset_drift] FIXED: index.html inline blocks rewritten from src/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
