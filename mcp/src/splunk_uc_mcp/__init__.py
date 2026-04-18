"""Splunk Monitoring Use Cases — Model Context Protocol server.

Exposes the static catalogue (6,424 use cases, 60 regulations, 105 equipment
slugs, and the signed provenance ledger) to LLM agents via JSON-RPC over
stdio. Serves compliance officers and detection engineers equally: every tool
is read-only, purely introspects pre-built ``api/v1/*.json`` endpoints, and
degrades from a local clone to the hosted GitHub Pages mirror when the local
tree is unavailable.

See :mod:`splunk_uc_mcp.server` for the MCP wiring and
:mod:`splunk_uc_mcp.catalog` for the data loader.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
