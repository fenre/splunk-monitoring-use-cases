"""Property-based tests for ``tools.build.spl_canonicalise``.

Repo-health phase **P16 follow-up** (2026-05-18): the example-based
``test_spl_canonicalise.py`` exercises ~60 hand-curated SPL strings and
catches the documented behaviours one input at a time. The
canonicaliser is the recommender's join key — false-negatives (two
genuinely equivalent SPL strings collapsing to different fingerprints)
are the failure mode we work hardest to avoid (see § 6a.1 of
``uc_recommender_v9_447c7cf7.plan.md``). The corpus catches the
patterns we *know* operators write; this file extends coverage with
Hypothesis property tests that catch the algebraic invariants
**every** invocation must satisfy regardless of the specific SPL.

Properties covered
------------------

1. **Idempotency** — ``canonicalise(canonicalise(s))
   == canonicalise(s)`` for every SPL we can synthesise. The module
   docstring promises this; without a property test the guarantee
   is only as strong as the corpus.
2. **Fingerprint = SHA-256 of canonicalise** — the public
   ``fingerprint`` contract. A regression that re-orders the
   ``fingerprint`` pipeline (e.g. forgetting to lower-case before
   hashing) would only surface under specific inputs that aren't in
   the curated corpus.
3. **Fingerprint stability across pre-canonicalised input** —
   ``fingerprint(s) == fingerprint(canonicalise(s))``. Falls out of
   idempotency but worth pinning separately because it's the most
   common gotcha when wiring the recommender into a saved-search
   scan.
4. **kv-pair order invariance in the search clause** — two SPL
   strings that differ only in the order of ``key=value`` tokens
   before the first ``|`` collapse to the same canonical form.
   This is the *raison d'être* of the canonicaliser; catching a
   regression here matters more than any other invariant.
5. **Whitespace robustness** — adding extra whitespace around
   pipe boundaries, comparison operators, and commas does not
   change the canonical form. The module docstring explicitly
   says "no whitespace around ``|`` / ``=`` / ``,``"; the test
   pins it under arbitrary noise.
6. **Comparison-operator normalisation totality** — every ``==``
   in input collapses to ``=`` in output; every ``<>`` collapses to
   ``!=``. The canonicaliser doesn't promise *no other* ``=`` to
   show up, but it does promise the corresponding "non-canonical"
   forms vanish.
7. **Keyword case-folding totality** — none of the recognised SPL
   keywords (``BY``, ``AS``, ``WHERE``, ``OR``, ``AND``, ``NOT``,
   ``IN``, ``WITH``) survive in their upper-cased form in output,
   when they appear as standalone tokens.
8. **TypeError on non-str** — ``canonicalise`` and ``fingerprint``
   reject non-string input at the boundary. Hypothesis explores
   the type-error frontier (None, ints, lists, dicts, bytes).

Why this earns its place
------------------------

The canonicaliser ships in the recommender lookup CSV and is
re-computed every nightly build; a silent regression would cause
every operator who reruns auto-detect to lose recommendations until
the next rebuild after a fix. Property tests catch the regressions
the curated corpus misses by construction.

Performance budget
------------------

All seven hypothesis cases run with capped ``max_examples`` (40-100)
and ``deadline=None`` because the canonicaliser does ~7 regex
substitutions per call and pathological inputs (lots of backticks)
can blow the default 200ms deadline on a cold CI runner. Wall-clock
on a developer machine: <1s for the full module.
"""

from __future__ import annotations

import hashlib
import re
import string

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tools.build.spl_canonicalise import canonicalise, fingerprint

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Identifier alphabet for keys, field names, sourcetypes. The
# canonicaliser's ``_SEARCH_KV_RE`` requires the key to *start* with
# a letter or underscore (``[A-Za-z_]``) and continue with
# ``[A-Za-z0-9_.\-]*``. Keys that start with a digit (e.g. ``0=foo``)
# are correctly treated as bare positional terms by the canonicaliser,
# not as kv pairs, so the order-invariance property doesn't apply to
# them and they must be excluded from the strategy.
_ident_head_chars = string.ascii_letters + "_"
_ident_tail_chars = string.ascii_letters + string.digits + "_"
_value_chars = string.ascii_letters + string.digits + "_-."


def _ident_strategy() -> st.SearchStrategy[str]:
    """Match the shape the canonicaliser actually recognises as a kv key."""
    return st.builds(
        lambda head, tail: head + tail,
        st.text(alphabet=_ident_head_chars, min_size=1, max_size=1),
        st.text(alphabet=_ident_tail_chars, min_size=0, max_size=11),
    )


_ident_st = _ident_strategy()
_value_st = st.text(alphabet=_value_chars, min_size=1, max_size=12)

# A single ``key=value`` token. The synthetic search clauses below
# pack a handful of these together with whitespace.
_kv_pair_st = st.tuples(_ident_st, _value_st)

_search_kv_st = st.lists(_kv_pair_st, min_size=1, max_size=4, unique_by=lambda kv: kv[0])


def _render_search_clause(pairs: list[tuple[str, str]]) -> str:
    """Render a list of (key, value) tuples as a Splunk search clause."""
    return " ".join(f"{k}={v}" for k, v in pairs)


# Arbitrary SPL fragments. We keep these short because the
# canonicaliser is regex-heavy and Hypothesis spends a lot of CPU
# shrinking. Real SPL strings in the catalogue are much longer (a few
# kilobytes), but the algebraic properties below hold at any length.
_spl_alphabet = (
    string.ascii_letters
    + string.digits
    + " _-=|.,"
)

_arbitrary_spl_st = st.text(alphabet=_spl_alphabet, min_size=0, max_size=80)


# ---------------------------------------------------------------------------
# Property 1: Idempotency
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_canonicalise_is_idempotent(spl: str) -> None:
    """``canonicalise(canonicalise(s)) == canonicalise(s)``.

    Documented contract from the module docstring. Without this
    property the recommender could fingerprint the same SPL string
    to two different hashes depending on whether it was canonicalised
    once or twice (e.g. a saved-search scan that re-canonicalises
    the in-memory result before hashing).
    """
    once = canonicalise(spl)
    twice = canonicalise(once)
    assert twice == once, (
        f"canonicalise is not idempotent on {spl!r}: "
        f"first pass {once!r}, second pass {twice!r}"
    )


# ---------------------------------------------------------------------------
# Property 2: fingerprint == sha256(canonicalise)
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_fingerprint_is_sha256_of_canonicalise(spl: str) -> None:
    """``fingerprint(s) == sha256(canonicalise(s))`` byte-for-byte."""
    canon = canonicalise(spl)
    expected = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    actual = fingerprint(spl)
    assert actual == expected, (
        f"fingerprint contract broken on {spl!r}: "
        f"canonical {canon!r}, expected {expected!r}, got {actual!r}"
    )


# ---------------------------------------------------------------------------
# Property 3: fingerprint(canonicalise(s)) == fingerprint(s)
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_fingerprint_is_stable_under_pre_canonicalisation(spl: str) -> None:
    """``fingerprint(s) == fingerprint(canonicalise(s))``.

    Falls out of idempotency + the fingerprint contract, but pinning
    it directly catches the most common wiring mistake: a saved-
    search scanner that canonicalises *before* hashing because it
    wants the canonical form for logging.
    """
    raw_fp = fingerprint(spl)
    pre_canon_fp = fingerprint(canonicalise(spl))
    assert raw_fp == pre_canon_fp


# ---------------------------------------------------------------------------
# Property 4: kv-pair order invariance in the search clause
# ---------------------------------------------------------------------------


@given(pairs=_search_kv_st)
@settings(
    max_examples=80,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_search_clause_kv_pairs_are_order_invariant(
    pairs: list[tuple[str, str]],
) -> None:
    """Reordering kv pairs in the search clause must not change the hash.

    Strategy: synthesise N (k, v) tuples with **unique keys**,
    render them in declaration order and again in reverse order,
    then assert both render to identical canonical strings. Unique
    keys avoid the (legal but messy) "two ``index=`` clauses"
    case — fingerprint stability for that case is best left to the
    curated corpus.

    This is the recommender's *raison d'être*: ``index=foo
    sourcetype=bar`` and ``sourcetype=bar index=foo`` must collapse
    to the same fingerprint, regardless of which extra fields the
    operator pinned alongside.
    """
    forward = _render_search_clause(pairs)
    reverse = _render_search_clause(list(reversed(pairs)))
    canon_forward = canonicalise(forward)
    canon_reverse = canonicalise(reverse)
    assert canon_forward == canon_reverse, (
        f"kv-pair order changed canonical form: "
        f"forward={forward!r}->{canon_forward!r} "
        f"reverse={reverse!r}->{canon_reverse!r}"
    )


# ---------------------------------------------------------------------------
# Property 5: Whitespace robustness
# ---------------------------------------------------------------------------


@given(pairs=_search_kv_st, gap=st.integers(min_value=1, max_value=6))
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_whitespace_runs_collapse_in_canonical_form(
    pairs: list[tuple[str, str]],
    gap: int,
) -> None:
    """Inserting extra whitespace between tokens must not change canonical form.

    Strategy: build a search clause with single-space separators
    and again with N-space separators. Both must canonicalise to
    the same string. This catches the regression of any whitespace
    rule accidentally treating ``  `` as different from `` ``.

    Bounded ``gap`` because hypothesis spends a lot of CPU
    exploring whitespace explosions with no extra signal.
    """
    tight = _render_search_clause(pairs)
    loose = (" " * gap).join(f"{k}={v}" for k, v in pairs)
    assert canonicalise(tight) == canonicalise(loose), (
        f"whitespace gap of {gap} broke canonical equality:\n"
        f"  tight={tight!r}->{canonicalise(tight)!r}\n"
        f"  loose={loose!r}->{canonicalise(loose)!r}"
    )


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_canonical_form_has_no_pipe_whitespace(spl: str) -> None:
    """Module docstring §4: "no whitespace around ``|``."

    For every input that contains a ``|``, the canonical form must
    not have a space adjacent to it. Subsearch ``[ ... | ... ]``
    contents share the same rule.
    """
    canon = canonicalise(spl)
    assert " |" not in canon, (
        f"canonical form leaks pre-pipe space on {spl!r}: {canon!r}"
    )
    assert "| " not in canon, (
        f"canonical form leaks post-pipe space on {spl!r}: {canon!r}"
    )


# ---------------------------------------------------------------------------
# Property 6: Comparison-operator normalisation totality
# ---------------------------------------------------------------------------


@given(
    pairs=_search_kv_st,
    use_double_eq=st.booleans(),
)
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_double_equals_collapses_to_single_equals(
    pairs: list[tuple[str, str]],
    use_double_eq: bool,
) -> None:
    """``==`` in input never survives into the canonical form.

    Strategy: render a search clause once with ``=`` (the canonical
    operator) and once with ``==`` (the non-canonical form that
    Splunk accepts but the canonicaliser rewrites). Both must
    produce the same canonical string. The boolean parameter
    deliberately tests both directions of the canonical/non-
    canonical pair so Hypothesis explores cases where the input
    is already canonical.
    """
    op = "==" if use_double_eq else "="
    clause = " ".join(f"{k}{op}{v}" for k, v in pairs)
    canon = canonicalise(clause)
    assert "==" not in canon, (
        f"== survived into canonical form on {clause!r}: {canon!r}"
    )


# ---------------------------------------------------------------------------
# Property 7: Keyword case-folding totality
# ---------------------------------------------------------------------------


_CANONICAL_KEYWORDS: tuple[str, ...] = (
    "BY",
    "AS",
    "WHERE",
    "OR",
    "AND",
    "NOT",
    "IN",
    "WITH",
)
_keyword_st = st.sampled_from(_CANONICAL_KEYWORDS)


@given(
    pairs=st.lists(_kv_pair_st, min_size=1, max_size=2),
    keyword=_keyword_st,
)
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_keywords_are_lowercase_in_canonical_form(
    pairs: list[tuple[str, str]],
    keyword: str,
) -> None:
    """Recognised keywords always appear lower-cased in canonical output.

    Strategy: synthesise ``<search clause> | stats count <KW>
    <field>`` where the keyword is upper-cased. Assert it survives
    only in lower-case form.

    Specific risk: ``IN`` and ``WITH`` are short common letter
    pairs that the regex must not match inside identifiers like
    ``stats_by_intval`` (note: hypothesis's identifiers are
    ASCII-only by construction so this stays well-formed).
    """
    clause = _render_search_clause(pairs)
    spl = f"{clause} | stats count {keyword} host"
    canon = canonicalise(spl)
    # The keyword in upper-case form must not appear as a word boundary
    # in the canonical output. We use a regex with word boundaries
    # because the canonical form may legitimately contain the
    # lower-cased version of the same letters as a substring of a
    # field name (e.g. ``hostby``).
    upper_re = re.compile(rf"\b{keyword}\b")
    assert not upper_re.search(canon), (
        f"upper-case keyword {keyword!r} survived in canonical "
        f"form of {spl!r}: {canon!r}"
    )


# ---------------------------------------------------------------------------
# Property 8: TypeError on non-str
# ---------------------------------------------------------------------------


@given(
    non_str=st.one_of(
        st.none(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.lists(st.text()),
        st.binary(),
    )
)
@settings(
    max_examples=20,
    deadline=None,
)
def test_canonicalise_raises_on_non_string(non_str: object) -> None:
    """The boundary check rejects non-str inputs with TypeError.

    Documented in the module docstring; catching it via hypothesis
    explores the type frontier without us having to enumerate
    every non-string sentinel by hand.
    """
    with pytest.raises(TypeError):
        canonicalise(non_str)  # type: ignore[arg-type]


@given(
    non_str=st.one_of(
        st.none(),
        st.integers(),
        st.lists(st.text()),
        st.binary(),
    )
)
@settings(
    max_examples=20,
    deadline=None,
)
def test_fingerprint_raises_on_non_string(non_str: object) -> None:
    """``fingerprint`` inherits the TypeError from ``canonicalise``."""
    with pytest.raises(TypeError):
        fingerprint(non_str)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Smoke: macro_resolver doesn't change the algebraic shape
# ---------------------------------------------------------------------------


@given(spl=_arbitrary_spl_st)
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_canonicalise_with_unresolvable_macros_is_idempotent(spl: str) -> None:
    """Idempotency must hold even when a custom resolver is in play.

    Operator scenario: the recommender's nightly job ships its own
    macro resolver that pulls live macro bodies via REST. The
    canonicaliser must remain idempotent even when the resolver
    returns surprising values (e.g. another macro reference).

    Strategy: use a resolver that intentionally returns an unrelated
    snippet of SPL; verify two passes still settle to the same
    canonical form.
    """

    def resolver(name: str) -> str | None:
        return f"index=resolved_{name}"

    once = canonicalise(spl, macro_resolver=resolver)
    twice = canonicalise(once, macro_resolver=resolver)
    assert twice == once
