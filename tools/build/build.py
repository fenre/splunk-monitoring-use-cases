#!/usr/bin/env python3
"""tools.build.build — v7.0 build pipeline entrypoint.

Usage
-----
    python3 tools/build/build.py --out dist
    python3 tools/build/build.py --out dist --reproducible
    python3 tools/build/build.py --out dist --check
    python3 tools/build/build.py --out dist --only parse api

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
While the per-stage native renderers are landing, parts of the pipeline
still rely on the v6 root ``build.py``. Legacy parsing loads that module
through ``parse_content._legacy_module()``, which imports root ``build.py``
via ``importlib`` (as a Python module), not by spawning it as a subprocess.
As each native renderer ships, the corresponding section of the legacy pass
is short-circuited; v7.1 removes the legacy pass entirely.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from build import build_info, integrity, parse_content  # noqa: E402
from build import render_api, render_assets, render_exports  # noqa: E402
from build import render_meta, render_metrics, render_pages, render_search  # noqa: E402
from build import render_telemetry  # noqa: E402

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
    "metrics",
)


@dataclass
class BuildOptions:
    out_dir: Path
    reproducible: bool = False
    check: bool = False
    only: tuple[str, ...] = ALL_STAGES
    verbose: bool = False


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
    """Copy static project assets into dist/.

    Copies two kinds of content:
    1. ``public/`` directory — verbatim static assets (favicons, etc.)
    2. Project-root files and directories that the deployed site serves
       but are NOT generated by the v7 render stages (static HTML pages,
       JS data files, content directories like docs/ and schemas/).

    The v7 render stages own all dynamic outputs:
    - ``render_api.py``   → ``api/`` (cat-N.json, catalog-index.json, v1/)
    - ``render_pages.py`` → ``index.html``, ``uc/``, ``category/``, ``browse/``
    - ``render_meta.py``  → ``sitemap*.xml``, ``llms*.txt``, ``feed.xml``
    - ``render_assets.py``→ ``assets/*.css``, ``assets/*.js``
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

    _copy_project_assets(out)
    _log("public/ + project assets copied", t0)


def _copy_project_assets(out: Path) -> None:
    """Copy project-root files and directories into dist/.

    These are static assets and content directories that the site serves
    directly. They are NOT generated by any build stage — they exist in
    the repo as committed files.

    Excludes: source-only directories (.git, tools, scripts, src, content,
    mcp, .github, .cursor), build outputs (dist), and anything the v7
    render stages own (api/cat-*.json, api/catalog-index.json).
    """
    skip_dirs = {
        ".git", ".github", ".cursor", ".idea", ".vscode",
        "node_modules", ".venv", ".venv-feasibility", "venv", "env",
        "dist", "tools", "scripts", "mcp", "src", "content",
        "public", "terminals", "build", "test-results", "other",
        "__pycache__", "legacy", "agent-notes", "agent-transcripts",
    }
    skip_extensions = {".pyc", ".pyo", ".pyd", ".swp", ".swo"}

    # Files owned by v7 render stages — never overwrite from project root.
    v7_owned = re.compile(
        r"^api/cat-\d+\.json$|^api/catalog-index\.json$|^api/manifest\.json$"
    )

    # Static top-level files the site needs.
    for fname in _PROJECT_STATIC_FILES:
        src = PROJECT_ROOT / fname
        if not (src.exists() and src.is_file()):
            continue
        dst = out / fname
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if fname == "index.html":
            browse_dst = out / "browse" / "index.html"
            browse_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, browse_dst)

    # Content directories the site serves directly.
    for dname in _PROJECT_CONTENT_DIRS:
        src = PROJECT_ROOT / dname
        if not src.exists() or not src.is_dir():
            continue
        for path in src.rglob("*"):
            if path.is_dir():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.suffix in skip_extensions:
                continue
            rel = path.relative_to(PROJECT_ROOT)
            if v7_owned.match(str(rel)):
                continue
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)

    # Companion tools that ship as public content.
    for tool_rel in _COMPANION_TOOLS:
        src = PROJECT_ROOT / Path(tool_rel)
        if not src.exists() or not src.is_dir():
            continue
        for path in src.rglob("*"):
            if path.is_dir():
                continue
            rel_to_tool = path.relative_to(src)
            if any(part in skip_dirs for part in rel_to_tool.parts):
                continue
            if path.suffix in skip_extensions:
                continue
            rel = path.relative_to(PROJECT_ROOT)
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)


_PROJECT_STATIC_FILES = (
    "index.html",
    "catalog.json",
    "openapi.yaml",
    "scorecard.html",
    "scorecard.json",
    "regulatory-primer.html",
    "guide-reader.html",
    "clause-navigator.html",
    "compliance-story.html",
    "api-docs.html",
    "graph.html",
    "graph-data.json",
    "docs.html",
    "non-technical-view.js",
    "docs-uc-map.js",
    "provenance.json",
    "provenance.js",
    "mitre_techniques.json",
    "recently-added.json",
    "llms.txt",
    "llm.txt",
    "llms-full.txt",
    "ai.txt",
    "robots.txt",
    "AGENTS.md",
    "AGENTS-EXAMPLES.md",
    "favicon.ico",
    "favicon.svg",
    "icon.svg",
    "icon-192.png",
    "icon-512.png",
    "og-image.png",
    "og-image-1200.png",
    ".nojekyll",
    "CNAME",
)

_PROJECT_CONTENT_DIRS = (
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
    "vendor",
)

_COMPANION_TOOLS = (
    "tools/data-sizing",
)


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




def _site_base_path() -> str:
    """Extract the URL path prefix from the SITE_URL env var or render_pages default.

    Returns e.g. ``/splunk-monitoring-use-cases`` for a GitHub Pages
    project site, or ``""`` for a root deployment.
    """
    from urllib.parse import urlparse
    site_url = os.environ.get("SITE_URL", render_pages.SITE_URL_DEFAULT).rstrip("/")
    return urlparse(site_url).path.rstrip("/")


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
    css_name = catalog.asset_hashes.get("styles_css")
    js_name = catalog.asset_hashes.get("app_js")
    if not css_name and not js_name:
        _log("html_rewrite skipped (no bundled assets)")
        return

    base_path = _site_base_path()

    # Process every SPA copy: the root and the /browse/ alias.
    candidates = [
        opts.out_dir / "index.html",
        opts.out_dir / "browse" / "index.html",
    ]
    total_saved = 0
    rewrote = 0
    for index_path in candidates:
        if not index_path.exists():
            continue
        # Skip if this is the SSG landing (not the SPA).
        if _looks_like_ssg_landing(index_path):
            continue

        html = index_path.read_text(encoding="utf-8")
        original_size = len(html)
        use_root_abs = index_path.parent != opts.out_dir
        if css_name:
            html = _swap_inline_style(html, css_name, catalog.critical_css, root_abs=use_root_abs, base_path=base_path)
        if js_name:
            html = _swap_inline_script(html, js_name, root_abs=use_root_abs, base_path=base_path)
        html = _drop_legacy_data_script(html)
        if base_path:
            html = _inject_base_path_config(html, base_path)
        if use_root_abs:
            html = _rewrite_relative_refs_to_root_abs(html, base_path=base_path)
        index_path.write_text(html, encoding="utf-8")
        total_saved += original_size - len(html)
        rewrote += 1

    # The legacy build.py mirror may have put a copy of data.js back into
    # dist/. Now that nothing references it, evict it so we don't ship the
    # 39 MB payload behind everyone's back.
    legacy_data_js = opts.out_dir / "data.js"
    if legacy_data_js.exists():
        legacy_data_js.unlink()

    _log(
        f"html_rewrite: {rewrote} SPA copies processed "
        f"({total_saved / 1024:.1f} KiB saved)",
        t0,
    )


def _swap_inline_style(html: str, css_name: str, critical_css: str, *, root_abs: bool = False, base_path: str = "") -> str:
    """Replace the first ``<style>...</style>`` block with bundle refs."""
    start = html.find("<style>")
    if start == -1:
        return html
    end = html.find("</style>", start)
    if end == -1:
        return html
    end += len("</style>")
    href_prefix = f"{base_path}/assets/" if root_abs else "assets/"
    replacement = (
        f"<style>{critical_css}</style>\n"
        f'<link rel="preload" href="{href_prefix}{css_name}" as="style" '
        f"onload=\"this.onload=null;this.rel='stylesheet'\">\n"
        f'<noscript><link rel="stylesheet" href="{href_prefix}{css_name}"></noscript>'
    )
    return html[:start] + replacement + html[end:]


def _swap_inline_script(html: str, js_name: str, *, root_abs: bool = False, base_path: str = "") -> str:
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
    src_prefix = f"{base_path}/assets/" if root_abs else "assets/"
    replacement = f'<script defer src="{src_prefix}{js_name}"></script>'
    return html[:start] + replacement + html[end:]


def _inject_base_path_config(html: str, base_path: str) -> str:
    """Inject a ``<script>`` block that sets the SPA base-path overrides.

    The SPA scripts (00-loader.js, 06-search.js) check for
    ``window.__CATALOG_API_BASE`` and ``window.__CATALOG_ASSETS_BASE``
    before falling back to root-absolute ``/api`` and ``/assets/``.
    For GitHub Pages project sites the base path is non-empty
    (e.g. ``/splunk-monitoring-use-cases``), so the overrides are needed.

    Also exposes ``window.__SITE_BASE_PATH`` so SPA code that builds
    links programmatically (e.g. ``window.open`` into the companion
    Data Sizing Tool under ``/tools/data-sizing/``) can produce a
    root-absolute URL that survives being served from ``/browse/``.
    """
    if not base_path:
        return html
    config_script = (
        f'<script>'
        f'window.__SITE_BASE_PATH="{base_path}";'
        f'window.__CATALOG_API_BASE="{base_path}/api";'
        f'window.__CATALOG_ASSETS_BASE="{base_path}/assets";'
        f'</script>\n'
    )
    # Insert just before </head> so the globals are available before any
    # deferred script runs.
    marker = "</head>"
    idx = html.find(marker)
    if idx == -1:
        return html
    return html[:idx] + config_script + html[idx:]


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
    re.compile(r'src="(docs-uc-map\.js)"'),
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
    re.compile(r'href="(docs\.html)"'),
    re.compile(r'href="(guide-reader\.html[^"]*)"'),
    # Legacy nested scripts and links shipped under tools/data-sizing/.
    # Covers both the <script src="..."> bootstrap include and the
    # "Data Sizing Tool" <a href="..."> in the footer / help text, so
    # the /browse/ copy resolves them to the GitHub Pages base path
    # instead of /browse/tools/... (which 404s).
    re.compile(r'src="(tools/data-sizing/[^"#?]+)"'),
    re.compile(r'href="(tools/data-sizing/[^"#?]+)"'),
)


def _rewrite_relative_refs_to_root_abs(html: str, *, base_path: str = "") -> str:
    """Rewrite relative href/src refs in the SPA to root-absolute paths.

    The legacy SPA was authored as a single-page document at the site
    root, so its asset and API references are relative ('assets/foo',
    'api/bar.json'). After relocation to /browse/ those refs would
    resolve to /browse/assets/foo, which 404s. We rewrite them to
    '{base_path}/assets/foo' and '{base_path}/api/bar.json' so the SPA
    works from any depth, including GitHub Pages project subpaths.

    Only rewrites refs that look like first-party paths under known
    top-level directories. Absolute URLs, fragments, mailto:, and
    template strings are left alone.
    """
    prefix = base_path or ""
    for pat in _RELATIVE_REWRITES:
        attr_kind = "src" if pat.pattern.startswith("src=") else "href"
        html = pat.sub(lambda m, k=attr_kind, p=prefix: f'{k}="{p}/' + m.group(1) + '"', html)
    for pat in _TOPLEVEL_FILE_REWRITES:
        attr_kind = "src" if pat.pattern.startswith("src=") else "href"
        html = pat.sub(lambda m, k=attr_kind, p=prefix: f'{k}="{p}/' + m.group(1) + '"', html)
    return html


def _stage_integrity(opts: BuildOptions) -> None:
    t0 = time.monotonic()
    integrity.write(opts.out_dir, reproducible=opts.reproducible)
    _log("integrity.json written", t0)


def _stage_build_info(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    build_info.write(opts.out_dir, catalog, reproducible=opts.reproducible)
    _log("BUILD-INFO.json written", t0)


def _stage_metrics(opts: BuildOptions, catalog: parse_content.Catalog) -> None:
    t0 = time.monotonic()
    render_metrics.render(catalog, opts.out_dir, reproducible=opts.reproducible)
    _log("metrics.json written", t0)


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

    # Stage durations are accumulated here so the metrics stage can
    # emit ``dist/build-telemetry.json`` for perf-regression dashboards.
    # The artefact is only written in non-reproducible mode (see
    # ``render_telemetry.render``); otherwise the wall-clock numbers
    # would break the byte-equal contract enforced by ``--check``.
    stage_telemetry: list[dict[str, Any]] = []

    if "parse" in opts.only:
        _ts = time.monotonic()
        catalog = _stage_parse(opts)
        stage_telemetry.append(
            {"stage": "parse", "duration_ms": int(round((time.monotonic() - _ts) * 1000))}
        )
    else:
        catalog = parse_content.empty()

    _post_parse_stages: list[tuple[str, Any]] = [
        ("assets", lambda: _stage_assets(opts, catalog)),
        ("pages", lambda: _stage_pages(opts, catalog)),
        ("api", lambda: _stage_api(opts, catalog)),
        ("search", lambda: _stage_search(opts, catalog)),
        ("exports", lambda: _stage_exports(opts, catalog)),
        ("meta", lambda: _stage_meta(opts, catalog)),
        ("public", lambda: _stage_public(opts)),
        ("html_rewrite", lambda: _stage_html_rewrite(opts, catalog)),
        ("integrity", lambda: _stage_integrity(opts)),
        ("build_info", lambda: _stage_build_info(opts, catalog)),
        ("metrics", lambda: _stage_metrics(opts, catalog)),
    ]
    for _name, _fn in _post_parse_stages:
        if _name not in opts.only:
            continue
        _ts = time.monotonic()
        _fn()
        stage_telemetry.append(
            {"stage": _name, "duration_ms": int(round((time.monotonic() - _ts) * 1000))}
        )

    total_seconds = time.monotonic() - t0
    render_telemetry.render(
        opts.out_dir,
        stage_telemetry,
        reproducible=opts.reproducible,
        total_seconds=total_seconds,
    )

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
