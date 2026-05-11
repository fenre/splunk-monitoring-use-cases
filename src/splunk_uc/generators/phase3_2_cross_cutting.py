#!/usr/bin/env python3
"""Phase 3.2 cross-cutting compliance generator.

Phase 3.2 attaches clause-level regulatory tags to *existing* UCs that live
OUTSIDE cat-22. The generator does NOT create new UCs and does NOT author
SPL. It reads the hand-curated manifest ``data/per-regulation/phase3.2.json``
and, for each target UC, idempotently merges new ``compliance[]`` entries
into the JSON SSOT sidecar at
``content/cat-NN-<slug>/UC-<id>.json``.

Why merge into the SSOT directly?
---------------------------------
``content/cat-*/UC-*.json`` is the single source of truth (ADR-0007). All
downstream tooling (``scripts/audit_compliance_mappings.py``,
``scripts/audit_compliance_gaps.py``, ``scripts/generate_api_surface.py``,
``scripts/generate_recommender_app.py``, the build pipeline) already reads
the SSOT, so writing the clause tags directly into the existing sidecar
keeps a single representation of the UC.

Idempotency rule
----------------
A compliance entry is considered "already present" when an existing entry in
the target sidecar's ``compliance[]`` array matches on the triple
``(regulation, version, clause)``. ``regulation`` comparison is
case-insensitive so that running the generator repeatedly never produces
duplicates even if the authoritative spelling drifts between aliases.

Safety gates
------------
* The generator refuses to touch any UC whose id starts with ``22.`` (those
  sidecars are owned by Phase 1.3 / 2.2 / 2.3 / 3.1 generators).
* The target sidecar MUST already exist in ``content/`` and the SSOT title
  MUST match the manifest title byte-for-byte. Any drift aborts the run
  with a clear error, so the manifest can never silently point at a
  non-existent or renamed UC.

Security notes
--------------
* All file writes are under repo-relative paths
  (``content/cat-NN-<slug>/``). No user input is evaluated; the manifest
  is schema-validated by ``scripts/audit_compliance_mappings.py`` after
  generation (codeguard-0-input-validation-injection,
  codeguard-0-file-handling-and-uploads).
* JSON is parsed with the stdlib, no network, no external code.
* The generator is deterministic: for a given manifest + repo state it
  produces byte-identical sidecars across runs (canonical field order,
  sorted iteration over UC IDs, no timestamps in output).

Usage
-----
    python3 -m splunk_uc generate-phase3-2-cross-cutting            # write
    python3 -m splunk_uc generate-phase3-2-cross-cutting --check    # drift

``--check`` exits non-zero if any tracked sidecar would change on disk.
Wired into ``.github/workflows/validate.yml`` as a CI gate so a forgotten
regeneration or a hand-edited sidecar both fail the pipeline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# audit-compliance-mappings requires every compliance entry to carry
# ``controlObjective`` and ``evidenceArtifact`` text. The Phase 4
# migration script is the canonical author of the templated drafts
# (``Auto-drafted — SME review required.`` suffix), so we re-use its
# helpers here rather than duplicating the templates. Imported at module
# scope so the dispatcher's smoke tests catch any breaking change in
# the helper signatures at import time.
from splunk_uc.migrations.migrate_compliance_phase4 import (
    synthesise_control_objective,
    synthesise_evidence_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"
MANIFEST_PATH = REPO_ROOT / "data" / "per-regulation" / "phase3.2.json"

# Matches the SSOT category folder name, e.g. ``cat-09-identity-access-management``.
_CAT_DIR_RE = re.compile(r"^cat-(?P<num>\d{2})-")

# Canonical sidecar field order. Mirrors Phase 1.6 / 2.2 / 2.3 / 3.1
# generators so that repeated runs of the whole generator pipeline keep
# sidecars byte-comparable. Fields not present in a given sidecar are
# simply skipped. Any unexpected extra keys (should be impossible given
# the uc.schema.json ``additionalProperties: false``) are emitted at the
# end so no information is ever dropped.
SIDECAR_FIELD_ORDER: tuple[str, ...] = (
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
# Sourced from the manifest schema ``per-regulation-phase3.2.schema.json``,
# plus ``controlObjective`` / ``evidenceArtifact`` which are auto-drafted
# in :func:`_apply_mappings` from the migration helpers
# (``synthesise_control_objective`` / ``synthesise_evidence_artifact``)
# so every new entry satisfies ``audit-compliance-mappings``'
# ``missing-control-objective`` / ``missing-evidence-artifact`` rules
# without manual SME backfill.
_ALLOWED_ENTRY_KEYS: tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
    "controlObjective",
    "evidenceArtifact",
)

# Order in which entry keys are emitted so diffs stay legible. Mirrors
# the on-disk layout produced by the v8.1 SSOT migration: identity
# (regulation/clause), satisfaction posture (mode/assurance/rationale),
# audit-evidence detail (controlObjective/evidenceArtifact). Pinning the
# order keeps :func:`_canonical_entry` byte-stable across regenerations
# so the ``--check`` drift gate stays green.
_ENTRY_FIELD_ORDER: tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
    "controlObjective",
    "evidenceArtifact",
)

# ---------------------------------------------------------------------------
# Low-level IO
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _encode_sidecar(sidecar: dict[str, Any]) -> str:
    """Serialise a sidecar dict with canonical field order + trailing newline."""
    ordered = _canonical_sidecar(sidecar)
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"


def _canonical_sidecar(sidecar: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in SIDECAR_FIELD_ORDER:
        if key in sidecar:
            ordered[key] = sidecar[key]
    # Defensive: preserve any unknown keys that pre-existed on disk.
    for key, value in sidecar.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _canonical_entry(entry: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in _ENTRY_FIELD_ORDER:
        if key in entry:
            ordered[key] = entry[key]
    return ordered


# ---------------------------------------------------------------------------
# Manifest + markdown validation
# ---------------------------------------------------------------------------


def _load_manifest() -> dict[str, Any]:
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

    SSOT category folders always use two-digit padding
    (``cat-01-server-compute``, ``cat-09-identity-access-management``,
    ``cat-14-iot-operational-technology-ot``).
    """
    head = uc_id.split(".", 1)[0]
    return head.zfill(2)


def _category_dir_index() -> dict[str, Path]:
    """Map two-digit category number -> SSOT folder path."""
    index: dict[str, Path] = {}
    for path in sorted(CONTENT_DIR.glob("cat-*-*")):
        if not path.is_dir():
            continue
        m = _CAT_DIR_RE.match(path.name)
        if not m:
            continue
        index[m.group("num")] = path
    return index


def _sidecar_path(uc_id: str, cat_index: dict[str, Path]) -> Path | None:
    """Resolve the SSOT sidecar path for ``uc_id`` (returns None if unknown)."""
    cat = _category_padded(uc_id)
    cat_dir = cat_index.get(cat)
    if cat_dir is None:
        return None
    return cat_dir / f"UC-{uc_id}.json"


def _build_ssot_title_index(
    cat_index: dict[str, Path],
) -> dict[str, tuple[str, Path]]:
    """Return ``{uc_id: (title, sidecar_path)}`` for every non-cat-22 SSOT UC.

    cat-22 UCs are intentionally excluded so we can assert that Phase 3.2
    never accidentally overlaps with cat-22 sidecar ownership.
    """
    index: dict[str, tuple[str, Path]] = {}
    for cat, cat_dir in cat_index.items():
        if cat == "22":
            continue
        for sidecar in sorted(cat_dir.glob("UC-*.json")):
            try:
                payload = _read_json(sidecar)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            uc_id = payload.get("id") or sidecar.stem.removeprefix("UC-")
            title = str(payload.get("title", "")).rstrip()
            index.setdefault(uc_id, (title, sidecar))
    return index


def _validate_targets(
    manifest: dict[str, Any],
    ssot_index: dict[str, tuple[str, Path]],
) -> None:
    """Fail loudly if the manifest points at non-existent or renamed UCs."""
    errors: list[str] = []
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
        if uc_id not in ssot_index:
            errors.append(
                f"  - {uc_id}: manifest title={title!r} but no matching UC sidecar found under content/cat-*/UC-*.json",
            )
            continue
        ssot_title, ssot_path = ssot_index[uc_id]
        if ssot_title != title:
            errors.append(
                f"  - {uc_id}: manifest title={title!r} differs from SSOT title={ssot_title!r} in {ssot_path.relative_to(REPO_ROOT)}",
            )
    if errors:
        print(
            "ERROR: Phase 3.2 manifest references UCs that do not match the SSOT:",
            file=sys.stderr,
        )
        for err in errors:
            print(err, file=sys.stderr)
        raise SystemExit(2)


# ---------------------------------------------------------------------------
# Compliance merge logic
# ---------------------------------------------------------------------------


def _normalise_regulation(name: str | None) -> str:
    return (name or "").strip().lower()


def _entry_key(entry: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _normalise_regulation(entry.get("regulation", "")),
        str(entry.get("version", "")).strip(),
        str(entry.get("clause", "")).strip(),
    )


def _build_new_entry(mapping: dict[str, Any]) -> dict[str, Any]:
    """Project a manifest mapping onto a canonical compliance[] entry."""
    entry: dict[str, Any] = {}
    for key in _ENTRY_FIELD_ORDER:
        if key in mapping:
            entry[key] = mapping[key]
    # Unknown/unexpected keys are dropped defensively (schema validation
    # happens upstream in audit_compliance_mappings.py).
    return {k: v for k, v in entry.items() if k in _ALLOWED_ENTRY_KEYS}


def _apply_mappings(
    sidecar: dict[str, Any],
    mappings: Iterable[dict[str, Any]],
) -> bool:
    """Idempotently append new manifest mappings to ``sidecar.compliance``.

    For every newly-added entry the helper also auto-drafts
    ``controlObjective`` and ``evidenceArtifact`` strings via the
    Phase 4 migration synthesizers (``Auto-drafted — SME review
    required.`` suffix). This keeps every Phase 3.2 cross-cutting
    mapping audit-clean against
    ``audit-compliance-mappings``' ``missing-control-objective`` /
    ``missing-evidence-artifact`` rules without forcing the manifest
    author to write the auditor-facing prose by hand. SMEs can refine
    the draft text later; idempotency means subsequent regenerations
    will not overwrite SME-curated text because the entry key already
    exists in ``existing_keys``.

    Returns True if any new entry was added (or an existing entry was
    touched by the canonical-order rewrite). Returns False when every
    mapping was already present.
    """
    existing: list[dict[str, Any]] = list(sidecar.get("compliance", []))
    existing_keys = {_entry_key(e) for e in existing}
    touched = False
    for mapping in mappings:
        new_entry = _build_new_entry(mapping)
        key = _entry_key(new_entry)
        if key in existing_keys:
            continue
        # Auto-draft the auditor-facing fields. These templates are
        # the canonical phrasing the v8.1 SSOT migration used; using
        # the same helper functions guarantees byte-stable output
        # (no template drift across generators).
        if "controlObjective" not in new_entry:
            new_entry["controlObjective"] = synthesise_control_objective(
                sidecar, new_entry, None
            )
        if "evidenceArtifact" not in new_entry:
            new_entry["evidenceArtifact"] = synthesise_evidence_artifact(
                sidecar, new_entry
            )
        existing.append(new_entry)
        existing_keys.add(key)
        touched = True
    if touched:
        # Canonicalise each entry's field order, but preserve the array
        # order: Phase 3.1 appends in manifest order, we do the same so
        # diffs stay legible.
        sidecar["compliance"] = [_canonical_entry(e) for e in existing]
    return touched


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _uc_sort_key(uc_id: str) -> list[int]:
    return [int(p) for p in uc_id.split(".")]


def _process(check_only: bool) -> int:
    manifest = _load_manifest()
    cat_index = _category_dir_index()
    ssot_index = _build_ssot_title_index(cat_index)
    _validate_targets(manifest, ssot_index)

    per_uc: dict[str, tuple[str, list[dict[str, Any]]]] = {}
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
    updated: list[str] = []

    for uc_id in sorted(per_uc, key=_uc_sort_key):
        _title, mappings = per_uc[uc_id]
        path = _sidecar_path(uc_id, cat_index)
        if path is None or not path.exists():
            print(
                f"ERROR: SSOT sidecar missing for {uc_id}; cannot apply Phase 3.2 mappings",
                file=sys.stderr,
            )
            return 2

        sidecar = _read_json(path)
        if not isinstance(sidecar, dict):
            print(
                f"ERROR: {path.relative_to(REPO_ROOT)}: sidecar is not a JSON object",
                file=sys.stderr,
            )
            return 2
        existing_id = sidecar.get("id")
        if existing_id and existing_id != uc_id:
            print(
                f"ERROR: {path.relative_to(REPO_ROOT)}: sidecar.id={existing_id!r} does not match manifest uc_id={uc_id!r}",
                file=sys.stderr,
            )
            return 2
        _apply_mappings(sidecar, mappings)

        new_text = _encode_sidecar(sidecar)
        on_disk = path.read_text(encoding="utf-8")
        if new_text == on_disk:
            continue
        if check_only:
            drift = True
        else:
            path.write_text(new_text, encoding="utf-8")
        updated.append(uc_id)

    total_mappings = sum(len(mappings) for _, mappings in per_uc.values())

    if check_only:
        if drift:
            print(
                "Phase 3.2 cross-cutting drift detected. Run "
                "`python -m splunk_uc generate-phase3-2-cross-cutting` and "
                "commit the result.",
                file=sys.stderr,
            )
            for uc_id in updated:
                resolved = _sidecar_path(uc_id, cat_index)
                if resolved is not None:
                    print(
                        f"  would-update: {resolved.relative_to(REPO_ROOT)}",
                        file=sys.stderr,
                    )
            return 1
        print(
            f"Phase 3.2 cross-cutting: OK ({len(per_uc)} UCs, "
            f"{total_mappings} mappings, no drift).",
        )
        return 0

    print(
        f"Phase 3.2 cross-cutting: updated {len(updated)} sidecar(s) covering "
        f"{len(per_uc)} UCs with {total_mappings} compliance mappings.",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.2 cross-cutting compliance generator. Idempotently "
            "merges clause-level regulatory tags into existing non-cat-22 "
            "UC sidecars under content/cat-NN-<slug>/UC-<id>.json. Reads "
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
