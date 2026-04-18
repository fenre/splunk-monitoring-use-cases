"""Resource URI helpers for the MCP server."""

from __future__ import annotations

from splunk_uc_mcp.resources.uri_scheme import (
    EQUIPMENT_ID_REGEX,
    LEDGER_URI,
    REGULATION_ID_REGEX,
    RESOURCE_URI_DOCS,
    UC_ID_REGEX,
    ParsedResourceUri,
    make_equipment_uri,
    make_ledger_uri,
    make_regulation_uri,
    make_use_case_uri,
    parse_resource_uri,
)

__all__ = [
    "EQUIPMENT_ID_REGEX",
    "LEDGER_URI",
    "REGULATION_ID_REGEX",
    "RESOURCE_URI_DOCS",
    "UC_ID_REGEX",
    "ParsedResourceUri",
    "make_equipment_uri",
    "make_ledger_uri",
    "make_regulation_uri",
    "make_use_case_uri",
    "parse_resource_uri",
]
