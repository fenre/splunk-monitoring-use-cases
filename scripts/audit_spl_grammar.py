#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.spl_grammar``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_spl_grammar.py`` invocation alive while the
new dispatcher (``python -m splunk_uc audit-spl-grammar``) becomes the
primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.spl_grammar import (
    RE_SPL_FENCE,
    RE_UC_HEAD,
    REPO_ROOT,
    USE_CASES,
    Finding,
    audit_file,
    audit_spl_block,
    check_case_wildcard,
    check_leading_pipe,
    check_multi_search_glue,
    check_stats_span,
    check_where_after_timechart,
    fix_file,
    fix_spl_block,
    fix_stats_span_in_spl,
    main,
)

__all__ = [
    "REPO_ROOT",
    "RE_SPL_FENCE",
    "RE_UC_HEAD",
    "USE_CASES",
    "Finding",
    "audit_file",
    "audit_spl_block",
    "check_case_wildcard",
    "check_leading_pipe",
    "check_multi_search_glue",
    "check_stats_span",
    "check_where_after_timechart",
    "fix_file",
    "fix_spl_block",
    "fix_stats_span_in_spl",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
