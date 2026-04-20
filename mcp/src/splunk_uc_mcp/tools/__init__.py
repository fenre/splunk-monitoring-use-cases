"""MCP tool implementations.

Each module exports one pure function per tool. All functions take a
:class:`~splunk_uc_mcp.catalog.Catalog` argument so tests can inject a
fixture catalogue; :mod:`splunk_uc_mcp.server` passes an explicit
``Catalog`` instance at startup.

Every tool is *read-only*: it inspects pre-built ``api/v1/*.json``
endpoints and returns a plain dict/list suitable for JSON serialisation.
No tool executes shell commands, opens sockets beyond the HTTPS fallback,
or mutates any file.
"""

from __future__ import annotations

from splunk_uc_mcp.tools.compliance import (
    FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
    FIND_COMPLIANCE_GAP_SCHEMA,
    find_compliance_gap,
)
from splunk_uc_mcp.tools.equipment import (
    GET_EQUIPMENT_OUTPUT_SCHEMA,
    GET_EQUIPMENT_SCHEMA,
    LIST_EQUIPMENT_OUTPUT_SCHEMA,
    LIST_EQUIPMENT_SCHEMA,
    get_equipment,
    list_equipment,
)
from splunk_uc_mcp.tools.regulation import (
    GET_REGULATION_OUTPUT_SCHEMA,
    GET_REGULATION_SCHEMA,
    LIST_REGULATIONS_OUTPUT_SCHEMA,
    LIST_REGULATIONS_SCHEMA,
    get_regulation,
    list_regulations,
)
from splunk_uc_mcp.tools.search import (
    SEARCH_USE_CASES_OUTPUT_SCHEMA,
    SEARCH_USE_CASES_SCHEMA,
    search_use_cases,
)
from splunk_uc_mcp.tools.use_case import (
    GET_USE_CASE_OUTPUT_SCHEMA,
    GET_USE_CASE_SCHEMA,
    LIST_CATEGORIES_OUTPUT_SCHEMA,
    LIST_CATEGORIES_SCHEMA,
    get_use_case,
    list_categories,
)

__all__ = [
    "FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA",
    "FIND_COMPLIANCE_GAP_SCHEMA",
    "GET_EQUIPMENT_OUTPUT_SCHEMA",
    "GET_EQUIPMENT_SCHEMA",
    "GET_REGULATION_OUTPUT_SCHEMA",
    "GET_REGULATION_SCHEMA",
    "GET_USE_CASE_OUTPUT_SCHEMA",
    "GET_USE_CASE_SCHEMA",
    "LIST_CATEGORIES_OUTPUT_SCHEMA",
    "LIST_CATEGORIES_SCHEMA",
    "LIST_EQUIPMENT_OUTPUT_SCHEMA",
    "LIST_EQUIPMENT_SCHEMA",
    "LIST_REGULATIONS_OUTPUT_SCHEMA",
    "LIST_REGULATIONS_SCHEMA",
    "SEARCH_USE_CASES_OUTPUT_SCHEMA",
    "SEARCH_USE_CASES_SCHEMA",
    "find_compliance_gap",
    "get_equipment",
    "get_regulation",
    "get_use_case",
    "list_categories",
    "list_equipment",
    "list_regulations",
    "search_use_cases",
]
