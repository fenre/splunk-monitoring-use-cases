"""Shared equipment-table accessor.

Re-exports the SSOT ``EQUIPMENT`` registry from ``tools/build/enrichment.py``
for scripts that need the (equipmentId, modelId) data without booting the
full build pipeline.

History
-------

Pre-P1-step-5c (before 2026-05-09) this module surgically parsed the
``EQUIPMENT = [...]`` literal out of the legacy repo-root ``build.py`` so
generators and audits didn't have to import the monolithic build script
(which ran 20+ markdown parses on import). After ADR-0008 codified the
"every constant in exactly one place" rule and ``tools/build/enrichment.py``
became the SSOT for ``EQUIPMENT``, this module became a thin shim: it
imports the live registry directly so any future schema change in
``enrichment.py`` propagates without re-parsing source.

Public API:
    load_equipment() -> list[dict]        Raw EQUIPMENT list.
    compile_patterns(equipment) -> list[tuple[str, str, str|None]]
        Flat list of (pattern_lower, equipment_id, model_id_or_None).
    match_equipment(text, patterns, min_pattern_len=4) -> tuple[set, set]
        Substring-match case-insensitively; returns (equipment_ids,
        compound_model_ids). ``compound_model_ids`` use the
        '<equipmentId>_<modelId>' format consumed by the UI.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Dict, List, Optional, Set, Tuple

# Make ``tools/`` importable so ``from build.enrichment import EQUIPMENT``
# works even when the package isn't pip-installed (e.g. CI runs that
# invoke scripts/equipment_lib.py from a checkout without ``pip install -e .``).
# Prefer the installed package if available; fall back to the in-tree path.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if _TOOLS_DIR.is_dir() and str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# noqa: E402 — sys.path manipulation above is intentional for in-tree usage.
from build.enrichment import EQUIPMENT as _SSOT_EQUIPMENT  # type: ignore[import-not-found]

_CACHE: Optional[List[Dict]] = None


def load_equipment() -> List[Dict]:
    """Return the SSOT ``EQUIPMENT`` list from ``tools/build/enrichment.py``.

    Cached on first call to avoid repeated validation overhead. The cache is
    a *new* list object — callers may not mutate it in place (the upstream
    SSOT list is a module-level constant and must not be perturbed).
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    equipment = list(_SSOT_EQUIPMENT)
    if not isinstance(equipment, list):
        raise RuntimeError(
            "tools/build/enrichment.py:EQUIPMENT did not produce a list."
        )
    for entry in equipment:
        if not isinstance(entry, dict) or "id" not in entry or "tas" not in entry:
            raise RuntimeError(f"EQUIPMENT entry malformed: {entry!r}")
    _CACHE = equipment
    return equipment


Pattern = Tuple[str, str, Optional[str]]


def compile_patterns(equipment: Optional[List[Dict]] = None) -> List[Pattern]:
    """Flatten EQUIPMENT into (pattern_lower, equipment_id, model_id_or_None) tuples.

    Each ``tas`` pattern becomes one tuple; models contribute additional
    tuples with a non-None ``model_id``.

    Pass ``equipment=None`` (or omit the argument) to use the cached
    real registry; pass an explicit list (including ``[]``) to compile
    that exact input. The previous ``equipment or load_equipment()``
    expression silently substituted the registry when callers passed
    an empty list — a property-based test in P16 surfaced this and the
    behaviour is now ``None``-only.
    """
    if equipment is None:
        equipment = load_equipment()
    out: List[Pattern] = []
    for eq in equipment:
        eq_id = eq["id"]
        for pattern in eq.get("tas", []):
            out.append((pattern.lower(), eq_id, None))
        for model in eq.get("models", []) or []:
            model_id = model["id"]
            for pattern in model.get("tas", []):
                out.append((pattern.lower(), eq_id, model_id))
    return out


def match_equipment(
    text: str,
    patterns: List[Pattern],
    min_pattern_len: int = 4,
) -> Tuple[Set[str], Set[str]]:
    """Substring-match ``text`` against ``patterns`` (case-insensitive).

    Returns:
        (equipment_ids, compound_model_ids)
        where compound_model_ids are formatted '<equipmentId>_<modelId>'
        to match how the UI and catalog consume them.

    ``min_pattern_len`` suppresses false positives from ultra-short patterns
    (e.g., a 2-char vendor slug that appears incidentally in other words).
    Patterns shorter than this are still respected for the ``app`` field
    (where they're authoritative), but suppressed when matching against
    larger narrative text blobs like ``spl`` or ``implementation``. Callers
    decide by passing the appropriate ``min_pattern_len``.
    """
    if not text:
        return set(), set()
    haystack = text.lower()
    eq_ids: Set[str] = set()
    model_compounds: Set[str] = set()
    for pattern, eq_id, model_id in patterns:
        if len(pattern) < min_pattern_len:
            continue
        if pattern not in haystack:
            continue
        eq_ids.add(eq_id)
        if model_id:
            model_compounds.add(f"{eq_id}_{model_id}")
    return eq_ids, model_compounds


__all__ = [
    "load_equipment",
    "compile_patterns",
    "match_equipment",
    "Pattern",
]
