"""Clock for rollups that are generated into ``dist/`` and not committed.

Resolution order:

1. ``SOURCE_DATE_EPOCH`` (CI sets this to ``git log -1 --format=%ct``).
2. The HEAD commit time, when this tree is a git checkout.
3. The fixed fallback below, only when git is not available.
4. The caller uses the wall clock when this module has no fallback for
   that key.

A commit therefore stamps the same instant in CI and in a local
checkout. The fixed dates stay for a tree that has no git history.
"""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Keys are generator-local names, not paths. Used only when git cannot
# name HEAD. license-inventory-git-head is a commit id, not a date.
_FROZEN: dict[str, str] = {
    "compliance-coverage": "2026-11-05T20:47:57Z",
    "equipment-app-map": "2026-11-05T21:59:04Z",
    "license-inventory": "2026-11-06T12:06:27Z",
    "license-inventory-git-head": "ecfc0a82088c1f0c83c6c71e6ec78d8deaeabff2",
    "provenance": "2026-11-06T12:04:34Z",
    "recommender-app": "2026-11-05T22:25:18Z",
    "scorecard": "2026-11-06T12:04:37Z",
}


def _epoch_from_env() -> str | None:
    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    return raw if raw.isdigit() else None


def head_commit_epoch() -> str | None:
    """Unix time of HEAD, or None when git cannot answer."""
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "log", "-1", "--format=%ct"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    ts = out.stdout.strip()
    return ts if ts.isdigit() else None


def _iso(epoch: str) -> str:
    return datetime.fromtimestamp(int(epoch), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def frozen_published_stamp(key: str) -> str | None:
    """Fixed fallback, only when neither the env clock nor git is available."""
    if _epoch_from_env() is not None or head_commit_epoch() is not None:
        return None
    return _FROZEN.get(key)


def resolve_published_stamp(key: str) -> str | None:
    """Commit clock for ``key``, else the fixed fallback, else None."""
    epoch = _epoch_from_env() or head_commit_epoch()
    if epoch is not None:
        return _iso(epoch)
    return _FROZEN.get(key)
