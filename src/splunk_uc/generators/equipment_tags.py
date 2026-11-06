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
    ``equipment`` and ``equipmentModels`` stay schema-validated arrays.
    The catalogue build computes them. Sidecars do not store them.
    ``tags_for_sidecar`` matches ``app`` plus the narrative against the
    EQUIPMENT table in build.py.

CONTRACT:
    - Deterministic: byte-for-byte identical output on re-runs at the same
      catalogue state. Sorted outputs, stable field order.
    - The catalogue build computes ``equipment[]`` and ``equipmentModels[]``.
      Sidecars do not store them. ``tags_for_sidecar`` is the function the
      build and the audits call. It uses the EQUIPMENT table, the evidence
      rule, ``data/equipment-tag-overrides.json``, and
      ``equipment_tag_retained.json`` for tags the text no longer implies.
    - Evidence-gated vendors (registry entries with an ``evidence`` block,
      currently Cisco) are tagged only from search evidence; see
      ``splunk_uc.equipment_evidence``. Their tags are replaced, not
      merged, on every run; reviewed exceptions live in
      ``data/equipment-tag-overrides.json``.
    - Idempotent: rerunning without source changes is a no-op.
    - --check mode for CI drift guards (exit 1 + list of stale files).
    - Empty arrays are ELIDED from the sidecar (keeps diffs small; matches
      the existing optional-field convention).

USAGE:
    python3 -m splunk_uc generate-equipment-tags           # strip stored tags
    python3 -m splunk_uc generate-equipment-tags --check   # exit 1 if any sidecar still stores them
    python3 -m splunk_uc generate-equipment-tags --report  # print the computed coverage
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# Path of this module: src/splunk_uc/generators/equipment_tags.py
# Repo root = this file's fourth-level ancestor.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTENT_UC_ROOT = _REPO_ROOT / "content"

# ``equipment_lib`` still lives under ``scripts/`` until Tier 2 of the P6
# migration ports it into the package as well.  Insert ``scripts/`` on
# ``sys.path`` so the sibling import keeps working from inside the
# package.  The insertion is idempotent.
_LEGACY_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_LEGACY_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGACY_SCRIPTS_DIR))

from equipment_lib import compile_patterns, load_equipment, match_equipment  # noqa: E402

from splunk_uc import equipment_evidence as _ev  # noqa: E402

_OVERRIDES_PATH = _REPO_ROOT / "data" / "equipment-tag-overrides.json"
_RETAINED_PATH = Path(__file__).resolve().parent / "equipment_tag_retained.json"
_ENGINE: tuple[Any, ...] | None = None

# Canonical sidecar field order.  Mirrors
# ``scripts/generate_phase3_1_backfill.py`` (queued for migration into
# ``src/splunk_uc/generators/`` in a later P6 batch) so repeated runs of
# all generators keep sidecars byte-comparable.  When adding a new
# property to ``schemas/uc.schema.json``, also add it here at the same
# position.
_SIDECAR_FIELD_ORDER: tuple[str, ...] = (
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
    "splVariants",
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
    "capabilities",
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
    """Yield every UC sidecar JSON file under ``content/`` (JSON SSOT)."""
    yield from sorted(_CONTENT_UC_ROOT.rglob("UC-*.json"))


def _read_sidecar(path: Path) -> dict[str, Any] | None:
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
    sidecar: dict[str, Any],
    patterns_all: list[Any],
) -> tuple[list[str], list[str]]:
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

    eq_app, models_app = match_equipment(app_text, patterns_all, min_pattern_len=_MIN_LEN_APP)
    eq_narr, models_narr = match_equipment(
        narrative_text, patterns_all, min_pattern_len=_MIN_LEN_NARRATIVE
    )

    equipment_ids: set[str] = eq_app | eq_narr
    model_compounds: set[str] = models_app | models_narr
    model_compounds = {m for m in model_compounds if not m.endswith("_generic")}

    return sorted(equipment_ids), sorted(model_compounds)


def variant_models(sidecar: dict[str, Any]) -> list[str]:
    """Model compounds that carry their own SPL in ``splVariants``."""
    out = []
    for v in sidecar.get("splVariants") or []:
        if isinstance(v, dict) and isinstance(v.get("model"), str):
            out.append(v["model"])
    return out


def _compute_gated_tags(
    sidecar: dict[str, Any],
    gated: list[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    """Evidence-gated (equipment, equipmentModels) for vendors with ``evidence``.

    See :mod:`splunk_uc.equipment_evidence` for the rule.
    """
    ev = _ev.extract_spl_evidence(sidecar.get("spl"), sidecar.get("cimSpl"))
    variants = variant_models(sidecar)
    eq_ids: set[str] = set()
    models: set[str] = set()
    for entry in gated:
        vendor, entry_models = _ev.compute_gated_tags(entry, sidecar.get("app") or "", ev, variants)
        if vendor:
            eq_ids.add(entry["id"])
        models |= entry_models
    return eq_ids, models


def _load_overrides(path: Path = _OVERRIDES_PATH) -> dict[str, dict[str, list[str]]]:
    """Reviewed hand corrections for gated tags, keyed by bare UC id."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, list[str]]] = {}
    for uc_id, entry in (data.get("overrides") or {}).items():
        out[uc_id.removeprefix("UC-")] = {
            "add": list(entry.get("add") or []),
            "remove": list(entry.get("remove") or []),
        }
    return out


def _load_retained(path: Path = _RETAINED_PATH) -> dict[str, tuple[list[str], list[str]]]:
    """Tags the text no longer implies, keyed by bare UC id.

    The generator used to merge computed tags with whatever a sidecar
    already stored, so a tag survived after its pattern stopped matching.
    Those residues are listed here. The file lives next to this module,
    not under ``data/``, because ``data/`` is copied into ``dist/``.
    """
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, tuple[list[str], list[str]]] = {}
    for uc_id, entry in (data.get("retained") or {}).items():
        out[str(uc_id).removeprefix("UC-")] = (
            [str(tag) for tag in entry.get("equipment") or []],
            [str(tag) for tag in entry.get("equipmentModels") or []],
        )
    return out


def clear_tag_cache() -> None:
    """Drop the compiled matcher. Tests patch the registry after import."""
    global _ENGINE
    _ENGINE = None


def _engine() -> tuple[
    Any,
    list[dict[str, Any]],
    frozenset[str],
    dict[str, dict[str, list[str]]],
    dict[str, tuple[list[str], list[str]]],
]:
    global _ENGINE
    if _ENGINE is None:
        equipment_registry = load_equipment()
        gated = _ev.gated_entries(equipment_registry)
        gated_ids = {e["id"] for e in gated}
        gated_owned = frozenset(
            gated_ids | {f"{e['id']}_{m['id']}" for e in gated for m in e.get("models") or []}
        )
        patterns = [p for p in compile_patterns(equipment_registry) if p[1] not in gated_ids]
        _ENGINE = (patterns, gated, gated_owned, _load_overrides(), _load_retained())
    return _ENGINE  # type: ignore[return-value]


def tags_for_sidecar(
    sidecar: dict[str, Any],
    *,
    include_retained: bool = True,
) -> tuple[list[str], list[str]]:
    """Return ``(equipment, equipmentModels)`` for one sidecar.

    Stored ``equipment`` / ``equipmentModels`` keys are ignored. The result
    is the matcher, the evidence rule, the overrides file, and (unless
    ``include_retained`` is false) the retained residue.
    """
    patterns, gated, gated_owned, overrides, retained = _engine()
    bare = dict(sidecar)
    bare.pop("equipment", None)
    bare.pop("equipmentModels", None)
    equipment, equipment_models = _compute_tags(bare, patterns)
    gated_eq, gated_models = _compute_gated_tags(bare, gated)
    equipment = sorted(set(equipment) | gated_eq)
    equipment_models = sorted(set(equipment_models) | gated_models)
    applied = _apply_tags(
        bare,
        equipment,
        equipment_models,
        gated_owned,
        overrides.get(str(sidecar.get("id") or "")),
    )
    eq = set(applied.get("equipment") or [])
    models = set(applied.get("equipmentModels") or [])
    if include_retained:
        extra_eq, extra_models = retained.get(str(sidecar.get("id") or ""), ([], []))
        eq |= set(extra_eq)
        models |= set(extra_models)
    return sorted(eq), sorted(models)


def with_resolved_tags(sidecar: dict[str, Any]) -> dict[str, Any]:
    """Fill equipment tags when the sidecar does not store them.

    A sidecar that already has ``equipment`` or ``equipmentModels`` is
    returned as-is, so a fixture that sets those keys keeps them. Empty
    computed results stay omitted.
    """
    if "equipment" in sidecar or "equipmentModels" in sidecar:
        return sidecar
    equipment, equipment_models = tags_for_sidecar(sidecar)
    if not equipment and not equipment_models:
        return sidecar
    out = dict(sidecar)
    if equipment:
        out["equipment"] = equipment
    if equipment_models:
        out["equipmentModels"] = equipment_models
    return out


def _reorder_sidecar(sidecar: dict[str, Any]) -> dict[str, Any]:
    """Return a dict with keys in ``_SIDECAR_FIELD_ORDER`` then sorted extras.

    Preserves values; only moves keys. Unknown keys are appended in
    alphabetical order so brand-new fields don't randomly drift in diffs.
    """
    ordered: dict[str, Any] = {}
    for k in _SIDECAR_FIELD_ORDER:
        if k in sidecar:
            ordered[k] = sidecar[k]
    for k in sorted(sidecar.keys()):
        if k not in ordered:
            ordered[k] = sidecar[k]
    return ordered


def _apply_tags(
    sidecar: dict[str, Any],
    equipment: list[str],
    equipment_models: list[str],
    gated_owned: frozenset[str] = frozenset(),
    override: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Return a new sidecar dict with ``equipment``/``equipmentModels`` set.

    Conventions:
        - Computed tags are **merged** with any existing values so that
          manually-set tags (from Gold uplift agents or hand-edits) are
          never lost. Exception: ids in ``gated_owned`` (evidence-gated
          vendors and their model compounds) are owned by this generator
          and replaced outright, as is any ``<gated vendor>_*`` model id
          that is no longer in the registry; hand corrections for them live
          in ``data/equipment-tag-overrides.json`` (``override``).
        - Empty arrays are ELIDED (key is removed). Keeps diffs small.
        - If the merged arrays equal the existing ones, no change.
        - Keys re-ordered to the canonical field order to keep sidecar
          outputs stable across generator runs.
    """
    out = dict(sidecar)
    existing_eq = set(sidecar.get("equipment") or []) - gated_owned
    existing_models = {
        m
        for m in sidecar.get("equipmentModels") or []
        if m not in gated_owned and m.split("_", 1)[0] not in gated_owned
    }

    eq_set = existing_eq | set(equipment)
    model_set = existing_models | set(equipment_models)
    if override:
        for tag in override.get("add") or []:
            vendor = tag.split("_", 1)[0]
            if tag != vendor and vendor in gated_owned:
                model_set.add(tag)
            eq_set.add(vendor)
        for tag in override.get("remove") or []:
            eq_set.discard(tag)
            model_set.discard(tag)
    merged_eq = sorted(eq_set)
    merged_models = sorted(model_set)

    if merged_eq:
        out["equipment"] = merged_eq
    else:
        out.pop("equipment", None)
    if merged_models:
        out["equipmentModels"] = merged_models
    else:
        out.pop("equipmentModels", None)
    return _reorder_sidecar(out)


def _serialise(sidecar: dict[str, Any]) -> str:
    # Every sidecar in this repo is emitted as indent=2 + ensure_ascii=False
    # + trailing newline. Keep that contract.
    return json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"


def _process_sidecars(
    check: bool,
) -> tuple[int, int, list[Path], Counter[str], Counter[str]]:
    """Strip stored tags. Return (processed, stripped, paths, eq_counts, model_counts)."""
    clear_tag_cache()
    processed = 0
    changed_paths: list[Path] = []
    eq_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()

    for path in _iter_sidecar_paths():
        sidecar = _read_sidecar(path)
        if sidecar is None:
            continue
        processed += 1
        equipment, equipment_models = tags_for_sidecar(sidecar)
        for tag in equipment:
            eq_counts[tag] += 1
        for tag in equipment_models:
            model_counts[tag] += 1
        if "equipment" not in sidecar and "equipmentModels" not in sidecar:
            continue
        changed_paths.append(path)
        if check:
            continue
        stripped = dict(sidecar)
        stripped.pop("equipment", None)
        stripped.pop("equipmentModels", None)
        path.write_text(_serialise(stripped), encoding="utf-8")

    return processed, len(changed_paths), changed_paths, eq_counts, model_counts


def _print_report(
    processed: int,
    changed: int,
    eq_counts: Counter[str],
    model_counts: Counter[str],
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


def main(argv: list[str] | None = None) -> int:
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
    args = parser.parse_args(argv)

    processed, changed, changed_paths, eq_counts, model_counts = _process_sidecars(check=args.check)

    if args.check:
        if changed > 0:
            print(
                f"FATAL: {changed}/{processed} UC sidecars still store "
                f"equipment/equipmentModels. The build computes those tags.",
                file=sys.stderr,
            )
            print(
                "Re-run `python -m splunk_uc generate-equipment-tags` to remove them. Affected files:",
                file=sys.stderr,
            )
            for p in changed_paths[:25]:
                print(f"  {p.relative_to(_REPO_ROOT)}", file=sys.stderr)
            if changed > 25:
                print(f"  ... and {changed - 25} more", file=sys.stderr)
            return 1
        print(f"OK: {processed} UC sidecars store no equipment tags.")
        return 0

    if args.report:
        _print_report(processed, changed, eq_counts, model_counts)
    else:
        print(f"Processed {processed} sidecars, stripped {changed}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
