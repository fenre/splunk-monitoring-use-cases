#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.baseline_clause_grammar_free``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_baseline_clause_grammar_free.py`` invocation
alive while the new dispatcher
(``python -m splunk_uc audit-baseline-clause-grammar-free``) becomes
the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.baseline_clause_grammar_free import (
    BASELINE_PATH,
    BASELINEABLE_FP_FIELD,
    FORBIDDEN_CODES,
    REPO_ROOT,
    main,
)

__all__ = [
    "BASELINEABLE_FP_FIELD",
    "BASELINE_PATH",
    "FORBIDDEN_CODES",
    "REPO_ROOT",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
