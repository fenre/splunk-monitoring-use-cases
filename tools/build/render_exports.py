"""tools.build.render_exports — bulk multi-format exports under /exports/.

Per docs/url-scheme.md, every release ships:

* ``/exports/catalog.csv``        all UCs, one row each
* ``/exports/catalog.json``       all UCs, structured
* ``/exports/catalog.oscal.json`` site-wide OSCAL bundle
* ``/exports/catalog.stix.json``  STIX bundle of security UCs
* ``/exports/catalog.zip``        ZIP of all the above + uc/*/uc.md

v7.0-dev behaviour
------------------
This module is a placeholder. The ``multi-format-exports`` todo (which
ships in v7.1) implements every emitter.

For v7.0 the only export is a CSV summary derived directly from the
in-memory Catalog so downstream BI tools have a single static URL to
pull from on day one.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from .parse_content import Catalog


def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    exports = out_dir / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    _write_catalog_csv(catalog, exports, reproducible=reproducible)


def _write_catalog_csv(catalog: Catalog, exports: Path, *, reproducible: bool) -> None:
    """Single-file CSV summary of every UC. v7.1 expands this to all formats."""
    p = exports / "catalog.csv"
    buf = io.StringIO()
    writer = csv.writer(buf, dialect="unix")
    writer.writerow(
        [
            "uc_id",
            "title",
            "category_id",
            "category_name",
            "subcategory_id",
            "subcategory_name",
            "criticality",
            "difficulty",
            "monitoring_type",
            "splunk_pillar",
            "regulations",
            "app_ta",
            "html_url",
            "json_url",
        ]
    )
    rows: list[list[str]] = []
    for cat in catalog.categories:
        cat_id = cat.get("i", "")
        cat_name = cat.get("n", "")
        for sub in cat.get("s", []):
            sub_id = sub.get("i", "")
            sub_name = sub.get("n", "")
            for uc in sub.get("u", []):
                uc_id = uc.get("i", "")
                if not uc_id:
                    continue
                rows.append(
                    [
                        f"UC-{uc_id}",
                        uc.get("n", ""),
                        str(cat_id),
                        cat_name,
                        sub_id,
                        sub_name,
                        uc.get("c", ""),
                        uc.get("d", ""),
                        uc.get("mtype", ""),
                        uc.get("pillar", ""),
                        ",".join(uc.get("regs", []) or []),
                        uc.get("a", ""),
                        f"/uc/UC-{uc_id}/",
                        f"/uc/UC-{uc_id}/index.json",
                    ]
                )
    if reproducible:
        rows.sort()
    for row in rows:
        writer.writerow(row)
    p.write_text(buf.getvalue(), encoding="utf-8")
