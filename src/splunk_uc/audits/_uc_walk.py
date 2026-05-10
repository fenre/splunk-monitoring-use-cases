"""Shared helpers for walking the JSON SSOT (``content/cat-*/UC-*.json``).

All ``src/splunk_uc/audits/*.py`` modules that pre-v8.2.0 walked the legacy
markdown corpus (``use-cases/cat-*.md``) now share these primitives instead.
The legacy markdown corpus was deleted in v8.2.0 — see
``docs/migration-status.md`` for the burndown record.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "content"


def iter_uc_sidecars() -> Iterator[tuple[Path, dict[str, Any]]]:
    """Yield ``(path, payload)`` tuples for every UC sidecar in the SSOT.

    Sidecars that fail to parse are silently skipped — the ``uc-structure``
    audit is the canonical place to surface parse errors so we don't
    double-report them across every audit that walks the corpus.
    """
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            with path.open(encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        yield path, payload


def cat_dirs() -> list[Path]:
    """Return sorted list of ``content/cat-NN-*/`` directories."""
    return sorted(d for d in CONTENT.iterdir() if d.is_dir() and d.name.startswith("cat-"))


def uc_label(path: Path, payload: dict[str, Any]) -> str:
    """Return ``UC-<id> (relpath)`` for human-readable findings."""
    uc_id = str(payload.get("id", "<unknown>"))
    rel = path.relative_to(REPO)
    return f"UC-{uc_id} ({rel})"


def get_text_field(payload: dict[str, Any], key: str) -> str:
    """Return the value of a UC text field, or an empty string."""
    v = payload.get(key)
    if isinstance(v, str):
        return v
    return ""


def get_list_field(payload: dict[str, Any], key: str) -> list[Any]:
    """Return the value of a UC list field, or an empty list."""
    v = payload.get(key)
    if isinstance(v, list):
        return v
    return []
