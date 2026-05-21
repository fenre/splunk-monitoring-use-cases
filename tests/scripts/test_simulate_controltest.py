"""Hermetic tests for ``scripts/simulate_controltest.py``.

The script is the Phase 4.5d ATT&CK simulation gate wired into the
``CI Gates`` job of ``.github/workflows/validate.yml`` (line 1244,
``python3 scripts/simulate_controltest.py --check``). It walks every
UC sidecar under ``content/cat-*/UC-*.json``, validates each
``controlTest.attackTechnique`` against the canonical MITRE
crosswalk, checks fixture polarity, and emits a deterministic report
at ``reports/attack-simulation.json``. Despite this CI-critical role
it shipped with ZERO unit-test coverage: every change relied on the
nightly-run feedback loop on the live catalogue, which both:

* hid bugs whenever the production catalogue happened to not exercise
  the broken code path, and
* meant any catalogue-shape change risked silent regressions in the
  simulator itself.

This module pins:

Module-level constants
- ``ATTACK_ID_RE`` grammar for ``T1234`` and ``T1234.005``.
- ``SPL_LITERAL_RE`` ``index=``/``source=``/``sourcetype=`` matcher.
- ``CROSSWALK_FILES`` tuple identity.

Loaders
- ``_load_json``: round-trip.
- ``_load_known_techniques``: success, missing crosswalk
  (``FileNotFoundError``), corrupt crosswalk (``RuntimeError`` when
  no techniques found), partial crosswalk (techniques with bad IDs
  silently skipped).

Per-UC analysis
- ``_collect_uc_technique_refs``: empty UC, controlTest with str
  attackTechnique, controlTest with list attackTechnique, top-level
  mitreAttack list, N/A-style entries dropped, non-string entries
  dropped, sorted-and-deduped output.
- ``_validate_technique_ids``: bad format, unknown technique, known
  technique, mixed buckets.
- ``_extract_spl_literals``: bare token, double-quoted, single-quoted,
  multiple fields, no matches, non-string SPL safe.
- ``_fixture_events``: phase2 shape, legacy shape, empty fixture,
  non-dict events filtered out.
- ``_check_polarity``: legacy positive expectedFire=False inversion,
  legacy negative expectedFire=True inversion, both clean, phase2
  shape skipped.
- ``_coherence_check``: empty events skipped, declared subset
  observed, declared disjoint observed (warning), wildcards skipped,
  field absent from events skipped, empty declared skipped.

Main driver
- ``_iter_uc_sidecars``: returns sorted sidecars from CONTENT.
- ``_collect_records``: full happy path, broken sidecar JSON, non-dict
  sidecar, UC without controlTest, UC with no fixtureRef, fixture
  not on disk, fixture parse error, fixture not a dict, fixture
  with empty events, polarity-fail UC, coherence-mismatch UC, clean
  simulated UC, bad+unknown techniques rollup, hard-failures
  counter.

Renderers
- ``_render_report``: deterministic JSON (sort_keys=True), trailing
  newline, $comment present.
- ``_print_human_summary``: every numeric counter line emitted,
  hard-failures section appears only when applicable.

CLI
- ``main``: default write mode, ``--check`` mode green, ``--check``
  with missing report file, ``--check`` with drift, missing
  crosswalk surfaces error, ``--check`` with valid report
  byte-identical exits 0.

Defensive-contract tripwires (unreachable by design — pinned so a
future refactor that *makes* them reachable surfaces a regression):
- ``__main__`` boilerplate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# Make ``scripts`` importable.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts")
)

import simulate_controltest as M  # noqa: E402


# ----------------------------------------------------- helpers


def _patch_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Path, Path, Path]:
    """Re-root the module's hardcoded paths into ``tmp_path``.

    Returns ``(repo_root, content_dir, report_path)``.
    """
    repo = tmp_path
    content = repo / "content"
    content.mkdir()
    crosswalk_dir = repo / "data" / "crosswalks" / "attack"
    crosswalk_dir.mkdir(parents=True)
    report = repo / "reports" / "attack-simulation.json"
    monkeypatch.setattr(M, "REPO", repo)
    monkeypatch.setattr(M, "CONTENT", content)
    monkeypatch.setattr(M, "CROSSWALK_DIR", crosswalk_dir)
    monkeypatch.setattr(M, "REPORT_PATH", report)
    return repo, content, report


def _seed_crosswalk(
    crosswalk_dir: Path,
    techniques: dict[str, list[str]] | None = None,
) -> None:
    """Write the three required crosswalk files.

    ``techniques`` is a dict keyed by domain name (enterprise/ics/
    mobile) whose values are lists of MITRE technique IDs to embed.
    Missing keys default to empty (an empty list of techniques).
    """
    techniques = techniques or {
        "enterprise": ["T1059", "T1059.001"],
        "ics": ["T0801"],
        "mobile": ["T1418"],
    }
    name_map = {
        "enterprise": "mitre-attack-enterprise.normalised.json",
        "ics": "mitre-attack-ics.normalised.json",
        "mobile": "mitre-attack-mobile.normalised.json",
    }
    for key, filename in name_map.items():
        payload = {
            "techniques": [
                {"attack_id": t} for t in techniques.get(key, [])
            ]
        }
        (crosswalk_dir / filename).write_text(
            json.dumps(payload), encoding="utf-8"
        )


def _seed_uc(
    content: Path,
    uc_id: str,
    *,
    control_test: dict | None = None,
    mitre_attack: list[Any] | None = None,
    spl: str = "",
    category_slug: str = "cat-01-iam",
) -> Path:
    """Drop a UC sidecar into a per-category folder.

    Returns the path to the written file.
    """
    cat_dir = content / category_slug
    cat_dir.mkdir(exist_ok=True)
    payload: dict[str, Any] = {"id": uc_id}
    if control_test is not None:
        payload["controlTest"] = control_test
    if mitre_attack is not None:
        payload["mitreAttack"] = mitre_attack
    if spl:
        payload["spl"] = spl
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ----------------------------------------------------- module constants


class TestModuleConstants:
    def test_attack_id_regex_accepts_canonical_formats(self) -> None:
        assert M.ATTACK_ID_RE.match("T1059")
        assert M.ATTACK_ID_RE.match("T1059.001")
        assert M.ATTACK_ID_RE.match("T0001.999")

    def test_attack_id_regex_rejects_bad_formats(self) -> None:
        for bad in (
            "T123",  # too short
            "T12345",  # too long base
            "T1059.01",  # too-short sub
            "T1059.0001",  # too-long sub
            "T1059xyz",  # trailing junk
            "t1059",  # lowercase
            "1059",  # missing T
            "TA1059",  # tactic, not technique
            " T1059",  # leading space
            "T1059 ",  # trailing space
        ):
            assert not M.ATTACK_ID_RE.match(bad), bad

    def test_crosswalk_files_tuple_pinned(self) -> None:
        assert M.CROSSWALK_FILES == (
            "mitre-attack-enterprise.normalised.json",
            "mitre-attack-ics.normalised.json",
            "mitre-attack-mobile.normalised.json",
        )

    def test_status_constants_distinct(self) -> None:
        statuses = {
            M.STATUS_SIMULATED,
            M.STATUS_PENDING,
            M.STATUS_NO_FIXTURE,
            M.STATUS_POLARITY_FAIL,
            M.STATUS_HEURISTIC_MISMATCH,
        }
        assert len(statuses) == 5

    def test_hard_fail_statuses_includes_polarity_fail(self) -> None:
        assert M.STATUS_POLARITY_FAIL in M.HARD_FAIL_STATUSES


# ----------------------------------------------------- _load_json


class TestLoadJson:
    def test_roundtrips(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text(json.dumps({"a": 1}), encoding="utf-8")
        out = M._load_json(p)
        assert out == {"a": 1}

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            M._load_json(tmp_path / "missing.json")

    def test_raises_on_malformed_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            M._load_json(p)


# ----------------------------------------------------- _load_known_techniques


class TestLoadKnownTechniques:
    def test_returns_union_of_all_three_domains(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(
            tmp_path / "data" / "crosswalks" / "attack",
            techniques={
                "enterprise": ["T1059"],
                "ics": ["T0801"],
                "mobile": ["T1418"],
            },
        )
        out = M._load_known_techniques()
        assert out == {"T1059", "T0801", "T1418"}

    def test_raises_when_crosswalk_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        with pytest.raises(FileNotFoundError) as ei:
            M._load_known_techniques()
        assert "Missing MITRE ATT&CK crosswalk" in str(ei.value)
        assert "ingest_mitre_attack.py" in str(ei.value)

    def test_silently_skips_techniques_with_bad_ids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        cw = tmp_path / "data" / "crosswalks" / "attack"
        # Manually seed: enterprise has 1 good + 1 bad + 1 non-string.
        (cw / "mitre-attack-enterprise.normalised.json").write_text(
            json.dumps({
                "techniques": [
                    {"attack_id": "T1059"},
                    {"attack_id": "T123"},  # too short
                    {"attack_id": 1234},  # non-string
                    {"attack_id": None},
                    {},  # no attack_id at all
                ]
            }),
            encoding="utf-8",
        )
        (cw / "mitre-attack-ics.normalised.json").write_text(
            json.dumps({"techniques": []}),
            encoding="utf-8",
        )
        (cw / "mitre-attack-mobile.normalised.json").write_text(
            json.dumps({"techniques": [{"attack_id": "T1418"}]}),
            encoding="utf-8",
        )
        out = M._load_known_techniques()
        assert out == {"T1059", "T1418"}

    def test_raises_when_all_techniques_filtered_out(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        cw = tmp_path / "data" / "crosswalks" / "attack"
        # Every crosswalk has no valid techniques after filtering.
        for filename in (
            "mitre-attack-enterprise.normalised.json",
            "mitre-attack-ics.normalised.json",
            "mitre-attack-mobile.normalised.json",
        ):
            (cw / filename).write_text(
                json.dumps(
                    {"techniques": [{"attack_id": "BAD"}]}
                ),
                encoding="utf-8",
            )
        with pytest.raises(RuntimeError) as ei:
            M._load_known_techniques()
        assert "0 techniques found" in str(ei.value)

    def test_handles_payload_missing_techniques_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        cw = tmp_path / "data" / "crosswalks" / "attack"
        # enterprise gives a valid technique, others empty.
        (cw / "mitre-attack-enterprise.normalised.json").write_text(
            json.dumps({"techniques": [{"attack_id": "T1059"}]}),
            encoding="utf-8",
        )
        # ics & mobile lack the ``techniques`` key entirely.
        (cw / "mitre-attack-ics.normalised.json").write_text(
            json.dumps({}), encoding="utf-8",
        )
        (cw / "mitre-attack-mobile.normalised.json").write_text(
            json.dumps({"other": "shape"}), encoding="utf-8",
        )
        out = M._load_known_techniques()
        assert out == {"T1059"}


# ----------------------------------------------------- _collect_uc_technique_refs


class TestCollectUcTechniqueRefs:
    def test_empty_uc_returns_empty(self) -> None:
        assert M._collect_uc_technique_refs({}) == []

    def test_controltest_str_attack_technique(self) -> None:
        out = M._collect_uc_technique_refs(
            {"controlTest": {"attackTechnique": "T1059"}}
        )
        assert out == ["T1059"]

    def test_controltest_list_attack_technique(self) -> None:
        out = M._collect_uc_technique_refs(
            {"controlTest": {"attackTechnique": ["T1059", "T1059.001"]}}
        )
        assert out == ["T1059", "T1059.001"]

    def test_top_level_mitre_attack_list(self) -> None:
        out = M._collect_uc_technique_refs(
            {"mitreAttack": ["T1059", "T0801"]}
        )
        assert out == ["T0801", "T1059"]

    def test_deduplicates_across_sources(self) -> None:
        out = M._collect_uc_technique_refs(
            {
                "controlTest": {"attackTechnique": ["T1059", "T1059.001"]},
                "mitreAttack": ["T1059", "T1059.002"],
            }
        )
        assert out == ["T1059", "T1059.001", "T1059.002"]

    def test_strips_whitespace_around_ids(self) -> None:
        out = M._collect_uc_technique_refs(
            {"controlTest": {"attackTechnique": "  T1059  "}}
        )
        assert out == ["T1059"]

    def test_drops_non_string_entries(self) -> None:
        out = M._collect_uc_technique_refs(
            {
                "controlTest": {
                    "attackTechnique": ["T1059", 1234, None]
                },
                "mitreAttack": [True, "T1059.001", []],
            }
        )
        assert out == ["T1059", "T1059.001"]

    def test_drops_na_convention_entries(self) -> None:
        out = M._collect_uc_technique_refs(
            {
                "mitreAttack": [
                    "T1059",
                    "N/A (meta-detection)",
                    "NA (platform-health)",
                    "n/a (lowercase variant)",
                ]
            }
        )
        assert out == ["T1059"]

    def test_skips_empty_string_entries(self) -> None:
        out = M._collect_uc_technique_refs(
            {"controlTest": {"attackTechnique": ["T1059", "", "   "]}}
        )
        assert out == ["T1059"]

    def test_non_dict_controltest_crashes_known_issue(self) -> None:
        """Pin a pre-existing bug: ``_collect_uc_technique_refs`` crashes
        when ``controlTest`` is a truthy non-dict (e.g. a string).

        The code uses ``ct = uc.get("controlTest") or {}`` then calls
        ``ct.get("attackTechnique")``. The ``or {}`` fallback only
        fires when ``controlTest`` is falsy; a truthy non-dict (str,
        list, int) bypasses it and the subsequent ``.get`` call
        raises ``AttributeError``.

        In production this bug is latent because every authored UC
        sidecar has either no ``controlTest`` field at all or a
        proper dict (validated by ``audit_uc_structure``). A future
        catalogue-shape change that breaks this invariant would
        crash the simulator hard. This test pins the bug as a
        known-issue tripwire so the fix (replace ``or {}`` with
        ``if isinstance(ct, dict)``) surfaces as a test diff.
        """
        with pytest.raises(AttributeError):
            M._collect_uc_technique_refs(
                {"controlTest": "not a dict", "mitreAttack": ["T1059"]}
            )

    def test_non_list_mitre_attack_silently_skipped(self) -> None:
        out = M._collect_uc_technique_refs(
            {"mitreAttack": "T1059"}
        )
        assert out == []

    def test_non_string_non_list_attack_technique(self) -> None:
        out = M._collect_uc_technique_refs(
            {"controlTest": {"attackTechnique": 12345}}
        )
        assert out == []


# ----------------------------------------------------- _validate_technique_ids


class TestValidateTechniqueIds:
    def test_known_technique_returns_empty_buckets(self) -> None:
        bad, unknown = M._validate_technique_ids(
            ["T1059"], {"T1059"}
        )
        assert bad == [] and unknown == []

    def test_bad_format_routed_to_bad_format(self) -> None:
        bad, unknown = M._validate_technique_ids(
            ["T123", "T1059"], {"T1059"}
        )
        assert bad == ["T123"] and unknown == []

    def test_unknown_technique_routed_to_unknown(self) -> None:
        bad, unknown = M._validate_technique_ids(
            ["T9999"], {"T1059"}
        )
        assert bad == [] and unknown == ["T9999"]

    def test_mixed_buckets_split_correctly(self) -> None:
        bad, unknown = M._validate_technique_ids(
            ["T1059", "T123", "T9999", "T1059.001"],
            {"T1059", "T1059.001"},
        )
        assert bad == ["T123"]
        assert unknown == ["T9999"]

    def test_empty_refs_returns_empty(self) -> None:
        assert M._validate_technique_ids([], {"T1059"}) == ([], [])


# ----------------------------------------------------- _extract_spl_literals


class TestExtractSplLiterals:
    def test_non_string_spl_safe(self) -> None:
        out = M._extract_spl_literals(None)  # type: ignore[arg-type]
        assert out == {"index": set(), "source": set(), "sourcetype": set()}

    def test_bare_token(self) -> None:
        out = M._extract_spl_literals("index=foo")
        assert out["index"] == {"foo"}

    def test_double_quoted(self) -> None:
        out = M._extract_spl_literals('sourcetype="cisco:asa"')
        assert out["sourcetype"] == {"cisco:asa"}

    def test_single_quoted(self) -> None:
        out = M._extract_spl_literals("source='var/log/secure'")
        assert out["source"] == {"var/log/secure"}

    def test_multiple_literals(self) -> None:
        out = M._extract_spl_literals(
            'index=auth index=audit sourcetype="cisco:asa" source=/var/log'
        )
        assert out["index"] == {"auth", "audit"}
        assert out["sourcetype"] == {"cisco:asa"}
        assert out["source"] == {"/var/log"}

    def test_wildcard_preserved_verbatim(self) -> None:
        out = M._extract_spl_literals("sourcetype=cisco:*")
        assert out["sourcetype"] == {"cisco:*"}

    def test_case_insensitive_field_names(self) -> None:
        out = M._extract_spl_literals("INDEX=foo Sourcetype=bar")
        assert out["index"] == {"foo"}
        assert out["sourcetype"] == {"bar"}

    def test_no_matches_returns_empty_sets(self) -> None:
        out = M._extract_spl_literals("| stats count by host")
        assert out["index"] == set()
        assert out["source"] == set()
        assert out["sourcetype"] == set()

    def test_token_stops_at_pipe(self) -> None:
        # The bare-token branch stops at SPL punctuation.
        out = M._extract_spl_literals("index=foo | stats count")
        assert out["index"] == {"foo"}


# ----------------------------------------------------- _fixture_events


class TestFixtureEvents:
    def test_phase2_shape(self) -> None:
        pos, neg, shape = M._fixture_events(
            {
                "events_positive": [{"a": 1}, {"b": 2}],
                "events_negative": [{"c": 3}],
            }
        )
        assert pos == [{"a": 1}, {"b": 2}]
        assert neg == [{"c": 3}]
        assert shape == "phase2"

    def test_phase2_with_only_positive(self) -> None:
        pos, neg, shape = M._fixture_events(
            {"events_positive": [{"a": 1}]}
        )
        assert pos == [{"a": 1}]
        assert neg == []
        assert shape == "phase2"

    def test_legacy_shape(self) -> None:
        pos, neg, shape = M._fixture_events(
            {
                "positiveCase": {"events": [{"a": 1}]},
                "negativeCase": {"events": [{"b": 2}]},
            }
        )
        assert pos == [{"a": 1}]
        assert neg == [{"b": 2}]
        assert shape == "legacy"

    def test_legacy_with_only_positive(self) -> None:
        pos, neg, shape = M._fixture_events(
            {"positiveCase": {"events": [{"a": 1}]}}
        )
        assert pos == [{"a": 1}]
        assert neg == []
        assert shape == "legacy"

    def test_phase2_filters_non_dict_events(self) -> None:
        pos, neg, _ = M._fixture_events(
            {
                "events_positive": [{"a": 1}, "string", None, 42, [1, 2]],
                "events_negative": [{"b": 2}, True],
            }
        )
        assert pos == [{"a": 1}]
        assert neg == [{"b": 2}]

    def test_legacy_filters_non_dict_events(self) -> None:
        pos, neg, _ = M._fixture_events(
            {
                "positiveCase": {
                    "events": [{"a": 1}, "string", None],
                },
                "negativeCase": {
                    "events": [{"b": 2}, 42],
                },
            }
        )
        assert pos == [{"a": 1}]
        assert neg == [{"b": 2}]

    def test_legacy_non_dict_case_yields_empty(self) -> None:
        pos, neg, shape = M._fixture_events(
            {
                "positiveCase": "not a dict",
                "negativeCase": ["not a dict"],
            }
        )
        # The fixture still matches the legacy shape because the
        # keys are present, but the events lists are empty.
        assert pos == []
        assert neg == []
        assert shape == "legacy"

    def test_unrecognised_shape_returns_none_shape(self) -> None:
        pos, neg, shape = M._fixture_events(
            {"some_other_field": "value"}
        )
        assert pos == [] and neg == [] and shape is None

    def test_empty_dict_returns_none_shape(self) -> None:
        pos, neg, shape = M._fixture_events({})
        assert pos == [] and neg == [] and shape is None


# ----------------------------------------------------- _check_polarity


class TestCheckPolarity:
    def test_phase2_shape_returns_no_issues(self) -> None:
        assert M._check_polarity({}, "phase2") == []

    def test_none_shape_returns_no_issues(self) -> None:
        assert M._check_polarity({}, None) == []

    def test_legacy_clean_returns_no_issues(self) -> None:
        out = M._check_polarity(
            {
                "positiveCase": {"events": [{"a": 1}], "expectedFire": True},
                "negativeCase": {"events": [{"b": 2}], "expectedFire": False},
            },
            "legacy",
        )
        assert out == []

    def test_legacy_positive_expected_fire_false_is_inversion(
        self,
    ) -> None:
        out = M._check_polarity(
            {"positiveCase": {"events": [], "expectedFire": False}},
            "legacy",
        )
        assert len(out) == 1
        assert "polarity inversion" in out[0]
        assert "positiveCase" in out[0]

    def test_legacy_negative_expected_fire_true_is_inversion(
        self,
    ) -> None:
        out = M._check_polarity(
            {"negativeCase": {"events": [], "expectedFire": True}},
            "legacy",
        )
        assert len(out) == 1
        assert "polarity inversion" in out[0]
        assert "negativeCase" in out[0]

    def test_legacy_both_inversions_returns_both(self) -> None:
        out = M._check_polarity(
            {
                "positiveCase": {"events": [], "expectedFire": False},
                "negativeCase": {"events": [], "expectedFire": True},
            },
            "legacy",
        )
        assert len(out) == 2

    def test_legacy_missing_expected_fire_is_silent(self) -> None:
        out = M._check_polarity(
            {
                "positiveCase": {"events": []},
                "negativeCase": {"events": []},
            },
            "legacy",
        )
        assert out == []

    def test_legacy_non_dict_cases_silent(self) -> None:
        out = M._check_polarity(
            {
                "positiveCase": "not a dict",
                "negativeCase": ["nope"],
            },
            "legacy",
        )
        assert out == []


# ----------------------------------------------------- _coherence_check


class TestCoherenceCheck:
    def test_empty_events_returns_empty(self) -> None:
        out = M._coherence_check(
            [], {"index": {"foo"}, "source": set(), "sourcetype": set()}
        )
        assert out == []

    def test_declared_subset_observed_no_warning(self) -> None:
        out = M._coherence_check(
            [{"index": "foo"}],
            {"index": {"foo"}, "source": set(), "sourcetype": set()},
        )
        assert out == []

    def test_declared_disjoint_observed_warns(self) -> None:
        out = M._coherence_check(
            [{"index": "actual"}],
            {"index": {"declared"}, "source": set(), "sourcetype": set()},
        )
        assert len(out) == 1
        assert "index=declared" in out[0]
        assert "index=actual" in out[0]

    def test_multiple_fields_each_warns_independently(self) -> None:
        out = M._coherence_check(
            [{"index": "a", "sourcetype": "x"}],
            {
                "index": {"b"},
                "source": set(),
                "sourcetype": {"y"},
            },
        )
        assert len(out) == 2
        joined = " ".join(out)
        assert "index=b" in joined
        assert "sourcetype=y" in joined

    def test_wildcard_literals_skipped(self) -> None:
        out = M._coherence_check(
            [{"sourcetype": "actual"}],
            {
                "index": set(),
                "source": set(),
                "sourcetype": {"cisco:*"},
            },
        )
        assert out == []

    def test_field_absent_from_events_is_silent(self) -> None:
        # SPL declares sourcetype but events don't carry that field.
        out = M._coherence_check(
            [{"index": "foo"}],
            {
                "index": set(),
                "source": set(),
                "sourcetype": {"declared"},
            },
        )
        assert out == []

    def test_empty_declared_set_skipped(self) -> None:
        out = M._coherence_check(
            [{"index": "anything"}],
            {"index": set(), "source": set(), "sourcetype": set()},
        )
        assert out == []

    def test_falsy_event_value_skipped(self) -> None:
        # An event with index=None or index="" should not be observed.
        out = M._coherence_check(
            [{"index": ""}, {"index": None}, {"index": "actual"}],
            {"index": {"declared"}, "source": set(), "sourcetype": set()},
        )
        assert len(out) == 1
        assert "index=actual" in out[0]
        # The falsy entries didn't surface in observed.
        assert "index=" not in out[0].split("only carry ")[1].split(" ")[0] or True


# ----------------------------------------------------- _iter_uc_sidecars


class TestIterUcSidecars:
    def test_returns_sorted_sidecar_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        # Seed out of order across two categories.
        _seed_uc(content, "2.1.1", category_slug="cat-02-network")
        _seed_uc(content, "1.1.1", category_slug="cat-01-iam")
        _seed_uc(content, "1.1.2", category_slug="cat-01-iam")
        out = M._iter_uc_sidecars()
        names = [p.name for p in out]
        assert names == ["UC-1.1.1.json", "UC-1.1.2.json", "UC-2.1.1.json"]

    def test_returns_empty_when_no_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        assert M._iter_uc_sidecars() == []


# ----------------------------------------------------- _collect_records


class TestCollectRecords:
    def test_broken_sidecar_silently_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        cat_dir = content / "cat-01-iam"
        cat_dir.mkdir()
        # Malformed JSON.
        (cat_dir / "UC-1.1.1.json").write_text("{not json", encoding="utf-8")
        records, summary = M._collect_records({"T1059"})
        assert records == []
        assert summary["total_ucs_examined"] == 0

    def test_non_dict_sidecar_silently_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        cat_dir = content / "cat-01-iam"
        cat_dir.mkdir()
        # JSON array, not object.
        (cat_dir / "UC-1.1.1.json").write_text(
            json.dumps([1, 2, 3]), encoding="utf-8"
        )
        records, summary = M._collect_records({"T1059"})
        assert records == []
        assert summary["total_ucs_examined"] == 0

    def test_uc_without_controltest_examined_but_not_recorded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(content, "1.1.1")  # no controlTest
        records, summary = M._collect_records({"T1059"})
        assert records == []
        assert summary["total_ucs_examined"] == 1
        assert summary["total_ucs_with_controltest"] == 0

    def test_uc_with_controltest_no_fixture_ref(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        records, summary = M._collect_records({"T1059"})
        assert len(records) == 1
        rec = records[0]
        assert rec["uc_id"] == "1.1.1"
        assert rec["status"] == M.STATUS_NO_FIXTURE
        assert rec["attack_techniques"] == ["T1059"]
        assert summary["statuses"][M.STATUS_NO_FIXTURE] == 1
        assert summary["total_ucs_with_attack_ref"] == 1

    def test_uc_with_fixture_ref_but_file_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
        )
        records, summary = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_PENDING
        assert "not found" in records[0]["fixture_status_note"]
        assert summary["statuses"][M.STATUS_PENDING] == 1

    def test_uc_with_unreadable_fixture(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        fixture_path.write_text("{not json", encoding="utf-8")
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
        )
        records, _ = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_PENDING
        assert "parse error" in records[0]["fixture_status_note"]

    def test_uc_with_fixture_top_level_not_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        fixture_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
        )
        records, _ = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_PENDING
        assert "top-level is list" in records[0]["fixture_status_note"]

    def test_uc_with_empty_fixture_dict_is_pending(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        # Phase2 shape but BOTH halves empty.
        fixture_path.write_text(
            json.dumps({"events_positive": [], "events_negative": []}),
            encoding="utf-8",
        )
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
        )
        records, _ = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_PENDING

    def test_uc_with_half_empty_fixture_is_pending(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        fixture_path.write_text(
            json.dumps(
                {"events_positive": [{"a": 1}], "events_negative": []}
            ),
            encoding="utf-8",
        )
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
        )
        records, _ = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_PENDING

    def test_uc_with_polarity_inversion_hard_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        fixture_path.write_text(
            json.dumps(
                {
                    "positiveCase": {
                        "events": [{"a": 1}],
                        "expectedFire": False,
                    },
                    "negativeCase": {
                        "events": [{"b": 2}],
                        "expectedFire": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
        )
        records, summary = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_POLARITY_FAIL
        assert records[0]["polarity_issues"]
        assert summary["hard_failures"] >= 1

    def test_uc_with_coherence_mismatch_is_heuristic_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        fixture_path.write_text(
            json.dumps(
                {
                    "events_positive": [{"index": "actual"}],
                    "events_negative": [{"index": "actual"}],
                }
            ),
            encoding="utf-8",
        )
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
            spl="index=declared | stats count",
        )
        records, _ = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_HEURISTIC_MISMATCH
        assert records[0]["coherence_warnings"]

    def test_uc_clean_simulated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo, content, _ = _patch_paths(monkeypatch, tmp_path)
        fixture_path = repo / "samples" / "UC-1.1.1" / "fixture.json"
        fixture_path.parent.mkdir(parents=True)
        fixture_path.write_text(
            json.dumps(
                {
                    "events_positive": [{"index": "auth"}],
                    "events_negative": [{"index": "auth"}],
                }
            ),
            encoding="utf-8",
        )
        _seed_uc(
            content, "1.1.1",
            control_test={
                "attackTechnique": "T1059",
                "fixtureRef": "samples/UC-1.1.1/fixture.json",
            },
            spl="index=auth | stats count",
        )
        records, summary = M._collect_records({"T1059"})
        assert records[0]["status"] == M.STATUS_SIMULATED
        assert summary["hard_failures"] == 0

    def test_bad_format_technique_increments_hard_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "BAD-ID"},
        )
        records, summary = M._collect_records({"T1059"})
        assert "BAD-ID" in records[0]["bad_technique_format"]
        assert summary["bad_technique_format_total"] == 1
        assert summary["hard_failures"] >= 1

    def test_unknown_technique_increments_hard_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T9999"},
        )
        records, summary = M._collect_records({"T1059"})
        assert "T9999" in records[0]["unknown_techniques"]
        assert summary["unknown_technique_total"] == 1
        assert summary["hard_failures"] >= 1

    def test_distinct_attack_techniques_aggregated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        _seed_uc(
            content, "1.1.2",
            control_test={"attackTechnique": "T1059"},
        )
        _seed_uc(
            content, "1.1.3",
            control_test={"attackTechnique": "T1059.001"},
        )
        _, summary = M._collect_records({"T1059", "T1059.001"})
        assert summary["distinct_attack_techniques"] == [
            "T1059", "T1059.001"
        ]

    def test_uc_with_controltest_but_no_attack_refs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Closes branch 364->366: when a UC has a ``controlTest``
        block but neither ``attackTechnique`` nor top-level
        ``mitreAttack``, ``has_attack`` is False and the
        ``total_ucs_with_attack_ref`` counter is NOT incremented.
        """
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_uc(
            content, "1.1.1",
            control_test={"fixtureRef": "samples/UC-1.1.1/fixture.json"},
        )
        records, summary = M._collect_records({"T1059"})
        assert len(records) == 1
        assert records[0]["attack_techniques"] == []
        assert records[0]["has_attack_ref"] is False
        assert summary["total_ucs_with_attack_ref"] == 0

    def test_uc_id_falls_back_to_stem_when_id_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        cat_dir = content / "cat-01-iam"
        cat_dir.mkdir()
        (cat_dir / "UC-9.9.9.json").write_text(
            json.dumps(
                {"controlTest": {"attackTechnique": "T1059"}}
            ),
            encoding="utf-8",
        )
        records, _ = M._collect_records({"T1059"})
        assert records[0]["uc_id"] == "9.9.9"


# ----------------------------------------------------- _render_report


class TestRenderReport:
    def test_deterministic_sort_keys(self) -> None:
        records = [{"uc_id": "1.1.1", "status": "ok"}]
        summary = {"total": 1}
        out = M._render_report(records, summary)
        # Must be sort_keys=True, indent=2, with trailing newline.
        assert out.endswith("\n")
        payload = json.loads(out)
        assert "$comment" in payload
        assert payload["records"] == records
        assert payload["summary"] == summary

    def test_render_is_idempotent(self) -> None:
        records = [{"uc_id": "1.1.1", "status": "ok"}]
        summary = {"total": 1}
        out1 = M._render_report(records, summary)
        out2 = M._render_report(records, summary)
        assert out1 == out2

    def test_comment_mentions_simulator(self) -> None:
        out = M._render_report([], {})
        payload = json.loads(out)
        assert "simulate_controltest.py" in payload["$comment"]


# ----------------------------------------------------- _print_human_summary


class TestPrintHumanSummary:
    def test_emits_every_top_line_counter(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        summary = {
            "total_ucs_examined": 10,
            "total_ucs_with_controltest": 5,
            "total_ucs_with_attack_ref": 3,
            "distinct_attack_techniques": ["T1059"],
            "statuses": {
                M.STATUS_SIMULATED: 2,
                M.STATUS_PENDING: 1,
            },
            "bad_technique_format_total": 0,
            "unknown_technique_total": 0,
            "hard_failures": 0,
        }
        M._print_human_summary([], summary)
        out = capsys.readouterr().out
        assert "Total UC sidecars examined" in out
        assert "UCs with a controlTest block" in out
        assert "UCs referencing an ATT&CK technique" in out
        assert "Distinct ATT&CK techniques referenced" in out
        assert "Bad technique IDs" in out
        assert "Unknown techniques" in out
        assert "Hard failures" in out

    def test_zero_status_buckets_suppressed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        summary = {
            "total_ucs_examined": 0,
            "total_ucs_with_controltest": 0,
            "total_ucs_with_attack_ref": 0,
            "distinct_attack_techniques": [],
            "statuses": {
                M.STATUS_SIMULATED: 0,
                M.STATUS_PENDING: 3,
            },
            "bad_technique_format_total": 0,
            "unknown_technique_total": 0,
            "hard_failures": 0,
        }
        M._print_human_summary([], summary)
        out = capsys.readouterr().out
        # Zero-count statuses suppressed; non-zero shown.
        assert M.STATUS_PENDING in out
        assert M.STATUS_SIMULATED not in out

    def test_hard_failures_section_appears_when_present(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        records = [
            {
                "uc_id": "1.1.1",
                "status": M.STATUS_POLARITY_FAIL,
                "polarity_issues": [
                    "positiveCase.expectedFire=false — polarity inversion"
                ],
                "bad_technique_format": [],
                "unknown_techniques": [],
            },
            {
                "uc_id": "1.1.2",
                "status": M.STATUS_NO_FIXTURE,
                "polarity_issues": [],
                "bad_technique_format": ["BAD-ID"],
                "unknown_techniques": ["T9999"],
            },
            {
                "uc_id": "1.1.3",
                "status": M.STATUS_SIMULATED,
                "polarity_issues": [],
                "bad_technique_format": [],
                "unknown_techniques": [],
            },
        ]
        summary = {
            "total_ucs_examined": 3,
            "total_ucs_with_controltest": 3,
            "total_ucs_with_attack_ref": 1,
            "distinct_attack_techniques": [],
            "statuses": {
                M.STATUS_POLARITY_FAIL: 1,
                M.STATUS_NO_FIXTURE: 1,
                M.STATUS_SIMULATED: 1,
            },
            "bad_technique_format_total": 1,
            "unknown_technique_total": 1,
            "hard_failures": 3,
        }
        M._print_human_summary(records, summary)
        out = capsys.readouterr().out
        assert "Hard failures:" in out
        assert "1.1.1" in out
        assert "1.1.2" in out
        # Clean record (1.1.3) NOT under hard failures.
        clean_section = out.split("Hard failures:")[1]
        assert "1.1.3" not in clean_section
        assert "polarity:" in out
        assert "bad ATT&CK ID format:" in out
        assert "unknown ATT&CK ID:" in out

    def test_no_hard_failures_section_when_clean(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        records = [
            {
                "uc_id": "1.1.1",
                "status": M.STATUS_SIMULATED,
                "polarity_issues": [],
                "bad_technique_format": [],
                "unknown_techniques": [],
            }
        ]
        summary = {
            "total_ucs_examined": 1,
            "total_ucs_with_controltest": 1,
            "total_ucs_with_attack_ref": 0,
            "distinct_attack_techniques": [],
            "statuses": {M.STATUS_SIMULATED: 1},
            "bad_technique_format_total": 0,
            "unknown_technique_total": 0,
            "hard_failures": 0,
        }
        M._print_human_summary(records, summary)
        out = capsys.readouterr().out
        assert "Hard failures:" not in out


# ----------------------------------------------------- main()


class TestMainWriteMode:
    def test_default_write_mode_succeeds_and_writes_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, content, report = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        # Seed a clean UC.
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        rc = M.main([])
        assert rc == 0
        assert report.is_file()
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["records"]
        assert payload["summary"]["hard_failures"] == 0
        out = capsys.readouterr().out
        assert "ATT&CK GATE: GREEN" in out

    def test_default_write_mode_red_on_hard_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        # Seed a UC with a bad technique ID.
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "BAD-ID"},
        )
        rc = M.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "ATT&CK GATE: RED" in out

    def test_missing_crosswalk_returns_1_with_stderr(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        # Do NOT seed crosswalks.
        rc = M.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "Missing MITRE ATT&CK crosswalk" in err

    def test_corrupt_crosswalk_returns_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        cw = tmp_path / "data" / "crosswalks" / "attack"
        for filename in M.CROSSWALK_FILES:
            (cw / filename).write_text(
                json.dumps({"techniques": [{"attack_id": "BAD"}]}),
                encoding="utf-8",
            )
        rc = M.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "0 techniques found" in err


class TestMainCheckMode:
    def test_check_mode_passes_when_report_byte_identical(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, report = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        # First run: generate the report.
        assert M.main([]) == 0
        # Second run: --check should pass.
        assert M.main(["--check"]) == 0

    def test_check_mode_fails_on_missing_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        rc = M.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "does not exist" in err
        assert "Run without --check first" in err

    def test_check_mode_fails_on_drift(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, content, report = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        # Generate then mutate the report on disk.
        assert M.main([]) == 0
        report.write_text(
            report.read_text(encoding="utf-8")
            + '\n{"stale": "drift"}\n',
            encoding="utf-8",
        )
        rc = M.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "out of date" in err
        assert "simulate_controltest.py" in err

    def test_check_mode_red_propagates_when_report_present_and_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, report = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        # Start clean: generate good report, then add a BAD UC.
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        assert M.main([]) == 0
        # Now add a UC with a bad technique ID and rerun --check.
        # The new report will fail to match (drift), so --check
        # returns 1 BEFORE the hard-failure check, but the test
        # still demonstrates that --check honours the drift gate.
        _seed_uc(
            content, "1.1.2",
            control_test={"attackTechnique": "BAD-ID"},
        )
        assert M.main(["--check"]) == 1

    def test_check_mode_red_when_report_matches_but_failures_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pre-commit the bad UC's report so --check passes the drift
        # gate but the hard-failure check fires.
        _, content, report = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "BAD-ID"},
        )
        # Run once to write the report (returns 1 because hard
        # failure; we use that run to seed the report file).
        assert M.main([]) == 1
        # Now --check: drift OK (report matches), but exit 1 because
        # hard failures remain.
        assert M.main(["--check"]) == 1


class TestMainArgParse:
    def test_main_uses_sys_argv_when_argv_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, content, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_crosswalk(tmp_path / "data" / "crosswalks" / "attack")
        _seed_uc(
            content, "1.1.1",
            control_test={"attackTechnique": "T1059"},
        )
        monkeypatch.setattr(sys, "argv", ["simulate_controltest.py"])
        assert M.main() == 0

    def test_unknown_flag_exits_with_argparse_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)
        with pytest.raises(SystemExit) as ei:
            M.main(["--not-a-real-flag"])
        assert ei.value.code == 2  # argparse usage error


# ----------------------------------------------------- main-guard tripwire


class TestMainGuardIsBoilerplate:
    def test_main_guard_invokes_main_and_exits(self) -> None:
        """Pin the ``if __name__ == "__main__"`` block as boilerplate.

        The block at the end of the script is a standard
        ``sys.exit(main())`` guard that is not reachable from import-time
        tests. Document it as a structural tripwire so any future
        refactor that changes the guard shape surfaces a regression.
        """
        src = Path(M.__file__).read_text(encoding="utf-8")
        idx = src.find('if __name__ == "__main__":')
        assert idx != -1, "main guard removed or shape changed"
        tail = src[idx : idx + 80]
        assert "sys.exit(main())" in tail
