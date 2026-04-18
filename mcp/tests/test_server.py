"""Tests for ``splunk_uc_mcp.server``.

Exercises the full MCP protocol handshake over in-memory streams so we
confirm the server advertises the right tools, accepts tool calls with
valid arguments, and refuses resource reads with bogus URIs.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.server import InitializationOptions, NotificationOptions

from splunk_uc_mcp import __version__
from splunk_uc_mcp.catalog import Catalog
from splunk_uc_mcp.server import (
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    _EXPECTED_SLUG_REGEXES,
    _TOOL_DEFINITIONS,
    build_server,
)


EXPECTED_TOOLS = {
    "search_use_cases",
    "get_use_case",
    "list_categories",
    "list_regulations",
    "get_regulation",
    "list_equipment",
    "get_equipment",
    "find_compliance_gap",
}


class TestToolDefinitions:
    def test_exposes_all_expected_tools(self) -> None:
        names = {t.name for t in _TOOL_DEFINITIONS()}
        assert names == EXPECTED_TOOLS

    def test_every_tool_has_input_and_output_schema(self) -> None:
        for tool in _TOOL_DEFINITIONS():
            assert tool.inputSchema is not None, f"{tool.name} missing inputSchema"
            assert (
                tool.outputSchema is not None
            ), f"{tool.name} missing outputSchema"
            # Descriptions must be human-readable sentences, not empty.
            assert tool.description and len(tool.description) >= 20

    def test_slug_regexes_are_frozen(self) -> None:
        # The drift guard (scripts/audit_mcp_tool_schemas.py) also asserts
        # this list end-to-end against the runtime tool surface; the local
        # length check here just stops a future contributor from silently
        # removing a regex without bumping the audit script in lock-step.
        assert len(_EXPECTED_SLUG_REGEXES) == 3


class _InMemoryStreams:
    """Pair of in-memory streams wired to the MCP server task group."""

    def __init__(self) -> None:
        self.client_to_server_tx, self.client_to_server_rx = (
            anyio.create_memory_object_stream(10)
        )
        self.server_to_client_tx, self.server_to_client_rx = (
            anyio.create_memory_object_stream(10)
        )


async def _drive_server(
    catalog: Catalog,
    body: "callable[[ClientSession], AsyncIterator[None]]",
) -> None:
    """Start the server on in-memory streams and run ``body`` against a client."""

    server = build_server(catalog)
    streams = _InMemoryStreams()
    init_options = InitializationOptions(
        server_name=SERVER_NAME,
        server_version=__version__,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
        instructions=SERVER_INSTRUCTIONS,
    )

    async with anyio.create_task_group() as tg:

        async def _run_server() -> None:
            try:
                await server.run(
                    streams.client_to_server_rx,
                    streams.server_to_client_tx,
                    init_options,
                )
            except Exception:  # pragma: no cover - surfaced via client asserts
                pass

        tg.start_soon(_run_server)
        async with ClientSession(
            streams.server_to_client_rx, streams.client_to_server_tx
        ) as client:
            await client.initialize()
            await body(client)

        tg.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_initialize_and_list_tools(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        tools = await client.list_tools()
        names = {t.name for t in tools.tools}
        assert names == EXPECTED_TOOLS

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_call_search_use_cases(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "search_use_cases", {"query": "GDPR", "limit": 2}
        )
        assert result.content
        payload = json.loads(result.content[0].text)
        assert payload["count"] == 2
        assert payload["totalMatched"] >= 1

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_call_get_use_case(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "get_use_case", {"uc_id": "22.1.1"}
        )
        payload = json.loads(result.content[0].text)
        assert payload["id"] == "22.1.1"

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_call_tool_invalid_input_returns_error_payload(
    live_catalog: Catalog,
) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "get_use_case", {"uc_id": "../../etc/passwd"}
        )
        payload = json.loads(result.content[0].text)
        assert payload["error"] == "invalid_input"

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_unknown_tool_returns_error(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        # Unknown tools propagate as server-side errors; the MCP client
        # surfaces them with isError=True on the result.
        result = await client.call_tool("unknown_tool", {})
        assert result.isError

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_ledger(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.read_resource("ledger://")
        assert result.contents
        payload = json.loads(result.contents[0].text)
        assert "merkleRoot" in payload
        assert payload.get("entryCount", 0) >= 1

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_use_case(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.read_resource("uc://usecase/22.1.1")
        payload = json.loads(result.contents[0].text)
        assert payload["id"] == "22.1.1"

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_invalid_uri_returns_error(
    live_catalog: Catalog,
) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.read_resource("file:///etc/passwd")
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "invalid_uri"

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_list_resources_returns_empty(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.list_resources()
        # We deliberately publish zero enumerable resources; clients must
        # use the list_* tools to discover IDs before reading URIs.
        assert list(result.resources) == []

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_equipment(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.read_resource("equipment://azure")
        payload = json.loads(result.contents[0].text)
        assert payload["id"] == "azure"

    await _drive_server(live_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_regulation(live_catalog: Catalog) -> None:
    async def body(client: ClientSession) -> None:
        result = await client.read_resource("reg://gdpr")
        payload = json.loads(result.contents[0].text)
        assert payload["id"] == "gdpr"

    await _drive_server(live_catalog, body)
