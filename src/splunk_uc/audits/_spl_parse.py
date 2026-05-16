"""SPL extraction helpers — pull structural references out of any SPL string.

This module is the shared parser substrate for every reference-validating
audit (``audit-spl-references`` and friends). It does *not* validate
anything by itself; it just yields structured references that downstream
audits compare against allow-lists.

The extractors are deliberately conservative: when the syntax is
ambiguous we prefer to under-report (silent miss) over over-report
(false positive flood). Catching a hallucination means surfacing it
loudly, but reporting *every* tokenised string as "unknown" floods the
report and trains reviewers to ignore it.

This file shares two primitives with ``spl_grammar.py``
(``_strip_comments``, ``_split_pipes``) — we re-export thin wrappers
rather than duplicating the implementation, so any future fix to the
pipe splitter benefits both audits.

Rationale on the regex vocabulary
---------------------------------
Patterns here are derived from Splunk's published `SPL command
reference`_ and the public CIM data-model documentation. They are
common-knowledge SPL syntax facts (e.g. macros are wrapped in
backticks, sourcetypes appear after ``sourcetype=``) — not creative
expression — and were written from scratch against the Splunk docs,
not lifted from any Splunk-licensed app. Where the Searchbase app's
``sp_search_decomposition`` macro happens to converge on similar
patterns, it's because both files describe the same underlying SPL
grammar.

.. _SPL command reference: https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from splunk_uc.audits.spl_grammar import _split_pipes, _strip_comments

__all__ = [
    "MacroRef",
    "SourcetypeRef",
    "IndexRef",
    "DatamodelRef",
    "LookupRef",
    "FunctionRef",
    "Extracted",
    "extract_all",
    "extract_macros",
    "extract_sourcetypes",
    "extract_indexes",
    "extract_datamodel_paths",
    "extract_lookups",
    "extract_eval_functions",
    "extract_stats_functions",
    "extract_commands",
    "strip_comments",
    "split_pipes",
]


# Re-export the internal helpers under public names so other audits can
# use them without importing the underscore-prefixed implementation.
def strip_comments(spl: str) -> str:
    """Strip ``comment("...")`` segments from SPL for parser consumption."""
    return _strip_comments(spl)


def split_pipes(spl: str) -> list[str]:
    """Split SPL on unquoted pipes into pipeline segments."""
    return _split_pipes(spl)


# ---------------------------------------------------------------------------
# Reference dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MacroRef:
    """A single ``\\`macroname(arg1, arg2)\\``` reference inside SPL."""

    name: str
    arity: int  # -1 == not parameterised (no parens at all)
    raw: str  # the literal `...` text including backticks


@dataclass(frozen=True)
class SourcetypeRef:
    """A single ``sourcetype=<value>`` reference inside SPL."""

    value: str  # raw value (may include wildcards, may be quoted)
    is_wildcard: bool  # true if value contains '*' or starts with the wildcard sigil


@dataclass(frozen=True)
class IndexRef:
    """A single ``index=<value>`` reference inside SPL."""

    value: str
    is_wildcard: bool


@dataclass(frozen=True)
class DatamodelRef:
    """A single ``datamodel=<Model>.<Dataset>`` (or ``Model:Dataset``) reference."""

    model: str
    dataset: str | None  # None when only the model is named


@dataclass(frozen=True)
class LookupRef:
    """A single ``lookup`` / ``inputlookup`` / ``outputlookup`` reference."""

    name: str  # lookup table name
    command: str  # one of {"lookup","inputlookup","outputlookup","outputcsv"}


@dataclass(frozen=True)
class FunctionRef:
    """An ``eval``/``where``/``stats`` function call (e.g. ``coalesce``, ``count``)."""

    name: str
    context: str  # one of {"eval","where","stats","tstats","fieldformat","filter"}


@dataclass(frozen=True)
class Extracted:
    """Aggregate extraction output for one SPL string."""

    commands: list[str]
    macros: list[MacroRef]
    sourcetypes: list[SourcetypeRef]
    indexes: list[IndexRef]
    datamodels: list[DatamodelRef]
    lookups: list[LookupRef]
    eval_functions: list[FunctionRef]
    stats_functions: list[FunctionRef]


# ---------------------------------------------------------------------------
# Internal regexes
# ---------------------------------------------------------------------------


# Backtick macro reference. Greedy-but-bounded: doesn't span newlines, and
# the macro name itself is restricted to identifier characters so we don't
# confuse this with a literal string that happens to contain backticks.
# Valid examples:
#   `myMacro`
#   `myMacro(arg)`
#   `myMacro(arg1,arg2)`
#   `security_content_summariesonly`
_MACRO_RE = re.compile(
    r"`(?P<name>[A-Za-z_][A-Za-z0-9_:.]*)\s*(?:\((?P<args>[^`]*)\))?`"
)

# index= or sourcetype= predicate. We accept double-quoted, single-quoted,
# or bare values; we stop at whitespace, pipe, paren, comma, or a stray
# backtick (which would otherwise smuggle in `\`` artefacts when the
# author wrapped the predicate in a comment). We explicitly reject
# token expansion (``$index$``) — those are Simple-XML tokens and are
# validated by ``audit-dashboard-spl``, not us.
#
# The ``=(?!=)`` requires exactly one ``=`` so we don't false-positive
# on the comparison operator inside ``eval``/``case``/``where`` contexts:
# ``case(sourcetype=="aws:cloudtrail", ...)`` is valid SPL and should
# NOT be reported as a sourcetype reference (the value is the *literal*
# in the case predicate, not a search-time filter).
_INDEX_RE = re.compile(
    r"\bindex\s*=(?!=)\s*(?P<v>\"[^\"]*\"|'[^']*'|[^\s|()\],`]+)",
    re.IGNORECASE,
)
_SOURCETYPE_RE = re.compile(
    r"\bsourcetype\s*=(?!=)\s*(?P<v>\"[^\"]*\"|'[^']*'|[^\s|()\],`]+)",
    re.IGNORECASE,
)

# datamodel=Model[.Dataset] OR datamodel=Model:Dataset OR
# tstats ... FROM datamodel=Model.Dataset
#
# We require the model to start with an UPPERCASE letter — every Splunk
# CIM datamodel and every published add-on datamodel follows that
# convention (Authentication, Network_Traffic, Risk, Endpoint, etc.).
# Without this constraint the regex matches things like
# ``datamodel=if(...)`` (an eval expression assigning to a field
# literally named ``datamodel``) and emits ``if`` as a fake datamodel.
_DATAMODEL_RE = re.compile(
    r"\bdatamodel\s*[=:]\s*\"?(?P<model>[A-Z][A-Za-z0-9_]*)"
    r"(?:[.:](?P<dataset>[A-Za-z_][A-Za-z0-9_.]*))?",
)

# lookup / inputlookup / outputlookup / outputcsv command references. We
# only match these as the *first* token of a pipeline segment; the
# Splunk parser allows the command in the middle of a search but we
# treat that as out-of-scope for reference extraction.
_LOOKUP_CMD_RE = re.compile(
    r"^\s*(?P<cmd>lookup|inputlookup|outputlookup|outputcsv)\b\s*"
    r"(?:append\s*=\s*\w+\s+)?"  # `append=true` modifier on lookup
    r"(?:override_if_null\s*=\s*\w+\s+)?"
    r"(?:max_matches\s*=\s*\d+\s+)?"
    r"(?:local\s*=\s*\w+\s+)?"
    r"(?P<name>\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_./-]+)",
    re.IGNORECASE,
)

# eval/where/stats function call. We match a bare identifier immediately
# followed by ``(`` with no intervening whitespace — Splunk function
# calls are always tight (``coalesce(``, ``count(``, ``case(``). The
# whitespace-tolerant variant matches false positives like
# ``WHERE nodename=Application_State (...)`` where the parens open a
# predicate group rather than calling a function.
#
# To minimise false positives we only emit this when the call is
# *inside* an eval/where/stats/timechart context (we tag the segment
# first via its leading command word).
_FUNC_CALL_RE = re.compile(r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\(")

# First word of a segment = command name. SPL allows `<command> ...` or
# leading `| <command>` (which the splitter has already stripped).
_CMD_HEAD_RE = re.compile(r"^\s*(?P<cmd>[A-Za-z_][A-Za-z0-9_]*)\b")

# Search-segment "context" detection — drives where eval/where/stats
# functions live. We look at the segment's leading command word.
_EVAL_LIKE = frozenset(
    {
        "eval",
        "where",
        "fieldformat",
        "fillnull",  # `value=...` allows eval expr in some versions
        "rangemap",
    }
)
_STATS_LIKE = frozenset(
    {
        "stats",
        "sistats",
        "eventstats",
        "streamstats",
        "tstats",
        "geostats",
        "chart",
        "sichart",
        "timechart",
        "sitimechart",
        "top",
        "rare",
        "addcoltotals",
        "mstats",
    }
)


def _unquote(value: str) -> str:
    """Strip matching surrounding double or single quotes from a value."""
    v = value.strip()
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1]
    return v


def _is_wildcard(value: str) -> bool:
    return "*" in _unquote(value)


# ---------------------------------------------------------------------------
# Individual extractors
# ---------------------------------------------------------------------------


def extract_macros(spl: str) -> list[MacroRef]:
    """Return every macro reference (``\\`name\\``` or ``\\`name(args)\\```) in SPL.

    The arity is the number of comma-separated arguments inside the
    parens, with -1 reserved for "no parens at all" (i.e. a parameter-less
    macro reference). Empty parens (``\\`name()\\```) yield arity 0.
    """
    cleaned = _strip_comments(spl)
    refs: list[MacroRef] = []
    for m in _MACRO_RE.finditer(cleaned):
        name = m.group("name")
        args = m.group("args")
        if args is None:
            arity = -1
        elif args.strip() == "":
            arity = 0
        else:
            # Naive comma split (doesn't handle nested commas in quoted
            # arguments) — acceptable for vocabulary extraction.
            arity = len([a for a in args.split(",") if a.strip() != ""])
        refs.append(MacroRef(name=name, arity=arity, raw=m.group(0)))
    return refs


def extract_indexes(spl: str) -> list[IndexRef]:
    """Return every ``index=<value>`` predicate in the SPL."""
    cleaned = _strip_comments(spl)
    out: list[IndexRef] = []
    for m in _INDEX_RE.finditer(cleaned):
        raw = m.group("v")
        out.append(IndexRef(value=_unquote(raw), is_wildcard=_is_wildcard(raw)))
    return out


def extract_sourcetypes(spl: str) -> list[SourcetypeRef]:
    """Return every ``sourcetype=<value>`` predicate in the SPL."""
    cleaned = _strip_comments(spl)
    out: list[SourcetypeRef] = []
    for m in _SOURCETYPE_RE.finditer(cleaned):
        raw = m.group("v")
        out.append(SourcetypeRef(value=_unquote(raw), is_wildcard=_is_wildcard(raw)))
    return out


def extract_datamodel_paths(spl: str) -> list[DatamodelRef]:
    """Return every ``datamodel=Model[.Dataset]`` reference in the SPL."""
    cleaned = _strip_comments(spl)
    out: list[DatamodelRef] = []
    for m in _DATAMODEL_RE.finditer(cleaned):
        out.append(
            DatamodelRef(
                model=m.group("model"),
                dataset=m.group("dataset"),
            )
        )
    return out


def extract_lookups(spl: str) -> list[LookupRef]:
    """Return every ``lookup``/``inputlookup``/``outputlookup`` invocation."""
    cleaned = _strip_comments(spl)
    out: list[LookupRef] = []
    for seg in _split_pipes(cleaned):
        m = _LOOKUP_CMD_RE.match(seg)
        if not m:
            continue
        out.append(
            LookupRef(
                name=_unquote(m.group("name")),
                command=m.group("cmd").lower(),
            )
        )
    return out


def extract_commands(spl: str) -> list[str]:
    """Return every per-segment leading command in the SPL.

    Implicit-search predicates of the form ``<field>=<value>`` (e.g.
    ``source="WinEventLog"``, ``index=foo sourcetype=bar``) are NOT
    commands — they're the implicit ``search`` clause. We detect them
    by checking whether the leading identifier is immediately followed
    by ``=`` (after optional whitespace) and skip them.
    """
    cleaned = _strip_comments(spl)
    out: list[str] = []
    for seg in _split_pipes(cleaned):
        m = _CMD_HEAD_RE.match(seg)
        if not m:
            continue
        # Look ahead past the matched identifier to see whether the next
        # non-space character is ``=`` (predicate form).
        tail = seg[m.end() :].lstrip()
        if tail.startswith("="):
            continue
        cmd = m.group("cmd").lower()
        out.append(cmd)
    return out


def _functions_in_segment(seg: str, context: str) -> list[FunctionRef]:
    out: list[FunctionRef] = []
    for fm in _FUNC_CALL_RE.finditer(seg):
        name = fm.group("name").lower()
        # Skip the segment's leading command — we don't want to report the
        # command itself as a function call.
        head = _CMD_HEAD_RE.match(seg)
        if head and fm.start() == head.start("cmd") and name == head.group("cmd").lower():
            continue
        # Skip SQL-ish keywords that appear in `where` clauses.
        if name in {"and", "or", "not", "in", "like", "is"}:
            continue
        out.append(FunctionRef(name=name, context=context))
    return out


def extract_eval_functions(spl: str) -> list[FunctionRef]:
    """Return every function call inside ``eval`` / ``where`` / ``fieldformat`` segments."""
    cleaned = _strip_comments(spl)
    out: list[FunctionRef] = []
    for seg in _split_pipes(cleaned):
        head = _CMD_HEAD_RE.match(seg)
        if not head:
            continue
        cmd = head.group("cmd").lower()
        if cmd in _EVAL_LIKE:
            out.extend(_functions_in_segment(seg, context=cmd))
    return out


def extract_stats_functions(spl: str) -> list[FunctionRef]:
    """Return every aggregator inside ``stats``/``timechart``/``tstats``/etc segments."""
    cleaned = _strip_comments(spl)
    out: list[FunctionRef] = []
    for seg in _split_pipes(cleaned):
        head = _CMD_HEAD_RE.match(seg)
        if not head:
            continue
        cmd = head.group("cmd").lower()
        if cmd in _STATS_LIKE:
            out.extend(_functions_in_segment(seg, context=cmd))
    return out


def extract_all(spl: str) -> Extracted:
    """Run every extractor and return an ``Extracted`` aggregate."""
    return Extracted(
        commands=extract_commands(spl),
        macros=extract_macros(spl),
        sourcetypes=extract_sourcetypes(spl),
        indexes=extract_indexes(spl),
        datamodels=extract_datamodel_paths(spl),
        lookups=extract_lookups(spl),
        eval_functions=extract_eval_functions(spl),
        stats_functions=extract_stats_functions(spl),
    )
