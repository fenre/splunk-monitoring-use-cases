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
    clear_cache() -> None                 Drop cached registry / index state.
    resolve_equipment_slug(slug) -> str   Map legacy aliases to canonical ids.
    get_equipment_kind(eq_id) -> str      Registry ``kind`` (default ``equipment``).
    get_equipment_vendor(eq_id) -> str    Registry ``vendor`` (empty when unknown).
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
from typing import Any, Dict, List, Optional, Set, Tuple

# Make ``tools/`` importable so ``from build.enrichment import EQUIPMENT``
# works even when the package isn't pip-installed (e.g. CI runs that
# invoke scripts/equipment_lib.py from a checkout without ``pip install -e .``).
# Prefer the installed package if available; fall back to the in-tree path.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if _TOOLS_DIR.is_dir() and str(_TOOLS_DIR) not in sys.path:  # pragma: no branch
    # False arm reachable only at module-import time when EITHER the
    # ``tools/`` directory was removed from the checkout OR the test
    # harness already injected it into ``sys.path``. The first case
    # would also make the ``from build.enrichment import EQUIPMENT``
    # line below raise ``ImportError`` (the import is mandatory),
    # so any environment that reaches this module with the False
    # arm must already have ``tools/`` on ``sys.path`` via some
    # other mechanism (``pip install -e .``, a pytest conftest that
    # pre-prepends, an editor in-process loader, etc.). Exercising
    # the False arm deterministically would require re-importing the
    # module under conditions outside the test process's control.
    # The branch is preserved as a defensive insertion guard so
    # the module remains importable from a bare ``python3`` invocation
    # without ``pip install -e .``.
    sys.path.insert(0, str(_TOOLS_DIR))

# noqa: E402 — sys.path manipulation above is intentional for in-tree usage.
from build.enrichment import EQUIPMENT as _SSOT_EQUIPMENT  # type: ignore[import-not-found]

_CACHE: Optional[List[Dict[str, Any]]] = None
_ID_INDEX: Optional[Dict[str, Dict[str, Any]]] = None

# Legacy / alternate spellings seen in sidecars and prose. Canonical ids
# match ``tools/build/enrichment.py`` ``EQUIPMENT[].id`` values.
EQUIPMENT_ALIASES: Dict[str, str] = {
    "palo_alto": "paloalto",
    "palo-alto": "paloalto",
    "paloaltonetworks": "paloalto",
    "splunk-es": "splunk_es",
    "splunk-soar": "splunk_soar",
    "splunk-itsi": "itsi",
    "splunk-stream": "stream",
    "5g": "fiveg",
}


def clear_cache() -> None:
    """Drop cached registry data and derived indexes."""
    global _CACHE, _ID_INDEX
    _CACHE = None
    _ID_INDEX = None


def resolve_equipment_slug(slug: str) -> str:
    """Return the canonical equipment id for ``slug`` (identity when unknown)."""
    return EQUIPMENT_ALIASES.get(slug, slug)


def _id_index() -> Dict[str, Dict[str, Any]]:
    global _ID_INDEX
    if _ID_INDEX is None:
        _ID_INDEX = {entry["id"]: entry for entry in load_equipment()}
    return _ID_INDEX


def get_equipment_kind(eq_id: str) -> str:
    """Return the registry ``kind`` for ``eq_id`` (default ``equipment``)."""
    entry = _id_index().get(resolve_equipment_slug(eq_id))
    if entry is None:
        return "equipment"
    kind = entry.get("kind")
    if isinstance(kind, str) and kind:
        return kind
    return "equipment"


def get_equipment_vendor(eq_id: str) -> str:
    """Return the registry ``vendor`` for ``eq_id`` (empty when unknown)."""
    entry = _id_index().get(resolve_equipment_slug(eq_id))
    if entry is None:
        return ""
    vendor = entry.get("vendor")
    if isinstance(vendor, str):
        return vendor
    return ""


def load_equipment() -> List[Dict[str, Any]]:
    """Return the SSOT ``EQUIPMENT`` list from ``tools/build/enrichment.py``.

    Cached on first call to avoid repeated validation overhead. The cache is
    a *new* list object — callers may not mutate it in place (the upstream
    SSOT list is a module-level constant and must not be perturbed).
    """
    global _CACHE, _ID_INDEX
    if _CACHE is not None:
        return _CACHE
    equipment = list(_SSOT_EQUIPMENT)
    if not isinstance(equipment, list):  # pragma: no cover - unreachable.
        # ``list(iterable)`` ALWAYS returns a list object, so
        # ``isinstance(equipment, list)`` is invariably True here.
        # The check is preserved as a tripwire in case a future
        # refactor inlines or short-circuits the ``list(...)`` call
        # (e.g. ``equipment = _SSOT_EQUIPMENT if isinstance(_SSOT_EQUIPMENT, list) else ...``)
        # and lets a non-list slip through.
        raise RuntimeError(
            "tools/build/enrichment.py:EQUIPMENT did not produce a list."
        )
    for entry in equipment:
        if not isinstance(entry, dict) or "id" not in entry or "tas" not in entry:
            raise RuntimeError(f"EQUIPMENT entry malformed: {entry!r}")
    _CACHE = equipment
    _ID_INDEX = None
    return equipment


Pattern = Tuple[str, str, Optional[str]]


def compile_patterns(equipment: Optional[List[Dict[str, Any]]] = None) -> List[Pattern]:
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
    "EQUIPMENT_ALIASES",
    "clear_cache",
    "load_equipment",
    "resolve_equipment_slug",
    "get_equipment_kind",
    "get_equipment_vendor",
    "compile_patterns",
    "match_equipment",
    "Pattern",
]
