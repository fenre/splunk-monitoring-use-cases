"""tools.build — v7.0 build pipeline for the Splunk monitoring use case catalog.

This package owns the entire static-site build for splunk-monitoring.io.
It is intentionally stdlib-only (no third-party dependencies) so that the
build runs deterministically on any GitHub Actions ubuntu-latest runner
without `pip install`.

Modules
-------
build           — CLI entrypoint. Orchestrates the pipeline.
parse_content   — Reads the source-of-truth (content/, data/, src/) into
                  an in-memory Catalog object that every renderer consumes.
render_assets   — Bundles, fingerprints, and inlines CSS/JS/images.
render_pages    — Static-site generator for /, /browse/, /uc/, /category/,
                  /regulation/, /equipment/, /embed/.
render_api      — Emits /api/v1/, /api/catalog-index.json, /api/cat-N.json.
render_exports  — Bulk multi-format exports (CSV, OSCAL, STIX, ZIP).
render_meta     — sitemap-index, llms.txt, llms-full.txt, feed.xml,
                  openapi.yaml, robots.txt, manifest.webmanifest.
integrity       — dist/integrity.json (SHA-256 manifest of every artefact).
build_info      — dist/BUILD-INFO.json (git SHA, schema versions, counts).

Stability
---------
The CLI surface (`python3 tools/build/build.py --out dist`) is stable per
docs/architecture.md. The internal module API may change between v7.x
minor versions; only `build:main` is a public entry point.
"""

__version__ = "7.0.0-dev"
__all__ = ["build"]
