"""Cloud Infrastructure (cat-04) expansion taxonomy — real telemetry surfaces only."""

from .taxonomy import ALL_ENTRIES, crawl_uc_ids
from . import taxonomy_expand  # noqa: F401 — extends ALL_ENTRIES
from . import taxonomy_expand2  # noqa: F401 — extends ALL_ENTRIES
from . import taxonomy_expand3  # noqa: F401 — extends ALL_ENTRIES
from . import taxonomy_expand4  # noqa: F401 — extends ALL_ENTRIES

__all__ = ["ALL_ENTRIES", "crawl_uc_ids"]
