#!/usr/bin/env python3
"""Phase 3.3 derivative-regulation propagation generator.

Phase 3.3 materialises derivative-regulation compliance[] entries on every UC
sidecar by walking the ``derivesFrom`` graph declared in
``data/regulations.json``. For each parent-regulation entry present on a UC
(e.g. ``GDPR@2016/679 Art.32``) the generator computes the matching clause on
each derivative regulation (UK GDPR, CCPA/CPRA, Swiss nFADP, LGPD, APPI) and
appends an inherited compliance[] entry tagged with ``derivationSource`` so
auditors can trace the lineage.

Why propagate at all?
---------------------
Derivative regulations re-use the substance of their parent framework.
A UC that detects unauthorised access to a database already "satisfies"
GDPR Art.32, UK GDPR Art.32, LGPD Art.46 and APPI Art.23 simultaneously —
the same SPL, dashboard and evidence-pack artefact covers them all.
Representing this explicitly turns tier-2 coverage from 0 % (no native
mapping exists) to a defensible partial/contributing claim while still
leaving room for SME review to upgrade or invalidate the inherited entry.

Propagation semantics
---------------------
``data/regulations.json`` -> ``derivesFrom`` is the single source of truth.
Each derivative declares:

* ``inheritanceMode``
    * ``identity`` (UK GDPR): clause numbering is preserved 1:1; any
      parent Art.N propagates to derivative Art.N unless listed in
      ``divergences``.
    * ``mapped`` (CCPA/nFADP/LGPD/APPI): only clauses explicitly listed
      in ``clauseMapping`` propagate. The mapping is hand-curated against
      the derivative's own authoritative commentary.
* ``clauseMapping``: ``{parent-clause: derivative-clause}``. Required
  when ``inheritanceMode == "mapped"``.
* ``divergences``: informational per-clause notes. Propagation still
  happens, but the inherited entry carries ``derivationSource.divergenceNote``
  so legal/SME review can flag the scope mismatch.

The inherited entry always adopts:

* ``regulation``      -> derivative framework ``shortName`` from regulations.json
* ``version``         -> derivative ``versions[0].version``
* ``clause``          -> resolved target clause (identity or mapping)
* ``mode``            -> mirrors the parent entry's mode
* ``assurance``       -> degraded one step (full -> partial, partial -> contributing).
                         Contributing parents never propagate (we would
                         otherwise emit a "contributing derived from
                         contributing" mapping, which is noise).
* ``assurance_rationale`` -> auto-generated, explicit about the lineage
* ``provenance``      -> ``derived-from-parent``
* ``derivationSource`` -> structured lineage object (parent reg/version/clause,
                         parent assurance, inheritanceMode, optional
                         divergenceNote).

Precedence rule
---------------
Native (hand-authored / crosswalk / exemplar-authored) entries always win.
If a UC already has an entry for a (derivative, version, clause) key, the
generator leaves it untouched and emits nothing — even if the native
assurance is weaker than what would have been derived. Auditors expect
a hand-curated mapping to be authoritative over a mechanically-derived
one; Phase 3.3 augments coverage, it never overrides it.

Idempotency and determinism
---------------------------
* Every run produces byte-identical sidecars for a given manifest state.
* Previously-derived entries (identified by
  ``provenance == "derived-from-parent"`` or by the presence of
  ``derivationSource``) are regenerated from scratch each run. This is
  how deletions propagate: if a parent entry is removed from a sidecar,
  the corresponding derived entries disappear on the next run.
* Canonical field order mirrors Phase 3.2 so diffs stay legible.

Safety & determinism
--------------------
* No network I/O. No code execution. Only stdlib JSON parsing
  (codeguard-0-input-validation-injection, codeguard-0-xml-and-serialization
  — we do not parse XML).
* All writes are under repo-relative use-cases/cat-NN/ directories
  (codeguard-0-file-handling-and-uploads).
* No secrets, no credentials, no hardcoded tokens
  (codeguard-1-hardcoded-credentials).
* Output is deterministic: sorted iteration over UC IDs, sorted iteration
  over derivative ids, canonical field order, no timestamps.

Usage
-----
    python3 scripts/generate_phase3_3_derivatives.py            # write
    python3 scripts/generate_phase3_3_derivatives.py --check    # drift

``--check`` exits non-zero if any tracked sidecar would change on disk.
Wired into ``.github/workflows/validate.yml`` as a CI gate so a forgotten
regeneration or a manually-edited derived entry both fail the pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
USE_CASES_DIR = REPO_ROOT / "use-cases"
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"

# Canonical sidecar field order. Mirrors Phase 3.2 / 3.1 / 2.2 generators
# so repeated runs of the full generator pipeline keep sidecars
# byte-comparable.
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

# Order in which compliance[] entry keys are emitted so diffs stay legible.
# Matches schemas/uc.schema.json property declaration order and Phase 3.2
# output. ``derivationSource`` is last because it is the largest sub-object.
ENTRY_FIELD_ORDER: Tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
    "provenance",
    "signedBy",
    "derivationSource",
)

DERIVATION_SOURCE_FIELD_ORDER: Tuple[str, ...] = (
    "parentRegulation",
    "parentVersion",
    "parentClause",
    "parentAssurance",
    "inheritanceMode",
    "divergenceNote",
)

# Assurance degradation rule. Mapping is: parent -> inherited.
# ``contributing`` is absent because it does not propagate further.
ASSURANCE_DEGRADATION: Dict[str, str] = {
    "full": "partial",
    "partial": "contributing",
}


# ---------------------------------------------------------------------------
# regulations.json ingestion
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class FrameworkIndex:
    """Helper wrapper around data/regulations.json.

    Provides canonical-id lookup, version enumeration, and access to the
    derivesFrom graph, all in constant time.
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self._by_id: Dict[str, Dict[str, Any]] = {}
        for framework in data.get("frameworks", []):
            self._by_id[framework["id"]] = framework
        # Lower-cased alias index. aliasIndex values are framework ids.
        raw_alias = data.get("aliasIndex", {}) or {}
        self._alias: Dict[str, str] = {
            str(k).strip().lower(): str(v).strip()
            for k, v in raw_alias.items()
            if not str(k).startswith("$")
        }
        # Also register shortName/name/id itself as self-aliases so we
        # accept e.g. "GDPR", "gdpr" and "General Data Protection Regulation".
        for fw_id, fw in self._by_id.items():
            for candidate in (fw_id, fw.get("shortName"), fw.get("name")):
                if not candidate:
                    continue
                self._alias.setdefault(candidate.strip().lower(), fw_id)

    @property
    def derives_from(self) -> Dict[str, Dict[str, Any]]:
        raw = self._data.get("derivesFrom", {}) or {}
        return {k: v for k, v in raw.items() if not k.startswith("$")}

    def resolve_id(self, regulation: str) -> Optional[str]:
        if not isinstance(regulation, str):
            return None
        return self._alias.get(regulation.strip().lower())

    def framework(self, framework_id: str) -> Optional[Dict[str, Any]]:
        return self._by_id.get(framework_id)

    def short_name(self, framework_id: str) -> str:
        fw = self._by_id.get(framework_id)
        if not fw:
            return framework_id
        return fw.get("shortName") or fw.get("name") or framework_id

    def first_version(self, framework_id: str) -> Optional[str]:
        """Return the primary version string used for derived entries.

        Derivatives in the project (UK GDPR, CCPA, LGPD, APPI, nFADP)
        each declare exactly one version; we pick ``versions[0].version``
        deterministically.
        """
        fw = self._by_id.get(framework_id)
        if not fw:
            return None
        versions = fw.get("versions", []) or []
        if not versions:
            return None
        return versions[0].get("version")


# ---------------------------------------------------------------------------
# Propagation plan
# ---------------------------------------------------------------------------


class PropagationPlan:
    """Materialised view of the derivesFrom graph, keyed for fast lookup.

    Exposes a single method ``targets_for_parent_clause`` that returns,
    for a given (parent_id, parent_version, parent_clause), the list of
    (derivative_id, derivative_name, derivative_version, target_clause,
    inheritance_mode, divergence_note) tuples that should be propagated.
    """

    def __init__(self, index: FrameworkIndex) -> None:
        self.index = index
        # Map: (parent_id, parent_version) -> list of derivatives
        self._by_parent: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for deriv_id, spec in sorted(index.derives_from.items()):
            parent_id = spec.get("parent")
            parent_version = spec.get("parentVersion")
            if not parent_id or not parent_version:
                raise SystemExit(
                    f"regulations.json: derivesFrom[{deriv_id!r}] missing "
                    f"parent or parentVersion"
                )
            mode = spec.get("inheritanceMode")
            if mode not in ("identity", "mapped"):
                raise SystemExit(
                    f"regulations.json: derivesFrom[{deriv_id!r}] has "
                    f"invalid inheritanceMode={mode!r} "
                    f"(expected 'identity' or 'mapped')"
                )
            clause_mapping = {
                k: v
                for k, v in (spec.get("clauseMapping", {}) or {}).items()
                if not k.startswith("$")
            }
            if mode == "mapped" and not clause_mapping:
                raise SystemExit(
                    f"regulations.json: derivesFrom[{deriv_id!r}] "
                    f"inheritanceMode=mapped but clauseMapping is empty"
                )
            divergences = {
                d.get("clause"): d.get("note", "")
                for d in (spec.get("divergences", []) or [])
                if d.get("clause")
            }
            self._by_parent.setdefault(
                (parent_id, parent_version), []
            ).append(
                {
                    "derivative_id": deriv_id,
                    "mode": mode,
                    "clauseMapping": clause_mapping,
                    "divergences": divergences,
                }
            )

    def targets_for_parent_clause(
        self,
        parent_id: str,
        parent_version: str,
        parent_clause: str,
    ) -> List[Dict[str, Any]]:
        """Compute propagation targets for a single parent entry.

        Returns a list of dicts ready to feed into the inherited entry
        builder. Empty list when no derivative applies or when the clause
        does not map under a ``mapped`` inheritance mode.
        """
        out: List[Dict[str, Any]] = []
        for deriv in self._by_parent.get((parent_id, parent_version), []):
            mode = deriv["mode"]
            if mode == "identity":
                target_clause = parent_clause
            else:  # mapped
                target_clause = deriv["clauseMapping"].get(parent_clause)
                if target_clause is None:
                    continue
            deriv_id = deriv["derivative_id"]
            deriv_version = self.index.first_version(deriv_id)
            deriv_name = self.index.short_name(deriv_id)
            if not deriv_version:
                raise SystemExit(
                    f"regulations.json: derivative {deriv_id!r} has "
                    f"no version declared; cannot propagate"
                )
            divergence_note = deriv["divergences"].get(parent_clause)
            out.append(
                {
                    "derivative_id": deriv_id,
                    "derivative_name": deriv_name,
                    "derivative_version": deriv_version,
                    "target_clause": target_clause,
                    "inheritance_mode": mode,
                    "divergence_note": divergence_note,
                }
            )
        return out


# ---------------------------------------------------------------------------
# Sidecar mutation
# ---------------------------------------------------------------------------


def _is_derived(entry: Dict[str, Any]) -> bool:
    """True if an entry was mechanically derived by this generator."""
    if entry.get("provenance") == "derived-from-parent":
        return True
    # Defensive fallback: if a sidecar was hand-edited to include
    # derivationSource without the provenance tag, still treat it as
    # derived so the next regeneration tidies it up.
    return isinstance(entry.get("derivationSource"), dict)


def _entry_key(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    """Canonical uniqueness key for a compliance entry."""
    return (
        str(entry.get("regulation", "")).strip().lower(),
        str(entry.get("version", "")).strip(),
        str(entry.get("clause", "")).strip(),
    )


def _canonical_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in ENTRY_FIELD_ORDER:
        if key in entry:
            value = entry[key]
            if key == "derivationSource" and isinstance(value, dict):
                value = _canonical_derivation_source(value)
            ordered[key] = value
    # Preserve any unknown keys at the tail so information is never lost.
    for key, value in entry.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _canonical_derivation_source(ds: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in DERIVATION_SOURCE_FIELD_ORDER:
        if key in ds:
            ordered[key] = ds[key]
    for key, value in ds.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _canonical_sidecar(sidecar: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in SIDECAR_FIELD_ORDER:
        if key in sidecar:
            ordered[key] = sidecar[key]
    for key, value in sidecar.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _encode_sidecar(sidecar: Dict[str, Any]) -> str:
    return json.dumps(_canonical_sidecar(sidecar), indent=2, ensure_ascii=False) + "\n"


def _build_inherited_entry(
    parent_entry: Dict[str, Any],
    parent_id: str,
    parent_version: str,
    target: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Build an inherited compliance entry for one derivative target.

    Returns ``None`` when the parent assurance is ``contributing`` (which
    does not propagate further).
    """
    parent_assurance = parent_entry.get("assurance")
    inherited_assurance = ASSURANCE_DEGRADATION.get(parent_assurance)
    if not inherited_assurance:
        return None

    rationale = (
        f"Derived from {parent_id.upper()}@{parent_version} "
        f"{parent_entry.get('clause')} "
        f"(parent assurance={parent_assurance!r}). "
    )
    if target["inheritance_mode"] == "identity":
        rationale += (
            f"{target['derivative_name']} preserves parent clause numbering; "
            f"inherited assurance degraded one step."
        )
    else:
        rationale += (
            f"Clause mapped per data/regulations.json derivesFrom graph; "
            f"inherited assurance degraded one step."
        )
    divergence_note = target.get("divergence_note")
    if divergence_note:
        rationale += (
            " Divergence recorded — SME review should confirm scope fit."
        )

    derivation_source: Dict[str, Any] = {
        "parentRegulation": parent_id,
        "parentVersion": parent_version,
        "parentClause": str(parent_entry.get("clause")),
        "parentAssurance": parent_assurance,
        "inheritanceMode": target["inheritance_mode"],
    }
    if divergence_note:
        derivation_source["divergenceNote"] = divergence_note

    return {
        "regulation": target["derivative_name"],
        "version": target["derivative_version"],
        "clause": target["target_clause"],
        "mode": parent_entry.get("mode", "satisfies"),
        "assurance": inherited_assurance,
        "assurance_rationale": rationale,
        "provenance": "derived-from-parent",
        "derivationSource": derivation_source,
    }


def _rewrite_sidecar(
    sidecar: Dict[str, Any],
    plan: PropagationPlan,
    index: FrameworkIndex,
) -> Tuple[bool, int]:
    """Replace derived entries in ``sidecar`` with the propagation result.

    Returns (changed, derived_count).

    * ``changed``       -- True when the sidecar's compliance[] differs
                           byte-for-byte from what was present before.
    * ``derived_count`` -- Number of inherited entries the generator
                           produced for this sidecar (0 is valid).
    """
    original = list(sidecar.get("compliance", []))
    native: List[Dict[str, Any]] = []
    for entry in original:
        if not isinstance(entry, dict):
            # Defensive: schema forbids this but we do not want a malformed
            # entry to crash the generator — let the audit script surface it.
            native.append(entry)
            continue
        if _is_derived(entry):
            continue
        native.append(entry)

    native_keys = {
        _entry_key(e) for e in native if isinstance(e, dict)
    }

    derived: List[Dict[str, Any]] = []
    derived_keys: set = set()
    for entry in native:
        if not isinstance(entry, dict):
            continue
        reg_raw = entry.get("regulation")
        version = str(entry.get("version", "")).strip()
        clause = str(entry.get("clause", "")).strip()
        if not reg_raw or not version or not clause:
            continue
        parent_id = index.resolve_id(reg_raw)
        if not parent_id:
            continue
        for target in plan.targets_for_parent_clause(parent_id, version, clause):
            inherited = _build_inherited_entry(entry, parent_id, version, target)
            if inherited is None:
                continue
            key = _entry_key(inherited)
            if key in native_keys:
                # Hand-authored mapping exists — native wins.
                continue
            if key in derived_keys:
                # Two parents would produce the same derivative clause
                # (e.g. GDPR Art.33 AND Art.34 both map to LGPD Art.48).
                # Keep the first one; deterministic because native[] is
                # iterated in on-disk order and ``plan.targets_for_parent_clause``
                # returns derivatives sorted by id.
                continue
            derived.append(inherited)
            derived_keys.add(key)

    new_compliance: List[Dict[str, Any]] = []
    for entry in native:
        if isinstance(entry, dict):
            new_compliance.append(_canonical_entry(entry))
        else:
            new_compliance.append(entry)
    for entry in derived:
        new_compliance.append(_canonical_entry(entry))

    sidecar["compliance"] = new_compliance

    if original == new_compliance:
        return False, len(derived)
    return True, len(derived)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _uc_sort_key(path: Path) -> Tuple[int, int, int]:
    # Filenames look like uc-9.1.1.json -> extract (9,1,1).
    stem = path.stem
    if stem.startswith("uc-"):
        stem = stem[3:]
    parts = stem.split(".")
    try:
        return tuple(int(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        # Unparseable stems sort last; this never happens in the tree but
        # defensive coding keeps the generator from crashing on a future
        # hand-edit.
        return (10**9, 10**9, 10**9)


def _process(check_only: bool) -> int:
    data = _read_json(REGULATIONS_PATH)
    index = FrameworkIndex(data)
    plan = PropagationPlan(index)

    drift = False
    updated: List[Path] = []
    total_derived = 0
    sidecars_touched = 0

    sidecar_paths = sorted(USE_CASES_DIR.glob("cat-*/uc-*.json"), key=_uc_sort_key)

    for path in sidecar_paths:
        try:
            sidecar = _read_json(path)
        except Exception as exc:  # noqa: BLE001 -- surfaces malformed sidecars
            print(
                f"ERROR: {path.relative_to(REPO_ROOT)}: cannot parse JSON: {exc}",
                file=sys.stderr,
            )
            return 2
        if not isinstance(sidecar, dict):
            print(
                f"ERROR: {path.relative_to(REPO_ROOT)}: sidecar is not a JSON object",
                file=sys.stderr,
            )
            return 2
        changed, derived_count = _rewrite_sidecar(sidecar, plan, index)
        total_derived += derived_count
        if not changed:
            continue
        sidecars_touched += 1
        new_text = _encode_sidecar(sidecar)
        on_disk = path.read_text(encoding="utf-8")
        if new_text == on_disk:
            continue
        if check_only:
            drift = True
            updated.append(path)
        else:
            path.write_text(new_text, encoding="utf-8")
            updated.append(path)

    if check_only:
        if drift:
            print(
                "Phase 3.3 derivative-regulation drift detected. Run "
                "scripts/generate_phase3_3_derivatives.py and commit the "
                "result.",
                file=sys.stderr,
            )
            for path in updated:
                print(
                    f"  would-update: {path.relative_to(REPO_ROOT)}",
                    file=sys.stderr,
                )
            return 1
        print(
            f"Phase 3.3 derivatives: OK "
            f"(scanned {len(sidecar_paths)} sidecars, "
            f"{total_derived} inherited entries, no drift).",
        )
        return 0

    print(
        f"Phase 3.3 derivatives: wrote {sidecars_touched} sidecar(s) with "
        f"{total_derived} inherited entries across {len(sidecar_paths)} UCs.",
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.3 derivative-regulation propagation generator. Walks "
            "the derivesFrom graph in data/regulations.json and emits "
            "inherited compliance[] entries on every UC sidecar that "
            "already maps to a parent regulation. Idempotent, "
            "deterministic, and compatible with --check drift detection."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Drift-detection mode. Regenerates into memory and diffs "
            "against the committed tree. Exits non-zero on any drift. "
            "Used by .github/workflows/validate.yml."
        ),
    )
    args = parser.parse_args(argv)
    return _process(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
