"""Entry point for ``python -m splunk_uc_mcp`` and the ``splunk-uc-mcp`` script.

Starts the MCP server on stdio. The CoSAI MCP guidance (see
``.cursor/rules/codeguard-0-mcp-security.mdc``) recommends stdio over HTTP for
local, single-tenant usage because it eliminates DNS-rebinding risks and
requires no authentication surface. An HTTP transport is intentionally
out-of-scope for v1 — it would only matter if we ever hosted the server for a
multi-tenant consumer, at which point we would add the full authn/z +
mutual-TLS + CORS stack the rule requires.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="splunk-uc-mcp",
        description=(
            "Run the Splunk Monitoring Use Cases MCP server on stdio. "
            "Read-only access to the use case catalogue, regulations, "
            "equipment tags, compliance gaps, and the signed provenance "
            "ledger."
        ),
    )
    parser.add_argument(
        "--catalog-root",
        type=Path,
        default=None,
        help=(
            "Path to a local clone of the repository (must contain api/v1/). "
            "If omitted, defaults to SPLUNK_UC_CATALOG_ROOT env var, then "
            "the current working directory if it looks like a checkout, "
            "otherwise falls back to the hosted GitHub Pages mirror."
        ),
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help=(
            "Override the HTTPS fallback base URL (defaults to "
            "SPLUNK_UC_BASE_URL env var, or "
            "https://fenre.github.io/splunk-monitoring-use-cases). "
            "Only used when the local catalog is missing a requested file."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Emit DEBUG-level logs to stderr (stdout is reserved for JSON-RPC).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
    )
    return parser


def _version_string() -> str:
    from splunk_uc_mcp import __version__

    return f"splunk-uc-mcp {__version__}"


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args and start the MCP stdio loop.

    Returns a shell exit code (0 on clean shutdown).
    """

    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    catalog_root: Path | None = args.catalog_root
    if catalog_root is None:
        env_root = os.environ.get("SPLUNK_UC_CATALOG_ROOT")
        if env_root:
            catalog_root = Path(env_root)

    base_url: str | None = args.base_url
    if base_url is None:
        base_url = os.environ.get("SPLUNK_UC_BASE_URL")

    from splunk_uc_mcp.server import run_stdio_server

    try:
        return run_stdio_server(catalog_root=catalog_root, base_url=base_url)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
