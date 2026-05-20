"""Unit tests for ``splunk_uc.audits._spl_parse`` (P16 wave E).

This module is the shared parser substrate for every reference-validating
SPL audit. Until this commit it had **zero unit-test coverage** despite
hosting eight extractors and being the foundation that
``audit-spl-references`` plus several downstream audits depend on. The
tests below pin every extractor's documented behaviour with the smallest
self-contained SPL snippets that exercise each branch, including:

* The empty-input and whitespace-only invariants.
* Quoted vs. bare values, single vs. double quotes, wildcard detection.
* The ``==`` comparison-operator carve-out (prevents false positives on
  ``case(sourcetype=="aws:s3", ...)`` style expressions).
* Leading-boolean and ``<field> IN (...)`` carve-outs in
  ``extract_commands`` (so ``NOT index=foo`` doesn't surface ``not`` as a
  command).
* Macro arity (-1 for parameter-less, 0 for ``()``, N for argument lists).
* Function-call extraction inside the eval-like vs. stats-like segments.
* The "command is also a function name" carve-out (e.g. ``where``).
* SQL-ish keywords (``and``/``or``/``not``/``in``/``like``/``is``)
  blocklist inside ``_functions_in_segment``.
* The aggregate ``extract_all`` and the re-exported ``strip_comments`` /
  ``split_pipes`` wrappers.
"""

from __future__ import annotations

import pytest

from splunk_uc.audits import _spl_parse as p

# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------


def test_unquote_strips_double_quotes() -> None:
    assert p._unquote('"hello"') == "hello"


def test_unquote_strips_single_quotes() -> None:
    assert p._unquote("'hello'") == "hello"


def test_unquote_returns_bare_value_unchanged() -> None:
    assert p._unquote("hello") == "hello"


def test_unquote_does_not_strip_mismatched_quotes() -> None:
    assert p._unquote("\"hello'") == "\"hello'"


def test_unquote_handles_empty_string() -> None:
    assert p._unquote("") == ""


def test_unquote_trims_surrounding_whitespace_first() -> None:
    assert p._unquote('  "hi"  ') == "hi"


def test_is_wildcard_detects_star() -> None:
    assert p._is_wildcard("foo*") is True
    assert p._is_wildcard("*foo") is True
    assert p._is_wildcard("fo*o") is True


def test_is_wildcard_false_for_plain_value() -> None:
    assert p._is_wildcard("foo") is False


def test_is_wildcard_unwraps_before_check() -> None:
    """Quoted wildcards still count."""
    assert p._is_wildcard('"foo*"') is True


# ----------------------------------------------------------------------
# Re-exported wrappers
# ----------------------------------------------------------------------


def test_strip_comments_removes_comment_function() -> None:
    """``comment("...")`` segments are stripped before parsing."""
    stripped = p.strip_comments('search index=foo `comment("ignored")` rest')
    # The comment macro is stripped by the underlying ``_strip_comments``
    # helper; the surrounding tokens survive.
    assert "ignored" not in stripped
    assert "index=foo" in stripped
    assert "rest" in stripped


def test_split_pipes_splits_on_unquoted_pipes() -> None:
    segs = p.split_pipes('search index=foo | stats count by host | head 10')
    assert len(segs) == 3
    assert "search" in segs[0]
    assert segs[1].lstrip().startswith("stats")
    assert segs[2].lstrip().startswith("head")


def test_split_pipes_keeps_quoted_pipes_intact() -> None:
    segs = p.split_pipes('rex "foo|bar" | stats count')
    assert len(segs) == 2
    assert "foo|bar" in segs[0]


# ----------------------------------------------------------------------
# extract_macros
# ----------------------------------------------------------------------


def test_extract_macros_finds_parameterless_reference() -> None:
    refs = p.extract_macros("search `my_macro` index=foo")
    assert len(refs) == 1
    assert refs[0].name == "my_macro"
    assert refs[0].arity == -1
    assert refs[0].raw == "`my_macro`"


def test_extract_macros_empty_parens_yields_arity_zero() -> None:
    refs = p.extract_macros("`my_macro()`")
    assert len(refs) == 1
    assert refs[0].arity == 0


def test_extract_macros_single_argument_yields_arity_one() -> None:
    refs = p.extract_macros("`my_macro(foo)`")
    assert refs[0].arity == 1


def test_extract_macros_multi_argument_yields_correct_arity() -> None:
    refs = p.extract_macros("`my_macro(a,b,c)`")
    assert refs[0].arity == 3


def test_extract_macros_handles_dotted_name_with_colon() -> None:
    """Macro names may contain ``:`` and ``.`` (e.g. namespaced macros)."""
    refs = p.extract_macros("`ns:my.macro`")
    assert refs[0].name == "ns:my.macro"


def test_extract_macros_empty_args_are_not_counted() -> None:
    """``my_macro(,)`` shouldn't claim 2 arguments \u2014 just one real one is empty."""
    refs = p.extract_macros("`my_macro(a,,)`")
    assert refs[0].arity == 1


def test_extract_macros_finds_multiple_references() -> None:
    refs = p.extract_macros("`m1` index=foo | `m2(a)` | `m3()`")
    assert [r.name for r in refs] == ["m1", "m2", "m3"]
    assert [r.arity for r in refs] == [-1, 1, 0]


def test_extract_macros_empty_input_returns_empty() -> None:
    assert p.extract_macros("") == []


def test_extract_macros_no_matches_returns_empty() -> None:
    assert p.extract_macros("search index=foo") == []


def test_extract_macros_strips_comments_first() -> None:
    """A macro reference inside a ``comment("...")`` is not extracted."""
    refs = p.extract_macros('`comment("`real_macro`")` index=foo')
    # The comment macro itself is the only one outside; the inner
    # backtick-quoted text is consumed by the comment stripper.
    names = [r.name for r in refs]
    assert "real_macro" not in names


# ----------------------------------------------------------------------
# extract_indexes
# ----------------------------------------------------------------------


def test_extract_indexes_bare_value() -> None:
    refs = p.extract_indexes("search index=main")
    assert len(refs) == 1
    assert refs[0].value == "main"
    assert refs[0].is_wildcard is False


def test_extract_indexes_double_quoted_value() -> None:
    refs = p.extract_indexes('search index="my main"')
    assert refs[0].value == "my main"


def test_extract_indexes_single_quoted_value() -> None:
    refs = p.extract_indexes("search index='primary'")
    assert refs[0].value == "primary"


def test_extract_indexes_wildcard_value() -> None:
    refs = p.extract_indexes("search index=app_*")
    assert refs[0].value == "app_*"
    assert refs[0].is_wildcard is True


def test_extract_indexes_does_not_match_double_equals() -> None:
    """``index==`` is a comparison predicate, not a search filter."""
    refs = p.extract_indexes('eval x=if(index=="bar", 1, 0)')
    assert refs == []


def test_extract_indexes_case_insensitive_keyword() -> None:
    refs = p.extract_indexes("search INDEX=main")
    assert refs[0].value == "main"


def test_extract_indexes_multiple_indexes() -> None:
    refs = p.extract_indexes("index=main OR index=audit")
    assert [r.value for r in refs] == ["main", "audit"]


def test_extract_indexes_empty_input() -> None:
    assert p.extract_indexes("") == []


# ----------------------------------------------------------------------
# extract_sourcetypes
# ----------------------------------------------------------------------


def test_extract_sourcetypes_bare_value() -> None:
    refs = p.extract_sourcetypes("search sourcetype=linux_secure")
    assert refs[0].value == "linux_secure"
    assert refs[0].is_wildcard is False


def test_extract_sourcetypes_double_quoted_value() -> None:
    refs = p.extract_sourcetypes('search sourcetype="aws:cloudtrail"')
    assert refs[0].value == "aws:cloudtrail"


def test_extract_sourcetypes_wildcard_value() -> None:
    refs = p.extract_sourcetypes('search sourcetype="aws:*"')
    assert refs[0].is_wildcard is True


def test_extract_sourcetypes_does_not_match_double_equals() -> None:
    """``sourcetype==`` inside ``case`` / ``where`` is not an extraction."""
    refs = p.extract_sourcetypes('eval x=case(sourcetype=="aws:s3", 1)')
    assert refs == []


def test_extract_sourcetypes_multiple_predicates() -> None:
    refs = p.extract_sourcetypes("sourcetype=foo OR sourcetype=bar")
    assert [r.value for r in refs] == ["foo", "bar"]


# ----------------------------------------------------------------------
# extract_datamodel_paths
# ----------------------------------------------------------------------


def test_extract_datamodel_paths_model_only() -> None:
    refs = p.extract_datamodel_paths("| tstats count from datamodel=Authentication")
    assert len(refs) == 1
    assert refs[0].model == "Authentication"
    assert refs[0].dataset is None


def test_extract_datamodel_paths_with_dataset_dot_form() -> None:
    refs = p.extract_datamodel_paths(
        "| tstats count from datamodel=Authentication.Authentication"
    )
    assert refs[0].model == "Authentication"
    assert refs[0].dataset == "Authentication"


def test_extract_datamodel_paths_with_dataset_colon_form() -> None:
    refs = p.extract_datamodel_paths("datamodel=Network_Traffic:All_Traffic")
    assert refs[0].model == "Network_Traffic"
    assert refs[0].dataset == "All_Traffic"


def test_extract_datamodel_paths_skips_lowercase_model() -> None:
    """Models must start with uppercase; ``datamodel=if(...)`` must not match."""
    refs = p.extract_datamodel_paths("eval x = if(datamodel=foo, 1, 0)")
    assert refs == []


def test_extract_datamodel_paths_handles_quoted_model_name() -> None:
    """``datamodel="Authentication"`` (with quotes) is accepted."""
    refs = p.extract_datamodel_paths('| tstats count from datamodel="Authentication"')
    assert len(refs) == 1
    assert refs[0].model == "Authentication"


def test_extract_datamodel_paths_finds_multiple_references() -> None:
    refs = p.extract_datamodel_paths(
        "datamodel=Authentication | append [datamodel=Risk.All_Risk]"
    )
    assert [r.model for r in refs] == ["Authentication", "Risk"]
    assert refs[1].dataset == "All_Risk"


# ----------------------------------------------------------------------
# extract_lookups
# ----------------------------------------------------------------------


def test_extract_lookups_lookup_command() -> None:
    refs = p.extract_lookups("search index=foo | lookup my_lookup uid OUTPUT name")
    assert len(refs) == 1
    assert refs[0].name == "my_lookup"
    assert refs[0].command == "lookup"


def test_extract_lookups_inputlookup() -> None:
    refs = p.extract_lookups("| inputlookup my_table.csv")
    assert refs[0].command == "inputlookup"
    assert refs[0].name == "my_table.csv"


def test_extract_lookups_outputlookup() -> None:
    refs = p.extract_lookups("| outputlookup my_output append=true")
    assert refs[0].command == "outputlookup"


def test_extract_lookups_outputcsv() -> None:
    refs = p.extract_lookups("| outputcsv my_results")
    assert refs[0].command == "outputcsv"


def test_extract_lookups_quoted_name() -> None:
    refs = p.extract_lookups('| inputlookup "my lookup with spaces"')
    assert refs[0].name == "my lookup with spaces"


def test_extract_lookups_with_modifiers() -> None:
    """Modifier flags (``append=true`` etc.) don't fool the name extractor.

    The regex matches modifiers in canonical order
    (``append`` \u2192 ``override_if_null`` \u2192 ``max_matches`` \u2192 ``local``);
    keep the snippet in that order so the test exercises the
    "skip every modifier" path.
    """
    refs = p.extract_lookups(
        "| lookup append=true override_if_null=true max_matches=1 local=true my_lookup field"
    )
    assert refs[0].name == "my_lookup"


def test_extract_lookups_no_match_mid_pipeline() -> None:
    """``lookup`` only matches at the head of a pipeline segment."""
    # ``lookup`` inside a search filter (not a leading command) should
    # not be picked up.
    refs = p.extract_lookups("search index=foo lookup_test=true")
    assert refs == []


def test_extract_lookups_case_insensitive_command() -> None:
    refs = p.extract_lookups("| LOOKUP my_lookup field")
    assert refs[0].command == "lookup"


# ----------------------------------------------------------------------
# extract_commands
# ----------------------------------------------------------------------


def test_extract_commands_basic_pipeline() -> None:
    cmds = p.extract_commands("search index=foo | stats count by host | head 10")
    assert cmds == ["search", "stats", "head"]


def test_extract_commands_skips_implicit_search_predicate() -> None:
    """A leading ``index=...`` is a predicate, not a command."""
    cmds = p.extract_commands("index=main sourcetype=foo")
    assert cmds == []


def test_extract_commands_skips_leading_boolean_operator_not() -> None:
    cmds = p.extract_commands("NOT index=foo | stats count")
    # The ``NOT index=foo`` is implicit-search, ``stats`` is the command.
    assert cmds == ["stats"]


def test_extract_commands_skips_leading_boolean_operator_or() -> None:
    cmds = p.extract_commands("OR sourcetype=bar | head 5")
    assert cmds == ["head"]


def test_extract_commands_skips_leading_boolean_operator_and() -> None:
    cmds = p.extract_commands("AND status=200 | stats count")
    assert cmds == ["stats"]


def test_extract_commands_skips_in_predicate() -> None:
    """``index IN (...)`` is a predicate, not a command."""
    cmds = p.extract_commands('index IN ("main","audit")')
    assert cmds == []


def test_extract_commands_skips_in_predicate_case_insensitive() -> None:
    cmds = p.extract_commands('index in ("main")')
    assert cmds == []


def test_extract_commands_returns_lowercase_command_names() -> None:
    cmds = p.extract_commands("SEARCH index=foo | STATS count")
    assert cmds == ["search", "stats"]


def test_extract_commands_skips_empty_segments() -> None:
    cmds = p.extract_commands("|  | search index=foo")
    assert cmds == ["search"]


def test_extract_commands_handles_consecutive_booleans() -> None:
    """``NOT OR ...`` walks past both booleans before deciding."""
    cmds = p.extract_commands("NOT OR foo=bar | stats count")
    assert cmds == ["stats"]


# ----------------------------------------------------------------------
# _functions_in_segment + extract_eval_functions
# ----------------------------------------------------------------------


def test_extract_eval_functions_finds_call() -> None:
    refs = p.extract_eval_functions("| eval x = coalesce(a, b)")
    names = [r.name for r in refs]
    assert "coalesce" in names
    assert all(r.context == "eval" for r in refs)


def test_extract_eval_functions_nested_calls() -> None:
    refs = p.extract_eval_functions(
        "| eval x = if(isnull(a), len(b), tostring(c))"
    )
    names = [r.name for r in refs]
    assert "if" in names
    assert "isnull" in names
    assert "len" in names
    assert "tostring" in names


def test_extract_eval_functions_skips_sql_keywords() -> None:
    """``and``/``or``/``not``/``in``/``like``/``is`` are not function calls."""
    # Note: the parser only recognises ``ident(`` style calls, so SQL
    # keywords that are followed by ``(`` (which is unusual) get skipped.
    refs = p.extract_eval_functions("| eval x = and(a, b)")
    names = [r.name for r in refs]
    assert "and" not in names


def test_extract_eval_functions_segment_command_is_not_a_function() -> None:
    """When ``where`` opens an eval-like segment we don't emit ``where`` as a function."""
    refs = p.extract_eval_functions('| where x > 5')
    names = [r.name for r in refs]
    assert "where" not in names


def test_extract_eval_functions_skips_leading_command_called_as_function() -> None:
    """``eval(`` appearing immediately at the segment head is the leading
    command, not a function call. The carve-out in ``_functions_in_segment``
    elides it while keeping any subsequent function calls.

    Strictly speaking ``eval(...)`` is not valid Splunk syntax, but the
    extractor still needs to be robust: it shouldn't emit ``eval`` as a
    function in this corner case.
    """
    refs = p.extract_eval_functions("eval(x) + tostring(y)")
    names = [r.name for r in refs]
    assert "eval" not in names
    assert "tostring" in names


def test_extract_eval_functions_fieldformat_context() -> None:
    refs = p.extract_eval_functions("| fieldformat duration = tostring(d, \"duration\")")
    assert any(r.name == "tostring" and r.context == "fieldformat" for r in refs)


def test_extract_eval_functions_no_match_when_command_is_not_eval_like() -> None:
    refs = p.extract_eval_functions("| stats count(host) by sourcetype")
    assert refs == []


def test_extract_eval_functions_handles_no_leading_command() -> None:
    """Segment with no leading identifier is skipped silently."""
    refs = p.extract_eval_functions("| 123start | eval x=1")
    # The first segment has no valid leading command; the second is
    # eval-like and contributes nothing (``eval x=1`` has no function call).
    assert refs == []


def test_extract_eval_functions_ignores_calls_inside_double_quoted_strings() -> None:
    """Function-call regex must NOT match identifiers that sit inside a
    quoted string literal.

    Real-world example from UC-3.2.9:

    .. code-block:: spl

        | eval is_synthetic=if(
              match(uri, "(?i)/healthz(\\?|$)") OR
              match(uri, "(?i)/readyz(\\?|$)")  OR
              match(uri, "(?i)/livez(\\?|$)"),
          1, 0)

    Before the quoted-string carve-out, the parser would emit
    ``healthz``, ``readyz`` and ``livez`` as unknown eval-functions
    because ``\\bword\\(`` matched the substrings inside the regex
    literals. None of those names are Splunk built-ins; they are
    Kubernetes HTTP probe paths. The audit reports become noisy and
    the maintainer chases ghosts.

    The carve-out wipes quoted-string content (single OR double-quoted)
    before applying the function regex while preserving the segment's
    leading command head so the ``is`` / ``and`` / ``or`` skip list
    still works.
    """

    spl = (
        '| eval is_synthetic=if(match(uri, "(?i)/healthz(\\?|$)") OR '
        'match(uri, "(?i)/readyz(\\?|$)") OR '
        'match(uri, "(?i)/livez(\\?|$)"), 1, 0)'
    )
    refs = p.extract_eval_functions(spl)
    names = [r.name for r in refs]

    # Real eval-function calls survive.
    assert "if" in names, names
    assert "match" in names, names

    # Substrings inside the quoted regex literals must NOT leak.
    assert "healthz" not in names, names
    assert "readyz" not in names, names
    assert "livez" not in names, names


def test_extract_eval_functions_ignores_calls_inside_single_quoted_strings() -> None:
    """SPL also accepts single-quoted string literals for some contexts.

    The carve-out must handle them symmetrically with double quotes.
    """

    spl = "| eval x = if(field='healthz(', 1, 0)"
    refs = p.extract_eval_functions(spl)
    names = [r.name for r in refs]
    assert "if" in names
    assert "healthz" not in names, names


def test_extract_stats_functions_ignores_calls_inside_quoted_strings() -> None:
    """The same quoted-string skip applies to ``stats`` / ``timechart``
    aggregators.
    """

    spl = '| stats count(eval(status="livez(")) AS livez_hits BY host'
    refs = p.extract_stats_functions(spl)
    names = [r.name for r in refs]
    assert "count" in names
    assert "eval" in names
    assert "livez" not in names, names


# ----------------------------------------------------------------------
# extract_stats_functions
# ----------------------------------------------------------------------


def test_extract_stats_functions_count_in_stats() -> None:
    refs = p.extract_stats_functions("| stats count(host) by sourcetype")
    assert any(r.name == "count" and r.context == "stats" for r in refs)


def test_extract_stats_functions_multiple_aggregators() -> None:
    refs = p.extract_stats_functions(
        "| stats count, dc(host) as hosts, perc95(latency) as p95"
    )
    names = [r.name for r in refs]
    assert "dc" in names
    assert "perc95" in names


def test_extract_stats_functions_timechart() -> None:
    refs = p.extract_stats_functions("| timechart span=1h avg(cpu) by host")
    assert any(r.name == "avg" and r.context == "timechart" for r in refs)


def test_extract_stats_functions_tstats() -> None:
    """The ``count()`` form (with parens) is what ``_FUNC_CALL_RE`` matches."""
    refs = p.extract_stats_functions(
        "| tstats count(host) from datamodel=Authentication.Authentication"
    )
    assert any(r.name == "count" and r.context == "tstats" for r in refs)


def test_extract_stats_functions_skips_when_command_not_stats_like() -> None:
    refs = p.extract_stats_functions("| eval x = count(a)")
    assert refs == []


def test_extract_stats_functions_handles_no_leading_command() -> None:
    refs = p.extract_stats_functions("| ")
    assert refs == []


# ----------------------------------------------------------------------
# extract_all (aggregate)
# ----------------------------------------------------------------------


def test_extract_all_returns_complete_aggregate() -> None:
    spl = (
        '`my_macro(foo)` index=main sourcetype="aws:cloudtrail" '
        '| tstats count from datamodel=Authentication.Authentication '
        '| lookup my_table id OUTPUT name '
        '| eval x = coalesce(a, b) '
        '| stats count(host) by sourcetype'
    )
    ext = p.extract_all(spl)

    assert "search" not in ext.commands  # SPL doesn't start with `search`
    # The commands list collects the leading words of each segment.
    assert "tstats" in ext.commands
    assert "lookup" in ext.commands
    assert "eval" in ext.commands
    assert "stats" in ext.commands

    assert [m.name for m in ext.macros] == ["my_macro"]
    assert ext.macros[0].arity == 1

    assert [s.value for s in ext.sourcetypes] == ["aws:cloudtrail"]
    assert [i.value for i in ext.indexes] == ["main"]

    assert [d.model for d in ext.datamodels] == ["Authentication"]
    assert ext.datamodels[0].dataset == "Authentication"

    assert [lk.name for lk in ext.lookups] == ["my_table"]

    eval_names = [f.name for f in ext.eval_functions]
    assert "coalesce" in eval_names

    stats_names = [f.name for f in ext.stats_functions]
    assert "count" in stats_names


def test_extract_all_empty_input() -> None:
    ext = p.extract_all("")
    assert ext.commands == []
    assert ext.macros == []
    assert ext.sourcetypes == []
    assert ext.indexes == []
    assert ext.datamodels == []
    assert ext.lookups == []
    assert ext.eval_functions == []
    assert ext.stats_functions == []


# ----------------------------------------------------------------------
# Dataclass frozenness contract
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "instance",
    [
        p.MacroRef(name="m", arity=-1, raw="`m`"),
        p.SourcetypeRef(value="v", is_wildcard=False),
        p.IndexRef(value="v", is_wildcard=False),
        p.DatamodelRef(model="Authentication", dataset=None),
        p.LookupRef(name="t", command="lookup"),
        p.FunctionRef(name="count", context="stats"),
    ],
)
def test_reference_dataclasses_are_immutable(instance: object) -> None:
    """All reference dataclasses are ``frozen=True``."""
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        instance.name = "mutated"  # type: ignore[attr-defined]
