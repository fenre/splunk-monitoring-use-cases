"""tools.build.render_assets — bundle, fingerprint, and inline static assets.

Owns ``dist/assets/``: fingerprinted CSS/JS, search-index shards, OG
images, sprite sheets, and the Service Worker.

Pipeline (v7.0)
---------------
1. Concatenate ``src/styles/*.css`` (sorted by filename) into a single
   stylesheet, content-hash it, and write
   ``dist/assets/styles.<hash>.css``.
2. Concatenate ``src/scripts/*.js`` (sorted by filename) into a single
   bundle, content-hash it, and write ``dist/assets/app.<hash>.js``.
3. Capture the critical above-the-fold CSS (tokens + base reset) for
   inlining by the html_rewrite stage. Critical = sources matching
   ``CRITICAL_CSS_PREFIXES`` (default ``("01-", "02-")``).
4. Copy ``src/img/`` and ``src/fonts/`` verbatim into ``dist/assets/``.
5. Record asset filenames + critical CSS on the Catalog so the
   html_rewrite stage can swap inline blocks in ``dist/index.html``
   for ``<link>``/``<script>`` references.

Stability
---------
Every emitted file under ``dist/assets/`` carries a 10-char SHA-256
content hash in its name. Once written, asset filenames are immutable
for the life of that build artefact (see docs/architecture.md).
Sources reference assets via root-relative ``assets/...`` paths so the
bundle works under any GitHub Pages subpath.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .parse_content import Catalog

CRITICAL_CSS_PREFIXES = ("01-", "02-")
HASH_LEN = 10


def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    """Emit ``out_dir/assets/`` and stash bundle hashes on ``catalog``."""
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    src_dir = catalog.project_root / "src"
    if not src_dir.exists():
        return

    css_hash, css_name, critical_css = _bundle_css(src_dir / "styles", assets)
    if css_name:
        catalog.asset_hashes["styles_css"] = css_name
        catalog.asset_hashes["styles_css_sha256"] = css_hash
        catalog.critical_css = critical_css

    js_hash, js_name = _bundle_js(src_dir / "scripts", assets)
    if js_name:
        catalog.asset_hashes["app_js"] = js_name
        catalog.asset_hashes["app_js_sha256"] = js_hash

    _copy_tree_verbatim(src_dir / "img", assets / "img")
    _copy_tree_verbatim(src_dir / "fonts", assets / "fonts")


# ---------------------------------------------------------------------------
# Bundlers
# ---------------------------------------------------------------------------


def _bundle_css(src_styles: Path, assets: Path) -> tuple[str, str, str]:
    """Concat all .css files in ``src_styles`` into one fingerprinted bundle.

    Returns (full_hash, "styles.<hash>.css", critical_css_payload).
    Returns ("", "", "") if no CSS files exist.
    """
    if not src_styles.exists():
        return ("", "", "")
    files = sorted(p for p in src_styles.glob("*.css") if p.is_file())
    if not files:
        return ("", "", "")

    bundle_parts: list[bytes] = []
    critical_parts: list[bytes] = []
    for path in files:
        data = path.read_bytes()
        bundle_parts.append(data)
        if path.name.startswith(CRITICAL_CSS_PREFIXES):
            critical_parts.append(data)

    bundle = b"".join(bundle_parts)
    full_hash = hashlib.sha256(bundle).hexdigest()
    short = full_hash[:HASH_LEN]
    name = f"styles.{short}.css"
    (assets / name).write_bytes(bundle)

    critical = b"".join(critical_parts).decode("utf-8")
    return (full_hash, name, critical)


def _bundle_js(src_scripts: Path, assets: Path) -> tuple[str, str]:
    """Concat all .js files in ``src_scripts`` into one fingerprinted bundle."""
    if not src_scripts.exists():
        return ("", "")
    files = sorted(p for p in src_scripts.glob("*.js") if p.is_file())
    if not files:
        return ("", "")

    bundle = b"".join(p.read_bytes() for p in files)
    full_hash = hashlib.sha256(bundle).hexdigest()
    short = full_hash[:HASH_LEN]
    name = f"app.{short}.js"
    (assets / name).write_bytes(bundle)
    return (full_hash, name)


def _copy_tree_verbatim(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        out_path = dst / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out_path)
