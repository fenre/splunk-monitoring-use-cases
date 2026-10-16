"""Use-case fabric: canonical entities and the links between them.

Narrative fields on a use case are never rewritten here. Registries name
the entities, and the build resolves only facts the sidecar already states.
"""

from __future__ import annotations

PREDICATES: dict[str, tuple[str, str]] = {
    "uses": ("usecase", "sourcetype"),
    "producedBy": ("sourcetype", "addon"),
    "emittedBy": ("sourcetype", "vendorProduct"),
    "mapsTo": ("sourcetype", "cimDataset"),
    "requiresField": ("usecase", "cimField"),
    "partOf": ("cimField", "cimDataset"),
    "covers": ("usecase", "complianceControl"),
    "requires": ("usecase", "usecase"),
    "runsOn": ("usecase", "vendorProduct"),
    "servesOutcome": ("usecase", "businessOutcome"),
    "inArea": ("usecase", "businessArea"),
    "forPersona": ("usecase", "persona"),
    "inIndustry": ("usecase", "industry"),
}

ENTITY_TYPES = (
    "usecase",
    "sourcetype",
    "vendorProduct",
    "addon",
    "cimDataset",
    "cimField",
    "complianceControl",
    "industry",
    "businessOutcome",
    "businessArea",
    "persona",
)

PROVENANCE = ("authored", "inferred")
