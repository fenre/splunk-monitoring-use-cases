"""Canonical UC sidecar field order and serialisation helpers.

A single source of truth for the order in which keys appear on disk in
a ``content/cat-NN-<slug>/UC-X.Y.Z.json`` sidecar. Every generator that
rewrites a sidecar (``equipment_tags``, ``grandma_explanations``,
``phase3_1_backfill``, ``phase3_2_cross_cutting``,
``phase3_3_derivatives``) must converge on the same order so the
cascade-regen ``--check`` gate is byte-identical across the chain. The
``lift-validate`` verb consumes this module too so a freshly-lifted
sidecar is already in canonical form and does not provoke a follow-up
reorder commit from the generator chain.

The constant mirrors the order used by the four generators that share
the longest published version of the tuple (``equipment_tags``,
``phase3_2_cross_cutting``, ``phase3_3_derivatives``,
``grandma_explanations``). The historical outlier in
``phase3_1_backfill`` (no ``industry`` field) is a latent bug tracked
separately; this module deliberately follows the majority position.

The module is intentionally tiny and stdlib-only so importers from
both the generator chain and the lift loop can depend on it without
risking a circular import.
"""

from __future__ import annotations

from typing import Any

#: Canonical UC sidecar field order. Mirrors the on-disk convention
#: used by every generator that rewrites sidecars in v8+. When a new
#: property is added to ``schemas/uc.schema.json``, append it here at
#: the same position so byte-level diffs stay legible across the
#: generator chain and the lift loop.
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


def canonical_sidecar(sidecar: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict with keys in :data:`SIDECAR_FIELD_ORDER` order.

    Keys absent from the input are skipped. Unknown keys (anything not
    in ``SIDECAR_FIELD_ORDER`` — should be impossible given the schema's
    ``additionalProperties: false`` but lift-surface fields such as
    ``detailedImplementation`` legitimately appear on individual UCs)
    are appended at the end in their original insertion order so no
    information is ever dropped.

    Args:
        sidecar: The parsed UC sidecar dict.

    Returns:
        A new dict with the same key-value pairs in canonical order.
    """
    ordered: dict[str, Any] = {}
    for key in SIDECAR_FIELD_ORDER:
        if key in sidecar:
            ordered[key] = sidecar[key]
    for key, value in sidecar.items():
        if key not in ordered:
            ordered[key] = value
    return ordered
