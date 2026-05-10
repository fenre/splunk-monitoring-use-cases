#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.generators.md_from_json``.

The implementation moved under ``src/splunk_uc/generators/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 1, generator
half). This shim keeps the historic
``scripts/generate_md_from_json.py`` invocation alive while the new
dispatcher (``python -m splunk_uc generate-md-from-json``) becomes the
primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.generators.md_from_json import (
    CONTENT_DIR,
    HEADER,
    REPO_ROOT,
    find_uc_json_files,
    main,
    process_file,
    render_md,
)

__all__ = [
    "CONTENT_DIR",
    "HEADER",
    "REPO_ROOT",
    "find_uc_json_files",
    "main",
    "process_file",
    "render_md",
]


if __name__ == "__main__":
    sys.exit(main())
