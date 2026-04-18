"""Shared equipment-table accessor.

Parses the ``EQUIPMENT`` list out of ``build.py`` once so generators and
audits don't have to duplicate the 100+ entries.

The EQUIPMENT table in ``build.py`` is the single source of truth for the
(equipmentId, modelId) registry that backs the UI's "What equipment do you
have?" dropdown. This module extracts it without importing the full build
pipeline.

Why parse instead of import?
    ``build.py`` executes a lot of top-level code (parsing 20+ markdown
    files, building catalog.json, etc.) when imported. Generators need only
    the EQUIPMENT literal, so we extract it surgically.

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
from typing import Dict, List, Optional, Set, Tuple

_BUILD_PY = pathlib.Path(__file__).resolve().parent.parent / "build.py"
_CACHE: Optional[List[Dict]] = None


def _extract_equipment_literal(build_py_source: str) -> str:
    """Surgically extract the ``EQUIPMENT = [...]`` list literal.

    We locate ``EQUIPMENT = [`` and walk brackets to the matching close. This
    is stable because the EQUIPMENT constant lives near the top of build.py
    and uses only dict/list literals (no function calls, no f-strings).
    """
    marker = "EQUIPMENT = ["
    start = build_py_source.find(marker)
    if start < 0:
        raise RuntimeError(
            f"EQUIPMENT marker not found in {_BUILD_PY}. "
            "scripts/equipment_lib.py assumes the top-level EQUIPMENT "
            "assignment exists; check for a rename."
        )
    i = start + len("EQUIPMENT = ")
    depth = 0
    while i < len(build_py_source):
        c = build_py_source[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return build_py_source[start : i + 1]
        i += 1
    raise RuntimeError("EQUIPMENT list never closed; build.py is malformed.")


def load_equipment() -> List[Dict]:
    """Return the EQUIPMENT list from build.py (cached)."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not _BUILD_PY.exists():
        raise FileNotFoundError(
            f"Cannot load EQUIPMENT: {_BUILD_PY} is missing. "
            "scripts/equipment_lib.py must run from a repo checkout."
        )
    source = _BUILD_PY.read_text(encoding="utf-8")
    literal_src = _extract_equipment_literal(source)
    # The literal is pure data; executing it in an isolated namespace is safe.
    ns: Dict[str, object] = {}
    # "EQUIPMENT = [ ... ]" -> just exec that snippet.
    exec(compile(literal_src, str(_BUILD_PY), "exec"), ns)  # noqa: S102  (intentional; data literal)
    equipment = ns.get("EQUIPMENT")
    if not isinstance(equipment, list):
        raise RuntimeError("EQUIPMENT literal did not produce a list.")
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
    """
    equipment = equipment or load_equipment()
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
        to match how the UI and data.js consume them.

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
