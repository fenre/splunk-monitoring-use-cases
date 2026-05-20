"""Tests for ``tools.build.spl_canonicalise``.

Two corpora drive these tests:

* ``tests/fixtures/spl_fingerprints/equivalent.json`` — groups of SPL
  strings that MUST collapse to a single canonical form.
* ``tests/fixtures/spl_fingerprints/non_equivalent.json`` — pairs of SPL
  strings that MUST resolve to distinct canonical forms.

The fixtures are intentionally hand-paired (~30 + 13 entries today, with
room to grow toward the plan's ~100 target) — every entry comes from a
real-world saved-search variant we expect operators to write.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from tools.build.spl_canonicalise import canonicalise, fingerprint

FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "spl_fingerprints"


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_canonicalise_is_idempotent_on_simple_input() -> None:
    once = canonicalise("index=foo | stats count BY host")
    twice = canonicalise(once)
    assert once == twice


def test_canonicalise_strips_block_and_inline_comments() -> None:
    spl = "```preamble``` index=foo `inline note` | stats count"
    canon = canonicalise(spl)
    assert "preamble" not in canon
    assert "inline note" not in canon
    assert "index=" in canon


def test_canonicalise_resolves_macros_to_question_mark_by_default() -> None:
    spl = "index=foo `mymacro` | stats count"
    canon = canonicalise(spl)
    assert "mymacro" not in canon
    assert "?" in canon


def test_canonicalise_uses_supplied_macro_resolver() -> None:
    def resolver(name: str) -> str | None:
        return "host=internal" if name == "scoped_hosts" else None

    canon = canonicalise(
        "`scoped_hosts` | stats count", macro_resolver=resolver
    )
    # `scoped_hosts` -> `host=internal`, which then runs through the
    # canonicaliser as part of the search clause.
    assert "host=" in canon


def test_canonicalise_replaces_dashboard_tokens_with_wildcard() -> None:
    canon = canonicalise("index=$idx_token$ sourcetype=$st|s$")
    # Both tokens collapse to `*`; quoting wraps them.
    assert canon.count('"*"') == 2
    assert "$" not in canon


def test_canonicalise_drops_trailing_eventstats_count_only_when_last() -> None:
    last = canonicalise(
        "index=foo | stats count BY host | eventstats count"
    )
    not_last = canonicalise(
        "index=foo | stats count BY host | eventstats count | where count>0"
    )
    assert "eventstats" not in last
    assert "eventstats" in not_last


def test_canonicalise_normalises_comparison_operators() -> None:
    canon_a = canonicalise("index=foo status==200")
    canon_b = canonicalise("index=foo status=200")
    canon_c = canonicalise("action<>allow")
    canon_d = canonicalise("action!=allow")
    assert canon_a == canon_b
    assert canon_c == canon_d


def test_canonicalise_lowercases_keywords_but_preserves_field_names() -> None:
    canon = canonicalise("index=foo | stats count BY HostField AS HostName")
    assert " by " in canon
    assert " as " in canon
    # Field name preserved.
    assert "HostField" in canon
    assert "HostName" in canon


def test_canonicalise_quotes_bare_word_values_consistently() -> None:
    canon = canonicalise("index=foo sourcetype=bar")
    assert 'index="foo"' in canon
    assert 'sourcetype="bar"' in canon


def test_fingerprint_is_64_char_hex() -> None:
    fp = fingerprint("index=foo | stats count")
    assert len(fp) == 64
    int(fp, 16)  # raises if not hex


def test_fingerprint_is_deterministic() -> None:
    fp1 = fingerprint("index=foo | stats count BY host")
    fp2 = fingerprint("index=foo | stats count BY host")
    assert fp1 == fp2


@pytest.mark.parametrize("group", _load("equivalent.json")["groups"])
def test_equivalent_corpus(group: dict) -> None:
    fingerprints = {fingerprint(spl) for spl in group["spl"]}
    canonicals = {canonicalise(spl) for spl in group["spl"]}
    assert len(fingerprints) == 1, (
        f"group '{group['name']}' fingerprints split: {fingerprints}; "
        f"canonical forms: {canonicals}"
    )


@pytest.mark.parametrize("pair", _load("non_equivalent.json")["pairs"])
def test_non_equivalent_corpus(pair: dict) -> None:
    fp_a = fingerprint(pair["a"])
    fp_b = fingerprint(pair["b"])
    assert fp_a != fp_b, (
        f"pair '{pair['name']}' collided. "
        f"canonical(a) = {canonicalise(pair['a'])!r}; "
        f"canonical(b) = {canonicalise(pair['b'])!r}"
    )


def test_canonicalise_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        canonicalise(123)  # type: ignore[arg-type]


def test_keep_tweaks_flag_preserves_head() -> None:
    canon = canonicalise(
        "index=foo | stats count | head 100",
        drop_operator_tweaks=False,
    )
    assert "head" in canon


# ---------------------------------------------------------------------------
# Macro-resolver corner cases — exception fallback, runaway expansion,
# empty-token guards (cover lines 175-176, 189, 230 in spl_canonicalise.py)
# ---------------------------------------------------------------------------


def test_canonicalise_swallows_exception_from_macro_resolver() -> None:
    """When the user-supplied resolver raises, the macro collapses to
    ``?`` rather than propagating the exception (line 175-176)."""

    def hostile_resolver(name: str) -> str | None:
        raise RuntimeError("resolver blew up")

    canon = canonicalise(
        "index=foo `mymacro` | stats count",
        macro_resolver=hostile_resolver,
    )
    assert "mymacro" not in canon
    assert "?" in canon


def test_canonicalise_bounds_recursive_macro_expansion() -> None:
    """A macro chain that flips between two names every iteration never
    converges to a fixed point. The resolver loop MUST still exit after
    the 8-iteration cap, returning whatever expansion happens to be
    current (line 189)."""

    def flip_resolver(name: str) -> str | None:
        if name == "alpha":
            return "`beta`"
        if name == "beta":
            return "`alpha`"
        return None

    # The fact that this call returns at all (rather than hanging) is the
    # contract under test — the 8-iteration cap fires.
    canon = canonicalise(
        "index=foo `alpha` | stats count",
        macro_resolver=flip_resolver,
    )
    # The remaining macro-shaped token gets shredded by the
    # post-resolution inline-comment stripper, so neither name leaks.
    assert "alpha" not in canon
    assert "beta" not in canon


def test_canonicalise_quoting_returns_empty_on_whitespace_token() -> None:
    """``_canonicalise_quoting('  ')`` returns the stripped empty string
    instead of producing ``""`` quotes (covers the early-return at line 230)."""

    from tools.build.spl_canonicalise import _canonicalise_quoting

    assert _canonicalise_quoting("   ") == ""
    assert _canonicalise_quoting("") == ""


# ---------------------------------------------------------------------------
# CLI entry point — lines 410-446 (_build_argparser) + 449-468 (main)
# ---------------------------------------------------------------------------


def test_main_canonicalise_subcommand_prints_canonical_form(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tools.build.spl_canonicalise import main

    rc = main(["canonicalise", "index=foo | stats count BY host"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    # Output is the canonical form — keywords lowercased, value quoted.
    assert 'index="foo"' in out
    assert " by " in out


def test_main_canonicalise_subcommand_honours_keep_tweaks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tools.build.spl_canonicalise import main

    rc = main(
        ["canonicalise", "--keep-tweaks", "index=foo | stats count | head 100"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    # --keep-tweaks preserves the `head` stage that drop-tweaks would strip.
    assert "head" in out


def test_main_fingerprint_subcommand_emits_64_char_hex(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tools.build.spl_canonicalise import main

    rc = main(["fingerprint", "index=foo | stats count"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert len(out) == 64
    int(out, 16)


def test_main_compare_subcommand_returns_zero_when_equivalent(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tools.build.spl_canonicalise import main

    rc = main(
        [
            "compare",
            "index=foo status==200",
            "index=foo status=200",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "equivalent: yes" in out


def test_main_compare_subcommand_returns_one_when_not_equivalent(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tools.build.spl_canonicalise import main

    rc = main(
        [
            "compare",
            "index=foo",
            "index=bar",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "equivalent: no" in out


def test_main_rejects_unknown_subcommand() -> None:
    from tools.build.spl_canonicalise import main

    # argparse turns the missing required subcommand into SystemExit(2);
    # an unknown subcommand likewise fails parsing.
    with pytest.raises(SystemExit):
        main(["totally-not-a-subcommand"])
