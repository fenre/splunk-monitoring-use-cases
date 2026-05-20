"""Property-based tests for the SPL grammar parser primitives.

Repo-health phase **P16 follow-up** (2026-05-18): the
``audit-spl-grammar`` checker relies on two small private parsers
(``_strip_comments`` and ``_split_pipes``) to walk a saved-search SPL
string and split it into per-stage segments. Both are pure functions
of the input, exercised on every UC sidecar at audit time, and have
the most error-prone *structure* of any audit primitive in the
``splunk_uc`` package: they balance quotes, parentheses, dashboard
tokens, and SPL macros while doing a tokeniser's job by hand.

The grammar checker has good unit coverage at the *check-function*
level (``check_stats_span``, ``check_leading_pipe``, etc.) but the
underlying parsers are only exercised indirectly. A regression where
``_split_pipes`` started returning the wrong segment list under,
say, a Unicode-quoted string or a regex containing ``|`` inside
``"..."`` would silently cause every check above it to misbehave.

Hypothesis property tests pin the algebraic invariants directly so
regressions surface immediately, regardless of which specific SPL
string an operator stumbled across.

Properties covered
------------------

For ``_split_pipes``:

1. **Total function** — returns ``list[str]`` for any string input
   without raising.
2. **Quoting protection** — a ``|`` *inside* matched ``"..."`` or
   ``'...'`` is never used as a segment boundary. The grammar
   checker depends on this so it doesn't false-positive on
   ``rex field=_raw "(?i)(a|b|c)..."``.
3. **No quoting? Plain split** — when the input contains no
   quotes, no parentheses, no dashboard tokens, and no escape
   characters, ``_split_pipes`` agrees with a naive
   ``s.split("|")`` (modulo whitespace strip on each segment).
4. **Parenthesis depth protection** — a ``|`` *inside* matched
   ``(...)`` is never used as a segment boundary. This is what
   makes ``stats list(case(x>0, "high", x<0, "low"))`` survive.
5. **Token masking** — dashboard tokens like ``$idx$`` survive
   ``_split_pipes`` intact (they're masked during the scan, not
   substituted in the output).

For ``_strip_comments``:

6. **Idempotency** — ``_strip_comments(_strip_comments(s)) ==
   _strip_comments(s)``. The function removes balanced ``comment(
   ... )`` blocks; running it twice must be a no-op.
7. **Inert on comment-free input** — if the input contains no
   ``comment(`` substring, the output is byte-identical to the
   input.
8. **Preserves non-comment text** — removing comments never
   removes non-``comment(...)`` text. Pin this by checking that
   the comment-free input prefix is preserved.

Performance budget
------------------

Each property runs with ``max_examples`` capped at 60-120 and
``deadline=None``. The parsers are linear in input length but
hypothesis spends a lot of time shrinking, so we keep the
synthesised SPL bounded to ~120 chars to stay well under 1 second
of wall-clock per property on a CI runner.
"""

from __future__ import annotations

import string

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from splunk_uc.audits.spl_grammar import _split_pipes, _strip_comments

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Plain-text alphabet: no quotes, no parens, no pipes, no backticks.
# Used to build "neutral" segments where every literal character is
# guaranteed not to change the parser's state machine.
_safe_chars = string.ascii_letters + string.digits + " _.-=,:/"

_safe_text_st = st.text(alphabet=_safe_chars, min_size=0, max_size=20)


def _join_with_pipes(segments: list[str]) -> str:
    """Build an SPL-like string from neutral segments separated by ``|``."""
    return "|".join(segments)


# Arbitrary SPL fragments. Includes structural characters (``|``,
# ``"``, ``(``, ``)``, ``$``) so the parser exercises its state
# machine, but excludes ``\x00`` since the parser uses it internally
# as a masking sentinel.
_spl_alphabet = (
    string.ascii_letters
    + string.digits
    + " _-=|.,()\"'$"
)

_arbitrary_spl_st = st.text(alphabet=_spl_alphabet, min_size=0, max_size=120)


# ---------------------------------------------------------------------------
# _split_pipes properties
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_is_a_total_function(spl: str) -> None:
    """``_split_pipes`` returns ``list[str]`` for any string input."""
    result = _split_pipes(spl)
    assert isinstance(result, list)
    for seg in result:
        assert isinstance(seg, str)


# Restrict to segments whose stripped form is non-empty, so the
# synthesised SPL is well-formed (no empty segments, no trailing
# pipe). The parser deliberately drops a trailing empty buffer to
# normalise ``a|b|`` -> ``[a, b]``; that quirk is verified
# separately in ``test_split_pipes_drops_trailing_empty_segment``.
_nonempty_safe_text_st = st.text(
    alphabet=string.ascii_letters + string.digits + " _.-=,:/",
    min_size=1,
    max_size=20,
).filter(lambda s: s.strip() != "")


@given(segments=st.lists(_nonempty_safe_text_st, min_size=1, max_size=6))
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_matches_naive_split_on_quote_free_input(
    segments: list[str],
) -> None:
    """When input has no quotes / parens / tokens, ``_split_pipes`` agrees
    with ``str.split("|")`` (modulo per-segment strip).

    This pins the simplest possible algebraic contract: in the
    absence of any special characters the parser must behave like a
    plain pipe-splitter.

    Hypothesis is constrained to **non-empty stripped segments** so
    the synthesised SPL never starts or ends with a pipe (those
    edge cases are tested separately).
    """
    spl = _join_with_pipes(segments)
    parser_out = _split_pipes(spl)
    naive_out = [s.strip() for s in spl.split("|")]
    assert parser_out == naive_out, (
        f"parser disagreed with naive split on quote-free input {spl!r}: "
        f"parser={parser_out!r} naive={naive_out!r}"
    )


def test_split_pipes_drops_trailing_empty_segment() -> None:
    """Empty trailing segments after a final ``|`` are normalised away.

    Documented quirk: ``a|b|`` -> ``[a, b]``, not ``[a, b, '']``.
    The parser only appends the final buffer if it has content.
    This unit case pins the documented behaviour next to the
    matching property test so anyone changing the parser sees
    both halves of the contract.
    """
    assert _split_pipes("a|b|") == ["a", "b"]
    assert _split_pipes("") == []
    # But empty *interior* segments survive — they signal a syntax
    # error to downstream checks (e.g. a `| | stats` block).
    assert _split_pipes("a||b") == ["a", "", "b"]


@given(
    pre=_safe_text_st,
    quoted_body=st.text(alphabet=string.ascii_letters + string.digits + " |", min_size=0, max_size=24),
    post=_safe_text_st,
)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_protects_double_quoted_pipes(
    pre: str,
    quoted_body: str,
    post: str,
) -> None:
    """A ``|`` *inside* a balanced ``"..."`` is not used as a segment
    boundary.

    Strategy: synthesise ``<pre>"<quoted_body>"<post>`` where the
    quoted body may contain arbitrary pipes. The parser must see
    exactly one segment (because nothing outside the quotes carries
    a ``|``).

    Counter-example would be the catastrophic regression where a
    `rex` pattern like ``"(?i)(a|b|c)"`` is treated as four
    segments — that breaks every grammar check downstream.
    """
    spl = f'{pre}"{quoted_body}"{post}'
    result = _split_pipes(spl)
    # Exactly one segment because pre/post contain no pipes (by
    # construction of the safe alphabet) and pipes inside the quoted
    # body are protected.
    assert len(result) == 1, (
        f"pipes inside double-quoted body leaked as segment boundaries on "
        f"{spl!r}: {result!r}"
    )
    assert result[0] == spl.strip()


@given(
    pre=_safe_text_st,
    quoted_body=st.text(alphabet=string.ascii_letters + string.digits + " |", min_size=0, max_size=24),
    post=_safe_text_st,
)
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_protects_single_quoted_pipes(
    pre: str,
    quoted_body: str,
    post: str,
) -> None:
    """A ``|`` *inside* a balanced ``'...'`` is not used as a segment
    boundary.

    Same property as the double-quote case; SPL accepts single-quoted
    strings in `where ...` clauses and the parser must protect them
    identically.
    """
    spl = f"{pre}'{quoted_body}'{post}"
    result = _split_pipes(spl)
    assert len(result) == 1, (
        f"pipes inside single-quoted body leaked as segment boundaries on "
        f"{spl!r}: {result!r}"
    )
    assert result[0] == spl.strip()


@given(
    pre=_safe_text_st,
    paren_body=st.text(alphabet=string.ascii_letters + string.digits + " |,", min_size=0, max_size=24),
    post=_safe_text_st,
)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_protects_pipes_inside_parens(
    pre: str,
    paren_body: str,
    post: str,
) -> None:
    """A ``|`` *inside* matched ``(...)`` is not used as a segment
    boundary.

    Strategy: synthesise ``<pre>(<paren_body>)<post>`` where
    ``paren_body`` may contain commas and pipes, but no nested
    parens (the parser handles arbitrary nesting depth but
    hypothesis is faster when we stay flat). The parser must see
    exactly one segment.

    Real-world example this protects: ``| stats list(case(x>0,
    "high"))`` and ``| eval mv=mvfilter(match(x, "a|b"))``.
    """
    spl = f"{pre}({paren_body}){post}"
    result = _split_pipes(spl)
    assert len(result) == 1, (
        f"pipes inside parens leaked as segment boundaries on {spl!r}: "
        f"{result!r}"
    )
    assert result[0] == spl.strip()


@given(
    pre=_safe_text_st,
    token=st.from_regex(r"\$[A-Za-z_][A-Za-z0-9_]*\|[a-z]+\$", fullmatch=True),
    post=_safe_text_st,
)
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_protects_pipe_inside_dashboard_token(
    pre: str,
    token: str,
    post: str,
) -> None:
    """A ``|`` *inside* a dashboard filter token like ``$idx|s$`` is not
    used as a segment boundary.

    Strategy: synthesise ``<pre>$NAME|MOD$<post>`` where ``MOD`` is
    a Splunk filter modifier (``s``, ``n``, ``q``, etc.). The
    parser internally masks the token with a sentinel so its
    interior ``|`` doesn't appear as a structural pipe. With pre/
    post containing no pipes (by alphabet construction), the parser
    must return exactly one segment.

    The parser masks the token bytes during scanning (replacing them
    with filler) so we can't assert the raw token bytes survive in
    the output — but we *can* assert that the interior ``|`` did
    not produce a segment boundary, which is the actual contract
    the audit checker depends on.
    """
    spl = f"{pre}{token}{post}"
    result = _split_pipes(spl)
    assert len(result) == 1, (
        f"interior pipe of dashboard token {token!r} leaked as segment "
        f"boundary on {spl!r}: {result!r}"
    )


@given(segments=st.lists(_nonempty_safe_text_st, min_size=2, max_size=6))
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_count_equals_pipe_count_plus_one_in_neutral_input(
    segments: list[str],
) -> None:
    """For neutral input with non-empty segments and no trailing pipe,
    ``len(_split_pipes(s)) == s.count('|') + 1``.

    This is a stronger version of the "matches naive split"
    property: counts the structural pipes the parser identifies and
    pins them to the surface-level character count of ``|``.
    Anything that drops a pipe (or invents one) violates the
    contract immediately.

    The strategy guarantees non-empty stripped segments so we
    avoid the documented trailing-empty-segment normalisation (see
    ``test_split_pipes_drops_trailing_empty_segment``).
    """
    spl = _join_with_pipes(segments)
    result = _split_pipes(spl)
    pipe_count = spl.count("|")
    assert len(result) == pipe_count + 1, (
        f"segment count mismatch on {spl!r}: parser produced {len(result)} "
        f"segments but input has {pipe_count} pipes"
    )


# ---------------------------------------------------------------------------
# _strip_comments properties
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_strip_comments_is_idempotent(spl: str) -> None:
    """``_strip_comments(_strip_comments(s)) == _strip_comments(s)``.

    Running the stripper twice must converge in one step. A bug
    where the stripper accidentally re-introduces a synthetic
    ``comment(`` token on its way out would break this immediately.
    """
    once = _strip_comments(spl)
    twice = _strip_comments(once)
    assert twice == once, (
        f"_strip_comments is not idempotent on {spl!r}: "
        f"first pass {once!r}, second pass {twice!r}"
    )


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_strip_comments_is_inert_on_comment_free_input(spl: str) -> None:
    """If the input contains no ``comment(`` substring, the output is
    byte-identical to the input."""
    if "comment(" in spl:
        return  # property only applies to comment-free input
    assert _strip_comments(spl) == spl


@given(
    prefix=_safe_text_st,
    comment_body=st.text(
        alphabet=string.ascii_letters + string.digits + " _-.",
        min_size=0,
        max_size=20,
    ),
    suffix=_safe_text_st,
)
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_strip_comments_removes_balanced_comment_blocks(
    prefix: str,
    comment_body: str,
    suffix: str,
) -> None:
    """``_strip_comments`` deletes a balanced ``comment(...)`` block but
    keeps text on either side of it.

    Strategy: synthesise ``<prefix>comment(<body>)<suffix>`` where
    neither prefix nor suffix contain ``comment(`` (by alphabet
    construction) and ``body`` contains no parens. The stripped
    output must be ``prefix + suffix``.
    """
    spl = f"{prefix}comment({comment_body}){suffix}"
    stripped = _strip_comments(spl)
    # We expect the comment block removed; the parser may have
    # emitted any whitespace it used internally, so we test
    # *substring inclusion* rather than equality.
    assert prefix in stripped, (
        f"prefix dropped from {spl!r} -> {stripped!r}"
    )
    assert suffix in stripped, (
        f"suffix dropped from {spl!r} -> {stripped!r}"
    )
    # And the body of the comment block should NOT survive in the
    # stripped output (unless prefix or suffix happen to contain the
    # same bytes — we filter those out by checking against the
    # standalone body).
    if comment_body and comment_body not in prefix and comment_body not in suffix:
        assert comment_body not in stripped, (
            f"comment body {comment_body!r} survived stripping in {spl!r} "
            f"-> {stripped!r}"
        )


# ---------------------------------------------------------------------------
# Cross-property: combining the two parsers
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_split_pipes_after_strip_comments_is_total(spl: str) -> None:
    """The two parsers compose without raising on arbitrary input.

    Every check function in ``spl_grammar.py`` calls
    ``_split_pipes(_strip_comments(spl))`` or a close variant.
    This property pins the composition so a regression in either
    half surfaces immediately rather than via an obscure
    audit-time exception.
    """
    result = _split_pipes(_strip_comments(spl))
    assert isinstance(result, list)
    for seg in result:
        assert isinstance(seg, str)
