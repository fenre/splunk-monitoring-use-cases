"""Splunk-core baseline vocabulary for SPL reference validation.

This is the *floor* of valid SPL identifiers. Anything in here is
considered known-good without any external corpus. Anything *not* here
gets a second chance: it might still be valid if it appears in the
local reference corpus emitted by ``tools/research/build_spl_reference.py``
(which adds Searchbase + ESCU + customer-app vocabulary on top).

Sources of truth — all referenced from the public Splunk docs:

* Eval functions:
  https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/CommonEvalFunctions
* Stats / timechart / tstats functions:
  https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Statistical-and-charting-functions
* Search commands:
  https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands
* CIM data models:
  https://docs.splunk.com/Documentation/CIM/latest/User/Overview

The valid-commands set lives in ``spl_hallucinations.py`` (``VALID_COMMANDS``);
we re-export it from here so reference audits don't need to import a
sibling audit's internals.
"""

from __future__ import annotations

# Re-export the existing VALID_COMMANDS so callers have one import.
from splunk_uc.audits.spl_hallucinations import (
    CIM_DATASETS as CIM_DATASETS,
)
from splunk_uc.audits.spl_hallucinations import (
    VALID_COMMANDS as VALID_COMMANDS,
)

__all__ = [
    "VALID_COMMANDS",
    "CIM_DATASETS",
    "VALID_EVAL_FUNCTIONS",
    "VALID_STATS_FUNCTIONS",
    "BUILTIN_FIELD_TOKENS",
    "is_perc_function",
]


# ---------------------------------------------------------------------------
# Eval functions (and where-clause functions, which use the same vocabulary)
# ---------------------------------------------------------------------------
# Source: SearchReference/CommonEvalFunctions, current as of Splunk 9.x.
# Categorised in the docs as bitwise, comparison & conditional, conversion,
# cryptographic, date/time, informational, JSON, mathematical, multivalue,
# statistical, text. We collapse them into a single set because eval
# accepts any of them in any context.
VALID_EVAL_FUNCTIONS: set[str] = {
    # Bitwise
    "bit_and",
    "bit_or",
    "bit_not",
    "bit_xor",
    "bit_shift_left",
    "bit_shift_right",
    # Comparison & conditional
    "case",
    "cidrmatch",
    "coalesce",
    "false",
    "if",
    "in",
    "like",
    "lookup",
    "match",
    "null",
    "nullif",
    "searchmatch",
    "true",
    "validate",
    # Conversion
    "ipmask",
    "printf",
    "tonumber",
    "tostring",
    # Cryptographic
    "md5",
    "sha1",
    "sha256",
    "sha512",
    # Date/time
    "now",
    "relative_time",
    "strftime",
    "strptime",
    "time",
    # Informational
    "isbool",
    "isint",
    "isnotnull",
    "isnull",
    "isnum",
    "isstr",
    "typeof",
    # JSON
    "json_object",
    "json_array",
    "json_array_to_mv",
    "json_append",
    "json_extend",
    "json_extract",
    "json_extract_exact",
    "json_keys",
    "json_set",
    "json_set_exact",
    "json_valid",
    "object_to_array",
    # Mathematical
    "abs",
    "ceiling",
    "ceil",
    "exact",
    "exp",
    "floor",
    "ln",
    "log",
    "pi",
    "pow",
    "round",
    "sigfig",
    "sqrt",
    "sum",
    # Multivalue
    "commands",
    "mvappend",
    "mvcount",
    "mvdedup",
    "mvfilter",
    "mvfind",
    "mvindex",
    "mvjoin",
    "mvmap",
    "mvmax",
    "mvmin",
    "mvrange",
    "mvsort",
    "mvzip",
    "mv_to_json_array",
    "split",
    # Statistical
    "max",
    "median",
    "min",
    "random",
    # Text
    "len",
    "lower",
    "ltrim",
    "replace",
    "rtrim",
    "spath",
    "substr",
    "trim",
    "upper",
    "urldecode",
    # Trigonometric (commonly used in geo/anomaly detection)
    "acos",
    "acosh",
    "asin",
    "asinh",
    "atan",
    "atan2",
    "atanh",
    "cos",
    "cosh",
    "hypot",
    "sin",
    "sinh",
    "tan",
    "tanh",
}


# ---------------------------------------------------------------------------
# Aggregator functions used in stats / timechart / chart / tstats / etc.
# ---------------------------------------------------------------------------
# Source: SearchReference/Statistical-and-charting-functions
VALID_STATS_FUNCTIONS: set[str] = {
    # Aggregate
    "avg",
    "count",
    "distinct_count",
    "dc",
    "estdc",
    "estdc_error",
    "exactperc",
    "max",
    "mean",
    "median",
    "min",
    "mode",
    "percentile",
    # The percentile family (perc<n>, p<n>, upperperc<n>, exactperc<n>) is
    # parametric in the function name itself, so we don't list every
    # variant here; ``is_perc_function`` matches them at call sites.
    "range",
    "stdev",
    "stdevp",
    "sum",
    "sumsq",
    "var",
    "varp",
    # Event-order
    "current",
    "earliest",
    "earliest_time",
    "first",
    "last",
    "latest",
    "latest_time",
    "list",
    "rate",
    "rate_avg",
    "rate_sum",
    "values",
    # Time aggregators
    "per_day",
    "per_hour",
    "per_minute",
    "per_second",
}


# ---------------------------------------------------------------------------
# Field tokens that look like sourcetypes/indexes/macros but are actually
# Splunk-internal magic. We exclude them from "unknown" reports.
# ---------------------------------------------------------------------------
BUILTIN_FIELD_TOKENS: set[str] = {
    # Built-in indexes
    "_internal",
    "_introspection",
    "_audit",
    "_telemetry",
    "_thefishbucket",
    "_metrics",
    "_metrics_rollup",
    "_dsphulk",
    "main",
    "history",
    "summary",
    "lastchanceindex",
    # Built-in fields commonly used in stats
    "_time",
    "_raw",
    "_indextime",
    "_serial",
    "_subsecond",
    "_cd",
    "_bkt",
}


def is_perc_function(name: str) -> bool:
    """Return ``True`` if ``name`` is a percentile aggregator like ``perc95`` / ``p99``.

    These are dynamically constructed (``perc<n>`` / ``upperperc<n>`` /
    ``exactperc<n>`` / ``p<n>``) so they don't appear in the static set.
    """
    lc = name.lower()
    for prefix in ("upperperc", "exactperc", "perc", "p"):
        if lc.startswith(prefix):
            tail = lc[len(prefix) :]
            if tail.isdigit():
                return True
    return False
