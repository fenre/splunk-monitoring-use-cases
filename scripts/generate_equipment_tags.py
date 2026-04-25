#!/usr/bin/env python3
"""Phase 5.5 — structured equipment tagging for UC sidecars.

PROBLEM (Apr 2026 audit of cat-22):
    33% of cat-22 regulatory UCs reference equipment (Azure, OPC UA, Modbus,
    ServiceNow, Palo Alto GlobalProtect, etc.) in their ``spl`` / ``dataSources``
    / ``implementation`` fields but NOT in their ``app`` field — so the
    build.py equipment substring match missed them and the UI's "Equipment"
    dropdown could not surface them. An auditor filtering by "Cisco Firewalls"
    or "Industrial Controls" got false-negative results.

FIX:
    Make ``equipment`` and ``equipmentModels`` first-class, schema-validated
    arrays on every UC sidecar. This generator is their sole writer. It
    computes them deterministically from substring-matching
    ``app`` + ``dataSources`` + ``spl`` + ``implementation`` against the
    EQUIPMENT table in build.py.

CONTRACT:
    - Deterministic: byte-for-byte identical output on re-runs at the same
      catalogue state. Sorted outputs, stable field order.
    - Generator-owned: ``equipment[]`` and ``equipmentModels[]`` in sidecars
      are always recomputed from source text. Do NOT hand-edit. Add missing
      patterns to build.py's EQUIPMENT table instead.
    - Idempotent: rerunning without source changes is a no-op.
    - --check mode for CI drift guards (exit 1 + list of stale files).
    - Empty arrays are ELIDED from the sidecar (keeps diffs small; matches
      the existing optional-field convention).

USAGE:
    scripts/generate_equipment_tags.py           # write in place
    scripts/generate_equipment_tags.py --check   # exit 1 on drift, print diff
    scripts/generate_equipment_tags.py --report  # also print per-equipment
                                                 #   coverage summary
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

# Local import from same directory.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from equipment_lib import compile_patterns, load_equipment, match_equipment

# Repo root = this file's parent's parent.
_REPO_ROOT = _SCRIPTS_DIR.parent
_CONTENT_UC_ROOT = _REPO_ROOT / "content"
_LEGACY_UC_ROOT = _REPO_ROOT / "use-cases"

# Canonical sidecar field order. Mirrors
# scripts/generate_phase3_1_backfill.py so repeated runs of all generators
# keep sidecars byte-comparable. When adding a new property to
# schemas/uc.schema.json, also add it here at the same position.
_SIDECAR_FIELD_ORDER: Tuple[str, ...] = (
    "$schema",
    "id",
    "title",
    "criticality",
    "difficulty",
    "monitoringType",
    "splunkPillar",
    "industry",
    "owner",
    "controlFamily",
    "exclusions",
    "evidence",
    "compliance",
    "controlTest",
    "dataSources",
    "app",
    "spl",
    "description",
    "value",
    "implementation",
    "visualization",
    "cimModels",
    "cimSpl",
    "schema",
    "dataModelAcceleration",
    "references",
    "knownFalsePositives",
    "mitreAttack",
    "detectionType",
    "securityDomain",
    "requiredFields",
    "equipment",
    "equipmentModels",
    "status",
    "lastReviewed",
    "splunkVersions",
    "reviewer",
    "premiumApps",
    "attackTechnique",
)

# Minimum pattern length for matching against the ``app`` field. The app
# field is authoritative and curated, so we trust every pattern (including
# short ones like "aws").
_MIN_LEN_APP = 1
# Minimum pattern length for matching against narrative text (``spl``,
# ``dataSources``, ``implementation``). Prevents false positives from
# short patterns colliding with substrings of unrelated words
# (e.g., "rhv" in "overhead", "k8s" in generic K8s references that are not
# really K8s-tagged workloads). 4 is empirically clean.
_MIN_LEN_NARRATIVE = 4


def _iter_sidecar_paths() -> Iterable[Path]:
    """Yield every UC sidecar JSON file under ``content/`` and ``use-cases/``."""
    yield from sorted(_CONTENT_UC_ROOT.rglob("UC-*.json"))
    yield from sorted(_LEGACY_UC_ROOT.rglob("uc-*.json"))


def _read_sidecar(path: Path) -> Optional[Dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARN: could not parse {path.relative_to(_REPO_ROOT)}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    if "id" not in data:
        return None
    return data


def _compute_tags(
    sidecar: Dict,
    patterns_all: List,
) -> Tuple[List[str], List[str]]:
    """Compute (equipment, equipmentModels) for a single sidecar.

    Uses two passes:
        1. Match the curated ``app`` field with min_pattern_len=1.
        2. Match the narrative text (``spl`` + ``dataSources`` +
           ``implementation``) with min_pattern_len=4 to filter noise.

    Returns sorted lists (for stable JSON output).
    """
    app_text = (sidecar.get("app") or "").replace("`", "")
    narrative_text = " ".join(
        (sidecar.get(f) or "").replace("`", "")
        for f in ("spl", "dataSources", "implementation", "description")
    )

    eq_app, models_app = match_equipment(
        app_text, patterns_all, min_pattern_len=_MIN_LEN_APP
    )
    eq_narr, models_narr = match_equipment(
        narrative_text, patterns_all, min_pattern_len=_MIN_LEN_NARRATIVE
    )

    equipment_ids: Set[str] = eq_app | eq_narr
    model_compounds: Set[str] = models_app | models_narr

    return sorted(equipment_ids), sorted(model_compounds)


def _reorder_sidecar(sidecar: Dict) -> Dict:
    """Return a dict with keys in ``_SIDECAR_FIELD_ORDER`` then sorted extras.

    Preserves values; only moves keys. Unknown keys are appended in
    alphabetical order so brand-new fields don't randomly drift in diffs.
    """
    ordered: Dict = {}
    for k in _SIDECAR_FIELD_ORDER:
        if k in sidecar:
            ordered[k] = sidecar[k]
    for k in sorted(sidecar.keys()):
        if k not in ordered:
            ordered[k] = sidecar[k]
    return ordered


def _apply_tags(
    sidecar: Dict,
    equipment: List[str],
    equipment_models: List[str],
) -> Dict:
    """Return a new sidecar dict with ``equipment``/``equipmentModels`` set.

    Conventions:
        - Computed tags are **merged** with any existing values so that
          manually-set tags (from Gold uplift agents or hand-edits) are
          never lost.
        - Empty arrays are ELIDED (key is removed). Keeps diffs small.
        - If the merged arrays equal the existing ones, no change.
        - Keys re-ordered to the canonical field order to keep sidecar
          outputs stable across generator runs.
    """
    out = dict(sidecar)
    existing_eq = set(sidecar.get("equipment") or [])
    existing_models = set(sidecar.get("equipmentModels") or [])

    merged_eq = sorted(existing_eq | set(equipment))
    merged_models = sorted(existing_models | set(equipment_models))

    if merged_eq:
        out["equipment"] = merged_eq
    else:
        out.pop("equipment", None)
    if merged_models:
        out["equipmentModels"] = merged_models
    else:
        out.pop("equipmentModels", None)
    return _reorder_sidecar(out)


def _serialise(sidecar: Dict) -> str:
    # Every sidecar in this repo is emitted as indent=2 + ensure_ascii=False
    # + trailing newline. Keep that contract.
    return json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"


def _process_sidecars(
    check: bool,
) -> Tuple[int, int, List[Path], Counter, Counter]:
    """Iterate every sidecar; return (processed, changed, changed_paths, eq_counts, model_counts)."""
    patterns = compile_patterns(load_equipment())
    processed = 0
    changed_paths: List[Path] = []
    eq_counts: Counter = Counter()
    model_counts: Counter = Counter()

    for path in _iter_sidecar_paths():
        sidecar = _read_sidecar(path)
        if sidecar is None:
            continue
        processed += 1

        equipment, equipment_models = _compute_tags(sidecar, patterns)
        for e in equipment:
            eq_counts[e] += 1
        for m in equipment_models:
            model_counts[m] += 1

        new_sidecar = _apply_tags(sidecar, equipment, equipment_models)
        new_text = _serialise(new_sidecar)
        old_text = path.read_text(encoding="utf-8")

        if new_text == old_text:
            continue

        changed_paths.append(path)
        if not check:
            path.write_text(new_text, encoding="utf-8")

    return processed, len(changed_paths), changed_paths, eq_counts, model_counts


def _print_report(
    processed: int,
    changed: int,
    eq_counts: Counter,
    model_counts: Counter,
) -> None:
    print()
    print(f"Processed sidecars:        {processed}")
    print(f"Sidecars with changed tags: {changed}")
    print()
    print(f"Equipment coverage ({len(eq_counts)} distinct ids):")
    for eid, count in eq_counts.most_common():
        print(f"  {eid:24} {count}")
    if model_counts:
        print()
        print(f"Equipment-model coverage ({len(model_counts)} distinct compounds):")
        for mid, count in model_counts.most_common():
            print(f"  {mid:36} {count}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing; exit 1 if any sidecar would change.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print per-equipment coverage counts after running.",
    )
    args = parser.parse_args()

    processed, changed, changed_paths, eq_counts, model_counts = _process_sidecars(
        check=args.check
    )

    if args.check:
        if changed > 0:
            print(
                f"FATAL: {changed}/{processed} UC sidecars have stale "
                f"equipment/equipmentModels tags.",
                file=sys.stderr,
            )
            print(
                "Re-run scripts/generate_equipment_tags.py to refresh. "
                "Affected files:",
                file=sys.stderr,
            )
            for p in changed_paths[:25]:
                print(f"  {p.relative_to(_REPO_ROOT)}", file=sys.stderr)
            if changed > 25:
                print(f"  ... and {changed - 25} more", file=sys.stderr)
            return 1
        print(f"OK: {processed} UC sidecars have up-to-date equipment tags.")
        return 0

    if args.report:
        _print_report(processed, changed, eq_counts, model_counts)
    else:
        print(f"Processed {processed} sidecars, updated {changed}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
