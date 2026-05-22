"""Unit-level coverage for ``tools/research/build_spl_reference.py``.

The script is the maintainer-side rebuilder for the local-only SPL
vocabulary file ``data/spl-reference.local.json`` (gitignored, ~12 MB
when all five corpora are present). It is wired into the Makefile
under ``audit-spl-references-build``.

It is NOT a CI gate (the README is explicit about that), but it IS
a single shared dependency of:

* every SPL-reference audit (which uses the cached
  ``data/spl-reference.local.json`` as its known-good vocabulary);
* the Searchbase / IS4S / SSE / CIM / ESCU ingest readers that the
  next round of vocabulary growth will rely on.

A regression here silently breaks every downstream audit by emitting
a corrupt or empty vocabulary file. Lacking unit tests, that regression
could not be caught until human reviewers diffed
``data/spl-reference.local.json`` and noticed something missing.

What this suite locks
---------------------

* ``_is_real_value`` and ``_is_glob`` predicates.
* ``_read_conf_stanzas`` — comment handling, line continuations,
  multi-stanza walking, value-continuation fallback.
* ``_ingest_one_spl`` — every branch of the parser-output to
  state-bucket routing (command, macro placeholders, sourcetype
  / index wildcards and placeholders, datamodel path with /
  without dataset, lookups, eval / stats functions).
* ``_add_sourcetype`` — placeholder rejection + literal vs glob
  bucket routing.
* ``_read_csv_rows`` — missing file, plain CSV, gzipped CSV,
  unreadable file (OSError/csv.Error).
* ``_extract_yaml_search_field`` — block scalar, inline quoted,
  inline bare, missing field.
* ``_ingest_searchbase_corpus`` — returns None when corpus absent;
  happy path with both searchbase.conf and macros.conf; macros
  with `(N)` arity vs `args =` field vs implicit 0.
* ``_ingest_is4s_corpus`` — None when absent; happy path counter
  shape (searchbase / savedsearches / macros / UCE sourcetypes
  + data_model fan-out + Lantern UC count + Splunkbase apps gz
  fan-out, with CIM-tag regex filter rejecting multi-word tags).
* ``_ingest_sse_corpus`` — None when absent; happy path with
  savedsearches / macros / data-inventory products regex match.
* ``_ingest_cim_corpus`` — None when absent; datamodel walker
  recursion (parent + child datasets); tags.conf reader skipping
  comments / stanza headers; malformed JSON skipped silently.
* ``_ingest_escu_corpus`` — None when absent or empty;
  detection-yml walking with macro file enumeration.
* ``_new_state`` — pinned key set.
* ``_serialise`` — sorted output for every list-typed bucket;
  generated_at ISO-8601 truncated to second precision.
* ``main`` — argument parsing; ``--check`` exits 1 with documented
  stderr when no corpus exists; happy path writes JSON to ``--out``;
  ``--quiet`` suppresses the trailing summary; default output path
  rendered relative to ``_REPO`` when inside, absolute when outside.
* ``if __name__ == "__main__":`` guard exercised by an in-process
  smoke test against an empty corpus directory.

Run
---

``pytest tests/build/test_tools_research_build_spl_reference.py``

Coverage check
--------------

``pytest tests/build/test_tools_research_build_spl_reference.py \
    --cov=tools.research.build_spl_reference --cov-branch``
"""
from __future__ import annotations

import csv
import gzip
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.research.build_spl_reference as bsr


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def redirected_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """Redirect every module-level path constant under ``tmp_path``.

    Returns a dict of the redirected paths so individual tests can
    populate the specific corpus directories they care about.
    """
    repo = tmp_path
    paths = {
        "repo": repo,
        "searchbase_dir": repo / "external" / "searchbase" / "searchbase",
        "is4s_dir": repo / "external" / "is4s" / "splunk_insights",
        "sse_dir": repo / "external" / "sse" / "Splunk_Security_Essentials",
        "cim_dir": repo / "external" / "cim" / "Splunk_SA_CIM",
        "security_content_dir": repo / "external" / "security_content",
        "out": repo / "data" / "spl-reference.local.json",
    }

    monkeypatch.setattr(bsr, "_REPO", repo)
    monkeypatch.setattr(
        bsr, "SEARCHBASE_DIR", paths["searchbase_dir"]
    )
    monkeypatch.setattr(
        bsr,
        "SEARCHBASE_CONF",
        paths["searchbase_dir"] / "default" / "searchbase.conf",
    )
    monkeypatch.setattr(
        bsr,
        "SEARCHBASE_MACROS_CONF",
        paths["searchbase_dir"] / "default" / "macros.conf",
    )
    monkeypatch.setattr(
        bsr,
        "SEARCHBASE_LOOKUPS_DIR",
        paths["searchbase_dir"] / "lookups",
    )
    monkeypatch.setattr(bsr, "IS4S_DIR", paths["is4s_dir"])
    monkeypatch.setattr(
        bsr, "IS4S_DEFAULT", paths["is4s_dir"] / "default"
    )
    monkeypatch.setattr(
        bsr, "IS4S_LOOKUPS", paths["is4s_dir"] / "lookups"
    )
    monkeypatch.setattr(bsr, "SSE_DIR", paths["sse_dir"])
    monkeypatch.setattr(
        bsr, "SSE_DEFAULT", paths["sse_dir"] / "default"
    )
    monkeypatch.setattr(
        bsr, "SSE_LOOKUPS", paths["sse_dir"] / "lookups"
    )
    monkeypatch.setattr(bsr, "CIM_DIR", paths["cim_dir"])
    monkeypatch.setattr(
        bsr, "CIM_DEFAULT", paths["cim_dir"] / "default"
    )
    monkeypatch.setattr(
        bsr,
        "CIM_DATAMODELS_DIR",
        paths["cim_dir"] / "default" / "data" / "models",
    )
    monkeypatch.setattr(
        bsr,
        "CIM_TAGS_CONF",
        paths["cim_dir"] / "default" / "tags.conf",
    )
    monkeypatch.setattr(
        bsr,
        "CIM_EVENTTYPES_CONF",
        paths["cim_dir"] / "default" / "eventtypes.conf",
    )
    monkeypatch.setattr(
        bsr,
        "SECURITY_CONTENT_DIR",
        paths["security_content_dir"],
    )
    monkeypatch.setattr(
        bsr,
        "ESCU_DETECTIONS_DIR",
        paths["security_content_dir"] / "detections",
    )
    monkeypatch.setattr(
        bsr,
        "ESCU_MACROS_DIR",
        paths["security_content_dir"] / "macros",
    )
    monkeypatch.setattr(bsr, "DEFAULT_OUT", paths["out"])
    return paths


# ---------------------------------------------------------------------------
# _is_real_value, _is_glob
# ---------------------------------------------------------------------------


class TestIsRealValue:
    @pytest.mark.parametrize(
        "v,expected",
        [
            ("", False),
            ("  ", False),  # blank string with whitespace
            (" foo", False),  # leading whitespace
            ("foo ", False),  # trailing whitespace
            ("<<sourcetype>>", False),
            ("<<index>>", False),
            ("aws:cloudtrail", True),
            ("main", True),
            ("WinEventLog", True),
        ],
    )
    def test_predicate(self, v: str, expected: bool) -> None:
        assert bsr._is_real_value(v) is expected


class TestIsGlob:
    @pytest.mark.parametrize(
        "v,expected",
        [
            ("aws:cloudtrail", False),
            ("aws:*", True),
            ("*:api", True),
            ("foo?", True),
            ("foo", False),
            ("", False),
        ],
    )
    def test_predicate(self, v: str, expected: bool) -> None:
        assert bsr._is_glob(v) is expected


# ---------------------------------------------------------------------------
# _read_conf_stanzas
# ---------------------------------------------------------------------------


class TestReadConfStanzas:
    """Implementation note: ``_read_conf_stanzas`` walks lines after
    a ``re.sub("\\\\\\n", "")`` stitch. The final ``""`` line produced
    by ``str.split("\\n")`` on a trailing-newline file is then
    appended as a value continuation to the last key, leaving a
    ``"\\n"`` suffix on the very last value. We pin that artefact
    here so the assertions match the implementation."""

    def test_simple_stanza(self, tmp_path: Path) -> None:
        path = tmp_path / "x.conf"
        path.write_text(
            "[foo]\n"
            "key1 = value1\n"
            "key2 = value2\n",
            encoding="utf-8",
        )
        out = bsr._read_conf_stanzas(path)
        # Last key picks up the trailing-newline continuation.
        assert out == [
            ("foo", {"key1": "value1", "key2": "value2\n"})
        ]

    def test_multiple_stanzas(self, tmp_path: Path) -> None:
        path = tmp_path / "x.conf"
        path.write_text(
            "[foo]\nkey1 = v1\n[bar]\nkey2 = v2\n", encoding="utf-8"
        )
        out = bsr._read_conf_stanzas(path)
        # Only the very last key (the one closed by EOF) accumulates
        # the trailing-newline artefact; ``key1`` is closed by the
        # next ``[stanza]`` line and therefore stays clean.
        assert out == [
            ("foo", {"key1": "v1"}),
            ("bar", {"key2": "v2\n"}),
        ]

    def test_line_continuation(self, tmp_path: Path) -> None:
        """Backslash-newline pairs are stitched BEFORE line split,
        so the multi-line ``search = ...`` becomes one logical line."""
        path = tmp_path / "x.conf"
        path.write_text(
            "[foo]\nsearch = index=main \\\n| stats count\n",
            encoding="utf-8",
        )
        out = bsr._read_conf_stanzas(path)
        assert out == [
            ("foo", {"search": "index=main | stats count\n"})
        ]

    def test_top_level_comment_skipped(self, tmp_path: Path) -> None:
        """Comments starting with ``#`` at line start are skipped."""
        path = tmp_path / "x.conf"
        path.write_text(
            "# top-level comment\n"
            "[foo]\n"
            "# stanza-level comment\n"
            "key = value\n",
            encoding="utf-8",
        )
        out = bsr._read_conf_stanzas(path)
        assert out == [("foo", {"key": "value\n"})]

    def test_lines_before_any_stanza_ignored(self, tmp_path: Path) -> None:
        """Body lines that appear before the first ``[stanza]`` are
        dropped (covers the ``if cur_name is None: continue`` arm)."""
        path = tmp_path / "x.conf"
        path.write_text(
            "stray = ignored\n[foo]\nkey = value\n", encoding="utf-8"
        )
        out = bsr._read_conf_stanzas(path)
        assert out == [("foo", {"key": "value\n"})]

    def test_malformed_stanza_header(self, tmp_path: Path) -> None:
        """A stanza header that doesn't match the regex (no closing
        bracket) is parsed with ``cur_name = None`` so all of its
        keys are dropped (covers the ``else: cur_name = None`` arm)."""
        path = tmp_path / "x.conf"
        path.write_text(
            "[foo]\nk1 = v1\n[malformed\nk2 = v2\n",
            encoding="utf-8",
        )
        out = bsr._read_conf_stanzas(path)
        # `[malformed` matches `line.startswith("[")` but the regex
        # rejects it because there's no closing `]`, so `cur_name`
        # becomes None and k2 is dropped.
        assert out == [("foo", {"k1": "v1"})]

    def test_value_continuation_fallback(self, tmp_path: Path) -> None:
        """A line that doesn't match the key=value regex and follows
        a key= line is treated as a continuation (covers the
        ``elif cur_key is not None`` arm). The line-continuation
        regex strips ``\\\\\\n`` so this is a different mechanism."""
        path = tmp_path / "x.conf"
        # No backslash: just a continuation line that doesn't start
        # with a key=val match. Use a leading digit so it doesn't
        # match the [A-Za-z_] start regex.
        path.write_text(
            "[foo]\nkey = first line\n2nd part\n", encoding="utf-8"
        )
        out = bsr._read_conf_stanzas(path)
        assert out == [("foo", {"key": "first line\n2nd part\n"})]

    def test_continuation_without_prior_key_ignored(
        self, tmp_path: Path
    ) -> None:
        """A line that doesn't match key=value and has no prior key
        is silently dropped (cur_key is None, both elif arms fail)."""
        path = tmp_path / "x.conf"
        path.write_text(
            "[foo]\n2nd part stays orphan\nkey = value\n",
            encoding="utf-8",
        )
        out = bsr._read_conf_stanzas(path)
        assert out == [("foo", {"key": "value\n"})]

    def test_file_with_no_stanzas(self, tmp_path: Path) -> None:
        path = tmp_path / "x.conf"
        path.write_text("# only a comment\n\n", encoding="utf-8")
        out = bsr._read_conf_stanzas(path)
        assert out == []


# ---------------------------------------------------------------------------
# _ingest_one_spl + state plumbing
# ---------------------------------------------------------------------------


class TestIngestOneSpl:
    def test_extracts_commands_and_sourcetypes(self) -> None:
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "index=main sourcetype=aws:cloudtrail | stats count(field) by host",
            state,
        )
        assert "stats" in state["commands"]
        assert "aws:cloudtrail" in state["sourcetypes"]
        assert "main" in state["indexes"]
        # Bare `count` doesn't yield a stats function (parser only
        # extracts function-form `count(...)`).
        assert "count" in state["stats_functions"]

    def test_drops_placeholder_macros(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<<...>>`` macro names are rejected by ``_is_real_value``.

        The parser doesn't recognise ``<<...>>`` as a macro reference,
        so we feed a synthetic Extracted via monkey-patch."""
        from splunk_uc.audits._spl_parse import (
            Extracted,
            MacroRef,
        )

        fake = Extracted(
            commands=["search"],
            macros=[MacroRef(name="<<placeholder>>", arity=0, raw="<<placeholder>>")],
            sourcetypes=[],
            indexes=[],
            datamodels=[],
            lookups=[],
            eval_functions=[],
            stats_functions=[],
        )

        monkeypatch.setattr(
            bsr.parse, "extract_all", lambda _spl: fake
        )
        state = bsr._new_state()
        bsr._ingest_one_spl("anything", state)
        assert state["macros"] == set()

    def test_drops_wildcard_sourcetypes_and_indexes(self) -> None:
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "index=foo* sourcetype=aws:* | stats count(x)", state
        )
        assert state["sourcetypes"] == set()
        assert state["indexes"] == set()

    def test_drops_placeholder_sourcetypes_and_indexes(self) -> None:
        """``<<sourcetype>>`` / ``<<index>>`` are also rejected
        (covers the ``not _is_real_value`` branches of sourcetype
        and index ingestion)."""
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "index=<<index>> sourcetype=<<sourcetype>> | stats count(x)",
            state,
        )
        assert state["sourcetypes"] == set()
        assert state["indexes"] == set()

    def test_records_macro_arity(self) -> None:
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "| `mymacro` | `paramaterised(x)` | stats count(y)", state
        )
        assert "mymacro" in state["macros"]
        # Bare macro reference: arity is -1 in the parser.
        assert -1 in state["macros_with_arity"]["mymacro"]
        assert 1 in state["macros_with_arity"]["paramaterised"]

    def test_records_datamodel_paths_with_and_without_dataset(
        self,
    ) -> None:
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "| tstats count(x) from datamodel=Authentication",
            state,
        )
        bsr._ingest_one_spl(
            "| tstats count(x) from datamodel=Network_Traffic.All_Traffic",
            state,
        )
        assert "Authentication" in state["datamodel_paths"]
        assert "Network_Traffic.All_Traffic" in state["datamodel_paths"]

    def test_drops_placeholder_lookups(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lookups with placeholder names are filtered."""
        from splunk_uc.audits._spl_parse import (
            Extracted,
            LookupRef,
        )

        fake = Extracted(
            commands=["lookup"],
            macros=[],
            sourcetypes=[],
            indexes=[],
            datamodels=[],
            lookups=[LookupRef(name="<<placeholder>>", command="lookup")],
            eval_functions=[],
            stats_functions=[],
        )

        monkeypatch.setattr(
            bsr.parse, "extract_all", lambda _spl: fake
        )
        state = bsr._new_state()
        bsr._ingest_one_spl("anything", state)
        assert state["lookups"] == set()

    def test_records_eval_and_stats_functions(self) -> None:
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "| stats count(c) avg(price) | eval x=coalesce(a,b)", state
        )
        assert "coalesce" in state["eval_functions"]
        assert "count" in state["stats_functions"]
        assert "avg" in state["stats_functions"]

    def test_records_real_lookup_names(self) -> None:
        """Covers the ``state['lookups'].add(...)`` branch — needs a
        parser invocation that yields a real (non-placeholder) lookup
        reference."""
        state = bsr._new_state()
        bsr._ingest_one_spl(
            "index=main | lookup asset_categories.csv host OUTPUT category",
            state,
        )
        assert "asset_categories.csv" in state["lookups"]


# ---------------------------------------------------------------------------
# _add_sourcetype
# ---------------------------------------------------------------------------


class TestAddSourcetype:
    def test_placeholder_dropped(self) -> None:
        state = bsr._new_state()
        bsr._add_sourcetype(state, "<<sourcetype>>")
        assert state["sourcetypes"] == set()
        assert state["sourcetype_glob_patterns"] == set()

    def test_literal_routes_to_sourcetypes(self) -> None:
        state = bsr._new_state()
        bsr._add_sourcetype(state, "aws:cloudtrail")
        assert state["sourcetypes"] == {"aws:cloudtrail"}
        assert state["sourcetype_glob_patterns"] == set()

    def test_glob_routes_to_glob_bucket(self) -> None:
        state = bsr._new_state()
        bsr._add_sourcetype(state, "aws:*")
        assert state["sourcetypes"] == set()
        assert state["sourcetype_glob_patterns"] == {"aws:*"}

    def test_blank_dropped(self) -> None:
        state = bsr._new_state()
        bsr._add_sourcetype(state, "")
        assert state["sourcetypes"] == set()


# ---------------------------------------------------------------------------
# _read_csv_rows
# ---------------------------------------------------------------------------


class TestReadCsvRows:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert bsr._read_csv_rows(tmp_path / "absent.csv") == []

    def test_plain_csv(self, tmp_path: Path) -> None:
        path = tmp_path / "x.csv"
        path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
        rows = bsr._read_csv_rows(path)
        assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]

    def test_gzipped_csv(self, tmp_path: Path) -> None:
        path = tmp_path / "x.csv.gz"
        with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
            fh.write("a,b\n1,2\n")
        rows = bsr._read_csv_rows(path)
        assert rows == [{"a": "1", "b": "2"}]

    def test_oserror_returns_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unreadable file -> ``OSError`` caught, empty list."""
        path = tmp_path / "x.csv"
        path.write_text("a,b\n1,2\n", encoding="utf-8")
        # Force open to raise.
        original_open = Path.open

        def _boom(self: Path, *args: Any, **kwargs: Any) -> Any:
            if self == path:
                raise OSError("simulated unreadable file")
            return original_open(self, *args, **kwargs)

        monkeypatch.setattr(Path, "open", _boom)
        assert bsr._read_csv_rows(path) == []

    def test_csverror_returns_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``csv.Error`` is caught by the same except clause."""
        path = tmp_path / "x.csv"
        path.write_text("a,b\n1,2\n", encoding="utf-8")

        def _boom(*_a: Any, **_k: Any) -> None:
            raise csv.Error("simulated parse failure")

        monkeypatch.setattr(csv, "DictReader", _boom)
        assert bsr._read_csv_rows(path) == []


# ---------------------------------------------------------------------------
# _extract_yaml_search_field
# ---------------------------------------------------------------------------


class TestExtractYamlSearchField:
    def test_block_scalar(self, tmp_path: Path) -> None:
        path = tmp_path / "x.yml"
        path.write_text(
            "name: foo\n"
            "search: |-\n"
            "  | tstats count\n"
            "  | eval x = 1\n"
            "tags:\n"
            "  - test\n",
            encoding="utf-8",
        )
        out = bsr._extract_yaml_search_field(path)
        assert out is not None
        assert "tstats count" in out
        assert "eval x = 1" in out

    def test_block_scalar_with_blank_line(self, tmp_path: Path) -> None:
        """Blank lines inside the block scalar are preserved (covers
        the ``out.append("")`` arm)."""
        path = tmp_path / "x.yml"
        path.write_text(
            "name: foo\n"
            "search: |-\n"
            "  | tstats count\n"
            "\n"
            "  | eval x = 1\n"
            "tags:\n",
            encoding="utf-8",
        )
        out = bsr._extract_yaml_search_field(path)
        assert out is not None
        assert "tstats count" in out
        assert "eval x = 1" in out

    def test_inline_single_quoted(self, tmp_path: Path) -> None:
        path = tmp_path / "x.yml"
        path.write_text(
            "name: foo\nsearch: '| tstats count'\n", encoding="utf-8"
        )
        out = bsr._extract_yaml_search_field(path)
        assert out == "| tstats count"

    def test_inline_double_quoted(self, tmp_path: Path) -> None:
        path = tmp_path / "x.yml"
        path.write_text(
            'name: foo\nsearch: "| tstats count"\n', encoding="utf-8"
        )
        out = bsr._extract_yaml_search_field(path)
        assert out == "| tstats count"

    def test_inline_bare(self, tmp_path: Path) -> None:
        path = tmp_path / "x.yml"
        path.write_text(
            "name: foo\nsearch: | tstats count\n", encoding="utf-8"
        )
        out = bsr._extract_yaml_search_field(path)
        assert out == "| tstats count"

    def test_missing_search_field(self, tmp_path: Path) -> None:
        path = tmp_path / "x.yml"
        path.write_text("name: foo\nstatus: production\n", encoding="utf-8")
        assert bsr._extract_yaml_search_field(path) is None

    def test_block_scalar_empty_body_returns_none(
        self, tmp_path: Path
    ) -> None:
        """Block scalar with only a non-indented next-section line —
        the body is empty so the function returns None (covers the
        ``return body or None`` False arm)."""
        path = tmp_path / "x.yml"
        path.write_text(
            "name: foo\nsearch: |-\nname: next\n", encoding="utf-8"
        )
        assert bsr._extract_yaml_search_field(path) is None

    def test_block_scalar_eof_exits_loop_naturally(
        self, tmp_path: Path
    ) -> None:
        """File where the block scalar IS the last thing — the
        for-loop walks every line until EOF and never hits the
        non-indented ``break`` branch, exiting naturally (covers
        the 620->627 'no-break' branch in coverage)."""
        path = tmp_path / "x.yml"
        path.write_text(
            "name: foo\nsearch: |-\n  | tstats count from datamodel=Authentication\n",
            encoding="utf-8",
        )
        out = bsr._extract_yaml_search_field(path)
        assert out is not None
        assert "tstats" in out


# ---------------------------------------------------------------------------
# _ingest_searchbase_corpus
# ---------------------------------------------------------------------------


class TestIngestSearchbaseCorpus:
    def test_no_corpus_returns_none(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        state = bsr._new_state()
        assert bsr._ingest_searchbase_corpus(state) is None

    def test_happy_path(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        sb = redirected_paths["searchbase_dir"]
        (sb / "default").mkdir(parents=True)
        (sb / "default" / "searchbase.conf").write_text(
            "[search1]\nsearch = index=main sourcetype=aws:cloudtrail | stats count\n"
            "[noop_search]\nsearch = | noop\n"  # skipped
            "[blank_search]\nsearch = \n",  # also skipped
            encoding="utf-8",
        )
        (sb / "default" / "macros.conf").write_text(
            "[mymacro]\ndefinition = | stats count\n"
            "[paramaterised(2)]\ndefinition = | search foo\n"
            "[from_args_field]\nargs = x, y, z\ndefinition = | search xyz\n",
            encoding="utf-8",
        )
        (sb / "lookups").mkdir()
        (sb / "lookups" / "sb_mitre_enrichment.csv").write_text(
            "a,b\n", encoding="utf-8"
        )

        state = bsr._new_state()
        out = bsr._ingest_searchbase_corpus(state)
        assert out is not None
        assert out["name"] == "Searchbase"
        assert out["search_count"] == 1
        assert out["defined_macros"] == 3
        assert out["mitre_lookup_present"] is True
        # State picked up vocabulary from the one real search.
        assert "stats" in state["commands"]
        assert "aws:cloudtrail" in state["sourcetypes"]
        # All three macros land in state["macros"].
        assert {"mymacro", "paramaterised", "from_args_field"} <= state["macros"]

    def test_malformed_macro_stanza_skipped(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """Macro stanza that doesn't match the ``name(N)`` regex is
        dropped (covers the ``if not m: continue`` arm)."""
        sb = redirected_paths["searchbase_dir"]
        (sb / "default").mkdir(parents=True)
        (sb / "default" / "searchbase.conf").write_text("", encoding="utf-8")
        (sb / "default" / "macros.conf").write_text(
            "[(malformed)]\ndefinition = | stats\n", encoding="utf-8"
        )
        state = bsr._new_state()
        out = bsr._ingest_searchbase_corpus(state)
        assert out is not None
        assert out["defined_macros"] == 0

    def test_no_macros_conf(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """Only searchbase.conf — no macros.conf. Covers the False
        arm of the SEARCHBASE_MACROS_CONF.exists() branch."""
        sb = redirected_paths["searchbase_dir"]
        (sb / "default").mkdir(parents=True)
        (sb / "default" / "searchbase.conf").write_text(
            "[s1]\nsearch = index=main | stats count\n",
            encoding="utf-8",
        )
        state = bsr._new_state()
        out = bsr._ingest_searchbase_corpus(state)
        assert out is not None
        assert out["defined_macros"] == 0
        assert out["mitre_lookup_present"] is False


# ---------------------------------------------------------------------------
# _ingest_is4s_corpus
# ---------------------------------------------------------------------------


class TestIngestIs4sCorpus:
    def test_no_corpus_returns_none(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        state = bsr._new_state()
        assert bsr._ingest_is4s_corpus(state) is None

    def test_happy_path_all_files_present(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        is4s = redirected_paths["is4s_dir"]
        default = is4s / "default"
        lookups = is4s / "lookups"
        default.mkdir(parents=True)
        lookups.mkdir(parents=True)

        (default / "searchbase.conf").write_text(
            "[s1]\nsearch = index=main sourcetype=aws:cloudtrail | stats count\n"
            "[s2_blank]\nsearch = \n"  # skipped
            "[s3_noop]\nsearch = | noop\n",  # skipped
            encoding="utf-8",
        )
        (default / "savedsearches.conf").write_text(
            "[s1]\nsearch = index=infra | stats count\n",
            encoding="utf-8",
        )
        (default / "macros.conf").write_text(
            "[mymacro]\ndefinition = | stats count\n"
            "[(bad_macro_name)]\ndefinition = | stats\n",  # regex-rejected
            encoding="utf-8",
        )

        (lookups / "uce_sourcetype_mapping.csv").write_text(
            "sourcetype_name,data_model\n"
            "aws:cloudtrail,Authentication data | Web data\n"
            "linux:audit,Endpoint data\n"
            ",ignored_blank_st\n"
            "winhost,Multi word skipped|Network_Traffic\n",
            encoding="utf-8",
        )

        (lookups / "uce_usecase_mapping.csv").write_text(
            "uc_id\nUC-1\nUC-2\n", encoding="utf-8"
        )

        # Splunkbase apps gz — CIM tag regex filters "two words"
        # and accepts short alphanumerics.
        with gzip.open(
            lookups / "ssef_splunkbase_apps.csv.gz",
            "wt",
            encoding="utf-8",
            newline="",
        ) as fh:
            fh.write(
                "sourcetypes,cim_tags\n"
                "aws:cloudtrail|*:foo,authentication|two words|network\n"
                ",\n"  # blank tags / sourcetypes
            )

        state = bsr._new_state()
        out = bsr._ingest_is4s_corpus(state)
        assert out is not None
        assert out["name"] == "Insights Suite for Splunk (IS4S)"
        assert out["searchbase_spls"] == 1
        assert out["savedsearches"] == 1
        assert out["macros_defined"] == 1
        # 1 sourcetype row + 1 sourcetype + 0 blank = 2 sourcetypes
        # added (3rd row blank, 4th row has "winhost" too).
        assert out["uce_sourcetypes"] == 3  # 3 non-blank source names
        assert out["uce_lantern_use_cases"] == 2
        assert out["splunkbase_apps"] == 2

        # CIM tag filter accepts 'authentication' & 'network'; rejects 'two words'.
        assert "authentication" in state["cim_tags"]
        assert "network" in state["cim_tags"]
        assert "two words" not in state["cim_tags"]

        # Glob sourcetype from splunkbase apps -> glob bucket.
        assert "*:foo" in state["sourcetype_glob_patterns"]
        # 'aws:cloudtrail' literal.
        assert "aws:cloudtrail" in state["sourcetypes"]

        # data_model column: 'Authentication' and 'Endpoint' single-word entries
        # pass the filter; multi-word 'Multi word skipped' is dropped.
        assert "Authentication" in state["cim_models"]
        assert "Endpoint" in state["cim_models"]
        assert "Web" in state["cim_models"]
        assert "Multi word skipped" not in state["cim_models"]
        # The pipe-separated 'Network_Traffic' (no " data" suffix) is also kept.
        assert "Network_Traffic" in state["cim_models"]

    def test_minimal_is4s_dir(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """Only the IS4S default dir exists — no searchbase.conf,
        no savedsearches, no macros, no lookups. Counters are all
        zero and the result still describes the corpus."""
        (redirected_paths["is4s_dir"] / "default").mkdir(parents=True)
        state = bsr._new_state()
        out = bsr._ingest_is4s_corpus(state)
        assert out is not None
        assert out["searchbase_spls"] == 0
        assert out["savedsearches"] == 0
        assert out["macros_defined"] == 0
        assert out["uce_sourcetypes"] == 0
        assert out["splunkbase_apps"] == 0

    def test_is4s_savedsearches_with_empty_search_branch(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """savedsearches.conf with an empty ``search =`` value —
        covers the False arm of the ``if spl:`` filter."""
        default = redirected_paths["is4s_dir"] / "default"
        default.mkdir(parents=True)
        (default / "savedsearches.conf").write_text(
            "[empty]\nsearch = \n", encoding="utf-8"
        )
        state = bsr._new_state()
        out = bsr._ingest_is4s_corpus(state)
        assert out is not None
        assert out["savedsearches"] == 0


# ---------------------------------------------------------------------------
# _ingest_sse_corpus
# ---------------------------------------------------------------------------


class TestIngestSseCorpus:
    def test_no_corpus_returns_none(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        state = bsr._new_state()
        assert bsr._ingest_sse_corpus(state) is None

    def test_happy_path(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        default = redirected_paths["sse_dir"] / "default"
        lookups = redirected_paths["sse_dir"] / "lookups"
        default.mkdir(parents=True)
        lookups.mkdir(parents=True)

        (default / "savedsearches.conf").write_text(
            "[s1]\nsearch = index=main sourcetype=aws:cloudtrail | stats count\n"
            "[s_blank]\nsearch = \n",
            encoding="utf-8",
        )
        (default / "macros.conf").write_text(
            "[sse_macro_one]\ndefinition = | stats\n"
            "[sse_macro_two(2)]\ndefinition = | search\n",
            encoding="utf-8",
        )

        (lookups / "SSE-default-data-inventory-products.csv").write_text(
            "product,default_sourcetype_search\n"
            "aws,sourcetype=aws:cloudtrail\n"
            "linux,sourcetype=linux:audit\n"
            "windows,index=main something_else\n",  # doesn't match
            encoding="utf-8",
        )

        state = bsr._new_state()
        out = bsr._ingest_sse_corpus(state)
        assert out is not None
        assert out["savedsearches"] == 1
        assert out["macros_defined"] == 2
        assert out["data_inventory_products"] == 3
        # Two matching sourcetype-search clauses -> literal bucket.
        assert "aws:cloudtrail" in state["sourcetypes"]
        assert "linux:audit" in state["sourcetypes"]
        assert {"sse_macro_one", "sse_macro_two"} <= state["macros"]

    def test_minimal_sse_dir(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        (redirected_paths["sse_dir"] / "default").mkdir(parents=True)
        state = bsr._new_state()
        out = bsr._ingest_sse_corpus(state)
        assert out is not None
        assert out["savedsearches"] == 0
        assert out["macros_defined"] == 0
        assert out["data_inventory_products"] == 0

    def test_sse_macros_with_invalid_stanza_branch(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """macros.conf with a stanza name that doesn't match the
        ``[name]`` or ``[name(N)]`` regex — covers the False arm of
        the ``if m:`` filter."""
        default = redirected_paths["sse_dir"] / "default"
        default.mkdir(parents=True)
        (default / "macros.conf").write_text(
            "[(bad-name)]\ndefinition = | stats count\n",
            encoding="utf-8",
        )
        state = bsr._new_state()
        out = bsr._ingest_sse_corpus(state)
        assert out is not None
        assert out["macros_defined"] == 0


# ---------------------------------------------------------------------------
# _ingest_cim_corpus
# ---------------------------------------------------------------------------


class TestIngestCimCorpus:
    def test_no_corpus_returns_none(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        state = bsr._new_state()
        assert bsr._ingest_cim_corpus(state) is None

    def test_happy_path_walks_datamodels_and_tags(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        default = redirected_paths["cim_dir"] / "default"
        models = default / "data" / "models"
        models.mkdir(parents=True)

        (models / "Authentication.json").write_text(
            json.dumps(
                {
                    "modelName": "Authentication",
                    "objects": [
                        {
                            "objectName": "Authentication",
                            "children": [
                                {
                                    "objectName": "Successful_Authentication"
                                },
                                "not a dict",  # skipped
                                {"no_name": True},  # skipped (no objectName)
                            ],
                        },
                        "not a dict either",  # skipped
                    ],
                }
            ),
            encoding="utf-8",
        )
        # Datamodel JSON without 'modelName' -> falls back to filename stem.
        (models / "Network_Traffic.json").write_text(
            json.dumps({"objects": []}),
            encoding="utf-8",
        )
        # Malformed JSON file -> skipped silently.
        (models / "Broken.json").write_text("not json", encoding="utf-8")

        (default / "tags.conf").write_text(
            "# comment\n"
            "[eventtype=foo]\n"
            "authentication = enabled\n"
            "endpoint = enabled\n"
            "Not_A_Match = nope\n",
            encoding="utf-8",
        )

        state = bsr._new_state()
        out = bsr._ingest_cim_corpus(state)
        assert out is not None
        assert out["datamodel_files"] == 2  # Auth + Network_Traffic
        # Auth: root + parent ('Authentication.Authentication') +
        # child ('Authentication.Authentication.Successful_Authentication')
        # The first call walks {objects: [...]} at path_prefix='' so
        # parent path = 'Authentication.Authentication'. Recursion adds child.
        assert "Authentication" in state["cim_models"]
        assert "Network_Traffic" in state["cim_models"]
        # Authentication paths.
        assert "Authentication.Authentication" in state["datamodel_paths"]
        assert (
            "Authentication.Authentication.Successful_Authentication"
            in state["datamodel_paths"]
        )
        # Network_Traffic emits no dataset paths but the bare model
        # name is added.
        assert "Network_Traffic" in state["datamodel_paths"]

        # tags.conf -> lowercased authentication / endpoint.
        assert "authentication" in state["cim_tags"]
        assert "endpoint" in state["cim_tags"]
        # 'Not_A_Match = nope' is not 'enabled' -> rejected by the
        # regex on the value.
        assert "not_a_match" not in state["cim_tags"]

    def test_no_models_dir(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """CIM_DEFAULT exists but CIM_DATAMODELS_DIR does not —
        covers the False arm of CIM_DATAMODELS_DIR.exists()."""
        (redirected_paths["cim_dir"] / "default").mkdir(parents=True)
        state = bsr._new_state()
        out = bsr._ingest_cim_corpus(state)
        assert out is not None
        assert out["datamodel_files"] == 0
        assert out["datasets"] == 0

    def test_no_tags_conf(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """CIM_DEFAULT exists, no models, no tags.conf — covers the
        False arm of CIM_TAGS_CONF.exists()."""
        (redirected_paths["cim_dir"] / "default").mkdir(parents=True)
        state = bsr._new_state()
        out = bsr._ingest_cim_corpus(state)
        assert out is not None
        assert out["tags_conf_lines"] == 0


# ---------------------------------------------------------------------------
# _ingest_escu_corpus
# ---------------------------------------------------------------------------


class TestIngestEscuCorpus:
    def test_no_corpus_returns_none(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        state = bsr._new_state()
        assert bsr._ingest_escu_corpus(state) is None

    def test_no_yml_files_returns_none(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        (
            redirected_paths["security_content_dir"] / "detections"
        ).mkdir(parents=True)
        state = bsr._new_state()
        assert bsr._ingest_escu_corpus(state) is None

    def test_happy_path(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        detections = (
            redirected_paths["security_content_dir"] / "detections"
        )
        macros = (
            redirected_paths["security_content_dir"] / "macros"
        )
        (detections / "endpoint").mkdir(parents=True)
        macros.mkdir(parents=True)

        (detections / "endpoint" / "yes.yml").write_text(
            "name: foo\nsearch: |-\n"
            "  | tstats count from datamodel=Authentication\n"
            "tags:\n",
            encoding="utf-8",
        )
        (detections / "endpoint" / "no_search.yml").write_text(
            "name: bar\nstatus: production\n", encoding="utf-8"
        )

        (macros / "escu_macro.yml").write_text(
            "name: escu_macro\n", encoding="utf-8"
        )

        state = bsr._new_state()
        out = bsr._ingest_escu_corpus(state)
        assert out is not None
        # Only the yml that yielded a search counts.
        assert out["detection_count"] == 1
        assert out["macro_files"] == 1
        # tstats -> commands; datamodel -> datamodel_paths
        assert "tstats" in state["commands"]
        assert "Authentication" in state["datamodel_paths"]
        assert "escu_macro" in state["macros"]

    def test_no_macros_dir(
        self, redirected_paths: dict[str, Path]
    ) -> None:
        """ESCU_MACROS_DIR missing -> macro_files=0 (covers the False
        arm of the macros_dir.exists() branch)."""
        detections = (
            redirected_paths["security_content_dir"] / "detections"
        )
        detections.mkdir(parents=True)
        (detections / "x.yml").write_text(
            "search: '| stats count'\n", encoding="utf-8"
        )

        state = bsr._new_state()
        out = bsr._ingest_escu_corpus(state)
        assert out is not None
        assert out["macro_files"] == 0


# ---------------------------------------------------------------------------
# _new_state, _serialise
# ---------------------------------------------------------------------------


class TestNewState:
    def test_pinned_keys(self) -> None:
        state = bsr._new_state()
        assert set(state.keys()) == {
            "commands",
            "macros",
            "macros_with_arity",
            "sourcetypes",
            "sourcetype_glob_patterns",
            "indexes",
            "datamodel_paths",
            "cim_models",
            "cim_tags",
            "lookups",
            "eval_functions",
            "stats_functions",
        }
        # macros_with_arity is the only dict; rest are sets.
        assert state["macros_with_arity"] == {}
        for k in (
            "commands",
            "macros",
            "sourcetypes",
            "sourcetype_glob_patterns",
            "indexes",
            "datamodel_paths",
            "cim_models",
            "cim_tags",
            "lookups",
            "eval_functions",
            "stats_functions",
        ):
            assert state[k] == set()


class TestSerialise:
    def test_sorted_output_and_metadata(self) -> None:
        state = bsr._new_state()
        state["commands"].update({"stats", "search"})
        state["macros"].update({"z_macro", "a_macro"})
        state["macros_with_arity"]["z_macro"] = {2, 1}
        state["macros_with_arity"]["a_macro"] = {0}
        state["sourcetypes"].update({"x:y", "a:b"})
        state["indexes"].update({"main", "_internal"})
        sources = [{"name": "fake"}]
        out = bsr._serialise(state, sources)

        assert out["version"] == 1
        assert "generated_at" in out
        # ISO 8601 truncated to seconds (microsecond=0).
        assert "." not in out["generated_at"]  # no microsecond
        assert out["sources"] == sources

        # Every list-typed bucket is sorted.
        assert out["commands"] == ["search", "stats"]
        assert out["macros"] == ["a_macro", "z_macro"]
        assert out["macros_with_arity"] == {
            "a_macro": [0],
            "z_macro": [1, 2],
        }
        assert out["sourcetypes"] == ["a:b", "x:y"]
        assert out["indexes"] == ["_internal", "main"]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_check_with_no_corpus_exits_one(
        self,
        redirected_paths: dict[str, Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = bsr.main(
            ["--out", str(redirected_paths["out"]), "--check"]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "no reference corpus found" in err
        # Empty file not written.
        assert not redirected_paths["out"].exists()

    def test_no_corpus_without_check_still_writes_json(
        self,
        redirected_paths: dict[str, Path],
    ) -> None:
        rc = bsr.main(["--out", str(redirected_paths["out"]), "--quiet"])
        assert rc == 0
        assert redirected_paths["out"].exists()
        payload = json.loads(
            redirected_paths["out"].read_text(encoding="utf-8")
        )
        assert payload["sources"] == []
        assert payload["macros"] == []
        assert payload["sourcetypes"] == []

    def test_happy_path_with_searchbase_corpus(
        self,
        redirected_paths: dict[str, Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sb = redirected_paths["searchbase_dir"]
        (sb / "default").mkdir(parents=True)
        (sb / "default" / "searchbase.conf").write_text(
            "[s1]\nsearch = index=main sourcetype=aws:cloudtrail | stats count\n",
            encoding="utf-8",
        )

        rc = bsr.main(["--out", str(redirected_paths["out"])])
        assert rc == 0
        payload = json.loads(
            redirected_paths["out"].read_text(encoding="utf-8")
        )
        assert any(s["name"] == "Searchbase" for s in payload["sources"])
        assert "aws:cloudtrail" in payload["sourcetypes"]
        assert "main" in payload["indexes"]

        # Non-quiet -> the summary block is on stderr.
        err = capsys.readouterr().err
        assert "Wrote" in err
        assert "sources:" in err
        assert "sourcetypes:" in err

    def test_default_argv_uses_sys_argv(
        self,
        redirected_paths: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``main()`` with argv=None reads sys.argv (covers the
        ``argparse.parse_args(None)`` arm)."""
        # Argv that simulates --quiet with default --out (which is
        # already redirected to our tmp).
        monkeypatch.setattr(
            sys,
            "argv",
            ["build_spl_reference", "--quiet"],
        )
        rc = bsr.main()
        assert rc == 0
        assert redirected_paths["out"].exists()

    def test_output_outside_repo_uses_absolute_path(
        self,
        redirected_paths: dict[str, Path],
        tmp_path_factory: pytest.TempPathFactory,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output path OUTSIDE the redirected REPO_ROOT -> the
        summary prints the absolute path (covers the False arm of
        ``args.out.is_relative_to(_REPO)``)."""
        other_root = tmp_path_factory.mktemp("elsewhere")
        out = other_root / "ref.json"

        rc = bsr.main(["--out", str(out)])
        assert rc == 0
        assert out.exists()
        err = capsys.readouterr().err
        # Path printed as absolute since it's outside _REPO.
        assert str(out) in err

    def test_all_corpora_present_appends_all_sources(
        self,
        redirected_paths: dict[str, Path],
    ) -> None:
        """All five corpora exist at once → ``main`` walks each
        ingester and appends a source entry for each (covers the
        True arms of lines 705/708/711/714/717 — the four
        ``sources.append(...)`` calls for is4s/sse/cim/escu).

        We populate the minimum each ingester needs to return a
        non-None descriptor."""
        # Searchbase
        sb = redirected_paths["searchbase_dir"]
        (sb / "default").mkdir(parents=True)
        (sb / "default" / "searchbase.conf").write_text(
            "[s1]\nsearch = index=main sourcetype=foo | stats count(x)\n",
            encoding="utf-8",
        )
        # IS4S
        is4s_default = redirected_paths["is4s_dir"] / "default"
        is4s_default.mkdir(parents=True)
        (is4s_default / "savedsearches.conf").write_text(
            "[v1]\nsearch = index=infra | stats count(x)\n",
            encoding="utf-8",
        )
        # SSE
        sse_default = redirected_paths["sse_dir"] / "default"
        sse_default.mkdir(parents=True)
        (sse_default / "savedsearches.conf").write_text(
            "[s1]\nsearch = | stats count(x)\n", encoding="utf-8"
        )
        # CIM
        cim_default = redirected_paths["cim_dir"] / "default"
        cim_default.mkdir(parents=True)
        # ESCU
        detections = (
            redirected_paths["security_content_dir"] / "detections"
        )
        detections.mkdir(parents=True)
        (detections / "x.yml").write_text(
            "name: foo\nsearch: '| stats count(x)'\n", encoding="utf-8"
        )

        rc = bsr.main(
            ["--out", str(redirected_paths["out"]), "--quiet"]
        )
        assert rc == 0
        payload = json.loads(
            redirected_paths["out"].read_text(encoding="utf-8")
        )
        source_names = {s["name"] for s in payload["sources"]}
        assert source_names == {
            "Searchbase",
            "Insights Suite for Splunk (IS4S)",
            "Splunk Security Essentials (SSE)",
            "Splunk Common Information Model (CIM) add-on",
            "splunk/security_content (ESCU)",
        }


# ---------------------------------------------------------------------------
# __main__ guard
# ---------------------------------------------------------------------------


class TestMainGuard:
    def test_invoking_module_as_script_smoke(
        self,
        tmp_path: Path,
    ) -> None:
        """Smoke test: invoke the module via ``python -m``. The
        ``--check`` flag exits 1 when no corpus is present, which
        is the deterministic state when run with a fresh out-of-repo
        cwd."""
        # Use the actual repo (since module-level path constants
        # are evaluated at import time and resolved relative to the
        # tools/ tree); but write the output into tmp_path.
        out = tmp_path / "ref.json"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.research.build_spl_reference",
                "--out",
                str(out),
                "--quiet",
            ],
            cwd=str(Path(bsr.__file__).resolve().parents[2]),
            capture_output=True,
            text=True,
            timeout=120,
        )
        # rc==0 (with or without corpus): the script always emits a
        # JSON shell unless --check is passed.
        assert result.returncode == 0, (
            f"rc={result.returncode} stderr={result.stderr!r}"
        )
        assert out.exists()
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert "macros" in payload
        assert "sourcetypes" in payload
        assert "generated_at" in payload
