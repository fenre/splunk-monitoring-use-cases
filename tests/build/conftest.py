"""Register ``tools.build`` for coverage when tests import ``build`` via ``tools/`` on path."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import tools.build  # noqa: F401

_REPO = Path(__file__).resolve().parents[2]
_TOOLS = str(_REPO / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from build import parse_content  # noqa: E402


@pytest.fixture(scope="session")
def real_catalog() -> parse_content.Catalog:
    """One parse of the live catalogue, shared by every test in the session."""
    return parse_content.load(_REPO, reproducible=True)
