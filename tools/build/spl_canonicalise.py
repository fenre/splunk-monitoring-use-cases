r"""SPL canonicalisation and fingerprinting (v9.0).

The recommender's auto-detect side hashes every saved-search SPL string in
the local Splunk environment and joins it against a CSV of pre-computed UC
fingerprints (``splunk-apps/splunk-uc-recommender/lookups/uc_fingerprints
.csv``). To make the join meaningful the SPL must first be reduced to a
**canonical form** so two semantically-equivalent searches collapse to the
same hash.

Algorithm (from ``uc_recommender_v9_447c7cf7.plan.md`` § 6a.1, written here
so the source can stand alone):

    1.  Strip comments — triple-backtick block comments and single-
        backtick inline comments.
    2.  Resolve macros — backtick-wrapped ``macro_name`` references ->
        literal text via the caller-supplied resolver. Unresolvable
        macros become ``?``. The default resolver substitutes ``?`` so
        the canonicaliser is hermetic.
    3.  Resolve dashboard tokens — ``$index$``, ``$sourcetype$``, etc.
        -> ``*``.
    4.  Normalise whitespace — collapse runs to a single space; strip
        leading/trailing whitespace per pipe stage; no whitespace around
        ``|``, ``=``, ``,``.
    5.  Lower-case keywords — ``BY``, ``AS``, ``WHERE``, ``OR``, ``AND``,
        ``NOT`` (case-insensitive). Field names and string literals are
        case-preserving.
    6.  Canonicalise quoting — bare-word string values become
        ``"value"``; backslash-escape any embedded ``"``. Already-
        quoted values are left as-is (after normalising the quote
        character to ``"``).
    7.  Sort ``key=value`` pairs lexicographically within each search
        clause (the part before the first ``|``). E.g.
        ``index=foo sourcetype=bar`` and ``sourcetype=bar index=foo``
        collide.
    8.  Drop operator tweaks — ``| head N``, ``| tail N``,
        ``| dedup N field``, ``| eventstats count`` (only when the
        latter is the last stage — operators add it during testing).
    9.  Normalise comparison operators — ``==`` -> ``=``. ``<>``
        collapses to ``!=``.
    10. SHA-256 hex-encoded; this is the fingerprint.

The canonicaliser is **deliberately approximate**: false-positives (two
different searches collapsing to the same hash) are acceptable because the
operator confirms a match via the dashboard's deep-link to the saved
search's name. Silent false-negatives (an equivalent search missing the
match) are the failure mode we work hardest to avoid, so case folding and
key=value sorting are aggressive.

Stdlib-only by design — the build pipeline deliberately avoids runtime
dependencies (cf. ``pyproject.toml`` ``dependencies = []``) so a fresh CI
runner can produce ``dist/`` without ``pip install``.

CLI::

    python -m tools.build.spl_canonicalise canonicalise '<spl>'
    python -m tools.build.spl_canonicalise fingerprint '<spl>'
    python -m tools.build.spl_canonicalise compare '<a>' '<b>'
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from typing import Callable, Optional

__all__ = [
    "canonicalise",
    "fingerprint",
    "MacroResolver",
]


MacroResolver = Callable[[str], Optional[str]]
"""Maps a macro name (without surrounding backticks) -> literal text or None.

``None`` (or an exception) signals "unresolvable" — the canonicaliser
substitutes the placeholder ``?`` so the rest of the SPL still hashes.
The default resolver (``_default_macro_resolver``) always returns ``None``
so the canonicaliser is hermetic; callers that want richer behaviour can
pass their own (typically by reading ``data/macros.csv`` or hitting
``| rest /services/data/macros`` at build time).
"""


# Comment patterns: ```block``` and `inline` (single backtick).
# Both can span the whole search; we strip greedily but keep the rest.
# Splunk supports ``` ... ``` for multi-line comments and `comment` for
# single-token inline comments.
_BLOCK_COMMENT_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_COMMENT_RE = re.compile(r"`[^`]*`")

# Macro reference: `macro_name` or `macro_name(arg1, arg2)`.
# We've already stripped backtick comments above, so any remaining `...`
# token is a macro invocation.
_MACRO_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)(?:\([^`)]*\))?`")

# Dashboard token: $name$. Trailing `|s` etc. variants strip together.
_TOKEN_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*(?:\|[a-z]+)?\$")

# Comparison operators we collapse: == -> =, <> -> !=.
# (We keep > >= < <= != as-is.)
_DOUBLE_EQ_RE = re.compile(r"==")
_NEQ_ANGLE_RE = re.compile(r"<>")

# SPL keyword boundaries we case-fold. Word boundaries on both sides keep
# us from rewriting field names that happen to match (e.g. ``by_pid``).
_KEYWORDS = ("BY", "AS", "WHERE", "OR", "AND", "NOT", "IN", "WITH")
_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Operator tweak commands we drop entirely. These are debug commands
# operators add while iterating, never part of the use-case definition.
_OPERATOR_TWEAK_HEAD_TAIL_RE = re.compile(
    r"\s*\|\s*(?:head|tail)\b[^|]*",
    re.IGNORECASE,
)
_OPERATOR_TWEAK_DEDUP_N_RE = re.compile(
    r"\s*\|\s*dedup\s+\d+\b[^|]*",
    re.IGNORECASE,
)
_TRAILING_EVENTSTATS_COUNT_RE = re.compile(
    r"\s*\|\s*eventstats\s+count\b[^|]*$",
    re.IGNORECASE,
)


def _default_macro_resolver(_name: str) -> Optional[str]:
    """Hermetic default — every macro resolves to ``?``."""
    return None


def _strip_block_comments(spl: str) -> str:
    """Drop triple-backtick block comments only.

    Inline backtick tokens that look like macro references survive this
    pass; ``_strip_inline_comments`` cleans them up later (after macro
    resolution).
    """
    return _BLOCK_COMMENT_RE.sub(" ", spl)


def _strip_inline_comments(spl: str) -> str:
    """Drop remaining single-backtick comments.

    Called *after* macro resolution so macro-shaped backtick tokens
    (which are identifier-only) get a chance to expand first; anything
    that remains is a free-form ``inline note`` and gets stripped.
    """
    return _INLINE_COMMENT_RE.sub(" ", spl)


def _resolve_macros(spl: str, resolver: MacroResolver) -> str:
    r"""Substitute literal text for backtick-wrapped macro references.

    Unresolvable macros (resolver returns ``None``, raises, or the SPL
    contains nested macros) collapse to a literal ``?`` so the rest of
    the canonical form survives. The resolver is run on the original
    macro name only; arguments inside ``\`name(arg1)\`-`` are dropped
    before resolution because the recommender doesn't have access to
    runtime macro arg values.

    Note: backtick comments have already been stripped by
    ``_strip_comments`` before this runs, so any remaining backtick-
    wrapped tokens really are macro references.
    """

    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        try:
            literal = resolver(name)
        except Exception:  # noqa: BLE001 - hermetic fallback
            literal = None
        if not isinstance(literal, str):
            return "?"
        return literal

    # Re-run until fixed-point so macros that expand to other macros also
    # resolve. Bound the loop so a pathological recursive macro can't
    # hang the build.
    for _ in range(8):
        replaced = _MACRO_RE.sub(_sub, spl)
        if replaced == spl:
            return spl
        spl = replaced
    return spl


def _resolve_tokens(spl: str) -> str:
    """Replace ``$dashboard_token$`` references with ``*`` placeholders."""
    return _TOKEN_RE.sub("*", spl)


def _normalise_comparisons(spl: str) -> str:
    """``==`` -> ``=``; ``<>`` -> ``!=``."""
    spl = _DOUBLE_EQ_RE.sub("=", spl)
    return _NEQ_ANGLE_RE.sub("!=", spl)


def _lowercase_keywords(spl: str) -> str:
    """Force SPL keywords to lower case while leaving everything else alone.

    Splunk treats ``BY`` and ``by`` as the same token but operators write
    them inconsistently across saved searches; the fingerprint must be
    insensitive to this.
    """
    return _KEYWORD_RE.sub(lambda m: m.group(0).lower(), spl)


def _canonicalise_quoting(token: str) -> str:
    """Wrap a bare-word value in double quotes, normalising quote style.

    * ``foo`` -> ``"foo"``
    * ``"foo"`` -> ``"foo"`` (unchanged)
    * ``'foo'`` -> ``"foo"`` (single-quote -> double-quote)
    * ``foo bar`` -> ``"foo bar"`` (interior whitespace forces quoting)
    * Already-quoted values containing ``"`` get the embedded quote
      backslash-escaped.

    String values that look like wildcard expressions (``foo*``,
    ``*foo*``) and numeric literals are quoted too so the canonical form
    is uniform; consumers can strip surrounding quotes if they need the
    bare value.
    """
    s = token.strip()
    if not s:
        return s
    if s[0] == '"' and s[-1] == '"':
        return s
    if s[0] == "'" and s[-1] == "'":
        # Re-emit as double-quoted to keep one quote style.
        body = s[1:-1].replace('"', '\\"')
        return f'"{body}"'
    body = s.replace('"', '\\"')
    return f'"{body}"'


# Match key=value pairs where the key is an identifier and the value is
# either a quoted string, a wildcard expression, or a bare word. Inside
# a search clause we tokenise on whitespace and reassemble after sorting.
_SEARCH_KV_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_.\-]*)\s*"  # key
    r"(=|!=|>=|<=|>|<)\s*"             # operator
    r"("
    r'"(?:\\.|[^"\\])*"'               # double-quoted string
    r"|'(?:\\.|[^'\\])*'"              # single-quoted string
    r"|[^\s|]+"                         # bare word
    r")"
)


def _normalise_search_clause(clause: str) -> str:
    """Sort ``key=value`` pairs and canonicalise quoting in a search clause.

    The "search clause" is everything before the first ``|`` (or the whole
    SPL if there are no pipes). Sorting kv pairs collapses
    ``index=foo sourcetype=bar`` and ``sourcetype=bar index=foo`` to the
    same canonical string; bare positional terms (``error``, wildcard
    patterns, etc.) keep their relative order so phrase semantics aren't
    accidentally rewritten.
    """
    if not clause.strip():
        return ""

    pairs: list[tuple[str, str]] = []
    bare_positions: list[tuple[int, str]] = []
    cursor = 0
    out: list[str] = []
    for match in _SEARCH_KV_RE.finditer(clause):
        between = clause[cursor:match.start()]
        if between.strip():
            for tok in between.split():
                bare_positions.append((len(out), tok))
                out.append(tok)
        key = match.group(1).lower()
        op = match.group(2)
        value = _canonicalise_quoting(match.group(3))
        pairs.append((f"{key}{op}", value))
        cursor = match.end()
    trailing = clause[cursor:]
    if trailing.strip():
        for tok in trailing.split():
            bare_positions.append((len(out), tok))
            out.append(tok)

    # Sort kv pairs lexicographically by key+op, then by value for
    # determinism on duplicate keys.
    pairs.sort(key=lambda kv: (kv[0], kv[1]))

    rendered_pairs = [f"{key_op}{value}" for key_op, value in pairs]
    rendered = " ".join(out + rendered_pairs)
    return rendered.strip()


def _drop_operator_tweaks(spl: str) -> str:
    """Drop debug commands operators sprinkle into searches.

    ``| head N``, ``| tail N``, ``| dedup N field``, and a trailing
    ``| eventstats count`` are all common while iterating and rarely
    part of the use-case-defining pipeline.
    """
    spl = _OPERATOR_TWEAK_HEAD_TAIL_RE.sub("", spl)
    spl = _OPERATOR_TWEAK_DEDUP_N_RE.sub("", spl)
    return _TRAILING_EVENTSTATS_COUNT_RE.sub("", spl)


def _normalise_whitespace(spl: str) -> str:
    """Collapse runs of whitespace; tighten around ``|``, ``=``, ``,``.

    The result has at most one space between any two non-whitespace
    tokens, never any whitespace around ``|`` / ``=`` / ``,``, and no
    leading or trailing whitespace overall.
    """
    spl = re.sub(r"\s+", " ", spl)
    # Remove whitespace adjacent to structural punctuation.
    spl = re.sub(r"\s*\|\s*", "|", spl)
    spl = re.sub(r"\s*,\s*", ",", spl)
    # Collapse whitespace around comparison operators (longest first so
    # `>=` is preferred over a stray `>`). Note: kv= pairs in the search
    # clause are already canonicalised by ``_normalise_search_clause``;
    # this catches the same operators in later pipe stages (e.g. inside
    # ``where``).
    spl = re.sub(r"\s*(>=|<=|!=|==|=|>|<)\s*", r"\1", spl)
    return spl.strip()


def canonicalise(
    spl: str,
    *,
    macro_resolver: Optional[MacroResolver] = None,
    drop_operator_tweaks: bool = True,
) -> str:
    """Return the canonical form of ``spl``.

    Idempotent: ``canonicalise(canonicalise(s)) == canonicalise(s)``.
    Output is suitable for hashing or for textual diffing — there are no
    timestamps, no random elements, no caller-specific state baked in.

    Stages run in the order specified in ``§ 6a.1`` of the v9.0 plan:
    strip comments -> resolve macros -> resolve tokens -> normalise
    comparison operators -> sort and quote-normalise the search clause
    -> lower-case keywords -> drop operator tweaks (optional) -> tighten
    whitespace.

    ``macro_resolver`` is consulted with each macro name (without
    surrounding backticks). Returning ``None`` collapses the macro to
    ``?`` so unresolved macros don't break the canonical form.
    ``drop_operator_tweaks`` defaults to ``True`` to match the spec; set
    it to ``False`` to keep ``head``/``tail``/``dedup N``/trailing
    ``eventstats count`` (handy in tests that need the raw pipeline).
    """
    if not isinstance(spl, str):
        raise TypeError(f"canonicalise() expected str, got {type(spl).__name__}")
    resolver = macro_resolver or _default_macro_resolver

    spl = _strip_block_comments(spl)
    spl = _resolve_macros(spl, resolver)
    spl = _strip_inline_comments(spl)
    spl = _resolve_tokens(spl)
    spl = _normalise_comparisons(spl)

    # Split on `|` while preserving order for downstream stages. The
    # first stage is the search clause (subject to kv sorting); later
    # stages keep their token order — sorting them would change SPL
    # semantics (`stats count by foo` is not the same as
    # `stats by foo count`).
    stages = spl.split("|")
    if stages:
        head, *rest = stages
        head = _normalise_search_clause(head)
        stages = [head, *(s.strip() for s in rest)]

    spl = "|".join(stages)
    spl = _lowercase_keywords(spl)
    if drop_operator_tweaks:
        spl = _drop_operator_tweaks(spl)
    return _normalise_whitespace(spl)


def fingerprint(
    spl: str,
    *,
    macro_resolver: Optional[MacroResolver] = None,
    drop_operator_tweaks: bool = True,
) -> str:
    """Hex SHA-256 of ``canonicalise(spl, ...)``.

    The 64-character return value is what
    ``splunk-apps/splunk-uc-recommender/lookups/uc_fingerprints.csv``
    stores per UC and what the saved-search fingerprint scan computes
    against ``| rest /services/saved/searches`` rows at runtime.
    """
    canonical = canonicalise(
        spl,
        macro_resolver=macro_resolver,
        drop_operator_tweaks=drop_operator_tweaks,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spl_canonicalise",
        description=(
            "Canonicalise / fingerprint SPL strings for the v9.0 "
            "recommender. Stdlib-only; safe to run inside a hermetic "
            "build."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    can = sub.add_parser(
        "canonicalise",
        help="Print the canonical form of an SPL string.",
    )
    can.add_argument("spl", help="SPL string (use single-quotes in shells)")
    can.add_argument(
        "--keep-tweaks",
        action="store_true",
        help="Skip dropping head/tail/dedup-N/trailing eventstats count.",
    )

    fp = sub.add_parser(
        "fingerprint",
        help="Print the SHA-256 fingerprint of the canonical form.",
    )
    fp.add_argument("spl", help="SPL string")
    fp.add_argument("--keep-tweaks", action="store_true")

    cmp_ = sub.add_parser(
        "compare",
        help="Print equivalence (yes/no) and both canonical forms.",
    )
    cmp_.add_argument("a", help="First SPL string")
    cmp_.add_argument("b", help="Second SPL string")
    cmp_.add_argument("--keep-tweaks", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv)
    drop = not getattr(args, "keep_tweaks", False)
    if args.command == "canonicalise":
        print(canonicalise(args.spl, drop_operator_tweaks=drop))
        return 0
    if args.command == "fingerprint":
        print(fingerprint(args.spl, drop_operator_tweaks=drop))
        return 0
    if args.command == "compare":
        ca = canonicalise(args.a, drop_operator_tweaks=drop)
        cb = canonicalise(args.b, drop_operator_tweaks=drop)
        print(f"a: {ca}")
        print(f"b: {cb}")
        equal = ca == cb
        print(f"equivalent: {'yes' if equal else 'no'}")
        return 0 if equal else 1
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
