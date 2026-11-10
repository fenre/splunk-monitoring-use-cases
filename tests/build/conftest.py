"""Register ``tools.build`` for coverage when tests import ``build`` via ``tools/`` on path."""

from __future__ import annotations

import sys
from pathlib import Path

import tools.build  # noqa: F401

_REPO = Path(__file__).resolve().parents[2]
_TOOLS = str(_REPO / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
