"""tools.build.render_legacy_artifacts — emit catalog.json, data.js, llms*.txt.

Repo-overhaul plan §P1 step 2 (PR-4, 2026-05-08): the legacy v6 ``build.py``
script writes ``catalog.json`` / ``data.js`` / ``llms.txt`` / ``llm.txt`` /
``llms-full.txt`` into the **repository root** as committed artefacts.
``tools/build/build.py`` then *copies* those committed files into ``dist/``,
which made the CI determinism check vacuous (it diffed the same committed
files against themselves).

This module gives the new build pipeline its own writers for those five
artefacts, fed straight from the in-memory ``Catalog`` produced by
``parse_content.load()``. Output goes to ``dist/`` and is then **overwritten**
by ``_stage_public`` in ``tools/build/build.py``: the project-root copies
remain authoritative until two SSOT-completeness gates close.

Why this stage runs even though ``_stage_public`` overwrites it
---------------------------------------------------------------

When the SSOT migration ran in v7.0, ~1,330 UCs lost their ``cimModels`` (``a``)
field because the markdown→JSON converter did not capture every field.
A bare ``content/cat-*/UC-*.json`` walk therefore produces a catalog with
**+1,092 UCs gained** (canonical sidecars are richer in many places) but
**-1,330 UCs missing CIM models** in others. Net effect: replacing the
project-root catalog.json with this stage's output today is a regression
for CIM-driven consumers.

So we keep this stage running because:

1. It exercises the SSOT code path (loader → enrichment → writer) on every
   build, surfacing drift the moment it appears.
2. The CI determinism check (``pages.yml``) gains real teeth: two
   ``--reproducible`` builds must emit byte-identical catalog.json/llms*.txt
   from the SSOT, regardless of project-root state.
3. The parity test
   ``tests/build/test_legacy_artifacts_parity.py`` compares the two outputs
   and surfaces gaps (size, UC count, fields lost) so the migration
   backfill (P1 step 3) is data-driven.
4. Once the SSOT is field-complete, removing four lines from
   ``_PROJECT_STATIC_FILES`` makes this stage authoritative — no further
   code change required.

Once P1 step 5 deletes the legacy ``build.py``, this module becomes the
single source of truth and the project-root copies disappear from the
repository tree (they will live only in ``dist/`` from then on).

Public surface
--------------

``render(catalog: Catalog, out_dir: Path, *, reproducible: bool) -> None``

    Emit the five legacy artefacts under ``out_dir`` (typically the
    ``dist/`` directory). When ``reproducible`` is True, all timestamps
    that would otherwise embed a build-time clock are pinned to the
    catalog's ``last_modified`` ISO string — so the same input commit
    produces the same bytes every time.

The shape of every emitted file follows ``docs/catalog-schema.md`` exactly
and is governed by ``schemas/v2/catalog-index.schema.json`` for catalog.json
once the schema lands (P12).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .parse_content import Catalog
from build import enrichment as _enrichment  # type: ignore[import-not-found]

SITE_BASE_URL = _enrichment.SITE_BASE_URL


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    """Emit catalog.json + data.js + llms.txt + llm.txt + llms-full.txt.

    Parameters
    ----------
    catalog
        The in-memory catalog produced by ``parse_content.load()``. Carries
        the v6 short-key shape that downstream consumers (the SPA, MCP
        server, Splunk app readers) depend on.
    out_dir
        Output directory. Files are written under ``out_dir`` directly:
        ``catalog.json``, ``data.js``, ``llms.txt``, ``llm.txt``,
        ``llms-full.txt``.
    reproducible
        If True, embeds the catalog's ``last_modified`` timestamp instead
        of ``datetime.utcnow()``. Required for the determinism gate in
        ``pages.yml``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = catalog.categories
    cat_meta = catalog.cat_meta
    cat_groups = catalog.cat_groups
    equipment = catalog.equipment
    files = catalog.files
    total_uc = sum(
        len(s.get("u", []))
        for cat in data
        for s in cat.get("s", [])
    )
    recently_added = list(catalog.recently_added or [])
    last_modified = _last_modified_iso(reproducible=reproducible)
    version = _read_version()
    roadmap = _enrichment.compute_implementation_roadmap(data)

    # data.js (window.DATA, CAT_META, CAT_GROUPS, EQUIPMENT, ...)
    data_js_path = out_dir / "data.js"
    _enrichment.write_data_js(
        data, cat_meta, str(data_js_path), recently_added, roadmap
    )

    # catalog.json (machine-readable mirror of data.js)
    catalog_dict = _build_catalog_dict(
        data=data,
        cat_meta=cat_meta,
        cat_groups=cat_groups,
        equipment=equipment,
        roadmap=roadmap,
        version=version,
        last_modified=last_modified,
    )
    catalog_path = out_dir / "catalog.json"
    _atomic_write(
        catalog_path,
        json.dumps(catalog_dict, ensure_ascii=False, indent=2),
    )

    # llms.txt + llm.txt + llms-full.txt — temporarily flip into the writer's
    # output dir so we don't pollute the project root. The enrichment
    # writers hard-code the project root in their constants; we shim the
    # paths via the OUTPUT_* module-level globals.
    _write_llms_artefacts(
        out_dir, data=data, cat_meta=cat_meta, files=files, total_uc=total_uc
    )


# ---------------------------------------------------------------------------
# Catalog dict construction (lifted from legacy build.py:3984-4020)
# ---------------------------------------------------------------------------

_CATALOG_README = (
    "Splunk monitoring use case catalog. Keys are abbreviated — see "
    "_schema_url for full field reference. DATA contains categories with "
    "subcategories and use cases. CAT_META has per-category metadata. "
    "CAT_GROUPS maps domain groups to category IDs. EQUIPMENT lists "
    "technology/TA filter definitions. implementationRoadmap groups UC ids "
    "into crawl / walk / run / unassigned buckets per category for the "
    "'where do I start?' planner view."
)

_CATALOG_FIELD_MAP = {
    "_about": (
        "Abbreviated key → full field name. Category: i=id, n=name, "
        "s=subcategories. Subcategory: i=id, n=name, u=use_cases. Use case "
        "fields below."
    ),
    "i": "id", "n": "title", "c": "criticality", "f": "difficulty",
    "v": "value", "ge": "grandmaExplanation", "t": "app_ta",
    "d": "dataSources", "q": "spl", "qs": "cimSpl", "m": "implementation",
    "md": "detailedImplementation", "z": "visualization", "a": "cimModels",
    "dma": "dataModelAcceleration", "schema": "schema",
    "mtype": "monitoringType", "kfp": "knownFalsePositives",
    "refs": "references", "mitre": "mitreAttack",
    "dtype": "detectionType", "sdomain": "securityDomain",
    "reqf": "requiredFields", "script": "scriptExample",
    "premium": "premiumApps", "hw": "equipmentModels",
    "e": "equipmentIds", "em": "equipmentModelIds", "status": "status",
    "reviewed": "lastReviewed", "sver": "splunkVersions", "rby": "reviewer",
    "wv": "wave", "pre": "prerequisiteUseCases",
}


def _build_catalog_dict(
    *,
    data: list,
    cat_meta: dict,
    cat_groups: dict,
    equipment: list,
    roadmap: Any,
    version: str,
    last_modified: str,
) -> dict[str, Any]:
    return {
        "_schema_url": f"{SITE_BASE_URL}/docs/catalog-schema.md",
        "_agents_url": f"{SITE_BASE_URL}/AGENTS.md",
        "_agents_examples_url": f"{SITE_BASE_URL}/AGENTS-EXAMPLES.md",
        "_ai_policy_url": f"{SITE_BASE_URL}/ai.txt",
        "version": version,
        "lastModified": last_modified,
        "_readme": _CATALOG_README,
        "_field_map": _CATALOG_FIELD_MAP,
        "DATA": data,
        "CAT_META": cat_meta,
        "CAT_GROUPS": cat_groups,
        "EQUIPMENT": equipment,
        "implementationRoadmap": roadmap,
    }


# ---------------------------------------------------------------------------
# llms.txt / llm.txt / llms-full.txt
# ---------------------------------------------------------------------------


def _write_llms_artefacts(
    out_dir: Path,
    *,
    data: list,
    cat_meta: dict,
    files: list,
    total_uc: int,
) -> None:
    """Emit the three llms.txt-family files into ``out_dir``.

    The enrichment writers hard-code the repo-root output paths via
    ``OUTPUT_LLMS_TXT`` / ``OUTPUT_LLMS_FULL_TXT`` globals. We monkey-patch
    them for the duration of the call so the files land in ``dist/``
    without us having to fork the writer bodies. After P1 step 5 deletes
    the legacy build.py, the writers themselves move to take an ``out_dir``
    argument and this shim is removed.
    """
    llms_path = out_dir / "llms.txt"
    llm_path = out_dir / "llm.txt"
    llms_full_path = out_dir / "llms-full.txt"

    saved = {
        "OUTPUT_LLMS_TXT": getattr(_enrichment, "OUTPUT_LLMS_TXT", None),
        "OUTPUT_LLM_TXT": getattr(_enrichment, "OUTPUT_LLM_TXT", None),
        "OUTPUT_LLMS_FULL_TXT": getattr(
            _enrichment, "OUTPUT_LLMS_FULL_TXT", None
        ),
    }
    try:
        _enrichment.OUTPUT_LLMS_TXT = str(llms_path)
        _enrichment.OUTPUT_LLM_TXT = str(llm_path)
        _enrichment.OUTPUT_LLMS_FULL_TXT = str(llms_full_path)
        _enrichment.write_llms_txt(data, cat_meta, files, total_uc)
        if llms_path.exists():
            shutil.copy2(llms_path, llm_path)
        _enrichment.write_llms_full_txt(data, cat_meta, files, total_uc)
    finally:
        for k, v in saved.items():
            if v is None:
                if hasattr(_enrichment, k):
                    delattr(_enrichment, k)
            else:
                setattr(_enrichment, k, v)


# ---------------------------------------------------------------------------
# Helpers (small enough to keep here rather than import from legacy build.py)
# ---------------------------------------------------------------------------


def _read_version() -> str:
    """Read VERSION as the catalogue version label.

    Falls back to ``"0.0.0"`` if the file is missing — the build pipeline
    should never reach this branch on a checked-in tree.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    version_path = repo_root / "VERSION"
    if version_path.exists():
        return version_path.read_text(encoding="utf-8").strip() or "0.0.0"
    return "0.0.0"


def _generated_at_iso() -> str:
    """Produce a UTC ISO-8601 timestamp for non-reproducible builds."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _last_modified_iso(*, reproducible: bool) -> str:
    """Resolve the ``lastModified`` field for catalog.json.

    When ``reproducible`` is True, prefer ``SOURCE_DATE_EPOCH`` (set by
    ``tools/build/build.py`` from ``git log -1 --format=%ct HEAD``) so two
    builds at the same commit produce byte-identical catalog.json. When
    ``SOURCE_DATE_EPOCH`` is unset or 0, fall back to the Unix epoch — the
    same convention ``render_meta`` uses for sitemap timestamps.

    When ``reproducible`` is False (the default for ``make build`` on a
    developer's machine), return the wall-clock UTC timestamp so the SPA's
    "last refreshed" badge stays useful.
    """
    if not reproducible:
        return _generated_at_iso()
    epoch_str = os.environ.get("SOURCE_DATE_EPOCH", "0")
    try:
        epoch = int(epoch_str)
    except (TypeError, ValueError):
        epoch = 0
    if epoch <= 0:
        return "1970-01-01T00:00:00Z"
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_write(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` atomically using a tempfile-rename.

    Lifted from ``build.py:_atomic_write`` so this module does not need to
    import the legacy script. Trailing newline is preserved as written by
    the caller; we never strip or add one ourselves.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


__all__ = ["render"]
