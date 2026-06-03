#!/usr/bin/env python3
"""tools.audits.api_surface_nonempty — fail when the published v1 recommender
+ equipment indexes ship empty while the catalogue is populated.

Background (issue #68, 2026-06-03)
----------------------------------
``generate-api-surface`` loads the catalogue through
``_resolve_catalog_path()`` (``dist/catalog.json`` → legacy root
``catalog.json``). Both are gitignored, so on a fresh CI checkout neither
exists until ``tools/build/build.py`` has run. If the generator runs BEFORE
the build, ``_load_catalog()`` returns ``[]`` and every recommender +
equipment index is written with zero records — yet still serves HTTP 200.
Production v8.7.0 shipped exactly that.

This guard is the deterministic backstop: it compares the v1 index counts
against the populated ``catalog-index.json`` and exits non-zero if any index
is empty while the catalogue reports a non-trivial number of use cases. Run it
AFTER the publish build so it inspects what would actually ship.

Checked endpoints (relative to the dist root)::

    api/catalog-index.json                   → counts.useCases (the truth)
    api/index.json                           → non-empty CategorySummary[] array
    api/v1/recommender/uc-thin.json          → useCaseCount
    api/v1/recommender/sourcetype-index.json → sourcetypeCount
    api/v1/recommender/cim-index.json        → cimModelCount
    api/v1/recommender/app-index.json        → appCount
    api/v1/equipment/index.json              → useCasesWithEquipmentTotal

``api/index.json`` is the legacy category table-of-contents
(``CategorySummary[]``) documented in the root ``openapi.yaml`` and the
in-page API help. It was dropped in v8.2.0 (a separate facet of issue #68) and
restored in tools/build/render_api.py; this guard keeps it from regressing to a
404/empty array again.

``recommender/splunkbase-index.json`` is intentionally excluded — it is built
from ``data/splunkbase-catalog.json`` (not the UC catalogue), so it stays
populated even when ``_load_catalog()`` returns empty, and was reported
working in issue #68. ``equipment/index.json`` uses
``useCasesWithEquipmentTotal`` rather than ``equipmentCount`` because the
latter reflects the static EQUIPMENT registry (106 slugs) and is non-zero
even when no use case references any equipment.

Usage
-----
    python3 tools/audits/api_surface_nonempty.py [DIST_ROOT] [--min-catalog N]

``DIST_ROOT`` defaults to ``dist``. ``--min-catalog`` (default 100) is the
catalogue size above which empty indexes are treated as a hard failure; below
it the guard skips, since a tiny fixture catalogue legitimately yields small
or empty indexes.

Exit codes
----------
0 — every checked index is populated (or the catalogue is below the threshold)
1 — at least one index is empty while the catalogue is populated, or a
    required file is missing / unreadable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

#: (relative path under the dist root, JSON key holding the record count, label)
_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("api/v1/recommender/uc-thin.json", "useCaseCount", "recommender uc-thin"),
    (
        "api/v1/recommender/sourcetype-index.json",
        "sourcetypeCount",
        "recommender sourcetype-index",
    ),
    ("api/v1/recommender/cim-index.json", "cimModelCount", "recommender cim-index"),
    ("api/v1/recommender/app-index.json", "appCount", "recommender app-index"),
    ("api/v1/equipment/index.json", "useCasesWithEquipmentTotal", "equipment index"),
)

CATALOG_INDEX_REL = "api/catalog-index.json"

#: Legacy category table-of-contents (``CategorySummary[]``). A bare JSON
#: array, so it is checked separately from the count-keyed _CHECKS above.
CATEGORY_INDEX_REL = "api/index.json"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_uc_count(root: Path) -> int | None:
    """Return the use-case count from ``catalog-index.json``, or ``None``.

    Prefers the explicit ``counts.useCases`` field and falls back to the
    length of the ``ucs`` array. Returns ``None`` when the file is missing or
    unreadable so the caller can treat that as a hard failure.
    """
    path = root / CATALOG_INDEX_REL
    if not path.is_file():
        return None
    try:
        data = _read_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    counts = data.get("counts")
    if isinstance(counts, dict) and isinstance(counts.get("useCases"), int):
        return int(counts["useCases"])
    ucs = data.get("ucs")
    if isinstance(ucs, list):
        return len(ucs)
    return None


def check_surface(root: Path, *, min_catalog: int = 100) -> list[str]:
    """Return a list of violation strings; empty means the surface is healthy."""
    problems: list[str] = []

    catalog_uc = catalog_uc_count(root)
    if catalog_uc is None:
        problems.append(
            f"{CATALOG_INDEX_REL}: missing or unreadable — cannot verify the api/v1 surface"
        )
        return problems

    if catalog_uc < min_catalog:
        # A tiny fixture catalogue legitimately produces small/empty indexes;
        # there is nothing to assert against.
        return problems

    for rel, key, label in _CHECKS:
        path = root / rel
        if not path.is_file():
            problems.append(f"{rel}: missing (expected a populated {label})")
            continue
        try:
            data = _read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{rel}: unreadable JSON ({exc})")
            continue
        value = data.get(key) if isinstance(data, dict) else None
        if not isinstance(value, int):
            problems.append(f"{rel}: missing integer key {key!r}")
        elif value <= 0:
            problems.append(
                f"{rel}: {key}={value} but catalog-index reports {catalog_uc} "
                f"use cases (empty {label} — issue #68 regression)"
            )

    # api/index.json is a bare CategorySummary[] array (not count-keyed),
    # restored in v8.x after the v8.2.0 drop. Verify it ships as a non-empty
    # list so the documented openapi/UI-help endpoint can't 404 again.
    cat_index_path = root / CATEGORY_INDEX_REL
    if not cat_index_path.is_file():
        problems.append(
            f"{CATEGORY_INDEX_REL}: missing (expected a CategorySummary[] "
            f"table-of-contents — issue #68 regression)"
        )
    else:
        try:
            cat_index = _read_json(cat_index_path)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{CATEGORY_INDEX_REL}: unreadable JSON ({exc})")
        else:
            if not isinstance(cat_index, list) or not cat_index:
                problems.append(
                    f"{CATEGORY_INDEX_REL}: expected a non-empty array but got "
                    f"{type(cat_index).__name__} of length "
                    f"{len(cat_index) if isinstance(cat_index, list) else 'n/a'} "
                    f"(empty category index — issue #68 regression)"
                )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="api_surface_nonempty")
    parser.add_argument(
        "dist_root",
        nargs="?",
        default="dist",
        help="Path to the built site root containing api/ (default: dist).",
    )
    parser.add_argument(
        "--min-catalog",
        type=int,
        default=100,
        help="Catalogue size above which empty indexes are a hard failure (default: 100).",
    )
    args = parser.parse_args(argv)

    root = Path(args.dist_root).resolve()
    if not root.exists():
        sys.stderr.write(f"::error::[api_surface_nonempty] dist root not found: {root}\n")
        return 1

    problems = check_surface(root, min_catalog=args.min_catalog)
    if problems:
        sys.stderr.write(
            "::error::[api_surface_nonempty] empty api/v1 surface detected (issue "
            "#68). The recommender/equipment indexes serve HTTP 200 with zero "
            "records. Ensure tools/build/build.py runs BEFORE generate-api-surface "
            "so dist/catalog.json exists when the generators load the catalogue.\n"
        )
        for problem in problems:
            sys.stderr.write(f"  - {problem}\n")
        return 1

    catalog_uc = catalog_uc_count(root)
    sys.stdout.write(
        f"[api_surface_nonempty] OK — {len(_CHECKS)} v1 indexes + the category "
        f"table-of-contents populated (catalog-index: {catalog_uc} use cases) "
        f"under {root}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
