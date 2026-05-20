"""Unit tests for ``audit-spl-grammar`` check functions (P16 wave F).

The audit's parser primitives (``_split_pipes`` / ``_strip_comments``)
are pinned by hypothesis property tests in
:file:`test_spl_grammar_properties.py`. This module pins the
*check functions* layered on top of those primitives \u2014 the five
``check_*`` predicates plus the ``audit_spl_block``,
``audit_uc_payload``, and CLI ``main`` orchestrators.

Each check is exercised twice: at least one positive snippet that
triggers each finding category, and one negative snippet that
verifies the check does **not** fire on adjacent-but-correct SPL.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from splunk_uc.audits import spl_grammar as g

# ----------------------------------------------------------------------
# Parser primitives \u2014 escape-sequence + single-quote branches
# (the wave-D property tests cover invariants; these target specific
# branches that the property tests don't deterministically hit.)
# ----------------------------------------------------------------------


def test_strip_comments_handles_backslash_escape_inside_double_quote() -> None:
    """``comment("a \\"quoted\\" b")`` doesn't terminate the comment early."""
    out = g._strip_comments(r'search index=foo `comment("a \"quoted\" b")` | rest')
    assert "quoted" not in out
    assert "search index=foo" in out
    assert "| rest" in out


def test_strip_comments_handles_backslash_escape_inside_single_quote() -> None:
    out = g._strip_comments(r"search index=foo comment('a \'esc\' b') | rest")
    assert "esc" not in out
    assert "search index=foo" in out


def test_strip_comments_handles_single_quoted_string_inside_comment() -> None:
    out = g._strip_comments("search comment('hello world') | rest")
    assert "hello world" not in out


def test_strip_comments_handles_nested_parens_inside_comment() -> None:
    """``comment("outer(inner(deep))")`` closes only at the matching outer ``)``."""
    out = g._strip_comments("search index=foo comment(outer(inner(deep))) | rest")
    assert "outer" not in out
    assert "deep" not in out
    assert "| rest" in out


def test_strip_comments_no_match_returns_unchanged() -> None:
    src = "search index=foo | stats count by host"
    assert g._strip_comments(src) == src


def test_strip_comments_unterminated_comment_consumes_to_end() -> None:
    """An unterminated ``comment(`` consumes all input until EOF."""
    out = g._strip_comments("search comment(this never closes")
    assert "this never closes" not in out
    assert out == "search "


def test_split_pipes_handles_dashboard_token_with_internal_pipe() -> None:
    """Dashboard tokens like ``$field|s$`` contain ``|`` but must NOT split.

    The masker substitutes each token character with ``X`` so the
    token's internal ``|`` cannot be mistaken for a segment boundary;
    the *count* of segments is what callers rely on (the token's
    rendered form is a private implementation detail).
    """
    segs = g._split_pipes("search index=$idx|s$ | stats count")
    assert len(segs) == 2
    assert segs[1].startswith("stats")


def test_split_pipes_handles_backslash_escape_inside_double_quote() -> None:
    """A ``\\"`` inside ``"..."`` must not close the string."""
    segs = g._split_pipes(r'rex field=_raw "(?i)\"a|b\" foo" | stats count')
    assert len(segs) == 2


def test_split_pipes_handles_single_quoted_string() -> None:
    """``'a|b'`` is a single-quoted literal and the ``|`` must not split."""
    segs = g._split_pipes("rex field=_raw 'a|b|c' | stats count")
    assert len(segs) == 2


def test_split_pipes_handles_backslash_escape_inside_single_quote() -> None:
    segs = g._split_pipes(r"rex field=_raw 'a\'|b\'' | stats count")
    assert len(segs) == 2


def test_split_pipes_returns_empty_list_for_empty_input() -> None:
    assert g._split_pipes("") == []


def test_split_pipes_preserves_unbalanced_paren_depth() -> None:
    """A ``|`` inside ``stats list(case(x>0, "a", x<0, "b"))`` is protected."""
    segs = g._split_pipes('stats list(case(x>0, "a|b", x<0, "c|d"))')
    assert len(segs) == 1


# ----------------------------------------------------------------------
# check_stats_span
# ----------------------------------------------------------------------


def test_check_stats_span_flags_stats_with_span() -> None:
    findings = g.check_stats_span(
        "UC-1.1.1", "stub.json", "search index=foo | stats count by host span=1h"
    )
    assert len(findings) == 1
    f = findings[0]
    assert f.category == "stats-span-invalid"
    assert f.severity == "HIGH"
    assert "`stats ... span=` is invalid" in f.message
    assert f.snippet


def test_check_stats_span_flags_eventstats_with_span() -> None:
    findings = g.check_stats_span("UC-1.1.1", "stub.json", "| eventstats count by host span=15m")
    assert len(findings) == 1
    assert findings[0].category == "stats-span-invalid"
    assert "eventstats" in findings[0].message


def test_check_stats_span_flags_streamstats_with_span() -> None:
    findings = g.check_stats_span(
        "UC-1.1.1", "stub.json", "| streamstats avg(latency) by host span=1m"
    )
    assert len(findings) == 1
    assert "streamstats" in findings[0].message
    assert "window=<N>" in findings[0].message


def test_check_stats_span_silent_on_valid_timechart_span() -> None:
    """``timechart span=`` is perfectly valid \u2014 must not fire."""
    findings = g.check_stats_span("UC-1.1.1", "stub.json", "| timechart span=1h count by host")
    assert findings == []


def test_check_stats_span_silent_on_bin_span() -> None:
    """``bin _time span=...`` then ``stats`` is the recommended idiom."""
    findings = g.check_stats_span(
        "UC-1.1.1", "stub.json", "| bin _time span=1h | stats count by _time, host"
    )
    assert findings == []


def test_check_stats_span_silent_on_tstats_span() -> None:
    """``tstats`` legitimately supports ``span=``."""
    findings = g.check_stats_span(
        "UC-1.1.1",
        "stub.json",
        "| tstats count from datamodel=Authentication span=1h",
    )
    assert findings == []


def test_check_stats_span_silent_on_sistats_without_span() -> None:
    """Plain ``stats`` (or ``sistats``) without a ``span=`` token is fine."""
    findings = g.check_stats_span("UC-1.1.1", "stub.json", "| stats count by host")
    assert findings == []


def test_check_stats_span_strips_comments_first() -> None:
    """A ``span=`` inside a ``comment("...")`` block is ignored."""
    findings = g.check_stats_span(
        "UC-1.1.1",
        "stub.json",
        '| stats count by host `comment("span=1h note")`',
    )
    assert findings == []


def test_check_stats_span_finding_carries_file_and_uc() -> None:
    findings = g.check_stats_span(
        "UC-1.1.1", "/path/to/UC-1.1.1.json", "| stats count by host span=1h"
    )
    assert findings[0].file == "/path/to/UC-1.1.1.json"
    assert findings[0].uc_id == "UC-1.1.1"


# ----------------------------------------------------------------------
# check_leading_pipe
# ----------------------------------------------------------------------


def test_check_leading_pipe_silent_on_no_leading_pipe() -> None:
    findings = g.check_leading_pipe(
        "UC-1.1.1", "stub.json", "search index=foo | stats count by host"
    )
    assert findings == []


def test_check_leading_pipe_silent_on_tstats_generating_command() -> None:
    findings = g.check_leading_pipe(
        "UC-1.1.1", "stub.json", "| tstats count from datamodel=Authentication"
    )
    assert findings == []


def test_check_leading_pipe_silent_on_inputlookup_generating_command() -> None:
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| inputlookup my_table.csv")
    assert findings == []


def test_check_leading_pipe_silent_on_makeresults() -> None:
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| makeresults | eval x=1")
    assert findings == []


def test_check_leading_pipe_silent_on_backtick_macro() -> None:
    """``| `my_macro`` ` is a macro invocation \u2014 must not fire."""
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| `my_security_macro` | stats count")
    assert findings == []


def test_check_leading_pipe_silent_on_implicit_index_search() -> None:
    """``| index=foo`` is a degenerate but valid implicit-search idiom."""
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| index=foo sourcetype=bar")
    assert findings == []


def test_check_leading_pipe_silent_on_implicit_sourcetype_search() -> None:
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| sourcetype=aws:cloudtrail")
    assert findings == []


def test_check_leading_pipe_flags_leading_eval() -> None:
    """``| eval x = ...`` as the very first segment is malformed: ``eval``
    is a streaming command and needs an upstream generator."""
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| eval risk_score = 10")
    assert len(findings) == 1
    assert findings[0].category == "leading-pipe-invalid"
    assert "eval" in findings[0].message


def test_check_leading_pipe_flags_leading_stats() -> None:
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "| stats count by host")
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"


def test_check_leading_pipe_skips_comment_decorators() -> None:
    """Decorative ``| comment("...")`` segments at the front are skipped."""
    findings = g.check_leading_pipe(
        "UC-1.1.1",
        "stub.json",
        '| comment("header") | tstats count from datamodel=Authentication',
    )
    assert findings == []


def test_check_leading_pipe_flags_only_comments_block() -> None:
    """If the entire pipeline is just ``| comment(...)`` segments there's no search."""
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", '| comment("only header")')
    assert len(findings) == 1
    assert "only `| comment` segments" in findings[0].message


def test_check_leading_pipe_silent_on_bare_pipe_only() -> None:
    """A degenerate ``"|"`` input strips to an empty segment list \u2014 no findings."""
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "|")
    assert findings == []


def test_check_leading_pipe_silent_on_pipe_with_whitespace_only() -> None:
    findings = g.check_leading_pipe("UC-1.1.1", "stub.json", "|   ")
    assert findings == []


# ----------------------------------------------------------------------
# check_multi_search_glue
# ----------------------------------------------------------------------


def test_check_multi_search_glue_flags_two_index_searches_glued() -> None:
    spl = 'index=foo sourcetype=a | comment("then this:") | index=bar sourcetype=b'
    findings = g.check_multi_search_glue("UC-1.1.1", "stub.json", spl)
    assert len(findings) == 1
    assert findings[0].category == "multi-search-glue"
    assert findings[0].severity == "HIGH"


def test_check_multi_search_glue_silent_on_single_index() -> None:
    findings = g.check_multi_search_glue(
        "UC-1.1.1",
        "stub.json",
        'index=foo sourcetype=a | comment("annotated") | stats count',
    )
    assert findings == []


def test_check_multi_search_glue_silent_when_comment_absent() -> None:
    """Two ``index=`` predicates without a ``| comment(...)`` glue are not flagged here."""
    findings = g.check_multi_search_glue("UC-1.1.1", "stub.json", "index=foo OR index=bar")
    assert findings == []


# ----------------------------------------------------------------------
# check_case_wildcard
# ----------------------------------------------------------------------


def test_check_case_wildcard_flags_quoted_star_predicate() -> None:
    findings = g.check_case_wildcard(
        "UC-1.1.1",
        "stub.json",
        'eval class = case(host="prod-*", "high", true(), "low")',
    )
    assert len(findings) == 1
    assert findings[0].category == "case-wildcard-literal"
    assert findings[0].severity == "MED"
    assert "literal string" in findings[0].message


def test_check_case_wildcard_silent_on_bare_star_predicate() -> None:
    """``case(x>0, ...)`` and ``case(host="prod", ...)`` are both fine."""
    findings = g.check_case_wildcard(
        "UC-1.1.1", "stub.json", 'eval class = case(host="prod", "high")'
    )
    assert findings == []


def test_check_case_wildcard_silent_on_match_or_like() -> None:
    findings = g.check_case_wildcard(
        "UC-1.1.1",
        "stub.json",
        'eval class = case(match(host, "prod.*"), "high", true(), "low")',
    )
    assert findings == []


def test_check_case_wildcard_flags_multiple_predicates() -> None:
    findings = g.check_case_wildcard(
        "UC-1.1.1",
        "stub.json",
        'eval class = case(host="prod-*", "high"), env = case(env="qa-*", "yellow")',
    )
    assert len(findings) == 2


# ----------------------------------------------------------------------
# check_where_after_timechart
# ----------------------------------------------------------------------


def test_check_where_after_timechart_flags_dropped_field() -> None:
    spl = "search index=foo | timechart span=1h count by host | where dropped_field > 0"
    findings = g.check_where_after_timechart("UC-1.1.1", "stub.json", spl)
    assert len(findings) == 1
    assert findings[0].category == "where-after-timechart-unknown-field"
    assert findings[0].severity == "MED"
    assert "dropped_field" in findings[0].message


def test_check_where_after_timechart_silent_on_produced_field() -> None:
    """``where count > 5`` after a ``timechart count`` is valid \u2014 must not fire."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "search index=foo | timechart span=1h count by host | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_when_no_timechart() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "search index=foo | stats count by host | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_aliased_field() -> None:
    """``timechart count as events`` makes ``where events > 5`` valid."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count as events by host | where events > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_eval_assignment() -> None:
    """An intermediate ``| eval foo = ...`` produces ``foo`` for downstream ``where``."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | eval ratio = count/100 | where ratio > 0.5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_streamstats_alias() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | streamstats avg(count) as mean_count "
        "| where mean_count > 10",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_lookup_output() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host "
        "| lookup hosts.csv host OUTPUT criticality "
        '| where criticality = "high"',
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_rename() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | rename count as events | where events > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_addtotals_default() -> None:
    """``addtotals`` without a ``fieldname=`` adds a default ``Total`` field."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | addtotals | where total > 10",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_addtotals_named_fieldname() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | addtotals fieldname=Grand | where grand > 10",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_untable() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | untable _time host events | where events > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_xyseries() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | xyseries _time host count | where _time > 1",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_accum_aliased() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | accum count as running_total "
        "| where running_total > 100",
    )
    assert findings == []


def test_check_where_after_timechart_silent_on_keyword_subject() -> None:
    """SPL keywords (``and``, ``or``, ``not``, ``true``) must not be flagged."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | where count > 5 AND count < 100",
    )
    assert findings == []


def test_check_where_after_timechart_silent_when_comment_present() -> None:
    """The check skips entirely when the SPL contains ``comment(``."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        '| timechart span=1h count by host `comment("note")` | where dropped > 0',
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_predict_alias() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | predict count as forecast | where forecast > 100",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_fit_apply() -> None:
    """MLTK ``| fit`` / ``| apply`` emit ``isOutlier``-style fields by convention."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | apply density_model | where isoutlier = 1",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_fit_alias() -> None:
    """``| fit X as Y`` registers the alias ``Y`` for downstream ``where``."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | fit DensityFunction count as score "
        "| where score > 0.5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_when_unrecognised_command_intervenes() -> None:
    """An intervening command we don't track simply doesn't add to ``produced``;
    the check moves on to the next segment without firing."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | dedup host | where count > 5",
    )
    # ``count`` was produced by timechart, so the where is fine
    assert findings == []


def test_check_where_after_timechart_silent_with_anomalydetection() -> None:
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | anomalydetection action=annotate | where outlier = 1",
    )
    assert findings == []


# ----------------------------------------------------------------------
# Branch-completeness pins for the produced-field bookkeeping helper
# (every test below is silent — the goal is to exercise the False arm
# of an `if` guard inside ``check_where_after_timechart`` without
# tripping the where-after-timechart finding itself).
# ----------------------------------------------------------------------


def test_check_case_wildcard_silent_on_unquoted_star_predicate() -> None:
    """Pins the False arm of ``if re.search(r'\"[^\"]*\\*[^\"]*\"', predicate)``
    (branch ``385->381``): ``_RE_CASE_WILDCARD`` matches a ``case(<p>, ...)``
    body where ``<p>`` contains ``*`` but the ``*`` is bare (not inside a
    double-quoted string). The inner regex returns ``None``, so the
    loop must continue to the next match without emitting a finding."""
    findings = g.check_case_wildcard(
        "UC-1.1.1",
        "stub.json",
        'eval class = case(field=*, "high", true(), "low")',
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_timechart_without_by_clause() -> None:
    """Pins the False arm of ``if bm:`` (branch ``503->508``): a
    ``timechart`` without a trailing ``by <fields>`` clause skips the
    ``for f in bm.group(1).split(','):`` loop and goes straight to
    ``produced.add('_time')``."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_empty_by_field_token() -> None:
    """Pins the False arm of ``if f:`` (branch ``506->504``): an empty
    token inside ``by <fields>`` (produced by a stray double-comma like
    ``by host,,env``) is skipped by ``str.strip()`` returning ``''``.
    The non-empty fields are still added to ``produced`` so a downstream
    ``where`` referencing them is silent."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        '| timechart span=1h count by host,,env | where env = "prod"',
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_lookup_without_output_clause() -> None:
    """Pins the False arm of ``if om:`` (branch ``524->528``): a
    ``lookup`` without an ``OUTPUT``/``OUTPUTNEW`` clause produces no
    new aliases — ``produced`` is unchanged. The trailing ``where``
    references ``count`` (always emitted by ``timechart``) so the
    helper stays silent."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | lookup hosts.csv host | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_lookup_output_invalid_ident() -> None:
    """Pins the False arm of ``if tok and _IDENT_RE.fullmatch(tok):``
    (branch ``526->525``): an OUTPUT token that fails the identifier
    regex (e.g. starts with a digit) is skipped. The trailing ``where``
    references ``count`` (still produced by ``timechart``) so the
    helper stays silent."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host "
        "| lookup hosts.csv host OUTPUT 123badident | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_untable_too_few_args() -> None:
    """Pins the False arm of ``if len(parts) >= 4:`` (branch ``550->553``)
    for ``untable``: a malformed ``| untable host`` (only 2 parts) adds
    nothing to ``produced``. The trailing ``where`` references ``count``
    (still emitted by ``timechart``) so the helper stays silent."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | untable host | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_xyseries_too_few_args() -> None:
    """Pins the False arm of ``if len(parts) >= 4:`` (branch ``556->558``)
    for ``xyseries``: a malformed ``| xyseries _time`` (only 2 parts)
    adds nothing to ``produced``. The trailing ``where`` references
    ``count`` (still emitted by ``timechart``) so the helper stays
    silent."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | xyseries _time | where count > 5",
    )
    assert findings == []


def test_check_where_after_timechart_silent_with_accum_unparseable() -> None:
    """Pins the False arm of ``if accum_match:`` (branch ``575->577``):
    an ``accum`` invocation whose target argument fails the identifier
    regex (e.g. starts with a digit) yields ``accum_match is None``,
    so ``produced`` is unchanged. The trailing ``where`` references
    ``count`` (still emitted by ``timechart``) so the helper stays
    silent."""
    findings = g.check_where_after_timechart(
        "UC-1.1.1",
        "stub.json",
        "| timechart span=1h count by host | accum 123bogus | where count > 5",
    )
    assert findings == []


# ----------------------------------------------------------------------
# audit_spl_block (orchestrator)
# ----------------------------------------------------------------------


def test_audit_spl_block_runs_all_checks() -> None:
    """One SPL string can trigger multiple categories at once."""
    findings = g.audit_spl_block(
        "UC-1.1.1",
        "stub.json",
        "| stats count by host span=1h",
        field="spl",
    )
    cats = {f.category for f in findings}
    # ``stats span`` AND nothing else \u2014 the leading-pipe check sees
    # ``stats`` which is not a generator either, so this fires twice.
    assert "stats-span-invalid" in cats
    assert "leading-pipe-invalid" in cats
    for f in findings:
        assert f.field == "spl"


def test_audit_spl_block_empty_input_no_findings() -> None:
    findings = g.audit_spl_block("UC-1.1.1", "stub.json", "")
    assert findings == []


def test_audit_spl_block_clean_spl_no_findings() -> None:
    findings = g.audit_spl_block(
        "UC-1.1.1",
        "stub.json",
        "| tstats count from datamodel=Authentication.Authentication by Authentication.user",
    )
    assert findings == []


# ----------------------------------------------------------------------
# audit_uc_payload (iterates over SPL fields)
# ----------------------------------------------------------------------


def test_audit_uc_payload_inspects_all_four_spl_fields() -> None:
    payload: dict[str, object] = {
        "id": "1.1.1",
        "spl": "| stats count by host span=1h",
        "cimSpl": "| eval x=1",
        "rbaSpl": "search index=foo | stats count by host",
        "mvSpl": "",
    }
    findings = g.audit_uc_payload("stub.json", payload)
    fields_with_findings = {f.field for f in findings}
    # spl + cimSpl have findings; rbaSpl is clean; mvSpl is empty.
    assert "spl" in fields_with_findings
    assert "cimSpl" in fields_with_findings
    assert "rbaSpl" not in fields_with_findings
    assert "mvSpl" not in fields_with_findings


def test_audit_uc_payload_skips_non_string_spl_values() -> None:
    """A ``spl`` value that's not a string is silently skipped."""
    payload: dict[str, object] = {"id": "1.1.1", "spl": ["not", "a", "string"]}
    findings = g.audit_uc_payload("stub.json", payload)
    assert findings == []


def test_audit_uc_payload_skips_whitespace_only_spl() -> None:
    payload: dict[str, object] = {"id": "1.1.1", "spl": "   \n  "}
    findings = g.audit_uc_payload("stub.json", payload)
    assert findings == []


def test_audit_uc_payload_handles_missing_id() -> None:
    """When ``id`` is absent the uc_id becomes ``UC-<unknown>``."""
    payload: dict[str, object] = {"spl": "| stats count by host span=1h"}
    findings = g.audit_uc_payload("stub.json", payload)
    assert findings, "expected at least one finding"
    assert findings[0].uc_id == "UC-<unknown>"


# ----------------------------------------------------------------------
# Finding.human() rendering
# ----------------------------------------------------------------------


def test_finding_human_includes_severity_category_uc_message() -> None:
    f = g.Finding(
        file="/tmp/UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="HIGH",
        category="stats-span-invalid",
        message="boom",
        snippet="| stats count by host span=1h",
        field="spl",
    )
    s = f.human()
    assert "[HIGH]" in s
    assert "[stats-span-invalid]" in s
    assert "UC-1.1.1" in s
    assert "UC-1.1.1.json" in s
    assert ":spl)" in s
    assert "boom" in s
    assert "snippet:" in s


def test_finding_human_omits_field_marker_when_field_empty() -> None:
    f = g.Finding(
        file="/tmp/UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="MED",
        category="x",
        message="m",
    )
    s = f.human()
    assert ":" not in s.split("(")[1].split(")")[0]  # no `:field` inside the parens


def test_finding_human_truncates_long_snippet() -> None:
    long_snip = "x" * 500
    f = g.Finding(
        file="a.json",
        uc_id="UC-1.1.1",
        severity="LOW",
        category="x",
        message="m",
        snippet=long_snip,
    )
    s = f.human()
    # 140-char truncation
    assert long_snip not in s
    snippet_line = s.split("snippet: ")[1]
    assert len(snippet_line) <= 140


# ----------------------------------------------------------------------
# CLI main() smoke through monkeypatched sidecar walker
# ----------------------------------------------------------------------


def _stub_iter(
    payloads: list[tuple[Path, dict[str, object]]],
) -> Iterator[tuple[Path, dict[str, object]]]:
    yield from payloads


def test_main_returns_0_when_no_findings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty corpus produces no findings and exits 0."""
    monkeypatch.setattr(g, "iter_uc_sidecars", lambda: _stub_iter([]))
    rc = g.main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Sidecars scanned: 0" in captured.out


def test_main_emits_human_report_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The default (no ``--json``, no ``--check``) emits the human report."""
    payload: dict[str, object] = {"id": "1.1.1", "spl": "| stats count by host span=1h"}
    monkeypatch.setattr(g, "iter_uc_sidecars", lambda: _stub_iter([(Path("stub.json"), payload)]))
    rc = g.main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "SPL grammar audit" in captured.out
    assert "Sidecars scanned: 1" in captured.out
    assert "Findings by severity:" in captured.out
    assert "Findings by category:" in captured.out
    assert "FINDINGS:" in captured.out
    assert "stats-span-invalid" in captured.out


def test_main_emits_json_when_flag_set(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload: dict[str, object] = {"id": "1.1.1", "spl": "| stats count by host span=1h"}
    monkeypatch.setattr(g, "iter_uc_sidecars", lambda: _stub_iter([(Path("stub.json"), payload)]))
    rc = g.main(["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert any(f["category"] == "stats-span-invalid" for f in data)


def test_main_check_returns_1_on_high_finding(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--check`` exits 1 when at least one finding is at or above ``--severity``."""
    payload: dict[str, object] = {"id": "1.1.1", "spl": "| stats count by host span=1h"}
    monkeypatch.setattr(g, "iter_uc_sidecars", lambda: _stub_iter([(Path("stub.json"), payload)]))
    rc = g.main(["--check"])
    assert rc == 1


def test_main_check_returns_0_when_severity_threshold_excludes_finding(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A MED finding does NOT trip ``--severity HIGH``."""
    payload: dict[str, object] = {
        "id": "1.1.1",
        "spl": 'eval x = case(host="prod-*", "high")',  # case-wildcard-literal == MED
    }
    monkeypatch.setattr(g, "iter_uc_sidecars", lambda: _stub_iter([(Path("stub.json"), payload)]))
    rc = g.main(["--check", "--severity", "HIGH"])
    assert rc == 0


def test_main_check_returns_0_when_no_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(g, "iter_uc_sidecars", lambda: _stub_iter([]))
    rc = g.main(["--check"])
    assert rc == 0
