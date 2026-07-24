"""Industry Verticals (cat-21) expansion taxonomy."""

from __future__ import annotations

from .dedupe import dedupe_entries
from .fsi_residual import fsi_residual_entries
from .plan_loader import load_manifest_entries
from .sourcetype_matrix import matrix_entries
from .taxonomy import TaxonomyEntry, crawl_uc_ids

_raw: list[TaxonomyEntry] = (
    load_manifest_entries() + matrix_entries() + fsi_residual_entries()
)
ALL_ENTRIES: list[TaxonomyEntry] = dedupe_entries(_raw)

__all__ = ["ALL_ENTRIES", "TaxonomyEntry", "crawl_uc_ids", "dedupe_entries"]
