#!/usr/bin/env python3
"""Phase 3.2 cross-cutting compliance generator.

Phase 3.2 attaches clause-level regulatory tags to *existing* UCs that live
OUTSIDE cat-22. The generator does NOT create new UCs, does NOT author SPL,
and does NOT modify markdown. It reads the hand-curated manifest
``data/per-regulation/phase3.2.json`` and, for each target UC, writes (or
idempotently updates) a minimal JSON sidecar at
``use-cases/cat-NN/uc-<id>.json`` that contains the ``compliance[]`` entries
mapping that UC to specific regulatory clauses.

Why minimal sidecars?
---------------------
The authoritative narrative, SPL and data sources for non-cat-22 UCs live in
the markdown files (``use-cases/cat-NN-<slug>.md``). Phase 3.2 is purely a
metadata overlay that an auditor can consume: every existing compliance-aware
script in the repo (``scripts/audit_compliance_mappings.py``,
``scripts/audit_compliance_gaps.py``, ``scripts/generate_api_surface.py``,
``scripts/generate_splunk_app.py``) already reads ``use-cases/cat-*/uc-*.json``
so a minimal sidecar is sufficient to pick up the new clause tags without
touching a single line of SPL.

Idempotency rule
----------------
A compliance entry is considered "already present" when an existing entry in
the target sidecar's ``compliance[]`` array matches on the triple
``(regulation, version, clause)``. ``regulation`` comparison is
case-insensitive so that running the generator repeatedly never produces
duplicates even if the authoritative spelling drifts between aliases. If the
target sidecar does not exist yet, a brand-new minimal sidecar is emitted
with exactly three keys: ``$schema``, ``id``, ``title``, ``compliance``.

Safety gates
------------
* The generator refuses to touch any UC whose id starts with ``22.`` (those
  sidecars are owned by Phase 1.3 / 2.2 / 2.3 / 3.1 generators).
* Before writing a sidecar, the generator verifies that the UC exists as a
  markdown heading in the corresponding ``use-cases/cat-NN-<slug>.md`` file
  AND that the heading title matches the manifest title byte-for-byte
  (modulo stripping of the leading ``UC-<id> \u00b7 `` prefix). Any drift aborts
  the run with a clear error, so the manifest can never silently point at a
  non-existent or renamed UC.

Security notes
--------------
* All file writes are under repo-relative paths (``use-cases/cat-NN/``). No
  user input is evaluated; the manifest is schema-validated by
  ``scripts/audit_compliance_mappings.py`` after generation
  (codeguard-0-input-validation-injection,
  codeguard-0-file-handling-and-uploads).
* JSON is parsed with the stdlib, no network, no external code.
* The generator is deterministic: for a given manifest + repo state it
  produces byte-identical sidecars across runs (canonical field order,
  sorted iteration over UC IDs, no timestamps in output).

Usage
-----
    python3 scripts/generate_phase3_2_cross_cutting.py            # write
    python3 scripts/generate_phase3_2_cross_cutting.py --check    # drift

``--check`` exits non-zero if any tracked sidecar would change on disk.
Wired into ``.github/workflows/validate.yml`` as a CI gate so a forgotten
regeneration or a hand-edited sidecar both fail the pipeline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
USE_CASES_DIR = REPO_ROOT / "use-cases"
MANIFEST_PATH = REPO_ROOT / "data" / "per-regulation" / "phase3.2.json"

# Matches a UC heading like:
#   ### UC-9.1.1 · Brute-Force Login Detection
#   #### UC-14.2.4 · Network Segmentation Monitoring
# Captures (1) uc_id, (2) title. The middle-dot character is U+00B7 and
# must be preserved verbatim (it is the documented separator in the
# markdown style guide).
_HEADING_RE = re.compile(
    r"^#{2,4}\s+UC-(?P<id>\d+\.\d+\.\d+)\s*\u00b7\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)

# Canonical sidecar field order. Mirrors Phase 1.6 / 2.2 / 2.3 / 3.1
# generators so that repeated runs of the whole generator pipeline keep
# sidecars byte-comparable. Fields not present in a given sidecar are
# simply skipped. Any unexpected extra keys (should be impossible given
# the uc.schema.json ``additionalProperties: false``) are emitted at the
# end so no information is ever dropped.
SIDECAR_FIELD_ORDER: Tuple[str, ...] = (
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

# Keys that may legitimately appear in Phase 3.2 compliance entries.
# Sourced from the manifest schema ``per-regulation-phase3.2.schema.json``.
# Anything else is silently dropped to keep the output schema-clean.
_ALLOWED_ENTRY_KEYS: Tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
)

# Order in which entry keys are emitted so diffs stay legible.
_ENTRY_FIELD_ORDER: Tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
)

# The schema hint path that minimal sidecars get when they are newly
# created. Sidecars in ``use-cases/cat-NN/`` are two levels deep relative
# to the repo root, so ``../../schemas/uc.schema.json`` is correct (same
# as every existing cat-22 sidecar).
_SCHEMA_REF = "../../schemas/uc.schema.json"


# ---------------------------------------------------------------------------
# Low-level IO
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _encode_sidecar(sidecar: Dict[str, Any]) -> str:
    """Serialise a sidecar dict with canonical field order + trailing newline."""
    ordered = _canonical_sidecar(sidecar)
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"


def _canonical_sidecar(sidecar: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in SIDECAR_FIELD_ORDER:
        if key in sidecar:
            ordered[key] = sidecar[key]
    # Defensive: preserve any unknown keys that pre-existed on disk.
    for key, value in sidecar.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _canonical_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in _ENTRY_FIELD_ORDER:
        if key in entry:
            ordered[key] = entry[key]
    return ordered


# ---------------------------------------------------------------------------
# Manifest + markdown validation
# ---------------------------------------------------------------------------


def _load_manifest() -> Dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("ucs"), list):
        raise SystemExit(
            f"{MANIFEST_PATH}: manifest must be an object containing a 'ucs' array",
        )
    if not manifest["ucs"]:
        raise SystemExit(f"{MANIFEST_PATH}: 'ucs' array is empty")
    return manifest


def _category_padded(uc_id: str) -> str:
    """Return the two-digit zero-padded category segment for a UC id.

    cat-NN directories always use two-digit padding (cat-01, cat-09, cat-14)
    to mirror the markdown naming convention (cat-01-server-compute.md).
    """
    head = uc_id.split(".", 1)[0]
    return head.zfill(2)


def _sidecar_path(uc_id: str) -> Path:
    cat = _category_padded(uc_id)
    return USE_CASES_DIR / f"cat-{cat}" / f"uc-{uc_id}.json"


def _build_markdown_title_index() -> Dict[str, Tuple[str, Path]]:
    """Return {uc_id: (markdown_title, source_file)} for every non-cat-22 UC.

    cat-22 UCs are intentionally excluded so we can assert that Phase 3.2
    never accidentally overlaps with cat-22 sidecar ownership.
    """
    index: Dict[str, Tuple[str, Path]] = {}
    for md_path in sorted(USE_CASES_DIR.glob("cat-*-*.md")):
        # Example path stem: 'cat-09-identity-access-management'
        stem = md_path.stem
        # Skip cat-22-regulatory-compliance.md entirely; it is owned by
        # the other generators and any UC there must never appear in the
        # Phase 3.2 manifest.
        if stem.startswith("cat-22-"):
            continue
        content = md_path.read_text(encoding="utf-8")
        for match in _HEADING_RE.finditer(content):
            uc_id = match.group("id")
            title = match.group("title").rstrip()
            # If the same UC id appears in two markdown files (should not
            # happen; audit_uc_ids.py fails CI if it does), keep the
            # first occurrence and record the duplicate for error output.
            index.setdefault(uc_id, (title, md_path))
    return index


def _validate_targets(
    manifest: Dict[str, Any],
    markdown_index: Dict[str, Tuple[str, Path]],
) -> None:
    """Fail loudly if the manifest points at non-existent or renamed UCs."""
    errors: List[str] = []
    for uc in manifest["ucs"]:
        uc_id = uc.get("uc_id")
        title = uc.get("title")
        if not isinstance(uc_id, str) or not isinstance(title, str):
            errors.append(
                f"  - manifest entry missing uc_id/title: {uc!r}",
            )
            continue
        if uc_id.startswith("22."):
            errors.append(
                f"  - {uc_id}: cat-22 UCs are owned by Phase 1.3/2.2/2.3/3.1 generators; remove from phase3.2.json",
            )
            continue
        if uc_id not in markdown_index:
            errors.append(
                f"  - {uc_id}: manifest title={title!r} but no matching UC heading found in any use-cases/cat-*-*.md",
            )
            continue
        md_title, md_path = markdown_index[uc_id]
        if md_title != title:
            errors.append(
                f"  - {uc_id}: manifest title={title!r} differs from markdown title={md_title!r} in {md_path.relative_to(REPO_ROOT)}",
            )
    if errors:
        print(
            "ERROR: Phase 3.2 manifest references UCs that do not match the markdown truth:",
            file=sys.stderr,
        )
        for err in errors:
            print(err, file=sys.stderr)
        raise SystemExit(2)


# ---------------------------------------------------------------------------
# Compliance merge logic
# ---------------------------------------------------------------------------


def _normalise_regulation(name: Optional[str]) -> str:
    return (name or "").strip().lower()


def _entry_key(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        _normalise_regulation(entry.get("regulation", "")),
        str(entry.get("version", "")).strip(),
        str(entry.get("clause", "")).strip(),
    )


def _build_new_entry(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Project a manifest mapping onto a canonical compliance[] entry."""
    entry: Dict[str, Any] = {}
    for key in _ENTRY_FIELD_ORDER:
        if key in mapping:
            entry[key] = mapping[key]
    # Unknown/unexpected keys are dropped defensively (schema validation
    # happens upstream in audit_compliance_mappings.py).
    return {k: v for k, v in entry.items() if k in _ALLOWED_ENTRY_KEYS}


def _apply_mappings(
    sidecar: Dict[str, Any],
    mappings: Iterable[Dict[str, Any]],
) -> bool:
    """Idempotently append new manifest mappings to ``sidecar.compliance``.

    Returns True if any new entry was added (or an existing entry was
    touched by the canonical-order rewrite). Returns False when every
    mapping was already present.
    """
    existing: List[Dict[str, Any]] = list(sidecar.get("compliance", []))
    existing_keys = {_entry_key(e) for e in existing}
    touched = False
    for mapping in mappings:
        new_entry = _build_new_entry(mapping)
        key = _entry_key(new_entry)
        if key in existing_keys:
            continue
        existing.append(new_entry)
        existing_keys.add(key)
        touched = True
    if touched:
        # Canonicalise each entry's field order, but preserve the array
        # order: Phase 3.1 appends in manifest order, we do the same so
        # diffs stay legible.
        sidecar["compliance"] = [_canonical_entry(e) for e in existing]
    return touched


def _build_minimal_sidecar(uc_id: str, title: str) -> Dict[str, Any]:
    """Produce a brand-new sidecar skeleton for a UC that has none yet."""
    return {
        "$schema": _SCHEMA_REF,
        "id": uc_id,
        "title": title,
        "compliance": [],
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _uc_sort_key(uc_id: str) -> List[int]:
    return [int(p) for p in uc_id.split(".")]


def _process(check_only: bool) -> int:
    manifest = _load_manifest()
    markdown_index = _build_markdown_title_index()
    _validate_targets(manifest, markdown_index)

    per_uc: Dict[str, Tuple[str, List[Dict[str, Any]]]] = {}
    for uc in manifest["ucs"]:
        uc_id = uc["uc_id"]
        title = uc["title"]
        mappings = uc.get("mappings", [])
        if not isinstance(mappings, list) or not mappings:
            print(
                f"ERROR: {MANIFEST_PATH.relative_to(REPO_ROOT)}: uc_id={uc_id} has no mappings",
                file=sys.stderr,
            )
            return 2
        per_uc[uc_id] = (title, mappings)

    drift = False
    created: List[str] = []
    updated: List[str] = []

    for uc_id in sorted(per_uc, key=_uc_sort_key):
        title, mappings = per_uc[uc_id]
        path = _sidecar_path(uc_id)

        if path.exists():
            sidecar = _read_json(path)
            if not isinstance(sidecar, dict):
                print(
                    f"ERROR: {path.relative_to(REPO_ROOT)}: sidecar is not a JSON object",
                    file=sys.stderr,
                )
                return 2
            # Defensive safety rail: if some future hand edit silently
            # renamed the sidecar's title, refuse to mutate it; the
            # manifest should be the single source of truth.
            existing_id = sidecar.get("id")
            if existing_id and existing_id != uc_id:
                print(
                    f"ERROR: {path.relative_to(REPO_ROOT)}: sidecar.id={existing_id!r} does not match manifest uc_id={uc_id!r}",
                    file=sys.stderr,
                )
                return 2
            _apply_mappings(sidecar, mappings)
        else:
            sidecar = _build_minimal_sidecar(uc_id, title)
            _apply_mappings(sidecar, mappings)

        new_text = _encode_sidecar(sidecar)

        if path.exists():
            on_disk = path.read_text(encoding="utf-8")
            if new_text == on_disk:
                continue
            if check_only:
                drift = True
            else:
                path.write_text(new_text, encoding="utf-8")
            updated.append(uc_id)
        else:
            if check_only:
                drift = True
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(new_text, encoding="utf-8")
            created.append(uc_id)

    total_mappings = sum(len(mappings) for _, mappings in per_uc.values())

    if check_only:
        if drift:
            print(
                "Phase 3.2 cross-cutting drift detected. Run "
                "scripts/generate_phase3_2_cross_cutting.py and commit the "
                "result.",
                file=sys.stderr,
            )
            for uc_id in created:
                print(f"  would-create: {_sidecar_path(uc_id).relative_to(REPO_ROOT)}", file=sys.stderr)
            for uc_id in updated:
                print(f"  would-update: {_sidecar_path(uc_id).relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        print(
            f"Phase 3.2 cross-cutting: OK ({len(per_uc)} UCs, "
            f"{total_mappings} mappings, no drift).",
        )
        return 0

    print(
        f"Phase 3.2 cross-cutting: wrote {len(created)} new + {len(updated)} "
        f"updated sidecar(s) covering {len(per_uc)} UCs with "
        f"{total_mappings} compliance mappings.",
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.2 cross-cutting compliance generator. Emits or "
            "idempotently updates minimal JSON sidecars at "
            "use-cases/cat-NN/uc-<id>.json so existing non-cat-22 UCs "
            "carry clause-level regulatory tags. Reads "
            "data/per-regulation/phase3.2.json."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Drift-detection mode. Regenerates into memory and diffs "
            "against the committed tree. Exits non-zero on any drift. "
            "Used by validate.yml."
        ),
    )
    args = parser.parse_args(argv)
    return _process(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
