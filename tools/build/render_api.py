"""tools.build.render_api — emit /api/v1/, /api/catalog-index.json, /api/cat-N.json.

Owns ``dist/api/``:

* ``catalog-index.json``  (UC stubs for browse bootstrap; lazy-loads cat-N.json)
* ``cat-N.json``          (per-category lazy payload; emitted by legacy build today)
* ``manifest.json``       (global path index for machine consumers)
* ``shortlinks.json``     (``/v/{shortid}/`` map)
* ``v1/...``              (versioned API, semver-stable)
* ``v2/...``              (reserved)

Every JSON file SHOULD validate against its declared schema (see
docs/schema-versioning.md). Validation failure is currently a warning to
keep the v7.0 transition unblocked; CI gates promote it to a hard error
once the schema is marked ``stable``.

v7.0-dev behaviour
------------------
The legacy ``build.py`` already writes ``api/cat-N.json`` and
``api/index.json``, and ``scripts/generate_api_surface.py`` writes
``api/v1/``. We trust the legacy pass for those files (they're mirrored
into ``dist/api/`` by ``_mirror_legacy_root_into_dist``). This module
adds the v7-native artefacts on top:

* ``api/catalog-index.json`` — light bootstrap payload (~5 MB JSON,
  ~750 KB gzipped). Replaces the inline ``data.js`` global.
* ``api/manifest.json``      — machine-friendly path index.
* ``api/shortlinks.json``    — placeholder; populated when /v/ ships.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .parse_content import Catalog


# ---------------------------------------------------------------------------
# Field selection for catalog-index.json
# ---------------------------------------------------------------------------

# UC fields that stay out of the lightweight stub — they are the bulk of
# the per-UC payload (full SPL, narrative, references, screenshots) and
# are only ever needed when the user opens a detail panel. The detail
# panel lazy-fetches ``api/cat-{cat}.json`` to fill them in.
_UC_HEAVY_FIELDS = frozenset({
    "q",         # full SPL search string (often >1 KB each)
    "m",         # secondary mappings / matrices
    "md",        # the markdown narrative (the biggest field by far)
    "kfp",       # known false positives
    "refs",      # references list (often big)
    "script",    # Python/PS scripts
    "qs",        # query supplemental notes
    "z",         # zoom-out / why-it-matters narrative
    "sver",      # SPL version notes
    "reqf",      # required fields
    "rby",       # required-by hints
    "dma",       # data-model accelerator hints
    "schema",    # JSON-Schema overrides
    "screenshots",  # PNG/SVG references; not used in cards
})

# Inside ``sapp`` (Splunkbase apps), keep only the ids/names + presence of
# a predecessor list (which drives the "Successor App" chip on the card).
# Strip url/desc/screenshots/predecessor[*].url/predecessor[*].desc — they
# are detail-panel concerns.
_SAPP_KEEP = frozenset({"id", "name", "predecessor"})
_SAPP_PRED_KEEP = frozenset({"id", "name"})


def _trim_sapp(value: Any) -> Any:
    if not isinstance(value, list):
        return value
    out: list[dict[str, Any]] = []
    for app in value:
        if not isinstance(app, dict):
            continue
        slim = {k: v for k, v in app.items() if k in _SAPP_KEEP}
        pred = slim.get("predecessor")
        if isinstance(pred, list):
            slim["predecessor"] = [
                {k: v for k, v in p.items() if k in _SAPP_PRED_KEEP}
                for p in pred
                if isinstance(p, dict)
            ]
        out.append(slim)
    return out


def _stub_uc(uc: dict[str, Any], cat_id: int, sub_id: str) -> dict[str, Any]:
    """Return the catalog-index UC stub for a single use case."""
    stub: dict[str, Any] = {"i": uc.get("i"), "n": uc.get("n", ""), "cat": cat_id, "sub": sub_id}
    for key, value in uc.items():
        if key in {"i", "n"}:
            continue
        if key in _UC_HEAVY_FIELDS:
            continue
        if value is None:
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        if key == "sapp":
            trimmed = _trim_sapp(value)
            if trimmed:
                stub[key] = trimmed
            continue
        stub[key] = value
    return stub


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    api_dir = out_dir / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    _write_catalog_index(catalog, api_dir, reproducible=reproducible)
    _write_path_manifest(catalog, api_dir, reproducible=reproducible)
    _write_shortlinks_placeholder(api_dir, reproducible=reproducible)


# ---------------------------------------------------------------------------
# catalog-index.json
# ---------------------------------------------------------------------------

def _write_catalog_index(catalog: Catalog, api_dir: Path, *, reproducible: bool) -> None:
    """Emit ``dist/api/catalog-index.json`` — the lazy-bootstrap payload.

    Shape locked by ``schemas/v2/catalog-index.schema.json``. Loaded by
    ``src/scripts/00-loader.js`` on cold start when ``window.DATA`` is
    not present. The stubs carry every field the browse / list / filter
    UI needs; the per-UC heavy fields (full SPL, narrative, refs) are
    fetched on demand from ``api/cat-N.json`` when a detail panel opens.
    """
    categories_index: list[dict[str, Any]] = []
    ucs_index: list[dict[str, Any]] = []
    sub_count = 0

    for cat in sorted(catalog.categories, key=lambda c: c.get("i", 0)):
        cat_id_raw = cat.get("i")
        if cat_id_raw is None:
            continue
        cat_id = int(cat_id_raw)
        meta = catalog.cat_meta.get(str(cat_id), {}) or {}
        subs = cat.get("s", [])
        sub_summaries: list[dict[str, Any]] = []
        cat_uc_count = 0

        sub_iter = sorted(subs, key=lambda s: _sort_key(s.get("i", "0.0")))
        for sub in sub_iter:
            sub_id = sub.get("i", "")
            sub_ucs = sub.get("u", [])
            sub_uc_count = 0
            uc_iter = sorted(sub_ucs, key=lambda u: _sort_key(u.get("i", "0.0.0")))
            for uc in uc_iter:
                if not uc.get("i"):
                    continue
                ucs_index.append(_stub_uc(uc, cat_id, sub_id))
                sub_uc_count += 1
            cat_uc_count += sub_uc_count
            sub_count += 1
            sub_summaries.append({
                "i": sub_id,
                "n": sub.get("n", ""),
                "ucs": sub_uc_count,
            })

        cat_entry: dict[str, Any] = {
            "i": cat_id,
            "n": cat.get("n", ""),
            "ucs": cat_uc_count,
            "subs": sub_summaries,
            "lazyHref": f"api/cat-{cat_id}.json",
        }
        if meta.get("icon"):
            cat_entry["icon"] = meta["icon"]
        if meta.get("desc"):
            cat_entry["desc"] = meta["desc"]
        if meta.get("quick"):
            cat_entry["quick"] = meta["quick"]
        categories_index.append(cat_entry)

    regulations_index = _build_regulations_index(catalog)

    payload: dict[str, Any] = {
        "$schema": "/schemas/v2/catalog-index.schema.json",
        "version": "2.0.0",
        "generatedAt": _ts(reproducible),
        "counts": {
            "categories": len(categories_index),
            "subcategories": sub_count,
            "useCases": len(ucs_index),
            "regulations": len(regulations_index),
        },
        "catGroups": _normalise_cat_groups(catalog.cat_groups),
        "catMeta": _normalise_cat_meta(catalog.cat_meta),
        "equipment": catalog.equipment or [],
        "filterFacets": catalog.facets or {},
        "recentlyAdded": _sorted_unique(catalog.recently_added),
        "categories": categories_index,
        "ucs": ucs_index,
        "regulations": regulations_index,
    }

    out_path = api_dir / "catalog-index.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=reproducible, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _normalise_cat_groups(raw: Any) -> dict[str, list[int]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[int]] = {}
    for key, value in raw.items():
        if not isinstance(value, (list, tuple)):
            continue
        cleaned = [int(v) for v in value if isinstance(v, (int, float, str)) and str(v).lstrip("-").isdigit()]
        out[str(key)] = cleaned
    return out


def _normalise_cat_meta(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        out[str(key)] = {
            k: v for k, v in value.items()
            if v is not None and v != ""
        }
    return out


def _sorted_unique(values: Iterable[Any]) -> list[str]:
    seen: dict[str, None] = {}
    for v in values or []:
        if v is None:
            continue
        s = str(v)
        if s and s not in seen:
            seen[s] = None
    return sorted(seen.keys(), key=_sort_key)


def _build_regulations_index(catalog: Catalog) -> list[dict[str, Any]]:
    if not catalog.regulations:
        return []
    uc_counts = _count_ucs_per_regulation(catalog)
    out: list[dict[str, Any]] = []
    for reg_id in sorted(catalog.regulations.keys()):
        reg = catalog.regulations[reg_id]
        if not isinstance(reg, dict):
            continue
        slug = _slug(reg.get("shortName") or reg.get("name") or reg_id)
        entry: dict[str, Any] = {
            "id": reg_id,
            "slug": slug,
            "name": reg.get("name", reg_id),
        }
        if reg.get("shortName"):
            entry["shortName"] = reg["shortName"]
        if isinstance(reg.get("tier"), int):
            entry["tier"] = reg["tier"]
        if isinstance(reg.get("jurisdiction"), list):
            entry["jurisdiction"] = [str(j) for j in reg["jurisdiction"]]
        entry["ucCount"] = uc_counts.get(reg_id, 0)
        entry["lazyHref"] = f"regulation/{slug}/index.json"
        out.append(entry)
    return out


def _count_ucs_per_regulation(catalog: Catalog) -> dict[str, int]:
    """Count distinct UCs per regulation framework, derived from per-UC ``regs`` tags.

    A UC's ``regs`` field is an array of short framework labels such as
    ``"GDPR"``, ``"PCI DSS"``, ``"CMMC 2.0"``. We match each tag (entire
    string, case-insensitive, normalised whitespace/punctuation) against
    the framework's id, name, shortName, and aliases. A few common
    rewrites collapse near-duplicates ("EU NIS2" → "NIS2", "CMMC 2.0"
    → "CMMC"). When a tag carries a clause suffix (e.g. "GDPR Art.32"),
    we also accept a leading-prefix match against the framework token.
    """
    if not catalog.regulations:
        return {}

    rewrites = {
        "eu nis2": "nis2",
        "cmmc 2.0": "cmmc",
        "ccpa/cpra": "ccpa",
        "fisma / fedramp": "fisma",
        "hipaa privacy": "hipaa",
        "hipaa security": "hipaa-security",
        "eu cyber resilience act (cra)": "eu-cra",
        "fca ss1/21 operational resilience": "fca-ss1-21",
    }

    def _norm(value: str) -> str:
        return " ".join(value.strip().lower().split())

    aliases_by_id: dict[str, set[str]] = {}
    for reg_id, reg in catalog.regulations.items():
        if not isinstance(reg, dict):
            continue
        candidates: set[str] = {reg_id, reg.get("name", ""), reg.get("shortName", "")}
        if isinstance(reg.get("aliases"), list):
            for a in reg["aliases"]:
                candidates.add(str(a))
        aliases_by_id[reg_id] = {_norm(c) for c in candidates if c}

    counts: dict[str, set[str]] = {rid: set() for rid in catalog.regulations}
    for _cat, _sub, uc in catalog.iter_ucs():
        regs = uc.get("regs")
        if not isinstance(regs, list):
            continue
        uc_id = uc.get("i")
        if not uc_id:
            continue
        for raw_tag in regs:
            if not isinstance(raw_tag, str):
                continue
            tag = _norm(raw_tag)
            tag = rewrites.get(tag, tag)
            head = tag.split(" ", 1)[0]
            matched = False
            for reg_id, aliases in aliases_by_id.items():
                if tag in aliases:
                    counts[reg_id].add(uc_id)
                    matched = True
                    break
            if matched:
                continue
            for reg_id, aliases in aliases_by_id.items():
                if head and any(head == a or tag.startswith(a + " ") for a in aliases):
                    counts[reg_id].add(uc_id)
                    break
    return {rid: len(ucs) for rid, ucs in counts.items()}


# ---------------------------------------------------------------------------
# manifest.json + shortlinks.json
# ---------------------------------------------------------------------------

def _write_path_manifest(catalog: Catalog, api_dir: Path, *, reproducible: bool) -> None:
    """Emit ``dist/api/manifest.json`` — sitemap-shaped JSON for machines.

    Stable shape per docs/url-scheme.md. Consumers can read this to
    discover every ``/uc/``, ``/category/``, ``/regulation/`` URL without
    crawling.
    """
    manifest: dict[str, Any] = {
        "$schema": "/schemas/v2/manifest.schema.json",
        "version": "2.0.0",
        "generatedAt": _ts(reproducible),
        "counts": {
            "categories": len(catalog.categories),
            "regulations": len(catalog.regulations),
            "useCases": catalog.uc_count,
        },
        "paths": {
            "categories": [],
            "regulations": [],
            "ucs": [],
        },
    }
    for cat in sorted(catalog.categories, key=lambda c: c["i"]):
        slug = _slug(cat.get("n", str(cat["i"])))
        manifest["paths"]["categories"].append({
            "id": cat["i"],
            "slug": slug,
            "html": f"/category/{slug}/",
            "json": f"/category/{slug}/index.json",
            "name": cat.get("n", ""),
        })
        for sub in cat.get("s", []):
            for uc in sub.get("u", []):
                uc_id = uc.get("i", "")
                if not uc_id:
                    continue
                manifest["paths"]["ucs"].append({
                    "id": f"UC-{uc_id}",
                    "html": f"/uc/UC-{uc_id}/",
                    "json": f"/uc/UC-{uc_id}/index.json",
                    "category": cat["i"],
                    "subcategory": sub.get("i", ""),
                    "name": uc.get("n", ""),
                })

    for reg_id, reg in sorted(catalog.regulations.items()):
        manifest["paths"]["regulations"].append({
            "id": reg_id,
            "slug": reg_id,
            "html": f"/regulation/{reg_id}/",
            "json": f"/regulation/{reg_id}/index.json",
            "name": reg.get("name", reg_id) if isinstance(reg, dict) else reg_id,
        })

    out_path = api_dir / "manifest.json"
    out_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=reproducible, indent=2)
        + "\n",
        encoding="utf-8",
    )


def _write_shortlinks_placeholder(api_dir: Path, *, reproducible: bool) -> None:
    out_path = api_dir / "shortlinks.json"
    if out_path.exists():
        return
    payload = {
        "$schema": "/schemas/v2/shortlinks.schema.json",
        "version": "2.0.0",
        "shortlinks": {},
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=reproducible, indent=2)
        + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    out: list[str] = []
    last_dash = False
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
            last_dash = False
        elif not last_dash:
            out.append("-")
            last_dash = True
    s = "".join(out).strip("-")
    return s or "category"


def _ts(reproducible: bool) -> str:
    if reproducible:
        return "1970-01-01T00:00:00Z"
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sort_key(value: Any) -> tuple:
    """Sort UC / subcategory ids numerically (1.10.2 > 1.2.5)."""
    s = str(value or "")
    parts = []
    for chunk in s.split("."):
        try:
            parts.append((0, int(chunk)))
        except ValueError:
            parts.append((1, chunk))
    return tuple(parts)
