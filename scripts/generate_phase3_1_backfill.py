#!/usr/bin/env python3
"""Phase 3.1 clause-level backfill generator.

Phase 3.1 closes the remaining tier-1 clause gaps on existing cat-22 UCs
by authoring additional ``compliance[]`` entries; it does NOT create new
UCs, new SPL, or new markdown. The generator reads
``data/per-regulation/phase3.1.json`` (the authoritative mapping between
uncovered tier-1 clauses and the existing cat-22 UC that semantically
covers each one) and idempotently appends any missing compliance entry
to the target UC's JSON sidecar.

Idempotency rule
----------------
A compliance entry is considered "already present" when an existing entry
in the target UC's ``compliance[]`` array matches on the triple
``(regulation, version, clause)``. Match comparisons are case-insensitive
for ``regulation`` to absorb spelling drift between aliases (e.g.
``ISO/IEC 27001`` and ``ISO 27001``), but ``version`` and ``clause``
compare exactly since those are the load-bearing audit identifiers.

Security notes
--------------
- All file writes are under repo-relative paths (``use-cases/cat-22/``).
  No user input is evaluated; all mapping data lives in the JSON manifest
  at ``data/per-regulation/phase3.1.json`` which is schema-validated by
  ``scripts/audit_compliance_mappings.py`` after generation
  (codeguard-0-input-validation-injection,
  codeguard-0-file-handling-and-uploads).
- JSON is parsed with the stdlib (no external network, no schema
  resolution in flight at emission time).
- Output field order matches the canonical order used by Phase 1.6,
  Phase 2.2 and Phase 2.3 generators so that byte-level diffs stay
  legible.

Usage
-----
    python3 scripts/generate_phase3_1_backfill.py            # write changes
    python3 scripts/generate_phase3_1_backfill.py --check    # drift-detect

``--check`` exits non-zero if any tracked sidecar would change on disk.
Wired into ``.github/workflows/validate.yml`` as a CI gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SIDECAR_DIR = REPO_ROOT / "use-cases" / "cat-22"
MANIFEST_PATH = REPO_ROOT / "data" / "per-regulation" / "phase3.1.json"

# Canonical sidecar field order. Mirrors Phase 2.3 generator so that
# repeated runs of all generators keep sidecars byte-comparable.
SIDECAR_FIELD_ORDER: Tuple[str, ...] = (
    "$schema",
    "id",
    "title",
    "criticality",
    "difficulty",
    "monitoringType",
    "splunkPillar",
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

# Keys that may legitimately appear in Phase 3.1 compliance entries.
_ALLOWED_ENTRY_KEYS: Tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
    "provenance",
)


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def _canonical_sidecar(sidecar: Dict[str, Any]) -> Dict[str, Any]:
    """Emit the sidecar with keys in canonical order for deterministic output."""
    ordered: Dict[str, Any] = {}
    for key in SIDECAR_FIELD_ORDER:
        if key in sidecar:
            ordered[key] = sidecar[key]
    # Preserve any unexpected keys at the end in their original order so we
    # never silently drop information that pre-existed on disk.
    for key, value in sidecar.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


# ---------------------------------------------------------------------------
# Compliance merge logic
# ---------------------------------------------------------------------------

def _normalise_regulation(name: str) -> str:
    return (name or "").strip().lower()


def _entry_key(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        _normalise_regulation(entry.get("regulation", "")),
        str(entry.get("version", "")).strip(),
        str(entry.get("clause", "")).strip(),
    )


def _build_new_entry(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a compliance[] entry from a manifest mapping."""
    entry: Dict[str, Any] = {
        "regulation": mapping["regulation"],
        "version": mapping["version"],
        "clause": mapping["clause"],
        "mode": mapping["mode"],
        "assurance": mapping["assurance"],
        "assurance_rationale": mapping["assurance_rationale"],
    }
    if mapping.get("clauseUrl"):
        # Field order in the emitted entry: regulation, version, clause,
        # clauseUrl, mode, assurance, assurance_rationale. Mirrors the
        # convention used by Phase 2.3.
        entry = {
            "regulation": mapping["regulation"],
            "version": mapping["version"],
            "clause": mapping["clause"],
            "clauseUrl": mapping["clauseUrl"],
            "mode": mapping["mode"],
            "assurance": mapping["assurance"],
            "assurance_rationale": mapping["assurance_rationale"],
        }
    # Unknown/unexpected keys are dropped defensively.
    return {k: v for k, v in entry.items() if k in _ALLOWED_ENTRY_KEYS}


def _apply_mapping(sidecar: Dict[str, Any], mapping: Dict[str, Any]) -> bool:
    """Idempotently add the manifest mapping to the UC sidecar.

    Returns True if the sidecar was modified, False otherwise.
    """
    compliance: List[Dict[str, Any]] = list(sidecar.get("compliance", []))
    new_entry = _build_new_entry(mapping)
    new_key = _entry_key(new_entry)
    for existing in compliance:
        if _entry_key(existing) == new_key:
            return False
    compliance.append(new_entry)
    sidecar["compliance"] = compliance
    return True


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _load_manifest() -> List[Dict[str, Any]]:
    manifest = _read_json(MANIFEST_PATH)
    mappings = manifest.get("mappings", [])
    if not isinstance(mappings, list) or not mappings:
        raise SystemExit(
            f"{MANIFEST_PATH}: manifest must contain a non-empty 'mappings' array",
        )
    return mappings


def _sidecar_path(uc_id: str) -> Path:
    return SIDECAR_DIR / f"uc-{uc_id}.json"


def _process(check_only: bool) -> int:
    mappings = _load_manifest()
    # Group mappings per UC so a single UC picks up all relevant new entries
    # in a single read/write pass.
    per_uc: Dict[str, List[Dict[str, Any]]] = {}
    for mapping in mappings:
        per_uc.setdefault(mapping["uc_id"], []).append(mapping)

    drift = False
    changed_uc_ids: List[str] = []
    missing: List[str] = []

    for uc_id in sorted(per_uc, key=lambda s: [int(p) if p.isdigit() else p
                                              for p in s.split(".")]):
        path = _sidecar_path(uc_id)
        if not path.exists():
            missing.append(uc_id)
            continue
        sidecar = _read_json(path)
        original = json.dumps(sidecar, sort_keys=True, ensure_ascii=False)
        touched = False
        for mapping in per_uc[uc_id]:
            if _apply_mapping(sidecar, mapping):
                touched = True
        if not touched:
            continue
        ordered = _canonical_sidecar(sidecar)
        new_text = json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"
        on_disk = path.read_text(encoding="utf-8")
        if new_text == on_disk:
            # Reorder alone did not change bytes (the compliance[] append
            # was a no-op after canonical serialisation).
            continue
        if check_only:
            drift = True
        else:
            path.write_text(new_text, encoding="utf-8")
        changed_uc_ids.append(uc_id)
        # Bookkeeping only; never dropped into output to avoid noisy stdout.
        del original

    if missing:
        print(
            "ERROR: manifest references UC sidecars that do not exist:",
            file=sys.stderr,
        )
        for uc_id in missing:
            print(f"  - {uc_id} ({_sidecar_path(uc_id).relative_to(REPO_ROOT)})",
                  file=sys.stderr)
        return 2

    if check_only:
        if drift:
            print(
                "Phase 3.1 backfill drift detected. Run "
                "scripts/generate_phase3_1_backfill.py and commit the result.",
                file=sys.stderr,
            )
            for uc_id in changed_uc_ids:
                print(f"  drift: {uc_id}", file=sys.stderr)
            return 1
        print(f"Phase 3.1 backfill: OK ({len(mappings)} mappings, "
              f"{len(per_uc)} UCs, no drift).")
        return 0

    total_entries = sum(len(v) for v in per_uc.values())
    print(
        f"Phase 3.1 backfill: wrote {len(changed_uc_ids)} UC sidecar(s) "
        f"with up to {total_entries} new compliance entries "
        f"across {len(per_uc)} target UCs.",
    )
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.1 clause-level backfill generator. Appends clause-level "
            "compliance entries to existing cat-22 UC sidecars, closing the "
            "remaining tier-1 clause gaps for CMMC 2.0, ISO/IEC 27001:2013, "
            "NIST CSF 1.1 & 2.0, PCI-DSS v3.2.1, GDPR 2016/679, NIST SP "
            "800-53 Rev. 5 and HIPAA Security Rule 2013-final."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=("Drift-detection mode. Exits non-zero if any tracked sidecar "
              "would change on disk. Used by validate.yml."),
    )
    args = parser.parse_args(argv)
    return _process(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
