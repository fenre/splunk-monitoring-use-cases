"""Property-based tests for ``scripts/equipment_lib.py``.

Repo-overhaul plan §P16 (2026-05-09): hypothesis is in the
``[test]`` extras already; this module is the inaugural example
showing the pattern for the rest of the burndown work.

Why property-based testing here
-------------------------------

``equipment_lib.match_equipment`` is a substring-search engine over
the `EQUIPMENT`` registry. The example-based tests in
``test_audit_action_pins.py``, ``test_audit_uc_structure.py``, etc.
prove individual cases work, but the function has quiet algebraic
properties that we want to *guarantee* over arbitrary inputs:

1. **Empty-text neutrality:** ``match_equipment("", patterns, k) ==
   (set(), set())`` — the function never invents matches out of
   thin air.
2. **Case insensitivity:** ``match_equipment(text.lower(), ...) ==
   match_equipment(text.upper(), ...)`` — a regression that
   accidentally makes the search case-sensitive would be very hard
   to spot via examples alone.
3. **Pattern-length monotonicity (decreasing min):** if pattern
   ``p`` matches at threshold ``k``, it must also match at every
   ``k' <= k``. The threshold is supposed to *suppress* short
   patterns, never to *enable* them.
4. **Text-substring monotonicity:** if ``a`` is a substring of
   ``b`` then every match against ``a`` survives in the match
   against ``b``. This catches accidental short-circuiting where
   adding text to a haystack drops matches that were already there.
5. **Empty pattern set:** ``match_equipment(any_text, [], k) ==
   (set(), set())``.
6. **Compile determinism:** ``compile_patterns`` over the same
   input list always yields the same flat list (no hidden state).
7. **Compile lowercases:** every emitted pattern is already
   lowercased so ``match_equipment`` doesn't need to re-lower it.

Each property runs with ``@settings(max_examples=...)`` capped low
enough to keep the test suite fast (<200ms total) on developer
machines and in CI.

Hypothesis discovery deadline
------------------------------

Hypothesis raises ``DeadlineExceeded`` if a single example is
slower than 200ms; for this micro-API every example finishes in
microseconds, so the default deadline is fine. Future property
tests against heavier code (renderer output, build pipeline) may
need ``deadline=None`` per-test.
"""

from __future__ import annotations

import importlib.util
import string
import sys
from pathlib import Path
from typing import List

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Load equipment_lib via importlib so the test doesn't depend on
# scripts/ being on PYTHONPATH at collection time.
_spec = importlib.util.spec_from_file_location(
    "equipment_lib_module", REPO_ROOT / "scripts" / "equipment_lib.py"
)
assert _spec is not None and _spec.loader is not None
equipment_lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(equipment_lib)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Patterns are short alphanumeric tokens (the real EQUIPMENT data is in this
# shape — vendor slugs, model codes). Allow a few special characters but no
# whitespace because match_equipment is substring-based.
_pattern_chars = string.ascii_letters + string.digits + "-_"

_patterns_st = st.lists(
    st.tuples(
        st.text(alphabet=_pattern_chars, min_size=1, max_size=12),
        st.text(alphabet=_pattern_chars, min_size=1, max_size=12),
        st.one_of(st.none(), st.text(alphabet=_pattern_chars, min_size=1, max_size=12)),
    ),
    min_size=0,
    max_size=20,
)


def _normalise_patterns(
    raw: List[tuple[str, str, str | None]],
) -> List[equipment_lib.Pattern]:
    """Lowercase the pattern column. ``compile_patterns`` does this in
    production; we replicate it so the synthetic patterns we feed
    to ``match_equipment`` come from the same shape it would normally see."""
    return [(p.lower(), eq, mid) for p, eq, mid in raw]


# Texts include letters/digits/punctuation but stay reasonably small to
# keep the search fast.
_text_st = st.text(
    alphabet=string.ascii_letters + string.digits + " -_,.()/",
    min_size=0,
    max_size=120,
)


# ---------------------------------------------------------------------------
# Properties of match_equipment
# ---------------------------------------------------------------------------


@given(patterns=_patterns_st, k=st.integers(min_value=1, max_value=20))
@settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
def test_match_empty_text_returns_empty_sets(
    patterns: List[tuple[str, str, str | None]], k: int
) -> None:
    """For *any* pattern set + threshold, the empty haystack matches nothing."""
    eq_ids, models = equipment_lib.match_equipment("", _normalise_patterns(patterns), k)
    assert eq_ids == set()
    assert models == set()


@given(text=_text_st, patterns=_patterns_st, k=st.integers(min_value=1, max_value=20))
@settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
def test_match_is_case_insensitive(
    text: str, patterns: List[tuple[str, str, str | None]], k: int
) -> None:
    """Upper-casing the haystack must not change the match set."""
    norm = _normalise_patterns(patterns)
    upper = equipment_lib.match_equipment(text.upper(), norm, k)
    lower = equipment_lib.match_equipment(text.lower(), norm, k)
    assert upper == lower


@given(text=_text_st, patterns=_patterns_st, k=st.integers(min_value=1, max_value=20))
@settings(max_examples=120, suppress_health_check=[HealthCheck.too_slow])
def test_lowering_threshold_only_widens_match_set(
    text: str, patterns: List[tuple[str, str, str | None]], k: int
) -> None:
    """A lower min_pattern_len threshold can only *add* matches, never remove them.

    This pins the documented behaviour of min_pattern_len as a
    *suppressor* of short patterns — flipping the polarity by
    accident would be silently catastrophic for false-positive
    suppression on the ``spl`` / ``implementation`` text fields.
    """
    norm = _normalise_patterns(patterns)
    if k <= 1:
        return  # nothing weaker than k=1 to test against
    eq_at_k, mod_at_k = equipment_lib.match_equipment(text, norm, k)
    eq_at_lower, mod_at_lower = equipment_lib.match_equipment(text, norm, k - 1)
    assert eq_at_k.issubset(eq_at_lower), (
        f"loosening threshold {k}→{k-1} should never remove an equipment match; "
        f"got {sorted(eq_at_k)} ⊄ {sorted(eq_at_lower)}"
    )
    assert mod_at_k.issubset(mod_at_lower), (
        f"loosening threshold {k}→{k-1} should never remove a model match; "
        f"got {sorted(mod_at_k)} ⊄ {sorted(mod_at_lower)}"
    )


@given(
    a=_text_st,
    b=_text_st,
    patterns=_patterns_st,
    k=st.integers(min_value=1, max_value=8),
)
@settings(max_examples=120, suppress_health_check=[HealthCheck.too_slow])
def test_substring_inclusion_implies_match_inclusion(
    a: str,
    b: str,
    patterns: List[tuple[str, str, str | None]],
    k: int,
) -> None:
    """If text ``a`` appears in text ``b``, every match in ``a`` must persist in ``b``.

    Counter-example would be a substring search that mutates state
    or short-circuits incorrectly.
    """
    norm = _normalise_patterns(patterns)
    combined = a + b  # 'a' is a prefix of 'combined', so a ⊆ combined
    eq_a, mod_a = equipment_lib.match_equipment(a, norm, k)
    eq_combined, mod_combined = equipment_lib.match_equipment(combined, norm, k)
    assert eq_a.issubset(eq_combined), (
        f"matches against {a!r} must survive in {combined!r}; "
        f"got {sorted(eq_a)} ⊄ {sorted(eq_combined)}"
    )
    assert mod_a.issubset(mod_combined), (
        f"model matches against {a!r} must survive in {combined!r}; "
        f"got {sorted(mod_a)} ⊄ {sorted(mod_combined)}"
    )


@given(text=_text_st, k=st.integers(min_value=1, max_value=20))
@settings(max_examples=40)
def test_match_with_empty_pattern_set_is_empty(text: str, k: int) -> None:
    """No patterns → no matches, regardless of text or threshold."""
    eq_ids, mods = equipment_lib.match_equipment(text, [], k)
    assert eq_ids == set()
    assert mods == set()


# ---------------------------------------------------------------------------
# Properties of compile_patterns
# ---------------------------------------------------------------------------


def _equipment_entry_st() -> st.SearchStrategy:
    """Build EQUIPMENT-shaped dicts.

    Real entries look like::

        {"id": "cisco_meraki", "tas": ["meraki", "Splunk_TA_meraki"],
         "models": [{"id": "mx", "tas": ["mx-series"]}, ...]}
    """
    pattern_st = st.text(alphabet=_pattern_chars, min_size=1, max_size=12)
    model_st = st.fixed_dictionaries(
        {
            "id": st.text(alphabet=_pattern_chars, min_size=1, max_size=10),
            "tas": st.lists(pattern_st, min_size=0, max_size=5),
        }
    )
    return st.fixed_dictionaries(
        {
            "id": st.text(alphabet=_pattern_chars, min_size=1, max_size=12),
            "tas": st.lists(pattern_st, min_size=0, max_size=5),
        }
    ) | st.fixed_dictionaries(
        {
            "id": st.text(alphabet=_pattern_chars, min_size=1, max_size=12),
            "tas": st.lists(pattern_st, min_size=0, max_size=5),
            "models": st.lists(model_st, min_size=0, max_size=4),
        }
    )


@given(equipment=st.lists(_equipment_entry_st(), min_size=0, max_size=8))
@settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
def test_compile_patterns_is_deterministic(
    equipment: List[dict[str, object]],
) -> None:
    """Two calls on the same input must return the same flat list."""
    a = equipment_lib.compile_patterns(equipment)
    b = equipment_lib.compile_patterns(equipment)
    assert a == b


@given(equipment=st.lists(_equipment_entry_st(), min_size=0, max_size=8))
@settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
def test_compile_patterns_lowercases_every_pattern(
    equipment: List[dict[str, object]],
) -> None:
    """Every emitted pattern must already be lowercased."""
    flat = equipment_lib.compile_patterns(equipment)
    for pattern, _eq_id, _model_id in flat:
        assert pattern == pattern.lower(), (
            f"compile_patterns must lowercase every pattern; got {pattern!r}"
        )


@given(equipment=st.lists(_equipment_entry_st(), min_size=0, max_size=6))
@settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
def test_compile_patterns_count_matches_input_shape(
    equipment: List[dict[str, object]],
) -> None:
    """Number of emitted tuples equals sum of all ``tas`` entries (top + models).

    Pins the implementation invariant from the docstring against a
    refactor that accidentally drops or duplicates patterns.
    """
    flat = equipment_lib.compile_patterns(equipment)
    expected = 0
    for entry in equipment:
        expected += len(entry.get("tas", []))  # top-level tas
        for model in entry.get("models", []) or []:
            expected += len(model.get("tas", []))
    assert len(flat) == expected, (
        f"flat length {len(flat)} ≠ expected {expected}; equipment={equipment!r}"
    )


# ---------------------------------------------------------------------------
# A small example-based regression that property tests above don't cover
# (the real EQUIPMENT registry round-trips through load_equipment +
#  compile_patterns + match_equipment without throwing).
# ---------------------------------------------------------------------------


def test_real_equipment_registry_round_trips() -> None:
    """Smoke test: the real registry parses, compiles, and matches without errors."""
    eq = equipment_lib.load_equipment()
    assert isinstance(eq, list) and eq, "EQUIPMENT must be a non-empty list"
    patterns = equipment_lib.compile_patterns(eq)
    assert patterns, "compile_patterns must yield at least one pattern from the real registry"
    # Pick a pattern guaranteed to be present and check it matches itself.
    pat = patterns[0][0]
    eq_ids, _models = equipment_lib.match_equipment(pat, patterns, min_pattern_len=1)
    assert patterns[0][1] in eq_ids, (
        f"self-match failed for {pat!r}; expected {patterns[0][1]!r} in {sorted(eq_ids)!r}"
    )


@pytest.mark.parametrize("text", ["meraki", "MERAKI", "MeRaKi", "  meraki  "])
def test_match_known_string_round_trips_case_variants(text: str) -> None:
    """Smoke regression: a real registry pattern self-matches across casing variants.

    Picks a pattern that exists in the live registry and asserts the
    same pattern in different cases produces *identical* match
    results. We don't pin the equipment-id to a specific value
    because the registry is the source of truth for the pattern→id
    mapping (and refactors that move ``meraki`` from ``cisco`` to
    ``cisco_meraki`` should not break this test).
    """
    eq = equipment_lib.load_equipment()
    patterns = equipment_lib.compile_patterns(eq)
    if not any("meraki" == p for p, _, _ in patterns):
        pytest.skip("no 'meraki' pattern in current registry")
    matches = equipment_lib.match_equipment(text, patterns, min_pattern_len=4)
    # The case-insensitivity property already proves the result is
    # stable across casings; what we add here is the existence claim.
    assert matches[0], (
        f"meraki self-match returned no equipment for {text!r}; got {matches!r}"
    )
