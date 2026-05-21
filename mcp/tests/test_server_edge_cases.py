"""Targeted tests for ``splunk_uc_mcp.server`` edge cases.

The integration tests in ``test_server.py`` exercise the happy paths
over the full JSON-RPC stack. This module fills in the error / not-
found / hosted-only branches that the happy-path suite never
reaches:

* tool dispatch error envelopes — TypeError, KeyError,
  CatalogNotFoundError, CatalogError (server.py lines 195-200);
* the ``uc://category/<id>`` resource lookup, both hit and miss
  (server.py lines 403-412);
* equipment / regulation resource lookups that miss
  (server.py lines 433-438 — generic CatalogError catches);
* the ledger-from-hosted-mode short-circuit that returns
  ``not_found`` when ``load_data_file`` returns ``None``
  (server.py line 426);
* :func:`run_stdio_server` with the anyio loop stubbed so the
  function returns 0 without blocking on real stdin (server.py
  lines 136-159).

Every test stays hermetic (no live catalog), uses ``monkeypatch``
for stubs, and avoids touching the network or the disk outside
``tmp_path``.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.server import InitializationOptions, NotificationOptions

from splunk_uc_mcp import __version__
from splunk_uc_mcp.catalog import (
    Catalog,
    CatalogError,
    CatalogNotFoundError,
)
from splunk_uc_mcp.server import (
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    build_server,
    run_stdio_server,
)


# --------------------------------------------------------------------- #
# Shared in-memory driver
# --------------------------------------------------------------------- #


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
    """Mirrors the helper in test_server.py; copied here so the two test
    modules stay independent and a refactor in one can't silently break
    the other's setup."""

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


# --------------------------------------------------------------------- #
# Category resource — uc://category/<id>
# --------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_read_resource_category_hit(synthetic_catalog: Catalog) -> None:
    """The category branch (``parsed.kind == "category"``) iterates the
    ``list_categories`` tree and returns the first matching entry.
    The synthetic catalog only contains UCs in cat 1 and cat 22, so
    asking for cat 22 must return a dict whose ``id == "22"``."""

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("uc://category/22")
        assert result.contents
        payload = json.loads(result.contents[0].text)
        assert payload["id"] == "22"
        # The shape carries through from list_categories — subcategories
        # is the field the agent uses to drill in further.
        assert "subcategories" in payload

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_category_miss_returns_not_found(
    synthetic_catalog: Catalog,
) -> None:
    """When the category id is well-formed (digits only) but never
    appears in the catalogue, the ``match is None`` arm at server.py
    line 408 must raise :class:`CatalogNotFoundError`, which the
    outer try/except renders as the ``not_found`` JSON envelope.

    The synthetic catalog only knows cats 1 and 22; cat 9999 will
    miss."""

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("uc://category/9999")
        assert result.contents
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "not_found"
        assert "9999" in payload["message"]

    await _drive_server(synthetic_catalog, body)


# --------------------------------------------------------------------- #
# Equipment / regulation resource — generic not-found envelope
# --------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_read_resource_equipment_miss_returns_not_found(
    synthetic_catalog: Catalog,
) -> None:
    """``equipment://<slug>`` against a slug that doesn't have a
    matching JSON file under ``api/v1/equipment/`` must surface as
    the ``not_found`` envelope. Exercises the ``CatalogNotFoundError``
    catch in ``_read_resource`` (server.py lines 435-436)."""

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("equipment://nonexistent_slug")
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "not_found"

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_regulation_miss_returns_not_found(
    synthetic_catalog: Catalog,
) -> None:
    """Same shape for the regulation family: a well-formed but
    nonexistent regulation slug returns ``not_found``. The synthetic
    catalog only has ``gdpr``."""

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("reg://nonexistent")
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "not_found"

    await _drive_server(synthetic_catalog, body)


# --------------------------------------------------------------------- #
# Ledger resource — hosted-only short-circuit
# --------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_read_resource_ledger_returns_not_found_when_hosted_only(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """When ``catalog.load_data_file`` returns ``None`` (the hosted
    GitHub Pages path — no ``data/`` directory shipped), the ledger
    branch at server.py line 425-429 raises ``CatalogNotFoundError``
    so the caller sees the same ``not_found`` envelope as a missing
    UC.

    Implementation: monkeypatch ``load_data_file`` on the live
    ``Catalog`` instance to return ``None``. We use ``synthetic_catalog``
    (not ``live_catalog``) so the fixture is fast and there's no
    chance of mutating a session-scoped object."""

    monkeypatch.setattr(
        type(synthetic_catalog),
        "load_data_file",
        lambda self, relative_path: None,
    )

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("ledger://")
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "not_found"
        assert "ledger" in payload["message"].lower()

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_ledger_catalog_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """Pin the third catch in the outer try/except: a raw
    :class:`CatalogError` from ``load_data_file`` must surface as
    ``catalog_error`` rather than ``not_found`` or ``invalid_uri``.
    Exercises server.py lines 437-438."""

    def _boom(self: Catalog, relative_path: str) -> Any:
        raise CatalogError("backing file is corrupt")

    monkeypatch.setattr(type(synthetic_catalog), "load_data_file", _boom)

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("ledger://")
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "catalog_error"
        assert "corrupt" in payload["message"]

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_read_resource_ledger_validation_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """Pin the first catch in the outer try/except (server.py lines
    433-434): a ``CatalogValidationError`` from ``load_data_file``
    must surface as ``invalid_uri``. ``CatalogValidationError`` is a
    ``ValueError`` subclass in this codebase, so it lands in the
    ``(ValueError, CatalogValidationError)`` tuple.

    The ``ledger://`` URI parses cleanly upstream, so the only way
    to reach this branch is via the catalog accessor itself raising
    a validation error — which is exactly what we simulate here."""

    from splunk_uc_mcp.catalog import CatalogValidationError

    def _boom(self: Catalog, relative_path: str) -> Any:
        raise CatalogValidationError("path failed validation")

    monkeypatch.setattr(type(synthetic_catalog), "load_data_file", _boom)

    async def body(client: ClientSession) -> None:
        result = await client.read_resource("ledger://")
        payload = json.loads(result.contents[0].text)
        assert payload["error"] == "invalid_uri"
        assert "path failed validation" in payload["message"]

    await _drive_server(synthetic_catalog, body)


# --------------------------------------------------------------------- #
# Tool dispatch — error envelopes
# --------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_call_tool_unknown_use_case_returns_not_found(
    synthetic_catalog: Catalog,
) -> None:
    """The synthetic catalog only ships UCs 1.1.1 and 22.1.1. Asking
    for 99.99.99 raises :class:`CatalogNotFoundError` inside the
    handler, which the dispatch wrapper catches and renders as
    ``not_found`` (server.py lines 197-198)."""

    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "get_use_case", {"uc_id": "99.99.99"}
        )
        assert result.isError
        payload = json.loads(result.content[0].text)
        assert payload["error"] == "not_found"

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_call_tool_type_error_returns_invalid_input(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """A handler that raises :class:`TypeError` must hit the
    ``(TypeError, KeyError)`` catch at server.py lines 195-196 and
    surface as ``invalid_input``.

    The dispatch dict captures the tool function by closure at
    ``build_server`` time, so we must patch the symbol on the
    ``splunk_uc_mcp.server`` module (where ``_tool_dispatch`` looks it
    up) BEFORE ``_drive_server`` builds the server."""

    import splunk_uc_mcp.server as server_module

    def _bad_handler(*, catalog: Catalog, **kwargs: Any) -> None:
        raise TypeError("simulated bad argument type")

    monkeypatch.setattr(server_module, "search_use_cases", _bad_handler)

    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "search_use_cases", {"query": "GDPR"}
        )
        assert result.isError
        payload = json.loads(result.content[0].text)
        assert payload["error"] == "invalid_input"
        assert "simulated bad argument type" in payload["message"]

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_call_tool_key_error_returns_invalid_input(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """KeyError shares the same catch as TypeError. Distinct test so
    a future refactor that splits the exception tuple can't silently
    drop one half — we'd see the test go red. Patch the symbol on
    the server module for the same closure-capture reason as the
    TypeError test."""

    import splunk_uc_mcp.server as server_module

    def _bad_handler(*, catalog: Catalog, **kwargs: Any) -> None:
        raise KeyError("missing_field")

    monkeypatch.setattr(server_module, "search_use_cases", _bad_handler)

    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "search_use_cases", {"query": "GDPR"}
        )
        assert result.isError
        payload = json.loads(result.content[0].text)
        assert payload["error"] == "invalid_input"

    await _drive_server(synthetic_catalog, body)


@pytest.mark.asyncio
async def test_call_tool_catalog_error_returns_catalog_error(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """A bare :class:`CatalogError` from the handler must surface as
    ``catalog_error``, not ``not_found`` or ``invalid_input``.
    Exercises server.py lines 199-200. Patch the symbol on the
    server module for the closure-capture reason explained on the
    TypeError test."""

    import splunk_uc_mcp.server as server_module

    def _bad_handler(*, catalog: Catalog, **kwargs: Any) -> None:
        raise CatalogError("downstream JSON store is offline")

    monkeypatch.setattr(server_module, "search_use_cases", _bad_handler)

    async def body(client: ClientSession) -> None:
        result = await client.call_tool(
            "search_use_cases", {"query": "GDPR"}
        )
        assert result.isError
        payload = json.loads(result.content[0].text)
        assert payload["error"] == "catalog_error"
        assert "offline" in payload["message"]

    await _drive_server(synthetic_catalog, body)


# --------------------------------------------------------------------- #
# run_stdio_server — anyio.run stubbed so we never block on stdin
# --------------------------------------------------------------------- #


def test_run_stdio_server_returns_zero_with_stubbed_anyio_loop(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog_root: Path,
) -> None:
    """:func:`run_stdio_server` constructs a :class:`Catalog`, calls
    :func:`build_server`, builds the ``InitializationOptions``, then
    hands control to ``anyio.run(_main)``. We can't run the real
    stdio loop in a unit test — it would block on stdin — so we
    stub ``anyio.run`` and assert the function exits cleanly with
    return code 0.

    Use ``synthetic_catalog_root`` for the on-disk fixture so the
    Catalog constructor's ``_resolve_catalog_root`` validation
    (looks for ``api/v1/manifest.json``) passes without touching
    the real catalogue."""

    captured: list[Any] = []

    def _fake_anyio_run(fn: Any) -> None:
        captured.append(fn)

    import splunk_uc_mcp.server as server_module

    monkeypatch.setattr(server_module.anyio, "run", _fake_anyio_run)

    rc = run_stdio_server(catalog_root=synthetic_catalog_root, base_url=None)
    assert rc == 0
    assert len(captured) == 1
    # The captured object is the local async function _main, so it
    # must be callable. We don't await it because the test process
    # has no MCP client to talk to.
    assert callable(captured[0])


def test_run_stdio_server_executes_main_coroutine_with_stubbed_io(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog_root: Path,
) -> None:
    """Cover server.py lines 155-156: the ``async with stdio_server()
    as (read, write): await server.run(...)`` body inside ``_main``.

    The previous test stubbed ``anyio.run`` so ``_main`` never
    executed. Here we leave ``anyio.run`` alone and instead stub
    the I/O primitives so ``_main`` runs to completion without
    blocking on real stdin:

    1. ``stdio_server`` is replaced by an async context manager
       that yields ``(None, None)`` immediately.
    2. The :class:`mcp.server.Server` instance returned by
       :func:`build_server` has its ``run`` method monkeypatched to
       a no-op coroutine, so the await on line 156 returns at once.

    Together these stubs let the real ``_main`` body execute (the
    only way to cover those two lines) without bringing up a true
    JSON-RPC loop. The test asserts both stubs were invoked so a
    future refactor that bypasses one of them breaks immediately."""

    from contextlib import asynccontextmanager

    import splunk_uc_mcp.server as server_module

    stdio_calls: list[int] = []
    run_calls: list[tuple[Any, ...]] = []

    @asynccontextmanager
    async def _stub_stdio_server() -> Any:
        stdio_calls.append(1)
        yield (None, None)

    monkeypatch.setattr(server_module, "stdio_server", _stub_stdio_server)

    real_build_server = server_module.build_server

    def _patched_build_server(catalog: Catalog) -> Any:
        srv = real_build_server(catalog)

        async def _noop_run(*args: Any, **kwargs: Any) -> None:
            run_calls.append(args)

        # Bind the no-op directly to the instance, leaving the class
        # untouched so other tests still see the real .run method.
        srv.run = _noop_run  # type: ignore[method-assign]
        return srv

    monkeypatch.setattr(server_module, "build_server", _patched_build_server)

    rc = run_stdio_server(catalog_root=synthetic_catalog_root, base_url=None)
    assert rc == 0
    assert stdio_calls == [1]  # stdio_server context was entered exactly once
    assert len(run_calls) == 1  # server.run awaited exactly once
    # The real signature is (read_stream, write_stream, init_options);
    # confirm the third positional is the InitializationOptions
    # object so the contract stays pinned.
    assert run_calls[0][:2] == (None, None)
    from mcp.server import InitializationOptions as _InitOpts

    assert isinstance(run_calls[0][2], _InitOpts)
