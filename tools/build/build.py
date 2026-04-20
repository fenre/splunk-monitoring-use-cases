#!/usr/bin/env python3
"""tools.build.build — v7.0 build pipeline entrypoint.

Usage
-----
    python3 tools/build/build.py --out dist
    python3 tools/build/build.py --out dist --reproducible
    python3 tools/build/build.py --out dist --check
    python3 tools/build/build.py --out dist --skip-legacy

Stages
------
The pipeline runs as a series of independent stages, each owning a disjoint
subtree of `dist/`. Stages are sequential by default; CI can run them in
parallel jobs by sharding via `--only`.

    1. parse        — read content/, data/, src/, schemas/ into Catalog
    2. assets       — fingerprint and bundle src/styles + src/scripts
    3. pages        — emit dist/{index.html, browse/, uc/, category/, ...}
    4. api          — emit dist/api/*
    5. exports      — emit dist/exports/*
    6. meta         — emit dist/{sitemap*.xml, llms*.txt, feed.xml, ...}
    7. public       — copy public/ verbatim
    8. integrity    — emit dist/integrity.json
    9. build_info   — emit dist/BUILD-INFO.json

Reproducibility
---------------
With `--reproducible`:
* iteration order is sorted by primary key everywhere
* JSON output uses sort_keys=True and a fixed separator
* timestamps are taken from `git log -1 --format=%cI HEAD`
* LC_ALL is set to "C"
CI runs the full build twice and asserts byte-identical output.

Transitional behaviour (v7.0-dev)
---------------------------------
While the per-stage native renderers are landing, the pipeline still calls
the legacy `build.py` in `--legacy` mode to keep `dist/` byte-equivalent
to today's site. As each native renderer ships, the corresponding section
of the legacy pass is short-circuited; v7.1 removes the legacy pass
entirely.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from build import build_info, integrity, parse_content  # noqa: E402
from build import render_api, render_assets, render_exports  # noqa: E402
from build import render_meta, render_pages, render_search  # noqa: E402

DEFAULT_OUT = "dist"
ALL_STAGES = (
    "parse",
    "assets",
    "pages",
    "api",
    "search",
    "exports",
    "meta",
    "public",
    "html_rewrite",
    "integrity",
    "build_info",
)


@dataclass
class BuildOptions:
    out_dir: Path
    reproducible: bool = False
    check: bool = False
    skip_legacy: bool = False
    only: tuple[str, ...] = ALL_STAGES
    verbose: bool = False
    legacy_extras: tuple[str, ...] = field(
        default_factory=lambda: (
            "data.js",
            "catalog.json",
            "llms.txt",
            "llm.txt",
            "llms-full.txt",
            "sitemap.xml",
            "scorecard.json",
            "scorecard.html",
            "regulatory-primer.html",
            "api-docs.html",
            "mitre_techniques.json",
            "recently-added.json",
            "provenance.json",
            "provenance.js",
            "non-technical-view.js",
        )
    )


# ---------------------------------------------------------------------------
# Stage runner
# ---------------------------------------------------------------------------

def _log(msg: str, t0: Optional[float] = None) -> None:
    if t0 is None:
        print(f"[build] {msg}")
    else:
        print(f"[build] {msg}  ({time.monotonic() - t0:.2f}s)")


def _ensure_clean_out(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)


def _run_legacy_build(opts: BuildOptions) -> None:
    """Invoke the v6 ``build.py`` so legacy artefacts remain current.

    The legacy script writes data.js, catalog.json, llms*.txt, sitemap.xml,
    api/cat-N.json, scorecard.{html,json}, provenance.json. v7's renderers
    will progressively replace each of these; until they do, the legacy
    pass keeps dist/ byte-equivalent to the previous site.
    """
    if opts.skip_legacy:
        _log("legacy build skipped (--skip-legacy)")
        return
    legacy = PROJECT_ROOT / "build.py"
    if not legacy.exists():
        _log("WARN  legacy build.py not present; skipping")
        return
    t0 = time.monotonic()
    env = os.environ.copy()
    if opts.reproducible:
        env["LC_ALL"] = "C"
        env["TZ"] = "UTC"
        env["SOURCE_DATE_EPOCH"] = _git_commit_epoch()
    subprocess.run(
        [sys.executable, str(legacy)],
        check=True,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    _log("legacy build.py done", t0)


def _git_commit_epoch() -> str:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "HEAD"],
            cwd=str(PROJECT_ROOT),
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "0"


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def _stage_parse(opts: BuildOptions) -> parse_content.Catalog:
    t0 = time.monotonic()
    catalog = parse_content.load(PROJECT_ROOT, reproducible=opts.reproducible)
    _log(
        f"parsed {catalog.uc_count} UCs / "
        f"{len(catalog.categories)} categories / "
        f"{len(catalog.regulations)} regulations",
        t0,
    )
    return catalog


def _stage_assets(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_assets.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    _log("assets fingerprinted", t0)


def _stage_pages(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_pages.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    _log("pages emitted", t0)


def _stage_api(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_api.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    _log("api/ emitted", t0)


def _stage_search(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_search.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    n_tokens = catalog.asset_hashes.get("search_index_tokens", "?")
    n_docs = catalog.asset_hashes.get("search_index_docs", "?")
    _log(f"search index: {n_tokens} tokens × {n_docs} docs across "
         f"{render_search.SHARD_COUNT} shards", t0)


def _stage_exports(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_exports.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    _log("exports/ emitted", t0)


def _stage_meta(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_meta.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    _log("meta (sitemap, llms.txt, feed.xml) emitted", t0)


def _stage_public(opts: BuildOptions) -> None:
    """Copy the workspace's deployable surface into dist/.

    During the v7 transition this is the long-tail of files the legacy
    `build.py` produced (and that we still need byte-identical for the
    initial release). Once `render_pages` and `render_api` are emitting
    natively, the only thing copied here is `public/`.
    """
    t0 = time.monotonic()
    out = opts.out_dir
    pub = PROJECT_ROOT / "public"
    if pub.exists():
        for src in pub.rglob("*"):
            if src.is_dir():
                continue
            rel = src.relative_to(pub)
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    ssg_landing_present = (
        "pages" in opts.only
        and (out / "index.html").exists()
        and _looks_like_ssg_landing(out / "index.html")
    )

    if not opts.skip_legacy:
        _mirror_legacy_root_into_dist(
            out, opts, preserve_root_index=ssg_landing_present
        )

    _log("public/ + legacy mirror copied", t0)


def _looks_like_ssg_landing(path: Path) -> bool:
    """Detect the SSG landing page at dist/index.html via a small fingerprint.

    The landing template emits the marker class 'cta primary' inside the
    hero block and links into /browse/. The legacy SPA does not carry the
    'cta primary' marker. A false positive is harmless because the
    html_rewrite stage is idempotent.

    We read up to 64 KiB to span the inline critical CSS that the landing
    page emits in <head> before the hero markup. The whole landing page
    target is <30 KiB but inline CSS pushes the marker past the 8 KiB
    sniff window used by smaller files.
    """
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:65536]
    except OSError:
        return False
    return ('class="cta primary"' in head) and ("/browse/" in head)


# Top-level files and directories the v6 pages workflow uploaded as the
# Pages artefact. We mirror them into dist/ so the v7.0 cutover does not
# break a single existing URL while the native renderers land.
#
# v7 cut-over note: ``data.js`` is intentionally absent — its 39 MB
# payload has been replaced by the lazy-loaded ``api/catalog-index.json``
# (4.8 MB / 793 KB gzipped) plus on-demand ``api/cat-N.json`` shards.
# The ``html_rewrite`` stage strips the ``<script src="data.js">`` tag
# from ``dist/index.html`` so the file genuinely never ships.
LEGACY_TOP_LEVEL = (
    "index.html",
    "catalog.json",
    "openapi.yaml",
    "scorecard.html",
    "scorecard.json",
    "regulatory-primer.html",
    "api-docs.html",
    "non-technical-view.js",
    "provenance.json",
    "provenance.js",
    "mitre_techniques.json",
    "recently-added.json",
    "llms.txt",
    "llm.txt",
    "llms-full.txt",
    "robots.txt",
    "favicon.ico",
    "favicon.svg",
    "icon.svg",
    "icon-192.png",
    "icon-512.png",
    "og-image.png",
    "og-image-1200.png",
    ".nojekyll",
    "CNAME",
    # Note: ``sitemap.xml`` and ``manifest.json`` are intentionally NOT
    # mirrored — they are owned by ``render_meta.py`` from v7.0 onward.
    # Mirroring would clobber the SSG-emitted sharded sitemap-index and
    # machine-consumer manifest with the v6 flat artefacts.
)
LEGACY_TOP_DIRS = (
    "api",
    "assets",
    "data",
    "docs",
    "use-cases",
    "samples",
    "templates",
    "schemas",
    "reports",
    "splunk-apps",
    "ta",
    "img",
    "images",
    "embed",
)


def _mirror_legacy_root_into_dist(out: Path, opts: BuildOptions, *, preserve_root_index: bool = False) -> None:
    """Copy the v6 root tree into dist/ for byte-equivalent transition.

    With ``preserve_root_index=True`` the legacy ``index.html`` is
    relocated to ``dist/browse/index.html`` instead of overwriting the
    SSG-emitted slim landing at ``dist/index.html``.

    Skipped paths: .git, node_modules, vendor, .venv, dist, tools, scripts,
    mcp, src, content, public, terminals, .github, .cursor, .idea, .vscode.
    These are either source-only, third-party, or already handled.
    """
    skip_dirs = {
        ".git",
        ".github",
        ".cursor",
        ".idea",
        ".vscode",
        "node_modules",
        "vendor",
        ".venv",
        ".venv-feasibility",
        "venv",
        "env",
        "dist",
        "tools",
        "scripts",
        "mcp",
        "src",
        "content",
        "public",
        "terminals",
        "build",
        "test-results",
        "other",
        "Data Assessement tool",
        "__pycache__",
        "legacy",
    }
    skip_extensions = {".pyc", ".pyo", ".pyd", ".swp", ".swo"}

    for fname in LEGACY_TOP_LEVEL:
        legacy_src = PROJECT_ROOT / fname
        if not (legacy_src.exists() and legacy_src.is_file()):
            continue
        if fname == "index.html" and preserve_root_index:
            # SSG landing already owns dist/index.html. Drop the legacy
            # SPA into dist/browse/index.html so /browse/ keeps working
            # until the SPA is fully torn down.
            dst = out / "browse" / "index.html"
        else:
            dst = out / fname
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_src, dst)

    for dname in LEGACY_TOP_DIRS:
        src = PROJECT_ROOT / dname
        if not src.exists() or not src.is_dir():
            continue
        for path in src.rglob("*"):
            if path.is_dir():
                if path.name in skip_dirs:
                    continue
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.suffix in skip_extensions:
                continue
            rel = path.relative_to(PROJECT_ROOT)
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)


def _stage_html_rewrite(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    """Rewrite the SPA HTML to load fingerprinted bundles via root-absolute URLs.

    Operates on ``dist/browse/index.html`` (the relocated SPA) when the
    SSG landing owns ``dist/index.html``; falls back to the legacy
    location for byte-identical transitional builds.

    Runs after ``_stage_public`` (which mirrored the legacy inline
    ``index.html``) and after ``_stage_assets`` (which fingerprinted the
    bundles and stashed their names on ``catalog.asset_hashes``).

    Two surgical edits:

    1. The first ``<style>...</style>`` block (the entire ~950-line
       inline stylesheet) is replaced with a short ``<style>`` containing
       the critical above-the-fold CSS (tokens + base reset) followed by
       a preload link to the fingerprinted bundle, and a ``<noscript>``
       fallback for users without JS.
    2. The trailing bare ``<script>...</script>`` block (the entire
       ~2 700-line inline app code) is replaced with a single
       ``<script defer src="assets/app.<hash>.js"></script>``. The
       upstream ``<script src="data.js">`` etc. tags are left intact so
       the v6 data layer keeps working through the transition.

    No-ops if the bundles are not present (e.g. ``--only meta``).
    """
    t0 = time.monotonic()
    browse_path = opts.out_dir / "browse" / "index.html"
    root_path = opts.out_dir / "index.html"
    if browse_path.exists():
        index_path = browse_path
    elif root_path.exists():
        index_path = root_path
    else:
        _log("html_rewrite skipped (no SPA index.html)")
        return
    css_name = catalog.asset_hashes.get("styles_css")
    js_name = catalog.asset_hashes.get("app_js")
    if not css_name and not js_name:
        _log("html_rewrite skipped (no bundled assets)")
        return

    html = index_path.read_text(encoding="utf-8")
    original_size = len(html)
    use_root_abs = index_path.parent != opts.out_dir
    if css_name:
        html = _swap_inline_style(html, css_name, catalog.critical_css, root_abs=use_root_abs)
    if js_name:
        html = _swap_inline_script(html, js_name, root_abs=use_root_abs)
    html = _drop_legacy_data_script(html)
    if use_root_abs:
        html = _rewrite_relative_refs_to_root_abs(html)
    index_path.write_text(html, encoding="utf-8")

    # The legacy build.py mirror may have put a copy of data.js back into
    # dist/. Now that nothing references it, evict it so we don't ship the
    # 39 MB payload behind everyone's back.
    legacy_data_js = opts.out_dir / "data.js"
    if legacy_data_js.exists():
        legacy_data_js.unlink()

    saved = original_size - len(html)
    _log(
        f"html_rewrite: index.html {original_size:,} → {len(html):,} bytes "
        f"({saved / 1024:.1f} KiB saved)",
        t0,
    )


def _swap_inline_style(html: str, css_name: str, critical_css: str, *, root_abs: bool = False) -> str:
    """Replace the first ``<style>...</style>`` block with bundle refs."""
    start = html.find("<style>")
    if start == -1:
        return html
    end = html.find("</style>", start)
    if end == -1:
        return html
    end += len("</style>")
    href_prefix = "/assets/" if root_abs else "assets/"
    replacement = (
        f"<style>{critical_css}</style>\n"
        f'<link rel="preload" href="{href_prefix}{css_name}" as="style" '
        f"onload=\"this.onload=null;this.rel='stylesheet'\">\n"
        f'<noscript><link rel="stylesheet" href="{href_prefix}{css_name}"></noscript>'
    )
    return html[:start] + replacement + html[end:]


def _swap_inline_script(html: str, js_name: str, *, root_abs: bool = False) -> str:
    """Replace the bare ``<script>...</script>`` block with one ``defer`` link.

    Anchors on ``<script>\\n`` (with newline) to skip the inline
    ``<script type="application/ld+json">`` and any ``<script src=...>``
    references on the page.
    """
    needle = "<script>\n"
    start = html.rfind(needle)
    if start == -1:
        return html
    end = html.find("</script>", start)
    if end == -1:
        return html
    end += len("</script>")
    src_prefix = "/assets/" if root_abs else "assets/"
    replacement = f'<script defer src="{src_prefix}{js_name}"></script>'
    return html[:start] + replacement + html[end:]


# The v6 ``data.js`` global (window.DATA, EQUIPMENT, CAT_META, …) is
# replaced by ``api/catalog-index.json`` plus on-demand ``api/cat-N.json``.
# Strip the legacy script tag so browsers don't fetch a 39 MB JS file
# that no longer exists in dist/. Idempotent — safe to call when the tag
# is already absent.
_DATA_JS_TAG = '<script src="data.js"></script>\n'


def _drop_legacy_data_script(html: str) -> str:
    if _DATA_JS_TAG in html:
        html = html.replace(_DATA_JS_TAG, "", 1)
    # Be lenient about whitespace/newline variants.
    no_newline = '<script src="data.js"></script>'
    if no_newline in html:
        html = html.replace(no_newline, "", 1)
    return html


_RELATIVE_REWRITES = (
    re.compile(r'href="(api/[^"#?]+)"'),
    re.compile(r'src="(api/[^"#?]+)"'),
    re.compile(r'href="(assets/[^"#?]+)"'),
    re.compile(r'src="(assets/[^"#?]+)"'),
    re.compile(r'href="(use-cases/[^"#?]+)"'),
    re.compile(r'href="(schemas/[^"#?]+)"'),
    re.compile(r'href="(docs/[^"#?]+)"'),
    re.compile(r'href="(data/[^"#?]+)"'),
    re.compile(r'href="(samples/[^"#?]+)"'),
    re.compile(r'href="(reports/[^"#?]+)"'),
)
_TOPLEVEL_FILE_REWRITES = (
    # Legacy companion scripts the SPA loads via relative <script src>.
    re.compile(r'src="(provenance\.[^"#?]+)"'),
    re.compile(r'src="(non-technical-view\.js)"'),
    re.compile(r'src="(custom-text\.js)"'),
    re.compile(r'src="(mitre_techniques\.json)"'),
    re.compile(r'src="(recently-added\.json)"'),
    # Legacy companion files exposed via <link rel=alternate|preload|...>.
    re.compile(r'href="(provenance\.[^"#?]+)"'),
    re.compile(r'href="(scorecard\.[^"#?]+)"'),
    re.compile(r'href="(sitemap\.xml)"'),
    re.compile(r'href="(llms\.txt)"'),
    re.compile(r'href="(llms-full\.txt)"'),
    re.compile(r'href="(openapi\.yaml)"'),
    re.compile(r'href="(manifest\.json)"'),
    re.compile(r'href="(catalog\.json)"'),
    re.compile(r'href="(robots\.txt)"'),
    re.compile(r'href="(favicon\.(?:ico|svg))"'),
    re.compile(r'href="(icon(?:-\d+)?\.(?:svg|png))"'),
    re.compile(r'href="(og-image(?:-\d+)?\.png)"'),
    # Legacy nested scripts shipped under tools/data-sizing/.
    re.compile(r'src="(tools/data-sizing/[^"#?]+)"'),
)


def _rewrite_relative_refs_to_root_abs(html: str) -> str:
    """Rewrite relative href/src refs in the SPA to root-absolute paths.

    The legacy SPA was authored as a single-page document at the site
    root, so its asset and API references are relative ('assets/foo',
    'api/bar.json'). After relocation to /browse/ those refs would
    resolve to /browse/assets/foo, which 404s. We rewrite them to
    '/assets/foo' and '/api/bar.json' so the SPA works from any depth.

    Only rewrites refs that look like first-party paths under known
    top-level directories. Absolute URLs, fragments, mailto:, and
    template strings are left alone.
    """
    for pat in _RELATIVE_REWRITES:
        attr_kind = "src" if pat.pattern.startswith("src=") else "href"
        html = pat.sub(lambda m, k=attr_kind: f'{k}="/' + m.group(1) + '"', html)
    for pat in _TOPLEVEL_FILE_REWRITES:
        attr_kind = "src" if pat.pattern.startswith("src=") else "href"
        html = pat.sub(lambda m, k=attr_kind: f'{k}="/' + m.group(1) + '"', html)
    return html


def _stage_integrity(opts: BuildOptions) -> None:
    t0 = time.monotonic()
    integrity.write(opts.out_dir, reproducible=opts.reproducible)
    _log("integrity.json written", t0)


def _stage_build_info(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    build_info.write(opts.out_dir, catalog, reproducible=opts.reproducible)
    _log("BUILD-INFO.json written", t0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tools.build.build",
        description=(
            "Build splunk-monitoring.io into the directory passed via --out. "
            "Reproducible by default in CI; pass --reproducible locally to match."
        ),
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUT,
        help="Output directory (will be wiped and recreated). Defaults to ./dist",
    )
    parser.add_argument(
        "--reproducible",
        action="store_true",
        help=(
            "Sort iteration, freeze timestamps to git commit time, "
            "force LC_ALL=C. CI uses this to compare two consecutive builds."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Run the build twice and assert byte-identical output. "
            "Implies --reproducible."
        ),
    )
    parser.add_argument(
        "--skip-legacy",
        action="store_true",
        help=(
            "Do not invoke the v6 build.py; do not mirror legacy root files. "
            "Used by tests of the v7 native pipeline in isolation."
        ),
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=ALL_STAGES,
        default=list(ALL_STAGES),
        help="Run only these stages (default: all). Use to shard CI jobs.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose per-file logging.",
    )
    args = parser.parse_args(argv)

    if args.check:
        return _run_check(args)
    return _run_once(args)


def _run_check(args: argparse.Namespace) -> int:
    """Build twice and diff. CI uses this to enforce reproducibility."""
    out_a = Path(args.out + "1")
    out_b = Path(args.out + "2")
    args1 = argparse.Namespace(**vars(args))
    args1.out = str(out_a)
    args1.reproducible = True
    args1.check = False
    rc = _run_once(args1)
    if rc != 0:
        return rc
    args2 = argparse.Namespace(**vars(args))
    args2.out = str(out_b)
    args2.reproducible = True
    args2.check = False
    rc = _run_once(args2)
    if rc != 0:
        return rc

    diff = subprocess.run(
        ["diff", "-r", str(out_a), str(out_b)],
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        sys.stderr.write(
            "[build] FAIL: two consecutive --reproducible builds disagree.\n"
        )
        sys.stderr.write(diff.stdout[:4000])
        return 1
    _log("CHECK passed: two builds are byte-identical")
    return 0


def _run_once(args: argparse.Namespace) -> int:
    opts = BuildOptions(
        out_dir=Path(args.out).resolve(),
        reproducible=args.reproducible or args.check,
        check=False,
        skip_legacy=args.skip_legacy,
        only=tuple(args.only),
        verbose=args.verbose,
    )
    if opts.reproducible:
        os.environ["LC_ALL"] = "C"
        os.environ["TZ"] = "UTC"
        os.environ["PYTHONHASHSEED"] = "0"
        os.environ.setdefault("SOURCE_DATE_EPOCH", _git_commit_epoch())

    t0 = time.monotonic()
    _ensure_clean_out(opts.out_dir)
    _log(f"output directory: {opts.out_dir}")
    _run_legacy_build(opts)

    catalog = _stage_parse(opts) if "parse" in opts.only else parse_content.empty()

    if "assets" in opts.only:
        _stage_assets(opts, catalog)
    if "pages" in opts.only:
        _stage_pages(opts, catalog)
    if "api" in opts.only:
        _stage_api(opts, catalog)
    if "search" in opts.only:
        _stage_search(opts, catalog)
    if "exports" in opts.only:
        _stage_exports(opts, catalog)
    if "meta" in opts.only:
        _stage_meta(opts, catalog)
    if "public" in opts.only:
        _stage_public(opts)
    if "html_rewrite" in opts.only:
        _stage_html_rewrite(opts, catalog)
    if "integrity" in opts.only:
        _stage_integrity(opts)
    if "build_info" in opts.only:
        _stage_build_info(opts, catalog)

    bytes_total, files_total = _measure(opts.out_dir)
    _log(
        f"DONE  {files_total} files, {bytes_total / 1024 / 1024:.1f} MiB",
        t0,
    )
    return 0


def _measure(out: Path) -> tuple[int, int]:
    n_files = 0
    n_bytes = 0
    for p in out.rglob("*"):
        if p.is_file():
            n_files += 1
            n_bytes += p.stat().st_size
    return n_bytes, n_files


if __name__ == "__main__":
    sys.exit(main())
