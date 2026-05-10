#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.feasibility.oscal_generate_proof``.

The implementation moved under ``src/splunk_uc/feasibility/`` as part
of the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 9,
feasibility cluster). This shim keeps the historic
``scripts/feasibility/oscal_generate_proof.py`` invocation alive
while the new dispatcher (``python -m splunk_uc
feasibility-oscal-generate-proof``) becomes the primary entry-point.
The Node-side validator (``oscal_validate.mjs``) stays where it is at
``scripts/feasibility/oscal_validate.mjs`` — the new module continues
to invoke it via ``subprocess.run([node_bin, str(NODE_VALIDATOR), ...])``
so this shim has nothing to forward for the JS side.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.feasibility.oscal_generate_proof import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
