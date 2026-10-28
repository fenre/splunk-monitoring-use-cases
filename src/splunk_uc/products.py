"""Splunk product registry accessor (ADR-0017).

Every consumer that needs to know how a use case is implemented — which
fields it must carry, which audits and exports apply, which fields form its
identity fingerprint — asks this module. The facts live in
``data/splunk-products.json``; no consumer branches on a product id.

Functions accept either a canonical sidecar dict (``products`` /
``productArtifacts``) or a legacy short-key catalogue dict (``prd`` / ``pra``).
A use case without ``products`` is implemented in the registry's
``defaultProduct``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "splunk-products.json"

_PRODUCTS_KEYS = ("products", "prd")
_ARTIFACTS_KEYS = ("productArtifacts", "pra")


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    registry: dict[str, Any] = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return registry


@lru_cache(maxsize=1)
def _rows() -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in load_registry()["products"]}


def default_product_id() -> str:
    return str(load_registry()["defaultProduct"])


def product_ids() -> list[str]:
    return [row["id"] for row in load_registry()["products"]]


def all_products() -> list[dict[str, Any]]:
    return list(load_registry()["products"])


def product(product_id: str) -> dict[str, Any]:
    """Registry row for ``product_id``; raises ``KeyError`` when unknown."""
    return _rows()[product_id]


def display_name(product_id: str) -> str:
    """Short product name for badges; the id itself when unregistered."""
    row = _rows().get(product_id)
    if row is None:
        return product_id
    return str(row.get("shortName") or row["name"])


def _first_present(uc: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in uc:
            return uc[key]
    return None


def declared_products(uc: Mapping[str, Any]) -> list[str] | None:
    """The ``products`` list exactly as authored, or ``None`` when omitted."""
    raw = _first_present(uc, _PRODUCTS_KEYS)
    if not isinstance(raw, list):
        return None
    ids = [str(p).strip() for p in raw if isinstance(p, str) and p.strip()]
    return ids or None


def products_of(uc: Mapping[str, Any]) -> list[str]:
    """Products the use case is implemented in, primary first."""
    return declared_products(uc) or [default_product_id()]


def primary_product_id(uc: Mapping[str, Any]) -> str:
    return products_of(uc)[0]


def is_default(uc: Mapping[str, Any]) -> bool:
    return products_of(uc) == [default_product_id()]


def non_default_products(uc: Mapping[str, Any]) -> list[str] | None:
    """``products`` for emission, or ``None`` when it is the default."""
    return None if is_default(uc) else products_of(uc)


def artifacts_of(uc: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = _first_present(uc, _ARTIFACTS_KEYS)
    if not isinstance(raw, list):
        return []
    return [a for a in raw if isinstance(a, dict)]


def _known_rows(uc: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = _rows()
    return [rows[p] for p in products_of(uc) if p in rows]


def _primary_row(uc: Mapping[str, Any]) -> dict[str, Any]:
    rows = _rows()
    return rows.get(primary_product_id(uc)) or rows[default_product_id()]


def requires(uc: Mapping[str, Any]) -> list[str]:
    """Fields the primary product makes mandatory for this use case."""
    return list(_primary_row(uc)["requires"])


def applies(uc: Mapping[str, Any], audit: str) -> bool:
    """Whether audit family ``audit`` applies to any product the UC lists."""
    return any(audit in row["audits"] for row in _known_rows(uc))


def exports(uc: Mapping[str, Any], kind: str) -> bool:
    """Whether export ``kind`` (``savedSearches`` / ``dashboards``) applies."""
    return any(bool(row["exports"].get(kind)) for row in _known_rows(uc))


def fingerprint_fields(uc: Mapping[str, Any]) -> list[str]:
    """Fields hashed with ``title`` into the identity fingerprint."""
    return list(_primary_row(uc)["fingerprintFields"])


def implement_section(uc: Mapping[str, Any]) -> str:
    """Gold-tier heading for the step that builds the detection."""
    return str(_primary_row(uc)["qualityProfile"]["implementSection"])


def all_implement_sections() -> list[str]:
    return [row["qualityProfile"]["implementSection"] for row in load_registry()["products"]]


def validate(uc: Mapping[str, Any]) -> list[str]:
    """Registry-level problems with a UC's ``products`` / ``productArtifacts``."""
    issues: list[str] = []
    rows = _rows()
    declared = declared_products(uc) or []
    for pid in declared:
        if pid not in rows:
            issues.append(f"unknown product {pid!r} (not in data/splunk-products.json)")
    if len(set(declared)) != len(declared):
        issues.append("products lists a product more than once")
    listed = set(products_of(uc))
    for idx, artifact in enumerate(artifacts_of(uc)):
        artifact_pid = artifact.get("product")
        if artifact_pid not in listed:
            issues.append(f"productArtifacts[{idx}].product {artifact_pid!r} is not listed in products")
            continue
        row = rows.get(artifact_pid)
        if row is not None and artifact.get("type") not in row["artifactTypes"]:
            issues.append(
                f"productArtifacts[{idx}].type {artifact.get('type')!r} is not an artifact type "
                f"of {artifact_pid} (expected one of {row['artifactTypes']})"
            )
    return issues
