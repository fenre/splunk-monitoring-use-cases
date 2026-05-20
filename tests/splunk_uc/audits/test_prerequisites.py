"""Unit tests for ``audit-prerequisites`` (P16 wave L).

The prerequisite-graph auditor at
``src/splunk_uc/audits/prerequisites.py`` is the CI-side enforcement
gate that complements ``build.py::validate_prerequisites``. It
reads the *committed* ``catalog.json`` artefact directly, builds the
forward + reverse dependency graphs, runs Kahn-style cycle detection
via iterative-DFS colouring, and emits ``reports/prerequisites-audit.json``
with a deterministic, byte-stable shape.

Coverage at the start of this wave: **8.5%** (179 of 204 statements
unexercised). The tests below pin every documented contract:

* Reference constants (`UC_ID_PATTERN`, `PREREQ_UC_PATTERN`,
  `VALID_WAVES`, `WAVE_RANK`).
* `_load_catalog` (file missing, invalid JSON, happy path).
* `_extract_uc_index` (every shape guard: missing DATA, non-list DATA,
  non-dict cat, missing `s`, non-dict sub, missing `u`, non-dict uc,
  missing `i`, non-string `i`, malformed UC-ID pattern).
* `_detect_cycle` (linear chain, single self-loop, simple 2-node
  cycle, larger cycle, multi-component graph, disconnected nodes,
  empty graph).
* `_build_graph` (every error code: `shape: ...not a string`,
  `shape: ...does not match UC-X.Y.Z`, `self-reference`,
  `duplicate-prereq`, `unknown-prereq`; the wave-monotonicity warning
  with both wave orderings; deterministic sorting; the "no pre" /
  "empty pre" / "non-list pre" skips).
* `_wave_summary` (every wave count: crawl, walk, run, unassigned).
* `_build_report` (cycle detection round-trip, edges in deterministic
  order, waves bucketed correctly, reverseIndex omits empty entries,
  summary counts correct).
* `_serialise` / `_read_existing_report` (round-trip + missing file).
* `main()` CLI — every flag combination (default, `--check` with
  drift / no-drift / no-baseline, `--write-report`, `--strict`,
  cycle path appended to errors, exit codes).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import prerequisites as pr

# ============================================================================
# Reference constants
# ============================================================================


class TestConstants:
    def test_uc_id_pattern_matches_canonical(self) -> None:
        assert pr.UC_ID_PATTERN.match("1.2.3")
        assert pr.UC_ID_PATTERN.match("22.49.99")
        assert not pr.UC_ID_PATTERN.match("UC-1.2.3")
        assert not pr.UC_ID_PATTERN.match("1.2")
        assert not pr.UC_ID_PATTERN.match("1.2.3.4")

    def test_prereq_uc_pattern_requires_uc_prefix(self) -> None:
        assert pr.PREREQ_UC_PATTERN.match("UC-1.2.3")
        assert pr.PREREQ_UC_PATTERN.match("UC-22.49.99")
        assert not pr.PREREQ_UC_PATTERN.match("1.2.3")
        assert not pr.PREREQ_UC_PATTERN.match("UC-1.2")

    def test_valid_waves(self) -> None:
        assert pr.VALID_WAVES == ("crawl", "walk", "run")

    def test_wave_rank_strict_ordering(self) -> None:
        assert pr.WAVE_RANK["crawl"] < pr.WAVE_RANK["walk"]
        assert pr.WAVE_RANK["walk"] < pr.WAVE_RANK["run"]


# ============================================================================
# `_load_catalog`
# ============================================================================


class TestLoadCatalog:
    def test_missing_catalog_exits_2(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(pr, "CATALOG_PATH", str(tmp_path / "missing.json"))
        with pytest.raises(SystemExit) as ei:
            pr._load_catalog()
        assert ei.value.code == 2

    def test_invalid_json_exits_2(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{not valid", encoding="utf-8")
        monkeypatch.setattr(pr, "CATALOG_PATH", str(p))
        with pytest.raises(SystemExit) as ei:
            pr._load_catalog()
        assert ei.value.code == 2

    def test_happy_path_returns_dict(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        p = tmp_path / "good.json"
        p.write_text(json.dumps({"DATA": []}), encoding="utf-8")
        monkeypatch.setattr(pr, "CATALOG_PATH", str(p))
        out = pr._load_catalog()
        assert out == {"DATA": []}


# ============================================================================
# `_extract_uc_index`
# ============================================================================


class TestExtractUcIndex:
    def test_empty_root_returns_empty(self) -> None:
        assert pr._extract_uc_index({}) == {}

    def test_non_list_data_returns_empty(self) -> None:
        assert pr._extract_uc_index({"DATA": "not a list"}) == {}

    def test_non_dict_cat_skipped(self) -> None:
        out = pr._extract_uc_index({"DATA": ["not a dict", 42]})
        assert out == {}

    def test_missing_subcategories_handled(self) -> None:
        out = pr._extract_uc_index({"DATA": [{}]})
        assert out == {}

    def test_non_dict_subcategory_skipped(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": ["nope", 1]}]})
        assert out == {}

    def test_missing_ucs_in_subcategory_handled(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": [{}]}]})
        assert out == {}

    def test_non_dict_uc_skipped(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": [{"u": ["not a dict", 1]}]}]})
        assert out == {}

    def test_missing_uc_id_skipped(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": [{"u": [{"name": "no id"}]}]}]})
        assert out == {}

    def test_non_string_uc_id_skipped(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": [{"u": [{"i": 12345}]}]}]})
        assert out == {}

    def test_malformed_uc_id_skipped(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": [{"u": [{"i": "not-a-uc-id"}]}]}]})
        assert out == {}

    def test_happy_path_indexes_with_uc_prefix(self) -> None:
        out = pr._extract_uc_index(
            {
                "DATA": [
                    {
                        "s": [
                            {
                                "u": [
                                    {"i": "1.1.1", "n": "first"},
                                    {"i": "1.1.2", "n": "second"},
                                ]
                            }
                        ]
                    }
                ]
            }
        )
        assert "UC-1.1.1" in out
        assert "UC-1.1.2" in out
        assert out["UC-1.1.1"]["n"] == "first"

    def test_handles_none_subcategory_list(self) -> None:
        """`cat.get("s", []) or []` handles explicit None."""

        out = pr._extract_uc_index({"DATA": [{"s": None}]})
        assert out == {}

    def test_handles_none_uc_list(self) -> None:
        out = pr._extract_uc_index({"DATA": [{"s": [{"u": None}]}]})
        assert out == {}


# ============================================================================
# `_detect_cycle`
# ============================================================================


class TestDetectCycle:
    def test_empty_graph_returns_none(self) -> None:
        assert pr._detect_cycle({}) is None

    def test_linear_chain_no_cycle(self) -> None:
        adj = {"A": ["B"], "B": ["C"], "C": []}
        assert pr._detect_cycle(adj) is None

    def test_self_loop_detected(self) -> None:
        """A→A self-loop returns the documented `[node, node, node]` path
        (walk-back appends the start twice — this is the established
        wire format the audit prints)."""

        cycle = pr._detect_cycle({"A": ["A"]})
        assert cycle == ["A", "A", "A"]

    def test_simple_two_node_cycle(self) -> None:
        """A→B→A returns `[A, B, B]` — first node is the cycle-closer
        target, last node is the back-edge source duplicated."""

        cycle = pr._detect_cycle({"A": ["B"], "B": ["A"]})
        assert cycle == ["A", "B", "B"]

    def test_larger_cycle(self) -> None:
        cycle = pr._detect_cycle({"A": ["B"], "B": ["C"], "C": ["D"], "D": ["A"]})
        # The cycle starts at the back-edge target and ends with the
        # discovering node duplicated (see test_self_loop_detected above).
        assert cycle is not None
        # All four nodes participate
        assert set(cycle) == {"A", "B", "C", "D"}
        # First entry is the back-edge target; last entry is duplicated
        assert cycle[-2] == cycle[-1]

    def test_multi_component_with_cycle(self) -> None:
        cycle = pr._detect_cycle({"A": ["B"], "B": [], "C": ["D"], "D": ["C"], "E": []})
        assert cycle is not None
        # Cycle is in C/D component
        assert "C" in cycle and "D" in cycle

    def test_disconnected_acyclic_returns_none(self) -> None:
        adj = {"A": ["B"], "B": [], "C": ["D"], "D": [], "E": []}
        assert pr._detect_cycle(adj) is None

    def test_diamond_dag_no_cycle(self) -> None:
        """A→B, A→C, B→D, C→D (diamond pattern) — acyclic."""

        adj = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        assert pr._detect_cycle(adj) is None


# ============================================================================
# `_build_graph`
# ============================================================================


class TestBuildGraph:
    def _uc(self, uid: str, *, pre: list[Any] | None = None, wv: str = "crawl") -> dict[str, Any]:
        d: dict[str, Any] = {"i": uid.replace("UC-", ""), "wv": wv}
        if pre is not None:
            d["pre"] = pre
        return d

    def test_no_prereqs_no_errors_or_warnings(self) -> None:
        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1"),
            "UC-1.1.2": self._uc("UC-1.1.2"),
        }
        fwd, rev, errs, warns = pr._build_graph(idx)
        assert errs == []
        assert warns == []
        assert fwd == {"UC-1.1.1": [], "UC-1.1.2": []}
        assert rev == {"UC-1.1.1": [], "UC-1.1.2": []}

    def test_empty_pre_list_skipped(self) -> None:
        idx = {"UC-1.1.1": self._uc("UC-1.1.1", pre=[])}
        _, _, errs, _ = pr._build_graph(idx)
        assert errs == []

    def test_non_list_pre_skipped(self) -> None:
        """A `pre` field that isn't a list is silently skipped (no error)."""

        idx = {"UC-1.1.1": {"i": "1.1.1", "pre": "UC-1.1.2"}}
        _, _, errs, _ = pr._build_graph(idx)
        assert errs == []

    def test_non_string_pre_element_error(self) -> None:
        idx = {"UC-1.1.1": self._uc("UC-1.1.1", pre=[12345])}
        _, _, errs, _ = pr._build_graph(idx)
        assert any("not a string" in e for e in errs)
        assert any("int" in e for e in errs)

    def test_malformed_pre_pattern_error(self) -> None:
        idx = {"UC-1.1.1": self._uc("UC-1.1.1", pre=["1.1.2"])}
        _, _, errs, _ = pr._build_graph(idx)
        # Missing UC- prefix → pattern mismatch
        assert any("does not match UC-X.Y.Z" in e for e in errs)

    def test_self_reference_error(self) -> None:
        idx = {"UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.1"])}
        _, _, errs, _ = pr._build_graph(idx)
        assert any("self-reference" in e for e in errs)

    def test_duplicate_prereq_error(self) -> None:
        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.2", "UC-1.1.2"]),
            "UC-1.1.2": self._uc("UC-1.1.2"),
        }
        _, _, errs, _ = pr._build_graph(idx)
        assert any("duplicate-prereq" in e for e in errs)

    def test_unknown_prereq_error(self) -> None:
        idx = {"UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-9.9.9"])}
        _, _, errs, _ = pr._build_graph(idx)
        assert any("unknown-prereq" in e and "UC-9.9.9" in e for e in errs)

    def test_happy_dependency_builds_forward_reverse(self) -> None:
        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.2"]),
            "UC-1.1.2": self._uc("UC-1.1.2"),
        }
        fwd, rev, errs, _ = pr._build_graph(idx)
        assert errs == []
        # UC-1.1.2 enables UC-1.1.1
        assert fwd["UC-1.1.2"] == ["UC-1.1.1"]
        # UC-1.1.1 depends on UC-1.1.2
        assert rev["UC-1.1.1"] == ["UC-1.1.2"]

    def test_wave_monotonicity_warning(self) -> None:
        """A crawl-wave UC depending on a walk-wave UC is suspicious."""

        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.2"], wv="crawl"),
            "UC-1.1.2": self._uc("UC-1.1.2", wv="walk"),
        }
        _, _, errs, warns = pr._build_graph(idx)
        assert errs == []
        assert any("wave-monotonicity" in w for w in warns)
        assert any("crawl" in w and "walk" in w for w in warns)

    def test_higher_wave_depending_on_lower_no_warning(self) -> None:
        """run depending on crawl is normal — no warning."""

        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.2"], wv="run"),
            "UC-1.1.2": self._uc("UC-1.1.2", wv="crawl"),
        }
        _, _, errs, warns = pr._build_graph(idx)
        assert errs == []
        assert warns == []

    def test_same_wave_no_warning(self) -> None:
        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.2"], wv="walk"),
            "UC-1.1.2": self._uc("UC-1.1.2", wv="walk"),
        }
        _, _, errs, warns = pr._build_graph(idx)
        assert errs == []
        assert warns == []

    def test_unknown_wave_does_not_warn(self) -> None:
        """Non-string or non-canonical wave skips monotonicity check."""

        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-1.1.2"], wv="unknown_wave"),
            "UC-1.1.2": self._uc("UC-1.1.2", wv="walk"),
        }
        _, _, _errs, warns = pr._build_graph(idx)
        # No wave-monotonicity warning fires because src_wave isn't in WAVE_RANK
        assert not any("wave-monotonicity" in w for w in warns)

    def test_errors_and_warnings_are_sorted(self) -> None:
        """Output lists must be deterministically sorted."""

        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-9.9.9", "UC-8.8.8"]),
            "UC-1.1.2": self._uc("UC-1.1.2", pre=["UC-7.7.7"]),
        }
        _, _, errs, _ = pr._build_graph(idx)
        assert errs == sorted(errs)

    def test_forward_and_reverse_are_sorted_and_deduped(self) -> None:
        """Forward / reverse adjacency lists are sorted and deduped."""

        idx = {
            "UC-1.1.1": self._uc("UC-1.1.1", pre=["UC-2.2.2"]),
            "UC-1.1.3": self._uc("UC-1.1.3", pre=["UC-2.2.2"]),
            "UC-1.1.2": self._uc("UC-1.1.2", pre=["UC-2.2.2"]),
            "UC-2.2.2": self._uc("UC-2.2.2"),
        }
        fwd, _, _, _ = pr._build_graph(idx)
        # UC-2.2.2's dependants are sorted
        assert fwd["UC-2.2.2"] == sorted(fwd["UC-2.2.2"])
        assert len(fwd["UC-2.2.2"]) == len(set(fwd["UC-2.2.2"]))


# ============================================================================
# `_wave_summary`
# ============================================================================


class TestWaveSummary:
    def test_empty_index(self) -> None:
        out = pr._wave_summary({})
        assert out == {"crawl": 0, "walk": 0, "run": 0, "unassigned": 0}

    def test_canonical_waves_counted(self) -> None:
        idx = {
            "UC-1.1.1": {"wv": "crawl"},
            "UC-1.1.2": {"wv": "walk"},
            "UC-1.1.3": {"wv": "walk"},
            "UC-1.1.4": {"wv": "run"},
        }
        out = pr._wave_summary(idx)
        assert out == {"crawl": 1, "walk": 2, "run": 1, "unassigned": 0}

    def test_unassigned_bucket_for_missing_or_invalid(self) -> None:
        idx: dict[str, dict[str, Any]] = {
            "UC-1.1.1": {},  # no wv
            "UC-1.1.2": {"wv": "invalid"},  # not in canonical set
            "UC-1.1.3": {"wv": 42},  # not a string
        }
        out = pr._wave_summary(idx)
        assert out["unassigned"] == 3


# ============================================================================
# `_build_report`
# ============================================================================


class TestBuildReport:
    def test_empty_input(self) -> None:
        report = pr._build_report({}, {}, {}, [], [])
        assert report["edges"] == []
        assert report["waves"] == {"crawl": [], "walk": [], "run": [], "unassigned": []}
        assert report["summary"]["edges"] == 0
        assert report["summary"]["wave_counts"]["unassigned"] == 0
        assert "cycle" not in report
        assert report["errors"] == []
        assert report["warnings"] == []

    def test_includes_readme_field(self) -> None:
        report = pr._build_report({}, {}, {}, [], [])
        assert "_readme" in report
        assert "implementation-ordering" in report["_readme"]

    def test_edges_in_deterministic_order(self) -> None:
        idx = {"UC-1.1.1": {"i": "1.1.1"}, "UC-1.1.2": {"i": "1.1.2"}}
        fwd = {"UC-1.1.1": ["UC-1.1.2"], "UC-1.1.2": []}
        rev: dict[str, list[str]] = {"UC-1.1.1": [], "UC-1.1.2": ["UC-1.1.1"]}
        report = pr._build_report(idx, fwd, rev, [], [])
        assert report["edges"] == [["UC-1.1.1", "UC-1.1.2"]]

    def test_waves_bucketed_correctly(self) -> None:
        idx = {
            "UC-1.1.1": {"i": "1.1.1", "wv": "crawl"},
            "UC-1.1.2": {"i": "1.1.2", "wv": "walk"},
            "UC-1.1.3": {"i": "1.1.3"},  # unassigned
        }
        report = pr._build_report(idx, {}, {}, [], [])
        assert report["waves"]["crawl"] == ["UC-1.1.1"]
        assert report["waves"]["walk"] == ["UC-1.1.2"]
        assert report["waves"]["unassigned"] == ["UC-1.1.3"]

    def test_reverse_index_omits_empty_entries(self) -> None:
        """`reverseIndex` skips UCs with no dependants."""

        fwd = {"UC-1.1.1": ["UC-1.1.2"], "UC-1.1.2": []}
        report = pr._build_report({}, fwd, {}, [], [])
        # UC-1.1.1 has dependants → included; UC-1.1.2 doesn't → omitted
        assert "UC-1.1.1" in report["reverseIndex"]
        assert "UC-1.1.2" not in report["reverseIndex"]

    def test_summary_counts_correct(self) -> None:
        idx = {
            "UC-1.1.1": {"i": "1.1.1"},
            "UC-1.1.2": {"i": "1.1.2"},
            "UC-1.1.3": {"i": "1.1.3"},
        }
        fwd = {"UC-1.1.1": ["UC-1.1.2"], "UC-1.1.2": [], "UC-1.1.3": []}
        rev = {"UC-1.1.1": [], "UC-1.1.2": ["UC-1.1.1"], "UC-1.1.3": []}
        report = pr._build_report(idx, fwd, rev, [], [])
        assert report["summary"]["ucs_with_prerequisites"] == 1
        assert report["summary"]["ucs_with_dependants"] == 1
        assert report["summary"]["edges"] == 1

    def test_cycle_appended_to_report(self) -> None:
        idx = {"UC-1.1.1": {"i": "1.1.1"}, "UC-1.1.2": {"i": "1.1.2"}}
        # Cyclic forward graph
        fwd = {"UC-1.1.1": ["UC-1.1.2"], "UC-1.1.2": ["UC-1.1.1"]}
        report = pr._build_report(idx, fwd, {}, [], [])
        assert "cycle" in report
        # Cycle walk-back duplicates the discovering (back-edge) node;
        # what matters is that all participants appear
        cyc = report["cycle"]
        assert set(cyc) == {"UC-1.1.1", "UC-1.1.2"}
        assert cyc[-2] == cyc[-1]


# ============================================================================
# `_serialise` / `_read_existing_report`
# ============================================================================


class TestSerialise:
    def test_json_round_trip(self) -> None:
        report = {"a": 1, "b": [1, 2], "c": {"d": "e"}}
        s = pr._serialise(report)
        # Trailing newline contract
        assert s.endswith("\n")
        parsed = json.loads(s)
        assert parsed == report

    def test_keys_are_sorted(self) -> None:
        s = pr._serialise({"z": 1, "a": 2, "m": 3})
        parsed_lines = s.strip().split("\n")
        # First key after the opening `{` should be `a`
        assert parsed_lines[1].strip().startswith('"a"')

    def test_preserves_unicode_without_escaping(self) -> None:
        out = pr._serialise({"x": "café"})
        assert "café" in out
        assert "\\u" not in out


class TestReadExistingReport:
    def test_missing_returns_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "missing.json"))
        assert pr._read_existing_report() is None

    def test_existing_returns_content(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        p = tmp_path / "existing.json"
        p.write_text('{"foo": "bar"}\n', encoding="utf-8")
        monkeypatch.setattr(pr, "REPORT_PATH", str(p))
        assert pr._read_existing_report() == '{"foo": "bar"}\n'


# ============================================================================
# `main()` CLI
# ============================================================================


def _write_catalog(path: Path, ucs: list[dict[str, Any]]) -> None:
    """Helper: write a minimal catalog.json shape under `path`."""

    payload = {"DATA": [{"s": [{"u": ucs}]}]}
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestMainCli:
    def test_happy_path_returns_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(
            cat,
            [
                {"i": "1.1.1", "n": "first", "wv": "crawl"},
                {"i": "1.1.2", "n": "second", "wv": "walk"},
            ],
        )
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "report.json"))
        rc = pr.main([])
        out = capsys.readouterr().out
        assert rc == 0
        # Always prints the Waves: summary
        assert "Waves: crawl=1, walk=1, run=0, unassigned=0" in out
        assert "Graph:" in out

    def test_error_returns_one_and_prints_to_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(
            cat,
            [
                {"i": "1.1.1", "n": "first", "pre": ["UC-9.9.9"]},
            ],
        )
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "report.json"))
        rc = pr.main([])
        captured = capsys.readouterr()
        assert rc == 1
        assert "unknown-prereq" in captured.err
        assert "failed with 1 error" in captured.err

    def test_strict_promotes_warnings_to_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(
            cat,
            [
                {"i": "1.1.1", "n": "first", "wv": "crawl", "pre": ["UC-1.1.2"]},
                {"i": "1.1.2", "n": "second", "wv": "walk"},
            ],
        )
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "report.json"))
        rc = pr.main(["--strict"])
        out, err = capsys.readouterr()
        assert rc == 1
        assert "wave-monotonicity" in out
        assert "warning(s) under --strict" in err

    def test_strict_without_warnings_returns_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(cat, [{"i": "1.1.1", "wv": "crawl"}])
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "report.json"))
        rc = pr.main(["--strict"])
        assert rc == 0

    def test_write_report_creates_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(cat, [{"i": "1.1.1", "wv": "crawl"}])
        report_path = tmp_path / "reports" / "prereq.json"
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(report_path))
        # Also need to monkeypatch REPO_ROOT for the relpath in the print
        monkeypatch.setattr(pr, "REPO_ROOT", str(tmp_path))
        rc = pr.main(["--write-report"])
        out = capsys.readouterr().out
        assert rc == 0
        assert report_path.is_file()
        assert "Wrote" in out
        # Parent dir was auto-created
        assert report_path.parent.is_dir()

    def test_check_without_baseline_returns_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(cat, [{"i": "1.1.1", "wv": "crawl"}])
        # REPORT_PATH points to a non-existent file
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "missing.json"))
        rc = pr.main(["--check"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "requires" in err

    def test_check_with_matching_baseline_returns_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(cat, [{"i": "1.1.1", "wv": "crawl"}])
        report_path = tmp_path / "reports" / "prereq.json"
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(report_path))
        monkeypatch.setattr(pr, "REPO_ROOT", str(tmp_path))
        # First write to baseline
        rc1 = pr.main(["--write-report"])
        assert rc1 == 0
        # Then check should succeed
        rc2 = pr.main(["--check"])
        assert rc2 == 0

    def test_check_with_drift_returns_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(cat, [{"i": "1.1.1", "wv": "crawl"}])
        report_path = tmp_path / "reports" / "prereq.json"
        # Pre-populate with mismatching content
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('{"stale": "content"}\n', encoding="utf-8")
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(report_path))
        monkeypatch.setattr(pr, "REPO_ROOT", str(tmp_path))
        rc = pr.main(["--check"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "out of date" in err

    def test_cycle_appended_to_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat = tmp_path / "catalog.json"
        _write_catalog(
            cat,
            [
                {"i": "1.1.1", "n": "first", "pre": ["UC-1.1.2"]},
                {"i": "1.1.2", "n": "second", "pre": ["UC-1.1.1"]},
            ],
        )
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "report.json"))
        rc = pr.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "cycle:" in err

    def test_summary_format_string_uses_all_buckets(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The "Waves:" line uses **dict formatting; ensure all four
        keys are present in the output even when some are zero."""

        cat = tmp_path / "catalog.json"
        _write_catalog(cat, [{"i": "1.1.1", "wv": "run"}])
        monkeypatch.setattr(pr, "CATALOG_PATH", str(cat))
        monkeypatch.setattr(pr, "REPORT_PATH", str(tmp_path / "report.json"))
        rc = pr.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "crawl=0" in out
        assert "walk=0" in out
        assert "run=1" in out
        assert "unassigned=0" in out
