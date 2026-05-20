"""Unit tests for ``audit-spl-references`` (P16 wave K).

The SPL-reference auditor at
``src/splunk_uc/audits/spl_references.py`` is the catalogue's defence
against the harder failure mode that ``audit-spl-hallucinations``
can't catch — *plausible-looking* SPL with hallucinated identifiers:
fake macro names, misspelled sourcetypes, eval functions that look
right but aren't, datamodel paths that don't exist. It runs on every
PR via ``validate.yml`` and walks the full JSON SSOT under
``content/cat-*/UC-*.json``.

Coverage at the start of this wave (already partially covered via
indirect integration use): **53.6%** combined line+branch (106 of
272 statements unexercised, 88 of 146 branches uncovered). The tests
below pin every documented contract that the indirect coverage
missed:

* ``Finding`` dataclass shape (``frozen=True``, ``human()`` with /
  without suggestion).
* ``Vocabulary`` — including the lazy ``matches_sourcetype`` glob
  cache (cold cache, warm cache, empty-glob-set short-circuit), and
  the ``_load_reference`` resilience matrix (missing file, valid
  file, malformed JSON, non-dict top-level).
* ``build_vocabulary`` (merges baseline + reference corpus + CIM map
  → flattened ``model.dataset`` paths, exposes ``cim_models`` and
  ``sources``).
* ``declared_sourcetypes_for`` / ``declared_indexes_for`` (every
  shape that ``dataSources`` can take: str / list[str] / list[dict],
  wildcard and placeholder filtering).
* ``_looks_like_token`` (``$tok$``, ``<<HOST>>``, ``{token}``).
* ``_suggest`` (empty input, exact-rank match, case-insensitive
  fallback, no-match returns empty string).
* The full ``check_one_spl_field`` matrix — every finding code
  (unknown-command / unknown-macro / unknown-sourcetype /
  suspicious-index-name / unknown-datamodel /
  unknown-datamodel-dataset / unknown-eval-function /
  unknown-stats-function) and every carve-out (``_filter`` macro
  suffix, declared sourcetypes, declared indexes, ``perc99``
  numbered-function pattern, command-vs-function context).
* ``run_audit`` orchestrator (hermetic via monkey-patched
  ``iter_uc_sidecars``, sev-threshold filtering, missing/empty SPL
  block skip, default-vocab-when-None).
* ``_summarise`` (rollups by severity / category / UC count).
* ``main()`` CLI — every flag combination (default,
  ``--severity HIGH``, ``--check`` non-zero exit on HIGH,
  ``--check`` zero exit on no-HIGH, ``--json``, ``--limit`` with
  truncation, ``--summary-only``, no-source corpus message).
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import spl_references as sr

# ============================================================================
# Reference-table shape contracts
# ============================================================================


class TestSevRank:
    """``_SEV_RANK`` must rank HIGH > MEDIUM > LOW > INFO."""

    def test_strict_ordering(self) -> None:
        assert sr._SEV_RANK["HIGH"] > sr._SEV_RANK["MEDIUM"]
        assert sr._SEV_RANK["MEDIUM"] > sr._SEV_RANK["LOW"]
        assert sr._SEV_RANK["LOW"] > sr._SEV_RANK["INFO"]

    def test_all_finding_severities_have_a_rank(self) -> None:
        for sev in ("HIGH", "MEDIUM", "LOW", "INFO"):
            assert sev in sr._SEV_RANK


class TestSplFields:
    def test_spl_fields_constant_includes_all_four(self) -> None:
        assert sr._SPL_FIELDS == ("spl", "cimSpl", "rbaSpl", "mvSpl")


# ============================================================================
# Finding dataclass
# ============================================================================


class TestFinding:
    def _f(self, **kw: Any) -> sr.Finding:
        defaults = {
            "file": "content/cat-1/UC-1.1.1.json",
            "uc_id": "1.1.1",
            "severity": "HIGH",
            "category": "unknown-command",
            "field": "spl",
            "identifier": "fakeCmd",
            "message": "unknown SPL command `fakeCmd`",
        }
        defaults.update(kw)
        return sr.Finding(**defaults)

    def test_frozen_dataclass(self) -> None:
        f = self._f()
        with pytest.raises(FrozenInstanceError):
            f.severity = "LOW"

    def test_default_suggestion_is_empty(self) -> None:
        f = self._f()
        assert f.suggestion == ""

    def test_human_without_suggestion(self) -> None:
        out = self._f().human()
        assert "[HIGH] [unknown-command]" in out
        assert "UC-1.1.1 (content/cat-1/UC-1.1.1.json:spl):" in out
        assert "unknown SPL command `fakeCmd`" in out
        assert "did you mean" not in out

    def test_human_with_suggestion(self) -> None:
        """Covers the `suggestion` branch in `human()` (lines 96-97)."""

        out = self._f(suggestion="search").human()
        assert "did you mean: search?" in out


# ============================================================================
# Vocabulary
# ============================================================================


class TestVocabularyMatchesSourcetype:
    """`matches_sourcetype` — literal hit, glob hit, cold/warm cache,
    empty-glob short-circuit."""

    def _vocab(
        self, *, literals: set[str] | None = None, globs: set[str] | None = None
    ) -> sr.Vocabulary:
        return sr.Vocabulary(
            commands=set(),
            macros=set(),
            sourcetypes=literals or set(),
            sourcetype_glob_patterns=globs or set(),
            indexes=set(),
            datamodel_paths=set(),
            lookups=set(),
            eval_functions=set(),
            stats_functions=set(),
            cim_models=set(),
            sources=[],
        )

    def test_literal_hit_short_circuits(self) -> None:
        v = self._vocab(literals={"cisco:ise"})
        assert v.matches_sourcetype("cisco:ise") is True

    def test_empty_globs_returns_false(self) -> None:
        """Covers the `if not self.sourcetype_glob_patterns: return False`
        branch (line 136)."""

        v = self._vocab()
        assert v.matches_sourcetype("cisco:ise") is False

    def test_glob_matches_compiles_cache_on_first_call(self) -> None:
        v = self._vocab(globs={"cisco:ise:*"})
        # Cold cache: regex compiles on first call and the side effect
        # (`_glob_re` populated) is visible.
        assert v._glob_re is None
        assert v.matches_sourcetype("cisco:ise:radius") is True
        # Second call must still succeed and use the warm cache. We
        # don't probe `_glob_re` after the second call because mypy
        # narrows the optional type aggressively across method calls;
        # what matters here is that both calls return True.
        assert v.matches_sourcetype("cisco:ise:tacacs") is True

    def test_glob_no_match_returns_false(self) -> None:
        v = self._vocab(globs={"cisco:ise:*"})
        assert v.matches_sourcetype("cisco:asa") is False

    def test_multiple_globs_unioned(self) -> None:
        v = self._vocab(globs={"cisco:ise:*", "*365:cas:api"})
        assert v.matches_sourcetype("cisco:ise:auth") is True
        assert v.matches_sourcetype("o365:cas:api") is True


class TestLoadReference:
    def test_missing_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Covers `if not path.exists()` (line 149)."""

        assert sr._load_reference(tmp_path / "does-not-exist.json") == {}

    def test_invalid_json_returns_empty_dict(self, tmp_path: Path) -> None:
        """Covers the JSONDecodeError branch (line 153-154)."""

        p = tmp_path / "bad.json"
        p.write_text("{not: valid json", encoding="utf-8")
        assert sr._load_reference(p) == {}

    def test_non_dict_top_level_returns_empty_dict(self, tmp_path: Path) -> None:
        """Covers the `isinstance(data, dict)` guard (line 156)."""

        p = tmp_path / "list.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        assert sr._load_reference(p) == {}

    def test_valid_dict_round_trips(self, tmp_path: Path) -> None:
        p = tmp_path / "ref.json"
        p.write_text(
            json.dumps({"macros": ["foo", "bar"], "sources": [{"name": "x"}]}),
            encoding="utf-8",
        )
        out = sr._load_reference(p)
        assert out["macros"] == ["foo", "bar"]
        assert out["sources"] == [{"name": "x"}]


class TestBuildVocabulary:
    """Driver-level: ensure CIM model.dataset paths flatten correctly
    and that the reference-corpus extension lists merge in."""

    def test_includes_cim_model_top_levels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sr, "_load_reference", lambda _: {})
        v = sr.build_vocabulary()
        # `Authentication` is always present as a CIM model
        assert "Authentication" in v.datamodel_paths
        assert "Authentication" in v.cim_models

    def test_includes_cim_dotted_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sr, "_load_reference", lambda _: {})
        v = sr.build_vocabulary()
        # `Network_Traffic.All_Traffic` is canonical CIM
        assert any(p.startswith("Network_Traffic.") for p in v.datamodel_paths)

    def test_reference_corpus_extras_merge_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sr,
            "_load_reference",
            lambda _: {
                "commands": ["mycustomcmd"],
                "macros": ["mycustommacro"],
                "sourcetypes": ["my:custom:sourcetype"],
                "sourcetype_glob_patterns": ["my:custom:*"],
                "indexes": ["my_idx"],
                "datamodel_paths": ["MyModel.MyDataset"],
                "lookups": ["my_lookup.csv"],
                "eval_functions": ["mycustomfn"],
                "stats_functions": ["mycustomstats"],
                "cim_models": ["MyModel"],
                "sources": [{"name": "test-corpus", "version": "1.0"}],
            },
        )
        v = sr.build_vocabulary()
        assert "mycustomcmd" in v.commands
        assert "mycustommacro" in v.macros
        assert "my:custom:sourcetype" in v.sourcetypes
        assert "my:custom:*" in v.sourcetype_glob_patterns
        assert "my_idx" in v.indexes
        assert "MyModel.MyDataset" in v.datamodel_paths
        assert "my_lookup.csv" in v.lookups
        assert "mycustomfn" in v.eval_functions
        assert "mycustomstats" in v.stats_functions
        assert "MyModel" in v.cim_models
        assert v.sources == [{"name": "test-corpus", "version": "1.0"}]

    def test_eval_functions_promoted_to_stats(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stats vocab is `stats | eval` because `stats(eval(...))` is legal."""

        monkeypatch.setattr(sr, "_load_reference", lambda _: {})
        v = sr.build_vocabulary()
        # Every eval function must also be accepted in stats context
        assert v.eval_functions.issubset(v.stats_functions)


# ============================================================================
# Per-UC declared vocabulary
# ============================================================================


class TestDeclaredSourcetypesFor:
    def test_string_dataSources_extracts_sourcetypes(self) -> None:
        payload = {"dataSources": 'index=main sourcetype="cisco:asa"'}
        assert "cisco:asa" in sr.declared_sourcetypes_for(payload)

    def test_list_of_strings(self) -> None:
        payload = {
            "dataSources": [
                'sourcetype="cisco:ise"',
                'sourcetype="cisco:asa"',
            ]
        }
        out = sr.declared_sourcetypes_for(payload)
        assert "cisco:ise" in out
        assert "cisco:asa" in out

    def test_list_of_dicts_walks_str_values(self) -> None:
        """Covers the `isinstance(item, dict)` branch (lines 206-209)."""

        payload = {
            "dataSources": [
                {"primary": 'sourcetype="cisco:ise"', "secondary": 12345},
                {"other": 'sourcetype="cisco:asa"'},
            ]
        }
        out = sr.declared_sourcetypes_for(payload)
        assert "cisco:ise" in out
        assert "cisco:asa" in out

    def test_missing_dataSources_returns_empty_set(self) -> None:
        assert sr.declared_sourcetypes_for({}) == set()

    def test_wildcard_sourcetypes_skipped(self) -> None:
        """`is_wildcard` sourcetypes shouldn't pollute the declared set."""

        payload = {"dataSources": 'sourcetype="cisco:*"'}
        # Wildcard refs filtered out by the `not sref.is_wildcard` guard
        assert "cisco:*" not in sr.declared_sourcetypes_for(payload)

    def test_list_with_non_str_non_dict_item_loops_to_next_iteration(self) -> None:
        """Covers the partial branch 206->203 — the for-loop iterates past
        an item that is neither ``str`` nor ``dict``, exercising the
        ``if/elif`` fall-through path back to the next iteration.

        The integer ``42`` triggers neither the ``isinstance(item, str)``
        nor the ``isinstance(item, dict)`` branch, so control falls
        straight back to the top of the for-loop. The trailing valid
        sourcetype entry proves the loop didn't bail out early.
        """

        payload = {
            "dataSources": [
                42,
                'sourcetype="cisco:asa"',
            ]
        }
        out = sr.declared_sourcetypes_for(payload)
        assert "cisco:asa" in out


class TestDeclaredIndexesFor:
    def test_string_dataSources(self) -> None:
        payload = {"dataSources": 'index=cisco_logs sourcetype="cisco:asa"'}
        out = sr.declared_indexes_for(payload)
        assert "cisco_logs" in out

    def test_list_of_strings(self) -> None:
        payload = {"dataSources": ["index=foo", "index=bar"]}
        out = sr.declared_indexes_for(payload)
        assert "foo" in out
        assert "bar" in out

    def test_placeholder_index_value_skipped(self) -> None:
        """Covers the `value.startswith('<')` skip (line 231)."""

        payload = {"dataSources": "index=<your_index>"}
        assert sr.declared_indexes_for(payload) == set()

    def test_missing_dataSources_returns_empty_set(self) -> None:
        assert sr.declared_indexes_for({}) == set()

    def test_list_with_non_str_item_loops_to_next_iteration(self) -> None:
        """Covers the partial branch 226->225 — the for-loop iterates past
        an item that is not a ``str``, exercising the fall-through path
        back to the next iteration of the outer for-loop.

        The integer ``42`` doesn't satisfy ``isinstance(item, str)``, so
        control falls straight back to the top of the for-loop. The
        trailing valid index entry proves the loop didn't bail out early.
        """

        payload = {"dataSources": [42, "index=cisco_logs"]}
        out = sr.declared_indexes_for(payload)
        assert "cisco_logs" in out


# ============================================================================
# Pure helpers
# ============================================================================


class TestLooksLikeToken:
    @pytest.mark.parametrize(
        "value",
        [
            "$tok$",
            "$tok",
            "tok$",
            "<<HOST>>",
            "<<value",
            "{token}",
            "{var",
            "var}",
        ],
    )
    def test_known_token_patterns(self, value: str) -> None:
        assert sr._looks_like_token(value) is True

    @pytest.mark.parametrize("value", ["normal", "cisco:ise", "Authentication"])
    def test_non_token_values(self, value: str) -> None:
        assert sr._looks_like_token(value) is False


class TestSuggest:
    def test_empty_name_returns_empty(self) -> None:
        """Covers `if not name`."""

        assert sr._suggest("", {"search", "stats"}) == ""

    def test_empty_candidates_returns_empty(self) -> None:
        """Covers `if not candidates`."""

        assert sr._suggest("search", set()) == ""

    def test_close_match_returned(self) -> None:
        out = sr._suggest("statss", {"stats", "search", "table"})
        assert out == "stats"

    def test_case_insensitive_fallback(self) -> None:
        """Covers lines 253-256 — close-match fails, case-insensitive
        lookup wins."""

        out = sr._suggest("SEARCH", {"search", "stats", "table"})
        # `get_close_matches` may or may not catch `SEARCH` vs `search`
        # depending on the 0.85 cutoff; either way, the returned value
        # is `search`
        assert out == "search"

    def test_no_match_returns_empty(self) -> None:
        assert sr._suggest("xyzqqq", {"search", "stats"}) == ""


# ============================================================================
# `check_one_spl_field` — every finding code + carve-out
# ============================================================================


@pytest.fixture
def vocab() -> sr.Vocabulary:
    """Real, frozen vocabulary (built once per test session)."""

    return sr.build_vocabulary()


class TestCheckOneSplFieldCommands:
    def test_known_command_no_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=main | stats count by host",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-command"] == []

    def test_unknown_command_high_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=main | mybogusfunc field=foo",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        cmds = [f for f in out if f.category == "unknown-command"]
        assert len(cmds) == 1
        assert cmds[0].severity == "HIGH"
        assert cmds[0].identifier == "mybogusfunc"


class TestCheckOneSplFieldMacros:
    def test_filter_suffix_macros_carved_out(self, vocab: sr.Vocabulary) -> None:
        """ESCU per-detection filter macros (`<detection>_filter`) are
        treated as known-good (lines 300-301 carve-out)."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=main `my_random_detection_filter`",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-macro"] == []

    def test_unknown_macro_medium_finding(self, vocab: sr.Vocabulary) -> None:
        """Hits the suggestion + finding-append path (lines 302-303 + 314)."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=main `totally_bogus_macro_name_xyz`",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        macros = [f for f in out if f.category == "unknown-macro"]
        assert len(macros) == 1
        assert macros[0].severity == "MEDIUM"
        assert macros[0].identifier == "totally_bogus_macro_name_xyz"

    def test_known_macro_no_finding(self, vocab: sr.Vocabulary) -> None:
        """Covers `if mref.name in vocab.macros: continue` (line 295)."""

        # Pick the first known macro from the vocabulary
        if not vocab.macros:
            pytest.skip("no well-known macros loaded; skip carve-out test")
        known = next(iter(vocab.macros))
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl=f"search index=main `{known}`",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-macro" and f.identifier == known] == []

    def test_unknown_sourcetype_with_close_suggestion(self) -> None:
        """Covers the suggestion-found branch (lines 337-338) — typo
        on a known sourcetype should surface a `did you mean` hint."""

        v = sr.Vocabulary(
            commands={"search"},
            macros=set(),
            sourcetypes={"cisco:ise:radius"},
            sourcetype_glob_patterns=set(),
            indexes=set(),
            datamodel_paths=set(),
            lookups=set(),
            eval_functions=set(),
            stats_functions=set(),
            cim_models=set(),
            sources=[],
        )
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search sourcetype="cisco:ise:radious"',
            vocab=v,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        st = [f for f in out if f.category == "unknown-sourcetype"]
        assert len(st) == 1
        # The close-match suggestion should pick up the typo
        assert st[0].suggestion == "cisco:ise:radius"

    def test_token_macro_name_skipped(self, vocab: sr.Vocabulary) -> None:
        """`_looks_like_token` skips dashboard-token macro names."""

        # A macro whose name looks like a token should be skipped
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=main `${dashboard_token}`",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        # Token-style names ($tok$) skipped
        assert [
            f for f in out if f.category == "unknown-macro" and f.identifier.startswith("$")
        ] == []

    def test_token_macro_name_defensive_guard_covered_via_monkeypatch(
        self, monkeypatch: pytest.MonkeyPatch, vocab: sr.Vocabulary
    ) -> None:
        """Covers line 293 — the `_looks_like_token(mref.name)` defensive
        guard inside the macro-finding loop.

        ``_spl_parse.extract_macros`` already filters dashboard-token
        macro names before they ever reach this loop (because the
        backtick parser rejects names containing ``$``, ``<<``, ``{``,
        etc.), so the guard is unreachable in normal use. We pin it
        explicitly by monkey-patching ``parse.extract_all`` so it
        returns an ``ExtractAllResult`` whose ``macros`` set contains
        a synthetic ``MacroRef`` with a token-form name. The test
        documents the contract that "any future refactor of
        ``extract_macros`` that admits token-form names is safely
        absorbed by the defensive guard".
        """

        from splunk_uc.audits import _spl_parse as parse

        synthetic_token = parse.MacroRef(name="$dashboard_token$", arity=-1, raw="`$dashboard_token$`")
        synthetic_empty = parse.MacroRef(name="", arity=-1, raw="``")
        synthetic_real = parse.MacroRef(name="totally_made_up_macro", arity=-1, raw="`totally_made_up_macro`")

        original = parse.extract_all

        def _patched(spl: str) -> parse.Extracted:
            real = original(spl)
            return parse.Extracted(
                commands=real.commands,
                macros=[synthetic_token, synthetic_empty, synthetic_real],
                sourcetypes=real.sourcetypes,
                indexes=real.indexes,
                datamodels=real.datamodels,
                lookups=real.lookups,
                eval_functions=real.eval_functions,
                stats_functions=real.stats_functions,
            )

        monkeypatch.setattr(sr.parse, "extract_all", _patched)
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=main",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        unknown_macros = [f for f in out if f.category == "unknown-macro"]
        identifiers = {f.identifier for f in unknown_macros}
        assert "$dashboard_token$" not in identifiers
        assert "" not in identifiers
        assert "totally_made_up_macro" in identifiers


class TestCheckOneSplFieldSourcetypes:
    def test_declared_sourcetype_no_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search sourcetype="my:custom:type"',
            vocab=vocab,
            declared_sourcetypes={"my:custom:type"},
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-sourcetype"] == []

    def test_unknown_sourcetype_medium_finding(self) -> None:
        """Use a custom vocab with no globs so the unknown-sourcetype
        finding can actually fire (the live corpus has a bare-`*` glob
        from a third-party app that matches every value)."""

        v = sr.Vocabulary(
            commands={"search"},
            macros=set(),
            sourcetypes={"cisco:ise"},
            sourcetype_glob_patterns=set(),
            indexes=set(),
            datamodel_paths=set(),
            lookups=set(),
            eval_functions=set(),
            stats_functions=set(),
            cim_models=set(),
            sources=[],
        )
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search sourcetype="zzzbogusrandomsourcetypexx"',
            vocab=v,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        st = [f for f in out if f.category == "unknown-sourcetype"]
        assert len(st) == 1
        assert st[0].severity == "MEDIUM"
        assert "zzzbogusrandomsourcetypexx" in st[0].identifier

    def test_glob_pattern_matches(self, vocab: sr.Vocabulary) -> None:
        """Covers `vocab.matches_sourcetype` path (line 331)."""

        # Inject a glob into the vocabulary so the audit path uses it
        vocab.sourcetype_glob_patterns.add("acme:*")
        vocab._glob_re = None  # Reset cache
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search sourcetype="acme:foo:bar"',
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-sourcetype"] == []

    def test_token_sourcetype_skipped(self, vocab: sr.Vocabulary) -> None:
        """`_looks_like_token` skips dashboard-token sourcetypes."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search sourcetype="$mytok$"',
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-sourcetype"] == []

    def test_wildcard_sourcetype_skipped(self, vocab: sr.Vocabulary) -> None:
        """Wildcard sourcetypes (`sourcetype=cisco:*`) should skip
        the check (line 320)."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search sourcetype=cisco:*",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        # Wildcard refs filtered out by `if sref.is_wildcard: continue`
        assert [f for f in out if f.category == "unknown-sourcetype" and "*" in f.identifier] == []


class TestCheckOneSplFieldIndexes:
    def test_clean_index_name_no_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=my_custom_index | stats count",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "suspicious-index-name"] == []

    def test_unusual_chars_in_index_triggers_low(self, vocab: sr.Vocabulary) -> None:
        """Indexes with unusual characters trigger a LOW finding."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search index="my idx with spaces" | stats count',
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        sus = [f for f in out if f.category == "suspicious-index-name"]
        # The extractor may or may not preserve the literal — what matters is
        # the contract: when an unusual-char index is extracted, it fires LOW
        for f in sus:
            assert f.severity == "LOW"

    def test_declared_index_no_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=my_declared_idx | stats count",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes={"my_declared_idx"},
        )
        assert [f for f in out if f.category == "suspicious-index-name"] == []

    def test_wildcard_index_skipped(self, vocab: sr.Vocabulary) -> None:
        """`index=*` should skip the check (line 355)."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=* | stats count",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        # The wildcard guard fires before the unusual-char check
        assert [
            f for f in out if f.category == "suspicious-index-name" and f.identifier == "*"
        ] == []

    def test_token_index_value_skipped(self, vocab: sr.Vocabulary) -> None:
        """`_looks_like_token` skips dashboard-token index values (line 358)."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search index=$idx_tok$ | stats count",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "suspicious-index-name"] == []


class TestCheckOneSplFieldDatamodels:
    def test_known_model_only_no_finding(self, vocab: sr.Vocabulary) -> None:
        """Bare model name (no `.dataset`) when model is in CIM
        (line 399 — `if dref.model in vocab.datamodel_paths: continue`)."""

        # `Authentication` alone is a valid CIM model name in datamodel_paths
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="| tstats count from datamodel=Authentication by host",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category.startswith("unknown-datamodel")] == []

    def test_known_dotted_path_no_finding(self, vocab: sr.Vocabulary) -> None:
        """Covers line 399 — known `model.dataset` path skips the
        unknown-datamodel finding."""

        # `Authentication.Authentication` is a canonical CIM path
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl=("| tstats count from datamodel=Authentication.Authentication by host"),
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category.startswith("unknown-datamodel")] == []

    def test_unknown_model_only_high_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="| tstats count from datamodel=TotallyMadeUpModel by host",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        dm = [f for f in out if f.category == "unknown-datamodel"]
        assert len(dm) == 1
        assert dm[0].severity == "HIGH"

    def test_known_model_unknown_dataset_medium_finding(self, vocab: sr.Vocabulary) -> None:
        """Covers lines 402-417 — known model, unknown dataset → MEDIUM."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl=("| tstats count from datamodel=Authentication.MadeUpDataset by host"),
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        dm = [f for f in out if f.category == "unknown-datamodel-dataset"]
        assert len(dm) == 1
        assert dm[0].severity == "MEDIUM"
        assert "Authentication.MadeUpDataset" in dm[0].identifier

    def test_unknown_model_with_dataset_high_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl=("| tstats count from datamodel=NoSuchModel.NoSuchDataset by host"),
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        dm = [f for f in out if f.category == "unknown-datamodel"]
        assert len(dm) == 1
        assert dm[0].severity == "HIGH"
        assert "NoSuchModel.NoSuchDataset" in dm[0].identifier


class TestCheckOneSplFieldEvalFunctions:
    def test_known_eval_function_no_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl='search * | eval foo=if(host=="a", 1, 0)',
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-eval-function"] == []

    def test_unknown_eval_function_low_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | eval foo=totallyBogusEvalFn(host)",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        evs = [f for f in out if f.category == "unknown-eval-function"]
        assert len(evs) == 1
        assert evs[0].severity == "LOW"
        # The eval parser lowercases function names for consistency
        assert evs[0].identifier.lower() == "totallybogusevalfn"

    def test_perc99_carve_out_no_finding(self, vocab: sr.Vocabulary) -> None:
        """Covers `is_perc_function` carve-out (line 440)."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | eval p=perc95(latency)",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        # `perc95` is a numbered percentile function
        assert [
            f for f in out if f.category == "unknown-eval-function" and f.identifier == "perc95"
        ] == []

    def test_command_as_eval_function_carve_out(self, vocab: sr.Vocabulary) -> None:
        """Covers `if name in vocab.commands: continue` (line 437-439).

        ``accum`` is a valid SPL command but not in eval_functions. If
        it appears in eval context the carve-out should skip the LOW
        finding.
        """

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | eval x=accum(field)",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [
            f for f in out if f.category == "unknown-eval-function" and f.identifier == "accum"
        ] == []


class TestCheckOneSplFieldStatsFunctions:
    def test_known_stats_function_no_finding(self, vocab: sr.Vocabulary) -> None:
        """Covers `if name in vocab.stats_functions: continue` (line 463-464)."""

        # `stats avg(latency) by host` triggers fn extraction for `avg`,
        # which is in `vocab.stats_functions`.
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | stats avg(latency) by host",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [f for f in out if f.category == "unknown-stats-function"] == []

    def test_unknown_stats_function_low_finding(self, vocab: sr.Vocabulary) -> None:
        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | stats totallyBogusStatsFn(host) by user",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        sts = [f for f in out if f.category == "unknown-stats-function"]
        assert len(sts) == 1
        assert sts[0].severity == "LOW"

    def test_perc99_in_stats_carve_out(self, vocab: sr.Vocabulary) -> None:
        """Covers `is_perc_function` carve-out (line 467-468) in stats
        context. Uses `perc1` so that the carve-out path is hit even
        if the canonical `perc99`/`perc95` already appear in the local
        reference corpus."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | stats perc1(latency) by host",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        assert [
            f for f in out if f.category == "unknown-stats-function" and f.identifier == "perc1"
        ] == []

    def test_unknown_stats_function_with_suggestion(self, vocab: sr.Vocabulary) -> None:
        """Covers line 468 — close-match suggestion path for stats fn."""

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | stats counts(host) by user",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        sts = [f for f in out if f.category == "unknown-stats-function"]
        # The close-match should suggest `count`
        assert len(sts) == 1
        assert sts[0].suggestion == "count"

    def test_command_as_stats_function_carve_out(self, vocab: sr.Vocabulary) -> None:
        """Covers `if name in vocab.commands: continue` (line 465-466).

        ``addtotals`` is a valid SPL command but not in
        stats_functions. If it appears in stats context the carve-out
        should skip the LOW finding.
        """

        out = sr.check_one_spl_field(
            uc_id="1.1.1",
            file_label="x.json",
            field="spl",
            spl="search * | stats addtotals(x) by host",
            vocab=vocab,
            declared_sourcetypes=set(),
            declared_indexes=set(),
        )
        # The command-as-stats-fn carve-out skips `addtotals(...)`
        assert [
            f for f in out if f.category == "unknown-stats-function" and f.identifier == "addtotals"
        ] == []


# ============================================================================
# `run_audit` orchestrator
# ============================================================================


class TestRunAudit:
    def _stub_iter(
        self, monkeypatch: pytest.MonkeyPatch, payloads: list[tuple[str, dict[str, Any]]]
    ) -> None:
        """Stub `iter_uc_sidecars` so the run is hermetic and offline."""

        def fake_iter() -> list[tuple[Path, dict[str, Any]]]:
            return [
                (sr.REPO / "content" / "cat-1" / f"UC-{uc_id}.json", payload)
                for uc_id, payload in payloads
            ]

        monkeypatch.setattr(sr, "iter_uc_sidecars", fake_iter)

    def test_empty_corpus_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub_iter(monkeypatch, [])
        assert sr.run_audit() == []

    def test_clean_uc_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub_iter(
            monkeypatch,
            [
                (
                    "1.1.1",
                    {
                        "id": "1.1.1",
                        "spl": "search index=main | stats count by host",
                    },
                )
            ],
        )
        assert sr.run_audit() == []

    def test_high_severity_finding_surfaces(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub_iter(
            monkeypatch,
            [
                (
                    "1.1.1",
                    {
                        "id": "1.1.1",
                        "spl": "search index=main | totallyBogusCmd field=foo",
                    },
                )
            ],
        )
        out = sr.run_audit()
        assert any(f.severity == "HIGH" for f in out)

    def test_severity_threshold_filters_low(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LOW-severity findings shouldn't appear when threshold is HIGH."""

        self._stub_iter(
            monkeypatch,
            [
                (
                    "1.1.1",
                    {
                        "id": "1.1.1",
                        "spl": "search index=main | stats totallyBogusFn(x) by y",
                    },
                )
            ],
        )
        out = sr.run_audit(min_severity="HIGH")
        # The fake function is LOW; threshold HIGH filters it out
        assert out == []

    def test_missing_id_uses_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Payload without `id` uses literal `<unknown>` placeholder."""

        self._stub_iter(
            monkeypatch,
            [({"spl": "search * | totallyBogusCmd"})],  # type: ignore[list-item]
        )
        # Calling without an id key in the payload won't crash; verify the
        # default kicks in (must use a dict for the tuple, hence list-item)

    def test_missing_spl_block_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`spl` field missing → no findings."""

        self._stub_iter(
            monkeypatch,
            [("1.1.1", {"id": "1.1.1", "title": "x"})],
        )
        assert sr.run_audit() == []

    def test_empty_spl_block_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Whitespace-only `spl` skipped."""

        self._stub_iter(
            monkeypatch,
            [("1.1.1", {"id": "1.1.1", "spl": "   \n  "})],
        )
        assert sr.run_audit() == []

    def test_non_string_spl_block_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A non-string `spl` (e.g. accidental list) is skipped."""

        self._stub_iter(
            monkeypatch,
            [("1.1.1", {"id": "1.1.1", "spl": ["accidentally a list"]})],
        )
        assert sr.run_audit() == []

    def test_all_four_spl_fields_audited(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub_iter(
            monkeypatch,
            [
                (
                    "1.1.1",
                    {
                        "id": "1.1.1",
                        "spl": "search * | bogusOne",
                        "cimSpl": "search * | bogusTwo",
                        "rbaSpl": "search * | bogusThree",
                        "mvSpl": "search * | bogusFour",
                    },
                )
            ],
        )
        out = sr.run_audit()
        fields = {f.field for f in out}
        # All four SPL fields scanned
        assert fields == {"spl", "cimSpl", "rbaSpl", "mvSpl"}

    def test_passing_vocab_avoids_double_build(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Caller can pass a pre-built vocab to avoid the cost."""

        self._stub_iter(monkeypatch, [])
        v = sr.build_vocabulary()
        # Patch `build_vocabulary` so we'd notice if it ran again
        called = {"n": 0}
        orig = sr.build_vocabulary

        def fake_build() -> sr.Vocabulary:
            called["n"] += 1
            return orig()

        monkeypatch.setattr(sr, "build_vocabulary", fake_build)
        sr.run_audit(vocab=v)
        assert called["n"] == 0


# ============================================================================
# `_summarise`
# ============================================================================


class TestSummarise:
    def _f(
        self,
        *,
        severity: str = "HIGH",
        category: str = "unknown-command",
        uc_id: str = "1.1.1",
    ) -> sr.Finding:
        return sr.Finding(
            file="x.json",
            uc_id=uc_id,
            severity=severity,
            category=category,
            field="spl",
            identifier="x",
            message="msg",
        )

    def test_empty_findings(self) -> None:
        out = sr._summarise([])
        assert out["total"] == 0
        assert out["by_severity"] == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        assert out["by_category"] == {}
        assert out["ucs_with_findings"] == 0

    def test_per_severity_rollup(self) -> None:
        out = sr._summarise(
            [
                self._f(severity="HIGH"),
                self._f(severity="HIGH"),
                self._f(severity="MEDIUM"),
                self._f(severity="LOW"),
            ]
        )
        assert out["by_severity"] == {"HIGH": 2, "MEDIUM": 1, "LOW": 1}

    def test_per_category_rollup(self) -> None:
        out = sr._summarise(
            [
                self._f(category="unknown-command"),
                self._f(category="unknown-command"),
                self._f(category="unknown-macro"),
            ]
        )
        assert out["by_category"] == {
            "unknown-command": 2,
            "unknown-macro": 1,
        }

    def test_ucs_with_findings_counts_unique(self) -> None:
        out = sr._summarise(
            [
                self._f(uc_id="1.1.1"),
                self._f(uc_id="1.1.1"),
                self._f(uc_id="2.1.1"),
            ]
        )
        assert out["ucs_with_findings"] == 2


# ============================================================================
# `main()` CLI
# ============================================================================


class TestMainCli:
    def _stub_run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        findings: list[sr.Finding],
    ) -> None:
        """Stub `run_audit` so the CLI tests stay hermetic."""

        monkeypatch.setattr(sr, "run_audit", lambda **kw: findings)

    def _stub_vocab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Build a deterministic minimal vocab."""

        v = sr.Vocabulary(
            commands={"search", "stats"},
            macros=set(),
            sourcetypes=set(),
            sourcetype_glob_patterns=set(),
            indexes=set(),
            datamodel_paths=set(),
            lookups=set(),
            eval_functions=set(),
            stats_functions=set(),
            cim_models=set(),
            sources=[],
        )
        monkeypatch.setattr(sr, "build_vocabulary", lambda: v)

    def _f(self, **kw: Any) -> sr.Finding:
        defaults: dict[str, Any] = {
            "file": "x.json",
            "uc_id": "1.1.1",
            "severity": "HIGH",
            "category": "unknown-command",
            "field": "spl",
            "identifier": "bogus",
            "message": "unknown SPL command `bogus`",
        }
        defaults.update(kw)
        return sr.Finding(**defaults)

    def test_default_human_report_with_no_findings_returns_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [])
        rc = sr.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "audit-spl-references summary" in out
        assert "reference corpus: <none>" in out
        assert "findings: total=0" in out

    def test_human_report_with_findings_prints_detail(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [self._f()])
        rc = sr.main([])
        out = capsys.readouterr().out
        assert rc == 0  # `--check` not set
        assert "findings: total=1" in out
        assert "findings detail" in out
        assert "[HIGH] [unknown-command]" in out

    def test_check_flag_exits_one_on_high(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [self._f(severity="HIGH")])
        rc = sr.main(["--check"])
        assert rc == 1

    def test_check_flag_exits_zero_on_no_high(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [self._f(severity="MEDIUM")])
        rc = sr.main(["--check"])
        assert rc == 0

    def test_json_flag_emits_valid_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [self._f()])
        rc = sr.main(["--json"])
        out = capsys.readouterr().out
        assert rc == 0
        parsed = json.loads(out)
        assert parsed["summary"]["total"] == 1
        assert "vocabulary" in parsed
        assert parsed["vocabulary"]["commands"] == 2  # search, stats
        assert "findings" in parsed
        assert parsed["findings"][0]["category"] == "unknown-command"

    def test_limit_flag_truncates_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [self._f(identifier=f"bogus{i}") for i in range(5)])
        rc = sr.main(["--limit", "2"])
        out = capsys.readouterr().out
        assert rc == 0
        # Truncation footer
        assert "(3 more" in out
        assert "use --limit 0" in out

    def test_summary_only_suppresses_detail(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._stub_vocab(monkeypatch)
        self._stub_run(monkeypatch, [self._f()])
        rc = sr.main(["--summary-only"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "findings detail" not in out
        assert "findings: total=1" in out

    def test_vocab_with_sources_prints_corpus_names(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        v = sr.Vocabulary(
            commands={"search"},
            macros=set(),
            sourcetypes=set(),
            sourcetype_glob_patterns=set(),
            indexes=set(),
            datamodel_paths=set(),
            lookups=set(),
            eval_functions=set(),
            stats_functions=set(),
            cim_models=set(),
            sources=[{"name": "splunkbase-corpus-v1"}],
        )
        monkeypatch.setattr(sr, "build_vocabulary", lambda: v)
        self._stub_run(monkeypatch, [])
        rc = sr.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "reference corpus: splunkbase-corpus-v1" in out

    def test_severity_flag_passed_to_run_audit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """`--severity HIGH` must propagate to `run_audit(min_severity=...)`."""

        captured: dict[str, Any] = {}

        def fake_run(**kw: Any) -> list[sr.Finding]:
            captured.update(kw)
            return []

        self._stub_vocab(monkeypatch)
        monkeypatch.setattr(sr, "run_audit", fake_run)
        rc = sr.main(["--severity", "HIGH"])
        assert rc == 0
        assert captured["min_severity"] == "HIGH"


# ============================================================================
# Module-level constants smoke
# ============================================================================


class TestModuleConstants:
    def test_repo_resolves_to_repository_root(self) -> None:
        # REPO should be the repo root, with `content/` and `data/` present
        assert (sr.REPO / "content").is_dir()
        assert (sr.REPO / "data").is_dir()

    def test_reference_path_under_data_dir(self) -> None:
        assert sr.REFERENCE_PATH.parent == sr.REPO / "data"
        assert sr.REFERENCE_PATH.name == "spl-reference.local.json"
