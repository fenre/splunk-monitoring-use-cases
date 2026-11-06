"""Stamps for rollups that are generated into ``dist/`` and no longer committed.

The value is the stamp already published for that rollup. A later
commit that does not change the rollup body keeps the same stamp, so
``dist/`` stays byte-identical. ``SOURCE_DATE_EPOCH`` replaces the
frozen stamp: that is the reproducible build clock.
"""

from __future__ import annotations

import os

# Keys are generator-local names, not paths. The strings are the stamps
# in the last published copies of those rollups. The scorecard stamp is
# also the "today" its freshness scores are measured against.
# license-inventory-git-head is the commit the inventory was captured at.
_FROZEN: dict[str, str] = {
    "compliance-coverage": "2026-11-05T20:47:57Z",
    "equipment-app-map": "2026-11-05T21:59:04Z",
    "license-inventory": "2026-11-06T12:06:27Z",
    "license-inventory-git-head": "ecfc0a82088c1f0c83c6c71e6ec78d8deaeabff2",
    "provenance": "2026-11-06T12:04:34Z",
    "recommender-app": "2026-11-05T22:25:18Z",
    "scorecard": "2026-11-06T12:04:37Z",
}


def frozen_published_stamp(key: str) -> str | None:
    """Return the published stamp, or None when the reproducible clock is set."""
    if os.environ.get("SOURCE_DATE_EPOCH", "").strip():
        return None
    return _FROZEN.get(key)
