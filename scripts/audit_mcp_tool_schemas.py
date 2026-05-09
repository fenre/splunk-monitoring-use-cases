#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.mcp_tool_schemas``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_mcp_tool_schemas.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-mcp-tool-schemas``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.mcp_tool_schemas import (
    MCP_SRC,
    REPO_ROOT,
    main,
)

__all__ = [
    "MCP_SRC",
    "REPO_ROOT",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
