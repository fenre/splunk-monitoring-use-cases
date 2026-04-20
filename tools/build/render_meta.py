"""tools.build.render_meta — sitemap-index, llms.txt, feed.xml, openapi.yaml.

Owns the discovery surface:

* ``/sitemap.xml``                    — sitemap-index (top-level)
* ``/sitemap-pages.xml``              — landing + browse + api
* ``/sitemap-categories.xml``         — every category landing
* ``/sitemap-regulations.xml``        — every regulation rollup + index
* ``/sitemap-ucs-NN.xml``             — UCs sharded at 25 000/file
* ``/manifest.json``                  — global path index for machine consumers
* ``/manifest.webmanifest``           — PWA install manifest
* ``/feed.xml``                       — Atom feed of last 50 changed UCs
* ``/robots.txt``
* ``/.well-known/security.txt``

The ``ssg-regulation-equipment`` todo activates the sharded sitemap and
``manifest.json`` writers; both unconditionally overwrite any artefact a
prior stage may have produced so the SSG output is the canonical source
for crawlers.

LLM stubs (``llms.txt``, ``llms-full.txt``) and the legacy
``openapi.yaml`` are still authored by the v6 ``build.py`` pass and
mirrored into ``dist/`` by ``_stage_public``; the cleanup-and-docs todo
moves their authorship into this module.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from . import render_pages as _render_pages
from .parse_content import Catalog


# Hosting URL — used in absolute <loc> entries. Flipped to splunk-monitoring.io
# once the Pages+CDN cutover lands in distribution-channels.
SITE_URL = "https://fenre.github.io/splunk-monitoring-use-cases"


def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    _write_robots(out_dir)
    _write_pwa_manifest(out_dir)
    _write_security_txt(out_dir)
    _write_atom_feed(catalog, out_dir, reproducible=reproducible)
    _write_sitemap(catalog, out_dir, reproducible=reproducible)
    _write_machine_manifest(catalog, out_dir, reproducible=reproducible)
    _write_openapi_v2(catalog, out_dir, reproducible=reproducible)


def _write_robots(out_dir: Path) -> None:
    p = out_dir / "robots.txt"
    if p.exists():
        return
    p.write_text(
        "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                "Disallow: /assets/search-shard-",
                "",
                f"Sitemap: {SITE_URL}/sitemap.xml",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_pwa_manifest(out_dir: Path) -> None:
    p = out_dir / "manifest.webmanifest"
    if p.exists():
        return
    from urllib.parse import urlparse
    base_path = urlparse(SITE_URL).path.rstrip("/")
    payload: dict[str, Any] = {
        "name": "Splunk Monitoring Use Cases",
        "short_name": "Splunk UCs",
        "description": "Vendor-curated catalog of Splunk monitoring use cases.",
        "start_url": f"{base_path}/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#211d1c",
        "icons": [
            {"src": f"{base_path}/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": f"{base_path}/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": f"{base_path}/icon.svg", "sizes": "any", "type": "image/svg+xml"},
        ],
    }
    p.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_security_txt(out_dir: Path) -> None:
    p = out_dir / ".well-known" / "security.txt"
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "\n".join(
            [
                "Contact: https://github.com/fenre/splunk-monitoring-use-cases/security/advisories/new",
                "Expires: 2099-12-31T23:59:59Z",
                "Preferred-Languages: en",
                "Canonical: https://fenre.github.io/splunk-monitoring-use-cases/.well-known/security.txt",
                "Acknowledgments: https://github.com/fenre/splunk-monitoring-use-cases/security/advisories",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_atom_feed(catalog: Catalog, out_dir: Path, *, reproducible: bool) -> None:
    """Emit ``dist/feed.xml`` — Atom feed of the last 50 added UCs.

    Pulled from ``catalog.recently_added`` plus reverse-chronological
    fallback over UC IDs. Per Atom RFC 4287.
    """
    p = out_dir / "feed.xml"
    if p.exists():
        return

    site = "https://fenre.github.io/splunk-monitoring-use-cases"
    updated = "1970-01-01T00:00:00Z" if reproducible else datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    entries: list[str] = []
    seen: set[str] = set()
    for uc_id in catalog.recently_added[:50]:
        uc = catalog.uc_by_id(uc_id)
        if not uc or uc_id in seen:
            continue
        seen.add(uc_id)
        title = uc.get("n", uc_id)
        link = f"{site}/uc/UC-{uc_id}/"
        entries.append(_atom_entry(uc_id, title, link, updated))

    if not entries:
        for _cat, _sub, uc in catalog.iter_ucs():
            uc_id = uc.get("i", "")
            if not uc_id or uc_id in seen:
                continue
            seen.add(uc_id)
            title = uc.get("n", uc_id)
            link = f"{site}/uc/UC-{uc_id}/"
            entries.append(_atom_entry(uc_id, title, link, updated))
            if len(entries) >= 50:
                break

    body = "\n".join(
        [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<feed xmlns="http://www.w3.org/2005/Atom">',
            f"  <title>Splunk Monitoring Use Cases</title>",
            f"  <link href=\"{site}/feed.xml\" rel=\"self\" />",
            f"  <link href=\"{site}/\" />",
            f"  <id>{site}/</id>",
            f"  <updated>{updated}</updated>",
            *entries,
            "</feed>",
            "",
        ]
    )
    p.write_text(body, encoding="utf-8")


def _atom_entry(uc_id: str, title: str, link: str, updated: str) -> str:
    return "\n".join(
        [
            "  <entry>",
            f"    <id>{escape(link)}</id>",
            f"    <title>{escape(f'UC-{uc_id} {title}')}</title>",
            f'    <link href="{escape(link)}" />',
            f"    <updated>{updated}</updated>",
            "  </entry>",
        ]
    )


# ---------------------------------------------------------------------------
# Sharded sitemap-index — owned by render_meta from v7.0 onward
# ---------------------------------------------------------------------------


_UC_SHARD_SIZE = 25_000  # well under the 50 K URL hard cap of the spec


def _write_sitemap(catalog: Catalog, out_dir: Path, *, reproducible: bool) -> None:
    """Emit the sitemap-index plus per-section sitemaps.

    The legacy build's flat ``sitemap.xml`` is overwritten unconditionally
    so search engines see the new SSG URL surface even on partial builds.
    """
    cat_slug_for = _render_pages._build_slug_map(catalog)
    cat_name_for = {
        cat.get("i"): str(cat.get("n", ""))
        for cat in catalog.categories
        if cat.get("i") is not None
    }
    fw_slug_for, alias_to_fw_id = _render_pages._build_regulation_alias_index(catalog)

    today = _date_only(reproducible=reproducible)

    pages_locs: list[str] = [
        f"{SITE_URL}/",
        f"{SITE_URL}/browse/",
        f"{SITE_URL}/regulation/",
        f"{SITE_URL}/api/",
    ]

    cat_locs: list[str] = []
    for cat in sorted(catalog.categories, key=lambda c: c.get("i", 0)):
        cid = cat.get("i")
        if cid is None:
            continue
        slug = cat_slug_for.get(cid)
        if not slug:
            continue
        cat_locs.append(f"{SITE_URL}/category/{slug}/")

    matched_fw_ids: set[str] = set()
    for _cat, _sub, uc in catalog.iter_ucs():
        for tag in uc.get("regs") or []:
            fw_id = _render_pages._resolve_alias(tag, alias_to_fw_id)
            if fw_id:
                matched_fw_ids.add(fw_id)

    reg_locs: list[str] = [
        f"{SITE_URL}/regulation/{fw_slug_for[fw_id]}/"
        for fw_id in sorted(matched_fw_ids)
        if fw_id in fw_slug_for
    ]

    uc_locs: list[str] = []
    for cat, sub, uc in catalog.iter_ucs():
        uc_id = uc.get("i")
        if uc_id:
            uc_locs.append(f"{SITE_URL}/uc/UC-{uc_id}/")

    if reproducible:
        cat_locs.sort()
        reg_locs.sort()
        uc_locs.sort()

    _write_urlset(out_dir / "sitemap-pages.xml", pages_locs, lastmod=today)
    _write_urlset(out_dir / "sitemap-categories.xml", cat_locs, lastmod=today)
    _write_urlset(out_dir / "sitemap-regulations.xml", reg_locs, lastmod=today)

    # Stale UC shards from prior builds (e.g. when the catalogue shrinks)
    # would otherwise linger and resolve to 404 entries; clear them first.
    for stale in out_dir.glob("sitemap-ucs-*.xml"):
        stale.unlink()

    uc_shard_files: list[str] = []
    if uc_locs:
        for shard_idx, start in enumerate(range(0, len(uc_locs), _UC_SHARD_SIZE), start=1):
            shard = uc_locs[start:start + _UC_SHARD_SIZE]
            fname = f"sitemap-ucs-{shard_idx:02d}.xml"
            _write_urlset(out_dir / fname, shard, lastmod=today)
            uc_shard_files.append(fname)

    _write_sitemap_index(
        out_dir / "sitemap.xml",
        sitemaps=[
            "sitemap-pages.xml",
            "sitemap-categories.xml",
            "sitemap-regulations.xml",
            *uc_shard_files,
        ],
        lastmod=today,
    )


def _write_urlset(path: Path, locs: list[str], *, lastmod: str) -> None:
    """Write a single sitemap urlset; overwrites any existing file."""
    body_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in locs:
        body_parts.append(
            f"  <url><loc>{escape(loc)}</loc>"
            f"<lastmod>{escape(lastmod)}</lastmod></url>"
        )
    body_parts.append("</urlset>")
    body_parts.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body_parts), encoding="utf-8")


def _write_sitemap_index(path: Path, *, sitemaps: list[str], lastmod: str) -> None:
    body_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for fname in sitemaps:
        body_parts.append(
            f"  <sitemap><loc>{escape(SITE_URL)}/{escape(fname)}</loc>"
            f"<lastmod>{escape(lastmod)}</lastmod></sitemap>"
        )
    body_parts.append("</sitemapindex>")
    body_parts.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body_parts), encoding="utf-8")


# ---------------------------------------------------------------------------
# Machine-consumer manifest (`/manifest.json`)
# ---------------------------------------------------------------------------


def _write_machine_manifest(catalog: Catalog, out_dir: Path, *, reproducible: bool) -> None:
    """Emit ``/manifest.json`` — top-level URL index for machines.

    This is *not* the PWA manifest (that lives at ``/manifest.webmanifest``).
    ``manifest.json`` is a discovery sidecar consumed by automation tools
    that want the full SSG path tree without crawling. Each entry pairs an
    HTML URL with its JSON twin and groups by section so a downstream
    pipeline can subscribe to deltas per section.
    """
    cat_slug_for = _render_pages._build_slug_map(catalog)
    fw_slug_for, alias_to_fw_id = _render_pages._build_regulation_alias_index(catalog)

    matched_fw_ids: set[str] = set()
    for _cat, _sub, uc in catalog.iter_ucs():
        for tag in uc.get("regs") or []:
            fw_id = _render_pages._resolve_alias(tag, alias_to_fw_id)
            if fw_id:
                matched_fw_ids.add(fw_id)

    payload: dict[str, Any] = {
        "$schema": "/schemas/v2/manifest.schema.json",
        "version": "2.0.0",
        "generatedAt": _timestamp(reproducible=reproducible),
        "site": SITE_URL,
        "endpoints": {
            "landing":           f"{SITE_URL}/",
            "browse":            f"{SITE_URL}/browse/",
            "regulationsIndex":  f"{SITE_URL}/regulation/",
            "regulationsJson":   f"{SITE_URL}/regulation/index.json",
            "catalogIndex":      f"{SITE_URL}/api/catalog-index.json",
            "sitemap":           f"{SITE_URL}/sitemap.xml",
            "atom":              f"{SITE_URL}/feed.xml",
            "openapi":           f"{SITE_URL}/openapi.yaml",
            "llms":              f"{SITE_URL}/llms.txt",
            "llmsFull":          f"{SITE_URL}/llms-full.txt",
        },
        "stats": {
            "useCases":         catalog.uc_count,
            "categories":       len(catalog.categories),
            "regulations":      len(matched_fw_ids),
            "totalRegulations": len(catalog.regulations),
        },
        "categories": [
            {
                "id":    cat.get("i"),
                "name":  cat.get("n"),
                "slug":  cat_slug_for.get(cat.get("i"), ""),
                "html":  f"{SITE_URL}/category/{cat_slug_for.get(cat.get('i'), '')}/",
                "json":  f"{SITE_URL}/category/{cat_slug_for.get(cat.get('i'), '')}/index.json",
                "useCases": sum(len(s.get("u", [])) for s in cat.get("s", [])),
            }
            for cat in sorted(catalog.categories, key=lambda c: c.get("i", 0))
            if cat.get("i") is not None
        ],
        "regulations": [
            {
                "id":         fw_id,
                "shortName":  catalog.regulations[fw_id].get("shortName"),
                "name":       catalog.regulations[fw_id].get("name"),
                "slug":       fw_slug_for[fw_id],
                "html":       f"{SITE_URL}/regulation/{fw_slug_for[fw_id]}/",
                "json":       f"{SITE_URL}/regulation/{fw_slug_for[fw_id]}/index.json",
            }
            for fw_id in sorted(matched_fw_ids)
            if fw_id in fw_slug_for and fw_id in catalog.regulations
        ],
    }

    body = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=reproducible,
        indent=2,
    )
    (out_dir / "manifest.json").write_text(body + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# OpenAPI v2 — describes the SSG endpoint shape (per-UC, per-category,
# per-regulation, manifest, sitemap, atom feed). The legacy /openapi.yaml
# stays in place for the v6 surface; the cleanup-and-docs todo retires it.
# ---------------------------------------------------------------------------


def _write_openapi_v2(catalog: Catalog, out_dir: Path, *, reproducible: bool) -> None:
    api_dir = out_dir / "api" / "v2"
    api_dir.mkdir(parents=True, exist_ok=True)
    spec = _OPENAPI_V2_TEMPLATE.format(
        site_url=SITE_URL,
        generated_at=_timestamp(reproducible=reproducible),
        uc_count=catalog.uc_count,
        cat_count=len(catalog.categories),
        reg_count=len(catalog.regulations),
    )
    (api_dir / "openapi.yaml").write_text(spec, encoding="utf-8")


# Single-source-of-truth OpenAPI 3.1 description of the v7.0 SSG surface.
# Hand-curated; the cleanup-and-docs todo will replace this with a
# generated artefact once schema/openapi codegen lands.
_OPENAPI_V2_TEMPLATE = """openapi: 3.1.0
info:
  title: Splunk Monitoring Use Cases — SSG Catalog API (v2)
  summary: |
    Read-only static API describing every per-UC, per-category, and
    per-regulation rollup emitted by the v7.0 SSG pipeline.
  description: |
    Every endpoint is a plain ``GET`` returning a static JSON file
    (``index.json`` next to a paired ``index.html``) generated by
    ``tools/build/build.py``. There is no authentication, no rate
    limiting, and no server-side processing.

    Generated at: {generated_at}
    Catalogue: {uc_count} use cases, {cat_count} categories,
    {reg_count} regulatory frameworks.

    See ``/manifest.json`` for a programmatic index of every URL.
  version: "2.0.0"
  license:
    name: MIT
    url: https://github.com/fenre/splunk-monitoring-use-cases/blob/main/LICENSE
servers:
  - url: {site_url}
    description: GitHub Pages (production)
  - url: http://localhost:8000
    description: Local static file server
tags:
  - name: catalog
    description: Catalogue-wide index and discovery sidecars.
  - name: use-case
    description: Per-use-case JSON twin paired with a static HTML page.
  - name: category
    description: Per-category landing JSON twin.
  - name: regulation
    description: Per-regulation rollup JSON twin.
  - name: discovery
    description: Crawler and bot discovery surface.
paths:
  /manifest.json:
    get:
      tags: [catalog]
      summary: Site manifest — global URL index for machines.
      responses:
        "200":
          description: JSON object with endpoints, stats, categories, regulations.
          content:
            application/json:
              schema:
                $ref: '/schemas/v2/manifest.schema.json'
  /api/catalog-index.json:
    get:
      tags: [catalog]
      summary: Compact catalogue index — bootstraps /browse/.
      responses:
        "200":
          description: JSON array of slim UC records (i, n, c, d, cat, sub, mtype, regs, search_blob).
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
  /uc/{{useCaseId}}/index.json:
    get:
      tags: [use-case]
      summary: Per-use-case JSON twin.
      parameters:
        - in: path
          name: useCaseId
          required: true
          schema:
            type: string
            pattern: '^UC-\\d+\\.\\d+\\.\\d+$'
          description: 'e.g. UC-1.1.1'
      responses:
        "200":
          description: JSON twin of the corresponding /uc/UC-X.Y.Z/index.html page.
          content:
            application/json:
              schema:
                $ref: '/schemas/v2/uc.schema.json'
        "404":
          description: Use case not found.
  /category/{{slug}}/index.json:
    get:
      tags: [category]
      summary: Per-category JSON twin.
      parameters:
        - in: path
          name: slug
          required: true
          schema:
            type: string
            pattern: '^[a-z0-9-]+$'
      responses:
        "200":
          description: JSON twin of the per-category landing.
          content:
            application/json:
              schema:
                $ref: '/schemas/v2/category.schema.json'
        "404":
          description: Category not found.
  /regulation/index.json:
    get:
      tags: [regulation]
      summary: Index of every regulation rollup with non-zero UCs.
      responses:
        "200":
          description: JSON object listing all matched frameworks (descending UC count).
          content:
            application/json:
              schema:
                $ref: '/schemas/v2/regulation-index.schema.json'
  /regulation/{{slug}}/index.json:
    get:
      tags: [regulation]
      summary: Per-regulation JSON twin grouping UCs by category.
      parameters:
        - in: path
          name: slug
          required: true
          schema:
            type: string
            pattern: '^[a-z0-9-]+$'
      responses:
        "200":
          description: JSON twin of the per-regulation rollup.
          content:
            application/json:
              schema:
                $ref: '/schemas/v2/regulation.schema.json'
        "404":
          description: Framework not found or has zero matched UCs.
  /sitemap.xml:
    get:
      tags: [discovery]
      summary: Sharded sitemap-index.
      responses:
        "200":
          description: XML sitemap-index pointing at per-section sitemaps.
          content:
            application/xml: {{}}
  /feed.xml:
    get:
      tags: [discovery]
      summary: Atom feed of the last 50 changed UCs.
      responses:
        "200":
          description: Atom 1.0 feed.
          content:
            application/atom+xml: {{}}
"""


# ---------------------------------------------------------------------------
# Shared timestamp helper
# ---------------------------------------------------------------------------


def _date_only(*, reproducible: bool) -> str:
    return _timestamp(reproducible=reproducible)[:10]


def _timestamp(*, reproducible: bool) -> str:
    if reproducible:
        import os
        epoch = os.environ.get("SOURCE_DATE_EPOCH", "0")
        try:
            ts = int(epoch)
        except ValueError:
            ts = 0
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
