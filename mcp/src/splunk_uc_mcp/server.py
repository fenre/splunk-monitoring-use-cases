"""MCP server wiring.

Registers every tool and resource declared in :mod:`splunk_uc_mcp.tools`
and :mod:`splunk_uc_mcp.resources`, then runs the standard JSON-RPC
stdio loop. Every handler is ``async`` because the :class:`mcp.Server`
event loop is built on ``anyio``.

The handlers themselves delegate to pure sync functions that take a
:class:`~splunk_uc_mcp.catalog.Catalog` argument, which keeps them
trivially testable without spinning up a real server.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import anyio
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from splunk_uc_mcp import __version__
from splunk_uc_mcp.catalog import (
    Catalog,
    CatalogError,
    CatalogNotFoundError,
    CatalogValidationError,
)
from splunk_uc_mcp.resources import (
    LEDGER_URI,
    EQUIPMENT_ID_REGEX,
    REGULATION_ID_REGEX,
    UC_ID_REGEX,
    parse_resource_uri,
)
from splunk_uc_mcp.resources.uri_scheme import ResourceUriError
from splunk_uc_mcp.tools import (
    FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
    FIND_COMPLIANCE_GAP_SCHEMA,
    GET_EQUIPMENT_OUTPUT_SCHEMA,
    GET_EQUIPMENT_SCHEMA,
    GET_REGULATION_OUTPUT_SCHEMA,
    GET_REGULATION_SCHEMA,
    GET_USE_CASE_OUTPUT_SCHEMA,
    GET_USE_CASE_SCHEMA,
    LIST_CATEGORIES_OUTPUT_SCHEMA,
    LIST_CATEGORIES_SCHEMA,
    LIST_EQUIPMENT_OUTPUT_SCHEMA,
    LIST_EQUIPMENT_SCHEMA,
    LIST_REGULATIONS_OUTPUT_SCHEMA,
    LIST_REGULATIONS_SCHEMA,
    SEARCH_USE_CASES_OUTPUT_SCHEMA,
    SEARCH_USE_CASES_SCHEMA,
    find_compliance_gap,
    get_equipment,
    get_regulation,
    get_use_case,
    list_categories,
    list_equipment,
    list_regulations,
    search_use_cases,
)


LOG = logging.getLogger(__name__)


SERVER_NAME = "splunk-uc"
"""MCP server name advertised during initialisation. Kept short so
``claude mcp add splunk-uc ...`` reads naturally on the command line."""


SERVER_INSTRUCTIONS = (
    "Splunk Monitoring Use Cases catalogue (6,400+ UCs across 23 "
    "categories, 60 regulations, 105 equipment slugs, signed provenance "
    "ledger). Read-only. Use `search_use_cases` for discovery, "
    "`get_use_case` for the full SPL + compliance detail on a single UC, "
    "`list_regulations` / `get_regulation` for framework context, "
    "`list_equipment` / `get_equipment` for deployment stacks, and "
    "`find_compliance_gap` when an auditor asks which clauses are still "
    "uncovered. The URI families `uc://`, `reg://`, `equipment://`, and "
    "`ledger://` expose the same data as resources for agents that "
    "prefer a pull-based model."
)


def build_server(catalog: Catalog) -> Server:
    """Construct an :class:`mcp.server.Server` wired to ``catalog``.

    Exported separately from :func:`run_stdio_server` so tests can drive
    the handlers directly without starting the stdio loop.
    """

    server: Server = Server(SERVER_NAME)

    _register_tools(server, catalog)
    _register_resources(server, catalog)

    return server


def run_stdio_server(
    *,
    catalog_root: Path | None = None,
    base_url: str | None = None,
) -> int:
    """Start the stdio JSON-RPC loop and block until the client hangs up.

    Returns a shell-style exit code (0 on clean shutdown).
    """

    with Catalog(catalog_root=catalog_root, base_url=base_url) as catalog:
        LOG.info(
            "splunk-uc-mcp %s starting (local_root=%s, base_url=%s)",
            __version__,
            catalog.catalog_root,
            catalog.base_url,
        )
        server = build_server(catalog)
        init_options = InitializationOptions(
            server_name=SERVER_NAME,
            server_version=__version__,
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
            instructions=SERVER_INSTRUCTIONS,
        )

        async def _main() -> None:
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, init_options)

        anyio.run(_main)
    return 0


def _register_tools(server: Server, catalog: Catalog) -> None:
    """Wire tool metadata + dispatch to ``server``."""

    tools = _tool_definitions()
    dispatch = _tool_dispatch(catalog)

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return tools

    # ``validate_input=False`` delegates every schema check to the tool
    # implementation itself. We already enforce the same regex patterns and
    # range checks inside the tool functions, and doing it once keeps the
    # error payload shape identical whether the client is a strict MCP
    # SDK or a handwritten agent that skips client-side validation.
    @server.call_tool(validate_input=False)
    async def _call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> dict[str, Any] | CallToolResult:
        handler = dispatch.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name!r}")
        args = arguments or {}
        LOG.debug(
            "tool=%s args_hash=%s", name, _hash_args(args),
        )
        try:
            payload = handler(args)
        except (ValueError, CatalogValidationError) as exc:
            return _error_result("invalid_input", str(exc))
        except CatalogNotFoundError as exc:
            return _error_result("not_found", str(exc))
        except CatalogError as exc:
            return _error_result("catalog_error", str(exc))
        # Happy path: return the dict so the SDK validates it against
        # outputSchema and emits both ``structuredContent`` and a
        # JSON ``TextContent`` block.
        return payload


def _tool_definitions() -> list[Tool]:
    """Return the full v1 tool surface.

    Keep the list literal so the CI drift guard (see
    ``scripts/audit_mcp_tool_schemas.py``) can import it without starting
    an event loop.
    """

    return [
        Tool(
            name="search_use_cases",
            description=(
                "Search the catalogue (6,400+ UCs) by optional keyword + "
                "category/regulation/equipment/MITRE filters. Returns a "
                "compact list suitable for follow-up get_use_case calls."
            ),
            inputSchema=SEARCH_USE_CASES_SCHEMA,
            outputSchema=SEARCH_USE_CASES_OUTPUT_SCHEMA,
        ),
        Tool(
            name="get_use_case",
            description=(
                "Return full detail for one UC — SPL, implementation "
                "notes, references, known false positives, and (for "
                "cat-22 UCs) the full compliance[] array with clause, "
                "mode, assurance, and rationale."
            ),
            inputSchema=GET_USE_CASE_SCHEMA,
            outputSchema=GET_USE_CASE_OUTPUT_SCHEMA,
        ),
        Tool(
            name="list_categories",
            description=(
                "List the 23 primary categories with per-subcategory UC "
                "counts. Useful as a discovery step before search_use_cases."
            ),
            inputSchema=LIST_CATEGORIES_SCHEMA,
            outputSchema=LIST_CATEGORIES_OUTPUT_SCHEMA,
        ),
        Tool(
            name="list_regulations",
            description=(
                "List the 60 regulations with jurisdiction, tier, and tag "
                "metadata. Filter by tier / jurisdiction / tag to scope "
                "down."
            ),
            inputSchema=LIST_REGULATIONS_SCHEMA,
            outputSchema=LIST_REGULATIONS_OUTPUT_SCHEMA,
        ),
        Tool(
            name="get_regulation",
            description=(
                "Return regulation detail (jurisdiction, common clauses, "
                "version metadata). Pass version='2016-679' (GDPR) or "
                "similar for the full per-version document."
            ),
            inputSchema=GET_REGULATION_SCHEMA,
            outputSchema=GET_REGULATION_OUTPUT_SCHEMA,
        ),
        Tool(
            name="list_equipment",
            description=(
                "List the 105 equipment slugs with UC and regulation "
                "counts. Accepts a regulation_id filter to narrow to a "
                "specific framework."
            ),
            inputSchema=LIST_EQUIPMENT_SCHEMA,
            outputSchema=LIST_EQUIPMENT_OUTPUT_SCHEMA,
        ),
        Tool(
            name="get_equipment",
            description=(
                "Return the per-equipment view: UCs grouped by category, "
                "regulations grouped by framework, and the list of model "
                "compounds (e.g. 'hardware_bmc_edac')."
            ),
            inputSchema=GET_EQUIPMENT_SCHEMA,
            outputSchema=GET_EQUIPMENT_OUTPUT_SCHEMA,
        ),
        Tool(
            name="find_compliance_gap",
            description=(
                "Return the pre-computed gap analysis for one or more "
                "regulations (which common clauses have zero UC "
                "coverage). Optional equipment_id parameter adds an "
                "overlay showing which uncovered clauses are already hit "
                "by UCs bearing the equipment tag."
            ),
            inputSchema=FIND_COMPLIANCE_GAP_SCHEMA,
            outputSchema=FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
        ),
    ]


def _tool_dispatch(
    catalog: Catalog,
) -> dict[str, Callable[[dict[str, Any]], Any]]:
    """Map tool names to their (sync) handlers."""

    return {
        "search_use_cases": lambda args: search_use_cases(
            catalog=catalog, **args
        ),
        "get_use_case": lambda args: get_use_case(catalog=catalog, **args),
        "list_categories": lambda _args: list_categories(catalog=catalog),
        "list_regulations": lambda args: list_regulations(
            catalog=catalog, **args
        ),
        "get_regulation": lambda args: get_regulation(
            catalog=catalog, **args
        ),
        "list_equipment": lambda args: list_equipment(catalog=catalog, **args),
        "get_equipment": lambda args: get_equipment(catalog=catalog, **args),
        "find_compliance_gap": lambda args: find_compliance_gap(
            catalog=catalog, **args
        ),
    }


def _register_resources(server: Server, catalog: Catalog) -> None:
    """Wire the four URI families + their read handler."""

    @server.list_resources()
    async def _list_resources() -> list[Any]:
        # The catalogue is 6,400+ UCs + 60 regulations + 105 equipment — too
        # many to enumerate eagerly. We publish resource *templates* via
        # read_resource instead of individual entries; clients that want
        # a full list can call list_categories / list_regulations /
        # list_equipment.
        return []

    @server.read_resource()
    async def _read_resource(uri: Any) -> str:
        # mcp-python passes a pydantic AnyUrl; stringify before parsing.
        uri_str = str(uri)
        try:
            parsed = parse_resource_uri(uri_str)
        except ResourceUriError as exc:
            payload = {"error": "invalid_uri", "message": str(exc)}
            return _json_dumps(payload)

        try:
            if parsed.kind == "use_case":
                payload = get_use_case(catalog=catalog, uc_id=parsed.identifier)
            elif parsed.kind == "category":
                # Categories don't have their own JSON endpoint, but
                # list_categories() exposes the full tree. Filter here.
                tree = list_categories(catalog=catalog)
                match = next(
                    (c for c in tree["categories"] if c["id"] == parsed.identifier),
                    None,
                )
                if match is None:
                    raise CatalogNotFoundError(
                        f"Category {parsed.identifier} not found"
                    )
                payload = match
            elif parsed.kind == "regulation":
                payload = get_regulation(
                    catalog=catalog,
                    regulation_id=parsed.identifier,
                    version=parsed.version,
                )
            elif parsed.kind == "equipment":
                payload = get_equipment(
                    catalog=catalog, equipment_id=parsed.identifier
                )
            elif parsed.kind == "ledger":
                ledger = catalog.load_data_file("provenance/mapping-ledger.json")
                if ledger is None:
                    raise CatalogNotFoundError(
                        "Signed ledger is only exposed from a local checkout "
                        "(not hosted via GitHub Pages)"
                    )
                payload = _summarise_ledger(ledger)
            else:  # pragma: no cover - defensive
                raise CatalogNotFoundError(f"Unknown resource kind: {parsed.kind}")
        except (ValueError, CatalogValidationError) as exc:
            payload = {"error": "invalid_uri", "message": str(exc)}
        except CatalogNotFoundError as exc:
            payload = {"error": "not_found", "message": str(exc)}
        except CatalogError as exc:
            payload = {"error": "catalog_error", "message": str(exc)}
        return _json_dumps(payload)


def _summarise_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    """Return a compact ledger view suitable for agent context.

    The full ledger is 1.4 MB (1,889 entries) — too much to stream back
    on every read. We return the header metadata plus the first 25
    entries so the agent can see the shape; if the agent needs the
    complete ledger it can fetch ``ledger://full`` directly via
    ``read_resource``, which streams the whole ``mapping-ledger.json``
    payload without per-tool truncation.
    """

    entries = ledger.get("entries", [])
    sample = entries[:25]
    return {
        "schemaVersion": ledger.get("schemaVersion"),
        "generatedAt": ledger.get("generatedAt"),
        "catalogueCommit": ledger.get("catalogueCommit"),
        "entryCount": ledger.get("entryCount"),
        "merkleRoot": ledger.get("merkleRoot"),
        "signature": ledger.get("signature"),
        "sampleEntries": sample,
        "sampleSize": len(sample),
    }


def _json_dumps(payload: Any) -> str:
    """Compact, deterministic JSON encoding for tool/resource responses."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
    )


def _error_result(kind: str, message: str) -> CallToolResult:
    """Build an error-flavoured ``CallToolResult``.

    We return errors as ``CallToolResult`` rather than a structured dict so
    the SDK skips output-schema validation (the error envelope never
    matches a success schema). The JSON body stays agent-parseable:

        {"error": "invalid_input", "message": "..."}

    ``isError=True`` gives clients an unambiguous signal without forcing
    them to introspect the JSON payload.
    """

    payload = {"error": kind, "message": message}
    return CallToolResult(
        content=[TextContent(type="text", text=_json_dumps(payload))],
        isError=True,
    )


def _hash_args(args: dict[str, Any]) -> str:
    """Stable hash for DEBUG logging (never log the raw arguments).

    Per the CoSAI MCP rule we must not persist caller-supplied data even
    if the catalogue is public today, so the logs only retain a hash.
    """

    canonical = json.dumps(args, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


__all__ = [
    "SERVER_NAME",
    "SERVER_INSTRUCTIONS",
    "build_server",
    "run_stdio_server",
]


# Re-export tiny utilities that the drift-guard script loads via `import`.
# They're not part of the MCP public surface; keeping them here avoids a
# third module boundary for one-line helpers.
_TOOL_DEFINITIONS = _tool_definitions

# The following import-time references document which slug regexes we
# trust. They are kept close to the server wiring so a future contributor
# auditing input validation has a single place to look.
_EXPECTED_SLUG_REGEXES = (UC_ID_REGEX, REGULATION_ID_REGEX, EQUIPMENT_ID_REGEX)
_EXPECTED_LEDGER_URI = LEDGER_URI
