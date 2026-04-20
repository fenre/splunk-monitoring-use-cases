"""URI scheme for MCP resources exposed by this server.

Four URI families are supported:

``uc://usecase/{uc_id}``
    Full UC detail — maps to ``api/v1/compliance/ucs/{uc_id}.json`` (for
    cat-22 UCs) or to the compact record in
    ``api/v1/recommender/uc-thin.json`` for non-compliance UCs.

``uc://category/{category_id}``
    Category JSON reference. The URI returns the catalogue metadata
    for the category (UC count, subcategories, etc.).

``reg://{regulation_id}`` or ``reg://{regulation_id}@{version}``
    Regulation detail — maps to
    ``api/v1/compliance/regulations/{regulation_id}.json``
    (or the version-specific variant when ``@version`` is provided).

``equipment://{equipment_id}``
    Per-equipment detail — maps to
    ``api/v1/equipment/{equipment_id}.json``.

``ledger://`` (exactly ``ledger://`` with nothing after the double slash)
    The signed provenance ledger (``data/provenance/mapping-ledger.json``).

Every identifier is validated against the schema regexes shipped in
``schemas/uc.schema.json`` and the regulations index. This prevents path
traversal, HTML injection, and surprise directory escapes when the MCP
server maps the URI to an on-disk JSON file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


UC_ID_REGEX = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
"""Three dotted zero-or-positive integers. Mirrors
``schemas/uc.schema.json#/properties/id``."""


CATEGORY_ID_REGEX = re.compile(r"^(0|[1-9][0-9]*)$")
"""Single non-negative integer, e.g. ``"22"`` for the compliance category."""


REGULATION_ID_REGEX = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
"""Kebab-case slug, 1+ chars. Mirrors the ``id`` field in every
``api/v1/compliance/regulations/*.json`` document."""


REGULATION_VERSION_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-\.]*$")
"""Regulation version suffix after ``@`` in URIs like
``reg://gdpr@2016-679``. Mirrors the on-disk filename convention for
``api/v1/compliance/regulations/{id}@{version}.json`` while rejecting
any character that could escape the endpoint path.

Note: display versions with slashes (e.g. ``2016/679``) must be
dash-escaped in URIs (``2016-679``). The tool layer in
``tools/regulation.py`` accepts slashes and converts them internally
via ``_version_to_filename``."""


EQUIPMENT_ID_REGEX = re.compile(r"^[a-z0-9][a-z0-9_]*$")
"""Mirrors ``schemas/uc.schema.json#/properties/equipment/items``."""


LEDGER_URI = "ledger://"
"""Single, canonical URI for the signed provenance ledger."""


ResourceKind = Literal[
    "use_case",
    "category",
    "regulation",
    "equipment",
    "ledger",
]


@dataclass(frozen=True, slots=True)
class ParsedResourceUri:
    """Structured form of a resource URI after validation."""

    kind: ResourceKind
    identifier: str
    """Primary identifier. For ``ledger://`` this is the empty string."""

    version: str | None = None
    """Only populated for ``reg://{id}@{version}``."""


class ResourceUriError(ValueError):
    """Raised when a resource URI fails validation."""


def parse_resource_uri(uri: str) -> ParsedResourceUri:
    """Parse and validate a resource URI.

    Raises :class:`ResourceUriError` on any malformed input. The returned
    object is safe to hand to the catalogue loader.

    Examples
    --------
    >>> parse_resource_uri("uc://usecase/22.1.1").kind
    'use_case'
    >>> parse_resource_uri("reg://gdpr@2016-679").version
    '2016-679'
    >>> parse_resource_uri("ledger://").kind
    'ledger'
    """

    if not isinstance(uri, str):
        raise ResourceUriError("URI must be a string")
    if len(uri) > 256:
        raise ResourceUriError("URI exceeds 256 chars")

    if uri == LEDGER_URI:
        return ParsedResourceUri(kind="ledger", identifier="")

    if uri.startswith("uc://"):
        return _parse_uc_uri(uri)

    if uri.startswith("reg://"):
        return _parse_regulation_uri(uri)

    if uri.startswith("equipment://"):
        return _parse_equipment_uri(uri)

    raise ResourceUriError(f"Unsupported URI scheme: {uri!r}")


def _parse_uc_uri(uri: str) -> ParsedResourceUri:
    rest = uri[len("uc://") :]
    # Expect exactly "usecase/<id>" or "category/<id>".
    parts = rest.split("/")
    if len(parts) != 2 or not parts[1]:
        raise ResourceUriError(
            f"Malformed uc:// URI (expected uc://usecase/<id> or uc://category/<id>): {uri!r}"
        )
    kind, identifier = parts
    if kind == "usecase":
        if not UC_ID_REGEX.fullmatch(identifier):
            raise ResourceUriError(
                f"uc://usecase/ identifier must match {UC_ID_REGEX.pattern}: {identifier!r}"
            )
        return ParsedResourceUri(kind="use_case", identifier=identifier)
    if kind == "category":
        if not CATEGORY_ID_REGEX.fullmatch(identifier):
            raise ResourceUriError(
                f"uc://category/ identifier must match {CATEGORY_ID_REGEX.pattern}: {identifier!r}"
            )
        return ParsedResourceUri(kind="category", identifier=identifier)
    raise ResourceUriError(f"Unsupported uc:// resource kind: {kind!r}")


def _parse_regulation_uri(uri: str) -> ParsedResourceUri:
    rest = uri[len("reg://") :]
    if not rest or "/" in rest:
        raise ResourceUriError(
            f"Malformed reg:// URI (expected reg://<id> or reg://<id>@<version>): {uri!r}"
        )
    version: str | None = None
    if "@" in rest:
        identifier, _, version = rest.partition("@")
        if not version:
            raise ResourceUriError(f"reg://<id>@ requires a version: {uri!r}")
        if not REGULATION_VERSION_REGEX.fullmatch(version):
            raise ResourceUriError(
                f"reg:// version must match {REGULATION_VERSION_REGEX.pattern}: {version!r}"
            )
    else:
        identifier = rest
    if not REGULATION_ID_REGEX.fullmatch(identifier):
        raise ResourceUriError(
            f"reg:// identifier must match {REGULATION_ID_REGEX.pattern}: {identifier!r}"
        )
    return ParsedResourceUri(
        kind="regulation",
        identifier=identifier,
        version=version,
    )


def _parse_equipment_uri(uri: str) -> ParsedResourceUri:
    rest = uri[len("equipment://") :]
    if not rest or "/" in rest:
        raise ResourceUriError(
            f"Malformed equipment:// URI (expected equipment://<slug>): {uri!r}"
        )
    if not EQUIPMENT_ID_REGEX.fullmatch(rest):
        raise ResourceUriError(
            f"equipment:// slug must match {EQUIPMENT_ID_REGEX.pattern}: {rest!r}"
        )
    return ParsedResourceUri(kind="equipment", identifier=rest)


def make_use_case_uri(uc_id: str) -> str:
    """Construct ``uc://usecase/{uc_id}`` with validation."""

    if not UC_ID_REGEX.fullmatch(uc_id):
        raise ResourceUriError(
            f"UC ID must match {UC_ID_REGEX.pattern}: {uc_id!r}"
        )
    return f"uc://usecase/{uc_id}"


def make_regulation_uri(regulation_id: str, version: str | None = None) -> str:
    """Construct ``reg://{id}`` or ``reg://{id}@{version}`` with validation."""

    if not REGULATION_ID_REGEX.fullmatch(regulation_id):
        raise ResourceUriError(
            f"regulation_id must match {REGULATION_ID_REGEX.pattern}: {regulation_id!r}"
        )
    if version is None:
        return f"reg://{regulation_id}"
    if not REGULATION_VERSION_REGEX.fullmatch(version):
        raise ResourceUriError(
            f"version must match {REGULATION_VERSION_REGEX.pattern}: {version!r}"
        )
    return f"reg://{regulation_id}@{version}"


def make_equipment_uri(equipment_id: str) -> str:
    """Construct ``equipment://{slug}`` with validation."""

    if not EQUIPMENT_ID_REGEX.fullmatch(equipment_id):
        raise ResourceUriError(
            f"equipment_id must match {EQUIPMENT_ID_REGEX.pattern}: {equipment_id!r}"
        )
    return f"equipment://{equipment_id}"


def make_ledger_uri() -> str:
    """Return the canonical ledger URI."""

    return LEDGER_URI
