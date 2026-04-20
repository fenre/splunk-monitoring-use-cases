"""Regulation-centric tools: ``list_regulations`` + ``get_regulation``.

Both read the materialised regulation JSON under
``api/v1/compliance/regulations/`` — no assumptions about the cat-22
markdown structure leak into the tool output.
"""

from __future__ import annotations

import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError


REGULATION_ID_PATTERN = r"^[a-z0-9][a-z0-9\-]*$"


LIST_REGULATIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "tier": {
            "type": "integer",
            "description": (
                "Filter by regulatory tier. Tier 1 = core global baselines "
                "(GDPR, NIST 800-53, PCI DSS, ISO 27001, HIPAA, …); tier 2 "
                "= jurisdictional/industry add-ons."
            ),
            "minimum": 1,
            "maximum": 3,
        },
        "jurisdiction": {
            "type": "string",
            "description": (
                "ISO-ish jurisdiction code used by the catalogue (e.g. "
                "'EU', 'US', 'UK', 'JP'). Case-insensitive exact match."
            ),
            "maxLength": 16,
        },
        "tag": {
            "type": "string",
            "description": (
                "Filter by tag (e.g. 'privacy', 'financial', 'energy', "
                "'ics')."
            ),
            "maxLength": 48,
        },
    },
    "additionalProperties": False,
}


LIST_REGULATIONS_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["count", "regulations"],
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "regulations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "shortName": {"type": "string"},
                    "tier": {"type": "integer"},
                    "jurisdiction": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "versions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "endpoint": {"type": "string"},
                },
            },
        },
    },
}


GET_REGULATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["regulation_id"],
    "properties": {
        "regulation_id": {
            "type": "string",
            "description": "Kebab-case slug (e.g. 'gdpr', 'pci-dss').",
            "pattern": REGULATION_ID_PATTERN,
        },
        "version": {
            "type": "string",
            "description": (
                "Optional version suffix (e.g. '2016-679' for GDPR, "
                "'Rev.5 Baselines' for FedRAMP). When omitted, returns "
                "the base (version-less) regulation document and a list "
                "of available versioned endpoints."
            ),
            "maxLength": 64,
        },
    },
    "additionalProperties": False,
}


GET_REGULATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "name"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "shortName": {"type": "string"},
        "tier": {"type": "integer"},
        "jurisdiction": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "version": {"type": ["object", "string"]},
        "availableVersions": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Only populated when the caller asked for the base "
                "(version-less) document. Each entry is usable as the "
                "'version' argument on a follow-up call."
            ),
        },
    },
}


_REGULATION_ID_REGEX = re.compile(REGULATION_ID_PATTERN)
# Display versions carry slashes (e.g. "2016/679" for GDPR) and periods
# (e.g. "v5.9.4" for CJIS). We accept both; `_version_to_filename` below
# converts them to dashes before the string reaches the filesystem, so
# path traversal is not a concern.
_REGULATION_VERSION_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-\. /]*$")


_JURISDICTION_MAX_LEN = 16
_TAG_MAX_LEN = 48


def list_regulations(
    *,
    catalog: Catalog,
    tier: int | None = None,
    jurisdiction: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """Return the 60-regulation framework index with optional filters."""

    if tier is not None:
        if not isinstance(tier, int) or isinstance(tier, bool):
            raise ValueError(f"tier must be an integer (got {type(tier).__name__})")
        if tier < 1 or tier > 3:
            raise ValueError(f"tier must be in [1, 3] (got {tier})")
    if jurisdiction is not None:
        if not isinstance(jurisdiction, str):
            raise ValueError(
                f"jurisdiction must be a string (got {type(jurisdiction).__name__})"
            )
        if len(jurisdiction) > _JURISDICTION_MAX_LEN:
            raise ValueError(
                f"jurisdiction must be <= {_JURISDICTION_MAX_LEN} chars "
                f"(got {len(jurisdiction)})"
            )
    if tag is not None:
        if not isinstance(tag, str):
            raise ValueError(f"tag must be a string (got {type(tag).__name__})")
        if len(tag) > _TAG_MAX_LEN:
            raise ValueError(
                f"tag must be <= {_TAG_MAX_LEN} chars (got {len(tag)})"
            )

    index = catalog.load_json("compliance", "regulations", "index.json")
    frameworks: list[dict[str, Any]] = index.get("frameworks", [])

    jur_lower = jurisdiction.lower() if jurisdiction else None

    out: list[dict[str, Any]] = []
    for fw in frameworks:
        if tier is not None and fw.get("tier") != tier:
            continue
        if jur_lower is not None:
            fw_juris = [j.lower() for j in (fw.get("jurisdiction") or [])]
            if jur_lower not in fw_juris:
                continue
        if tag is not None and tag not in (fw.get("tags") or []):
            continue
        out.append(fw)

    return {"count": len(out), "regulations": out}


def get_regulation(
    *,
    catalog: Catalog,
    regulation_id: str,
    version: str | None = None,
) -> dict[str, Any]:
    """Return regulation detail for ``regulation_id``.

    When ``version`` is provided we load the versioned JSON directly. The
    catalogue's filename convention transforms slashes and spaces in the
    display version to dashes, so we do the same.

    Raises :class:`ValueError` on malformed input and
    :class:`~splunk_uc_mcp.catalog.CatalogNotFoundError` when no JSON
    document matches.
    """

    if not _REGULATION_ID_REGEX.fullmatch(regulation_id):
        raise ValueError(
            f"regulation_id must match {REGULATION_ID_PATTERN}: {regulation_id!r}"
        )
    if version is not None and not _REGULATION_VERSION_REGEX.fullmatch(version):
        raise ValueError(
            f"version must match {_REGULATION_VERSION_REGEX.pattern}: {version!r}"
        )

    if version is None:
        base = catalog.load_json(
            "compliance", "regulations", f"{regulation_id}.json"
        )
        base = _strip_meta(base)
        base["availableVersions"] = _available_versions(catalog, regulation_id)
        return base

    filename = f"{regulation_id}@{_version_to_filename(version)}.json"
    try:
        return _strip_meta(
            catalog.load_json("compliance", "regulations", filename)
        )
    except CatalogNotFoundError:
        versions = _available_versions(catalog, regulation_id)
        raise CatalogNotFoundError(
            f"Regulation {regulation_id} has no version {version!r} "
            f"(available: {', '.join(versions) or 'none'})"
        ) from None


def _available_versions(catalog: Catalog, regulation_id: str) -> list[str]:
    index = catalog.load_json("compliance", "regulations", "index.json")
    for fw in index.get("frameworks", []):
        if fw.get("id") == regulation_id:
            return list(fw.get("versions") or [])
    return []


def _version_to_filename(version: str) -> str:
    """Mirror the catalogue's filename slugging: spaces and slashes → ``-``."""

    return version.replace("/", "-").replace(" ", "-")


def _strip_meta(doc: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in doc.items() if not k.startswith("$") and k not in ("apiVersion", "generatedAt", "_meta")}
