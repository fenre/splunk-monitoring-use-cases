"""tools.build.render_pages — static-site generator for every public page.

Owns these subtrees of ``dist/``:

* ``/index.html``                     — slim landing page
* ``/uc/UC-X.Y.Z/index.html``         — per-UC HTML detail
* ``/uc/UC-X.Y.Z/index.json``         — JSON twin for machines
* ``/category/<slug>/index.html``     — per-category landing
* ``/category/<slug>/index.json``     — JSON twin

The ``ssg-regulation-equipment`` todo extends this module to emit
``/regulation/<slug>/`` and ``/equipment/<slug>/``.

Every HTML page is fully static (works with JS off), carries JSON-LD
(``TechArticle`` + ``HowTo`` + ``BreadcrumbList`` for UCs;
``CollectionPage`` for categories; ``WebSite`` for the landing) plus a
``<link rel="alternate" type="application/json">`` to the JSON twin
and semantic landmarks. See docs/url-scheme.md for the URL contract.

Reproducibility
---------------
With ``reproducible=True``:
* category and UC iteration is sorted by id
* JSON twins use ``sort_keys=True`` and a fixed separator
* timestamps are taken from ``SOURCE_DATE_EPOCH`` (set by build.py)

Threat model
------------
Static pages are pure data — no inline ``<script>`` other than JSON-LD
serialised through ``_helpers.jsonld_script`` which escapes ``</`` to
neutralise tag-injection attempts. CSS is inlined from the trusted
``templates/_css.py`` constant. Asset references are root-absolute so
the SPA at ``/browse/`` and the SSG pages share a single byte-pinned
asset bundle.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .parse_content import Catalog
from .templates import (
    _helpers,
    category as t_category,
    landing as t_landing,
    regulation as t_regulation,
    uc as t_uc,
)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


SITE_URL_DEFAULT = "https://fenre.github.io/splunk-monitoring-use-cases"


def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    """Emit every static HTML page under ``out_dir``."""
    if not catalog.categories:
        return

    ctx = _build_context(catalog, reproducible=reproducible)
    cat_slug_for = _build_slug_map(catalog)
    cat_name_for = {
        cat.get("i"): str(cat.get("n", ""))
        for cat in catalog.categories
        if cat.get("i") is not None
    }

    cats = catalog.categories
    if reproducible:
        cats = sorted(cats, key=lambda c: c.get("i", 0))

    n_uc = 0
    for cat in cats:
        cat_id = cat.get("i")
        if cat_id is None:
            continue
        slug = cat_slug_for.get(cat_id) or _helpers.slug(str(cat.get("n", "")))
        cat_meta = catalog.cat_meta.get(str(cat_id), {}) or catalog.cat_meta.get(cat_id, {}) or {}
        _emit_category(cat, slug=slug, cat_meta=cat_meta, out_dir=out_dir, ctx=ctx, reproducible=reproducible)
        for sub in cat.get("s", []):
            for uc in sub.get("u", []):
                if not uc.get("i"):
                    continue
                _emit_uc(uc, cat=cat, sub=sub, cat_slug=slug, out_dir=out_dir, ctx=ctx, reproducible=reproducible)
                n_uc += 1

    _emit_regulations(
        catalog,
        cat_slug_for=cat_slug_for,
        cat_name_for=cat_name_for,
        out_dir=out_dir,
        ctx=ctx,
        reproducible=reproducible,
    )
    # The SSG landing page is NOT emitted at /index.html — the legacy
    # Cisco Meraki-styled SPA owns the root URL. The SPA is mirrored
    # from the repo's index.html by _stage_public in build.py.


# ---------------------------------------------------------------------------
# Per-page emitters
# ---------------------------------------------------------------------------


def _emit_uc(
    uc: dict,
    *,
    cat: dict,
    sub: dict,
    cat_slug: str,
    out_dir: Path,
    ctx: _helpers.RenderContext,
    reproducible: bool,
) -> None:
    uc_id = str(uc.get("i", ""))
    if not uc_id:
        return
    uc_dir = out_dir / "uc" / f"UC-{uc_id}"
    uc_dir.mkdir(parents=True, exist_ok=True)

    html = t_uc.render_html(uc, cat, sub, cat_slug, ctx=ctx)
    (uc_dir / "index.html").write_text(html, encoding="utf-8")

    twin = t_uc.render_index_json(uc, cat, sub, cat_slug, ctx=ctx)
    _write_json(uc_dir / "index.json", twin, reproducible=reproducible)


def _emit_category(
    cat: dict,
    *,
    slug: str,
    cat_meta: dict,
    out_dir: Path,
    ctx: _helpers.RenderContext,
    reproducible: bool,
) -> None:
    cat_dir = out_dir / "category" / slug
    cat_dir.mkdir(parents=True, exist_ok=True)

    html = t_category.render_html(cat, cat_slug=slug, cat_meta=cat_meta, ctx=ctx)
    (cat_dir / "index.html").write_text(html, encoding="utf-8")

    twin = t_category.render_index_json(cat, cat_slug=slug, cat_meta=cat_meta, ctx=ctx)
    _write_json(cat_dir / "index.json", twin, reproducible=reproducible)


def _emit_landing(
    catalog: Catalog,
    *,
    cat_slug_for: dict[int, str],
    regulation_summaries: list[dict[str, Any]] | None,
    out_dir: Path,
    ctx: _helpers.RenderContext,
) -> None:
    html = t_landing.render_html(
        catalog,
        cat_slug_for=cat_slug_for,
        regulation_summaries=regulation_summaries,
        ctx=ctx,
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def _emit_regulations(
    catalog: Catalog,
    *,
    cat_slug_for: dict[int, str],
    cat_name_for: dict[int, str],
    out_dir: Path,
    ctx: _helpers.RenderContext,
    reproducible: bool,
) -> list[dict[str, Any]]:
    """Emit ``/regulation/<slug>/`` pages plus a ``/regulation/`` index.

    Builds an alias-driven mapping from per-UC ``regs`` strings to
    canonical framework records loaded from ``data/regulations.json``.
    Frameworks with zero matched UCs are silently skipped (the index
    only advertises actionable rollups).

    Returns a list of summary dicts (descending popularity) suitable for
    feeding into the landing page or other discovery surfaces. Each entry
    carries ``id``, ``slug``, ``shortName``, ``name``, ``tier``,
    ``jurisdiction``, ``useCaseCount``.
    """
    if not catalog.regulations:
        return []

    fw_slug_for, alias_to_fw_id = _build_regulation_alias_index(catalog)

    # Group UCs by framework id, copying only the fields the regulation
    # template needs so it never mutates the source catalog rows.
    grouped: dict[str, list[dict[str, Any]]] = {}
    for cat, _sub, uc in catalog.iter_ucs():
        regs_raw = uc.get("regs") or []
        if not regs_raw:
            continue
        matched: set[str] = set()
        for tag in regs_raw:
            fw_id = _resolve_alias(tag, alias_to_fw_id)
            if fw_id:
                matched.add(fw_id)
        if not matched:
            continue
        slim = {
            "i": uc.get("i"),
            "n": uc.get("n"),
            "v": uc.get("v"),
            "c": uc.get("c"),
            "f": uc.get("f"),
            "cat": cat.get("i"),
        }
        for fw_id in matched:
            grouped.setdefault(fw_id, []).append(slim)

    if not grouped:
        return []

    # Render each per-framework rollup.
    framework_rows: list[tuple[dict[str, Any], str, int]] = []
    for fw_id, ucs in grouped.items():
        fw = catalog.regulations.get(fw_id)
        if not fw:
            continue
        slug = fw_slug_for[fw_id]
        ucs_sorted = sorted(
            ucs,
            key=lambda u: _helpers.sort_key(u.get("i", "")),
        )
        out = out_dir / "regulation" / slug
        out.mkdir(parents=True, exist_ok=True)

        html = t_regulation.render_html(
            fw,
            slug=slug,
            ucs=ucs_sorted,
            cat_slug_for=cat_slug_for,
            cat_name_for=cat_name_for,
            ctx=ctx,
        )
        (out / "index.html").write_text(html, encoding="utf-8")

        twin = t_regulation.render_index_json(
            fw,
            slug=slug,
            ucs=ucs_sorted,
            cat_slug_for=cat_slug_for,
            cat_name_for=cat_name_for,
            ctx=ctx,
        )
        _write_json(out / "index.json", twin, reproducible=reproducible)

        framework_rows.append((fw, slug, len(ucs_sorted)))

    # Sort the index by descending UC count, then short name asc, for a
    # deterministic and useful default ordering.
    framework_rows.sort(
        key=lambda row: (
            -row[2],
            str(row[0].get("shortName") or row[0].get("name") or row[0].get("id") or "").lower(),
        )
    )

    index_dir = out_dir / "regulation"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_html = t_regulation.render_index_html(frameworks=framework_rows, ctx=ctx)
    (index_dir / "index.html").write_text(index_html, encoding="utf-8")
    index_payload = t_regulation.render_index_payload(frameworks=framework_rows, ctx=ctx)
    _write_json(index_dir / "index.json", index_payload, reproducible=reproducible)

    return [
        {
            "id":           fw.get("id"),
            "slug":         slug,
            "shortName":    fw.get("shortName"),
            "name":         fw.get("name"),
            "tier":         fw.get("tier"),
            "jurisdiction": fw.get("jurisdiction"),
            "useCaseCount": n,
        }
        for fw, slug, n in framework_rows
    ]


# ---------------------------------------------------------------------------
# Context + helpers
# ---------------------------------------------------------------------------


def _build_context(catalog: Catalog, *, reproducible: bool) -> _helpers.RenderContext:
    """Build the immutable RenderContext threaded through every template."""
    site_url = os.environ.get("SITE_URL", SITE_URL_DEFAULT).rstrip("/")
    asset_styles = catalog.asset_hashes.get("styles_css", "") if catalog.asset_hashes else ""
    asset_app_js = catalog.asset_hashes.get("app_js", "") if catalog.asset_hashes else ""

    uc_title_index, uc_reverse_prereq = _build_uc_prereq_indexes(catalog)

    return _helpers.RenderContext(
        site_url=site_url,
        site_name="Splunk Monitoring Use Cases",
        site_short="Splunk UCs",
        site_tagline=(
            "A vendor-curated catalog of Splunk monitoring use cases."
        ),
        asset_styles=asset_styles,
        asset_app_js=asset_app_js,
        build_id=os.environ.get("GITHUB_SHA", "")[:7],
        generated_at=_iso_timestamp(reproducible=reproducible),
        repo_url=os.environ.get(
            "REPO_URL",
            "https://github.com/fenre/splunk-monitoring-use-cases",
        ),
        uc_reverse_prereq=uc_reverse_prereq,
        uc_title_index=uc_title_index,
    )


def _build_uc_prereq_indexes(
    catalog: Catalog,
) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, ...]]]:
    """Precompute forward + reverse indexes for the prerequisite graph.

    Returns a tuple of:

    * ``uc_title_index``   — ``"UC-X.Y.Z" -> (title, wave)``. ``wave``
      is the canonical ``crawl``/``walk``/``run`` string or ``""`` when
      not set. Used to render tooltips + wave chips on clickable links.
    * ``uc_reverse_prereq`` — ``"UC-X.Y.Z" -> tuple(UC-ids that depend
      on it)``. The tuple is sorted ascending by ``(major, minor, patch)``
      so "Enables" lists render deterministically across builds.

    Unknown IDs, self-references, and cycle detection are handled by the
    authoring validator in ``build.py``; here we merely build the lookup
    structures for templates and silently ignore malformed IDs.
    """
    title_index: dict[str, tuple[str, str]] = {}
    reverse: dict[str, list[str]] = {}
    uc_id_pat = re.compile(r"^UC-(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
    for cat in catalog.categories:
        for sub in cat.get("s", []) or []:
            for uc in sub.get("u", []) or []:
                uid = str(uc.get("i") or "").strip()
                if not uid:
                    continue
                full = f"UC-{uid}"
                title = str(uc.get("n") or uc.get("t") or full)
                wave = str(uc.get("wv") or "").strip().lower()
                title_index[full] = (title, wave)

                pre = uc.get("pre") or []
                if not isinstance(pre, (list, tuple)):
                    continue
                for dep in pre:
                    dep_s = str(dep).strip()
                    if not uc_id_pat.match(dep_s) or dep_s == full:
                        continue
                    reverse.setdefault(dep_s, []).append(full)

    def _sort_key(uc_full: str) -> tuple[int, int, int, str]:
        m = re.match(r"^UC-(\d+)\.(\d+)\.(\d+)$", uc_full)
        if not m:
            return (10**9, 10**9, 10**9, uc_full)
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), uc_full)

    return (
        title_index,
        {k: tuple(sorted(set(v), key=_sort_key)) for k, v in reverse.items()},
    )


def _build_slug_map(catalog: Catalog) -> dict[int, str]:
    """Map ``cat_id`` → URL slug.

    Prefer the slug encoded in the source filename ``cat-NN-<slug>.md``
    so categories keep their canonical short URLs even if the display
    name is reformatted. Falls back to slugifying the display name.
    """
    out: dict[int, str] = {}
    seen_slugs: set[str] = set()
    file_pat = re.compile(r"^cat-(\d{2})-(.+)\.md$")
    file_slug_for: dict[int, str] = {}
    for fname in catalog.files or []:
        m = file_pat.match(fname)
        if m:
            file_slug_for[int(m.group(1))] = m.group(2)

    for cat in sorted(catalog.categories, key=lambda c: c.get("i", 0)):
        cid = cat.get("i")
        if cid is None:
            continue
        slug = file_slug_for.get(cid) or _helpers.slug(str(cat.get("n", "")))
        # Disambiguate any collision by appending the cat id.
        base = slug
        counter = 1
        while slug in seen_slugs:
            slug = f"{base}-{cid}" if counter == 1 else f"{base}-{cid}-{counter}"
            counter += 1
        seen_slugs.add(slug)
        out[cid] = slug
    return out


def _build_regulation_alias_index(
    catalog: Catalog,
) -> tuple[dict[str, str], dict[str, str]]:
    """Compute slug map and alias→framework lookup.

    Returns ``(fw_slug_for, alias_to_fw_id)`` where:
    * ``fw_slug_for`` maps each canonical framework id to its URL slug
      (already disambiguated against collisions).
    * ``alias_to_fw_id`` maps every recognised alias variant (lower-cased
      and whitespace-collapsed) to the canonical framework id. Earlier
      registrations win, so the framework's own id always beats an
      identically named alias on a different framework.

    Recognised aliases for each framework: ``id``, ``shortName``,
    ``name``, every entry in ``aliases``, and a normalised form with
    common version suffixes stripped (e.g. "PCI DSS v4.0" → "PCI DSS").
    """
    fw_slug_for: dict[str, str] = {}
    seen_slugs: set[str] = set()
    alias_to_fw_id: dict[str, str] = {}

    for fw_id in sorted(catalog.regulations):
        fw = catalog.regulations[fw_id]
        base_slug = _helpers.slug(str(fw.get("id") or fw.get("shortName") or fw_id))
        slug = base_slug
        counter = 1
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs.add(slug)
        fw_slug_for[fw_id] = slug

        for raw in _alias_candidates(fw):
            key = _normalise_alias(raw)
            if key and key not in alias_to_fw_id:
                alias_to_fw_id[key] = fw_id

    return fw_slug_for, alias_to_fw_id


def _alias_candidates(fw: dict[str, Any]):
    """Yield every recognised alias for a framework, including stripped variants."""
    for field_ in ("id", "shortName", "name"):
        value = fw.get(field_)
        if value:
            yield str(value)
    for alias in fw.get("aliases") or []:
        if alias:
            yield str(alias)


_VERSION_SUFFIX = re.compile(
    r"\s*(?:[\(\[]?\s*"
    r"(?:v(?:ersion)?\.?\s*)?"
    r"\d+(?:\.\d+)*(?:[a-z]\d*)?"
    r"(?:\s*\([^)]*\))?"
    r"\s*[\)\]]?)\s*$",
    re.IGNORECASE,
)


def _normalise_alias(raw: str) -> str:
    """Lower-case, collapse whitespace, drop trailing version markers.

    "ISO 27001:2022" → "iso 27001"
    "PCI DSS v4.0"   → "pci dss"
    "HIPAA Security Rule" → "hipaa security rule"
    """
    if not raw:
        return ""
    s = str(raw).strip().lower()
    s = re.sub(r"[\s/]+", " ", s)
    s = re.sub(r"[\u2013\u2014]", "-", s)  # en/em dash → ASCII hyphen
    s = re.sub(r":[^\s]*", "", s)          # strip ":2022"
    s = _VERSION_SUFFIX.sub("", s).strip()
    return s


def _resolve_alias(tag: Any, alias_to_fw_id: dict[str, str]) -> str:
    """Map a free-form ``regs`` string to a canonical framework id."""
    if tag is None:
        return ""
    s = str(tag).strip()
    if not s:
        return ""
    key = _normalise_alias(s)
    if key in alias_to_fw_id:
        return alias_to_fw_id[key]
    # Fallback: prefix match on a longer tag (e.g. "ISO 27001 Annex A").
    for known_key, fw_id in alias_to_fw_id.items():
        if known_key and (key.startswith(known_key + " ") or known_key.startswith(key + " ")):
            return fw_id
    return ""


def _iso_timestamp(*, reproducible: bool) -> str:
    if reproducible:
        epoch = os.environ.get("SOURCE_DATE_EPOCH", "0")
        try:
            ts = int(epoch)
        except ValueError:
            ts = 0
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, payload: dict, *, reproducible: bool) -> None:
    """Write ``payload`` as canonical JSON.

    Reproducible builds use ``sort_keys=True``. Either way we emit
    compact form (no whitespace) — the JSON twin is consumed by
    machines first, humans second.
    """
    body = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=reproducible,
        separators=(",", ":"),
    )
    path.write_text(body + "\n", encoding="utf-8")
