#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.spl_hallucinations``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_spl_hallucinations.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-spl-hallucinations``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.spl_hallucinations import (
    BAD_COMMAND_PATTERNS,
    CIM_DATASETS,
    CIM_SPL_MARKER,
    MITRE_INVALID_PATTERNS,
    MITRE_PATTERN,
    REPO_ROOT,
    SPL_FENCE,
    UC_HEADER,
    USE_CASES_DIR,
    VALID_COMMANDS,
    VALID_EVAL_FUNCS,
    VALID_STATS_FUNCS,
    Finding,
    audit_file,
    check_bad_patterns,
    check_in_with_wildcards_in_where_eval,
    check_mitre_ids,
    check_tstats,
    check_unknown_commands,
    extract_eval_funcs_used,
    extract_pipe_commands,
    extract_spl_blocks_with_labels,
    extract_tstats_components,
    main,
    split_spl_pipes,
    split_uc_blocks,
    strip_comments,
)

__all__ = [
    "BAD_COMMAND_PATTERNS",
    "CIM_DATASETS",
    "CIM_SPL_MARKER",
    "MITRE_INVALID_PATTERNS",
    "MITRE_PATTERN",
    "REPO_ROOT",
    "SPL_FENCE",
    "UC_HEADER",
    "USE_CASES_DIR",
    "VALID_COMMANDS",
    "VALID_EVAL_FUNCS",
    "VALID_STATS_FUNCS",
    "Finding",
    "audit_file",
    "check_bad_patterns",
    "check_in_with_wildcards_in_where_eval",
    "check_mitre_ids",
    "check_tstats",
    "check_unknown_commands",
    "extract_eval_funcs_used",
    "extract_pipe_commands",
    "extract_spl_blocks_with_labels",
    "extract_tstats_components",
    "main",
    "split_spl_pipes",
    "split_uc_blocks",
    "strip_comments",
]


if __name__ == "__main__":
    sys.exit(main())
