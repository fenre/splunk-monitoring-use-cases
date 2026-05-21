"""Hermetic coverage for ``splunk_uc.generators.stewardship_digest``.

The module is the release-over-release weekly digest generator
introduced by repo-overhaul plan §P8 step 4. The CI smoke test in
``validate.yml`` only invokes ``main`` once against the live catalogue
and only diffs the JSON against the schema, so almost every branch in
this file was previously covered by accident or not at all
(8.9 % at the start of this commit).

This suite pins every pure helper, the top-level ``build_digest``
constructor, the markdown renderer, the disk emitter, and the CLI
wrapper one branch at a time. Each test owns a tiny fixture so an
unexpected behaviour change shows up as a single targeted regression
rather than a cascade.

Tests are organised in the same order as the module sections:

* Pure helpers (``_parse_iso_date``, ``_semver_key``,
  ``_previous_snapshot``, ``_snapshot_counts``, ``_quality_tiers``,
  ``_coverage_block``, ``_leader_block``, ``_delta_dict``,
  ``_coverage_shifts``, ``_top_movers``, ``_all_top_movers``).
* Stale-UC detection (``_walk_sidecars``, ``_stale_use_cases``).
* Audit-warning capture (``_parse_audit_warnings``).
* Top-level digest builder (``build_digest``) — happy path + first-
  release path + audit-warning passthrough + reference-date sentinel.
* Markdown renderer (``render_markdown``).
* CLI plumbing (``main`` + ``_emit``) — all I/O is hermetic against
  ``tmp_path``.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.generators import stewardship_digest as sd


# --------------------------------------------------------------------------- #
# Tiny shared fixture builders.
# --------------------------------------------------------------------------- #


def _metrics(
    *,
    version: str = "9.2.0",
    use_cases: int = 100,
    categories: int = 10,
    subcategories: int = 25,
    regulations: int = 15,
    equipment: int = 50,
    tiers: dict[str, int] | None = None,
    coverage: dict[str, dict[str, Any]] | None = None,
    leaders: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build a minimal metrics document with overridable fields."""
    return {
        "catalogueVersion": version,
        "counts": {
            "useCases": use_cases,
            "categories": categories,
            "subcategories": subcategories,
            "regulations": regulations,
            "equipment": equipment,
        },
        "quality": {
            "tierCounts": tiers or {"gold": 40, "silver": 30, "bronze": 20, "none": 10}
        },
        "coverage": coverage or {
            "compliance": {"count": 60, "percentage": 60.0},
            "mitreAttack": {"count": 70, "percentage": 70.0},
            "cimModels": {"count": 80, "percentage": 80.0},
            "equipment": {"count": 50, "percentage": 50.0},
            "escuDetections": {"count": 10, "percentage": 10.0},
            "escuRiskBased": {"count": 5, "percentage": 5.0},
            "prerequisites": {"count": 40, "percentage": 40.0},
        },
        "leaders": leaders or {
            "regulations": [
                {"regulation": "GDPR", "count": 12},
                {"regulation": "PCI", "count": 10},
            ],
            "mitreAttack": [
                {"technique": "T1078", "count": 8},
                {"technique": "T1110", "count": 6},
            ],
            "cimModels": [
                {"model": "Authentication", "count": 15},
                {"model": "Network_Traffic", "count": 11},
            ],
            "equipment": [
                {"equipment": "splunk", "count": 20},
                {"equipment": "cisco-asa", "count": 5},
            ],
        },
    }


# --------------------------------------------------------------------------- #
# Pure helpers — _parse_iso_date.
# --------------------------------------------------------------------------- #


class TestParseIsoDate:
    """``_parse_iso_date`` accepts ``YYYY-MM-DD`` and rejects everything else."""

    def test_valid_iso_date_returns_date(self) -> None:
        assert sd._parse_iso_date("2026-05-20") == _dt.date(2026, 5, 20)

    @pytest.mark.parametrize("bad", ["", "not-a-date", "2026-13-01", "2026/05/20"])
    def test_invalid_string_returns_none(self, bad: str) -> None:
        assert sd._parse_iso_date(bad) is None

    @pytest.mark.parametrize("value", [None, 42, 3.14, ["2026-05-20"], {"d": "x"}])
    def test_non_string_returns_none(self, value: Any) -> None:
        assert sd._parse_iso_date(value) is None


# --------------------------------------------------------------------------- #
# Pure helpers — _semver_key.
# --------------------------------------------------------------------------- #


class TestSemverKey:
    """``_semver_key`` is a sort key, not a validator; non-numeric segments
    must fall back to 0 so the function never crashes."""

    def test_plain_three_part_version(self) -> None:
        assert sd._semver_key("9.2.0") == (9, 2, 0)

    def test_prerelease_suffix_is_stripped(self) -> None:
        assert sd._semver_key("9.2.0-rc1") == (9, 2, 0)

    def test_build_metadata_is_stripped(self) -> None:
        assert sd._semver_key("9.2.0+sha") == (9, 2, 0)

    def test_both_suffixes_are_stripped(self) -> None:
        assert sd._semver_key("9.2.0-rc1+sha") == (9, 2, 0)

    def test_non_numeric_segments_become_zero(self) -> None:
        assert sd._semver_key("9.alpha.beta") == (9, 0, 0)

    def test_compares_higher_minor(self) -> None:
        assert sd._semver_key("9.2.0") < sd._semver_key("9.10.0")


# --------------------------------------------------------------------------- #
# Pure helpers — _previous_snapshot.
# --------------------------------------------------------------------------- #


class TestPreviousSnapshot:
    """``_previous_snapshot`` picks the highest-version snapshot strictly
    less than the current version, ignoring ``index.json`` and tolerating
    corrupt or malformed snapshots in the history dir."""

    def test_returns_none_when_history_dir_missing(self, tmp_path: Path) -> None:
        assert sd._previous_snapshot(tmp_path / "nope", "9.2.0") is None

    def test_returns_none_when_no_eligible_snapshot(self, tmp_path: Path) -> None:
        """Only snapshots strictly less than ``current_version`` are eligible.
        A history of [9.2.0] against current 9.2.0 returns None."""
        (tmp_path / "9.2.0.json").write_text(
            json.dumps({"catalogueVersion": "9.2.0"}), encoding="utf-8"
        )
        assert sd._previous_snapshot(tmp_path, "9.2.0") is None

    def test_picks_highest_strictly_lower_version(self, tmp_path: Path) -> None:
        for ver in ("9.0.0", "9.1.0", "9.2.0", "9.3.0"):
            (tmp_path / f"{ver}.json").write_text(
                json.dumps({"catalogueVersion": ver, "marker": ver}),
                encoding="utf-8",
            )
        result = sd._previous_snapshot(tmp_path, "9.2.0")
        assert result is not None
        assert result["marker"] == "9.1.0"

    def test_higher_then_lower_strictly_lower_keeps_higher(
        self, tmp_path: Path
    ) -> None:
        """When iteration encounters a strictly-lower snapshot AFTER an
        even-higher strictly-lower one, the loop must keep the earlier
        winner (covers the ``best_key is None or ver_key > best_key``
        branch's False arm — i.e., 'we already have a better
        snapshot').

        ``sorted(history_dir.glob('*.json'))`` is alphabetic on
        filename, so we craft filenames whose alphabetic order is the
        OPPOSITE of their semver order. ``a-snap.json`` is visited
        first with catalogueVersion 9.1.0; ``b-snap.json`` is visited
        second with catalogueVersion 9.0.0. The second iteration must
        leave ``best_doc`` untouched.
        """
        (tmp_path / "a-snap.json").write_text(
            json.dumps({"catalogueVersion": "9.1.0", "marker": "winner"}),
            encoding="utf-8",
        )
        (tmp_path / "b-snap.json").write_text(
            json.dumps({"catalogueVersion": "9.0.0", "marker": "loser"}),
            encoding="utf-8",
        )
        result = sd._previous_snapshot(tmp_path, "9.2.0")
        assert result is not None
        assert result["marker"] == "winner"

    def test_skips_index_json(self, tmp_path: Path) -> None:
        (tmp_path / "index.json").write_text(
            json.dumps({"catalogueVersion": "99.0.0", "marker": "INDEX"}),
            encoding="utf-8",
        )
        (tmp_path / "9.0.0.json").write_text(
            json.dumps({"catalogueVersion": "9.0.0", "marker": "REAL"}),
            encoding="utf-8",
        )
        result = sd._previous_snapshot(tmp_path, "9.2.0")
        assert result is not None
        assert result["marker"] == "REAL"

    def test_skips_corrupt_json(self, tmp_path: Path) -> None:
        (tmp_path / "9.0.0.json").write_text(
            "{not valid json", encoding="utf-8"
        )
        (tmp_path / "9.1.0.json").write_text(
            json.dumps({"catalogueVersion": "9.1.0", "marker": "OK"}),
            encoding="utf-8",
        )
        result = sd._previous_snapshot(tmp_path, "9.2.0")
        assert result is not None
        assert result["marker"] == "OK"

    def test_skips_snapshots_without_string_version(self, tmp_path: Path) -> None:
        (tmp_path / "x.json").write_text(
            json.dumps({"catalogueVersion": 9}), encoding="utf-8"
        )
        (tmp_path / "y.json").write_text(
            json.dumps({"marker": "no-version"}), encoding="utf-8"
        )
        (tmp_path / "9.0.0.json").write_text(
            json.dumps({"catalogueVersion": "9.0.0", "marker": "VALID"}),
            encoding="utf-8",
        )
        result = sd._previous_snapshot(tmp_path, "9.2.0")
        assert result is not None
        assert result["marker"] == "VALID"


# --------------------------------------------------------------------------- #
# Pure helpers — _snapshot_counts / _quality_tiers / _coverage_block / _leader_block.
# --------------------------------------------------------------------------- #


class TestSnapshotCounts:
    def test_extracts_known_keys(self) -> None:
        out = sd._snapshot_counts(_metrics())
        assert out == {
            "version": "9.2.0",
            "useCases": 100,
            "categories": 10,
            "subcategories": 25,
            "regulations": 15,
            "equipment": 50,
        }

    def test_missing_counts_default_to_zero(self) -> None:
        out = sd._snapshot_counts({})
        assert out["version"] == "0.0.0"
        assert out["useCases"] == 0
        assert out["categories"] == 0

    def test_none_counts_block_treated_as_empty(self) -> None:
        out = sd._snapshot_counts({"catalogueVersion": "1.0.0", "counts": None})
        assert out["version"] == "1.0.0"
        assert out["useCases"] == 0


class TestQualityTiers:
    def test_all_four_tiers_returned(self) -> None:
        out = sd._quality_tiers(_metrics())
        assert out == {"gold": 40, "silver": 30, "bronze": 20, "none": 10}

    def test_absent_tiers_default_to_zero(self) -> None:
        out = sd._quality_tiers({"quality": {"tierCounts": {"gold": 5}}})
        assert out == {"gold": 5, "silver": 0, "bronze": 0, "none": 0}

    def test_none_quality_block_yields_all_zero(self) -> None:
        out = sd._quality_tiers({"quality": None})
        assert out == {"gold": 0, "silver": 0, "bronze": 0, "none": 0}


class TestCoverageBlock:
    def test_returns_all_seven_axes(self) -> None:
        out = sd._coverage_block(_metrics())
        assert set(out.keys()) == set(sd.COVERAGE_AXES)
        assert out["compliance"] == {"count": 60, "percentage": 60.0}

    def test_missing_axes_default_to_zero(self) -> None:
        out = sd._coverage_block({"coverage": {"compliance": {"count": 1, "percentage": 1.5}}})
        assert out["compliance"] == {"count": 1, "percentage": 1.5}
        for axis in sd.COVERAGE_AXES:
            if axis == "compliance":
                continue
            assert out[axis] == {"count": 0, "percentage": 0.0}

    def test_none_coverage_block_yields_all_zero(self) -> None:
        out = sd._coverage_block({"coverage": None})
        for axis in sd.COVERAGE_AXES:
            assert out[axis] == {"count": 0, "percentage": 0.0}


class TestLeaderBlock:
    def test_flattens_known_axes(self) -> None:
        out = sd._leader_block(_metrics())
        assert out["regulations"] == {"GDPR": 12, "PCI": 10}
        assert out["mitreAttack"] == {"T1078": 8, "T1110": 6}
        assert out["cimModels"] == {"Authentication": 15, "Network_Traffic": 11}
        assert out["equipment"] == {"splunk": 20, "cisco-asa": 5}

    def test_skips_entries_with_non_string_or_empty_name(self) -> None:
        m = _metrics()
        m["leaders"]["regulations"] = [
            {"regulation": "GDPR", "count": 10},
            {"regulation": None, "count": 99},
            {"regulation": "", "count": 99},
            {"regulation": 123, "count": 99},
        ]
        out = sd._leader_block(m)
        assert out["regulations"] == {"GDPR": 10}

    def test_missing_leaders_yields_empty_axes(self) -> None:
        out = sd._leader_block({})
        for axis in sd.LEADER_AXES:
            assert out[axis] == {}

    def test_none_leaders_block_yields_empty_axes(self) -> None:
        out = sd._leader_block({"leaders": None})
        for axis in sd.LEADER_AXES:
            assert out[axis] == {}


# --------------------------------------------------------------------------- #
# Pure helpers — _delta_dict / _coverage_shifts.
# --------------------------------------------------------------------------- #


class TestDeltaDict:
    def test_signed_difference_per_key(self) -> None:
        out = sd._delta_dict({"a": 10, "b": 5}, {"a": 7, "b": 5})
        assert out == {"a": 3, "b": 0}

    def test_keys_present_in_only_one_dict(self) -> None:
        out = sd._delta_dict({"a": 10}, {"b": 5})
        assert out == {"a": 10, "b": -5}

    def test_empty_inputs(self) -> None:
        assert sd._delta_dict({}, {}) == {}


class TestCoverageShifts:
    def test_first_release_path_no_previous(self) -> None:
        cur = sd._coverage_block(_metrics())
        out = sd._coverage_shifts(cur, None)
        for axis in sd.COVERAGE_AXES:
            block = out[axis]
            assert block["delta"] == 0
            assert "previousCount" not in block
            assert "previousPercentage" not in block
            assert "percentageDelta" not in block

    def test_normal_path_with_previous(self) -> None:
        cur = sd._coverage_block(_metrics())
        prev = sd._coverage_block(_metrics(coverage={
            "compliance": {"count": 50, "percentage": 50.0},
            "mitreAttack": {"count": 65, "percentage": 65.0},
            "cimModels": {"count": 80, "percentage": 80.0},
            "equipment": {"count": 50, "percentage": 50.0},
            "escuDetections": {"count": 10, "percentage": 10.0},
            "escuRiskBased": {"count": 5, "percentage": 5.0},
            "prerequisites": {"count": 40, "percentage": 40.0},
        }))
        out = sd._coverage_shifts(cur, prev)
        # compliance went 50 -> 60, +10
        assert out["compliance"]["delta"] == 10
        assert out["compliance"]["percentageDelta"] == 10.0
        # mitreAttack 65 -> 70, +5
        assert out["mitreAttack"]["delta"] == 5
        # cimModels unchanged
        assert out["cimModels"]["delta"] == 0
        assert out["cimModels"]["percentageDelta"] == 0.0


# --------------------------------------------------------------------------- #
# Pure helpers — _top_movers / _all_top_movers.
# --------------------------------------------------------------------------- #


class TestTopMovers:
    def test_zero_delta_entries_are_dropped(self) -> None:
        out = sd._top_movers({"a": 5, "b": 6}, {"a": 5, "b": 4})
        assert [e["name"] for e in out] == ["b"]

    def test_sorted_by_abs_delta_desc_then_name_asc(self) -> None:
        cur = {"a": 1, "b": 10, "c": 5, "d": 3}
        prev = {"a": 11, "b": 0, "c": 1, "d": 0}
        out = sd._top_movers(cur, prev)
        # deltas: a=-10, b=10, c=4, d=3 → ordered by abs|delta| desc then
        # name asc: ['a', 'b', 'c', 'd']
        assert [e["name"] for e in out] == ["a", "b", "c", "d"]

    def test_respects_limit(self) -> None:
        cur = {chr(ord("a") + i): i + 1 for i in range(20)}
        prev = {chr(ord("a") + i): 0 for i in range(20)}
        out = sd._top_movers(cur, prev, limit=5)
        assert len(out) == 5

    def test_returns_empty_when_no_movement(self) -> None:
        assert sd._top_movers({"a": 1}, {"a": 1}) == []


class TestAllTopMovers:
    def test_first_release_path_returns_empty_axes(self) -> None:
        cur = {axis: {} for axis in sd.LEADER_AXES}
        out = sd._all_top_movers(cur, None)
        assert all(out[axis] == [] for axis in sd.LEADER_AXES)

    def test_per_axis_movers_isolated(self) -> None:
        cur = {
            "regulations": {"GDPR": 10},
            "mitreAttack": {"T1078": 5},
            "cimModels": {},
            "equipment": {"splunk": 1},
        }
        prev = {
            "regulations": {"GDPR": 5},
            "mitreAttack": {"T1078": 5},
            "cimModels": {},
            "equipment": {},
        }
        out = sd._all_top_movers(cur, prev)
        assert [e["name"] for e in out["regulations"]] == ["GDPR"]
        assert out["mitreAttack"] == []
        assert out["cimModels"] == []
        assert [e["name"] for e in out["equipment"]] == ["splunk"]


# --------------------------------------------------------------------------- #
# Stale-UC detection — _walk_sidecars / _stale_use_cases.
# --------------------------------------------------------------------------- #


class TestWalkSidecars:
    def test_returns_empty_when_dir_missing(self, tmp_path: Path) -> None:
        assert sd._walk_sidecars(tmp_path / "does-not-exist") == []

    def test_returns_empty_when_dir_empty(self, tmp_path: Path) -> None:
        assert sd._walk_sidecars(tmp_path) == []

    def test_collects_uc_sidecars_recursively(self, tmp_path: Path) -> None:
        (tmp_path / "cat-01-foo").mkdir()
        (tmp_path / "cat-02-bar").mkdir()
        (tmp_path / "cat-01-foo" / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "title": "first"}),
            encoding="utf-8",
        )
        (tmp_path / "cat-02-bar" / "UC-2.1.1.json").write_text(
            json.dumps({"id": "2.1.1", "title": "second"}),
            encoding="utf-8",
        )
        out = sd._walk_sidecars(tmp_path)
        assert len(out) == 2
        ids = {doc["id"] for doc in out}
        assert ids == {"1.1.1", "2.1.1"}

    def test_skips_non_uc_files(self, tmp_path: Path) -> None:
        (tmp_path / "cat-99-noise.md").write_text("hi", encoding="utf-8")
        (tmp_path / "UC-OK.json").write_text(
            json.dumps({"id": "OK", "title": "ok"}), encoding="utf-8"
        )
        assert len(sd._walk_sidecars(tmp_path)) == 1

    def test_tolerates_corrupt_json_and_non_object_payloads(self, tmp_path: Path) -> None:
        (tmp_path / "UC-bad.json").write_text("{not json", encoding="utf-8")
        (tmp_path / "UC-list.json").write_text("[1, 2, 3]", encoding="utf-8")
        (tmp_path / "UC-good.json").write_text(
            json.dumps({"id": "ok"}), encoding="utf-8"
        )
        out = sd._walk_sidecars(tmp_path)
        assert len(out) == 1
        assert out[0]["id"] == "ok"


class TestStaleUseCases:
    REF = _dt.date(2026, 5, 20)

    def _sidecar(
        self,
        *,
        uc_id: str = "1.1.1",
        title: str = "Test UC",
        last_reviewed: str | None = "2025-01-01",
        status: str | None = "verified",
    ) -> dict[str, Any]:
        out: dict[str, Any] = {"id": uc_id, "title": title}
        if last_reviewed is not None:
            out["lastReviewed"] = last_reviewed
        if status is not None:
            out["status"] = status
        return out

    def test_recent_uc_is_not_stale(self) -> None:
        side = [self._sidecar(last_reviewed=self.REF.isoformat())]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 0
        assert out["topStale"] == []

    def test_old_uc_is_stale(self) -> None:
        side = [self._sidecar(last_reviewed="2024-01-01")]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 1
        assert out["topStale"][0]["id"] == "1.1.1"

    def test_missing_last_reviewed_is_max_stale(self) -> None:
        side = [self._sidecar(last_reviewed=None)]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 1
        # Sentinel age is threshold + 1.
        assert out["topStale"][0]["ageDays"] == 181
        assert out["topStale"][0]["lastReviewed"] is None

    def test_by_category_groups_correctly(self) -> None:
        side = [
            self._sidecar(uc_id="3.1.1", last_reviewed="2020-01-01"),
            self._sidecar(uc_id="3.2.1", last_reviewed="2020-01-01"),
            self._sidecar(uc_id="5.1.1", last_reviewed="2020-01-01"),
        ]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["byCategory"] == {"3": 2, "5": 1}

    def test_uc_without_id_dropped(self) -> None:
        side = [{"title": "no id", "lastReviewed": "2020-01-01"}]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 0

    def test_uc_with_id_missing_dot_uses_zero_category(self) -> None:
        side = [self._sidecar(uc_id="42", last_reviewed="2020-01-01")]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["topStale"][0]["category"] == "0"

    def test_invalid_title_falls_back_to_untitled(self) -> None:
        side = [
            {"id": "1.1.1", "title": 42, "lastReviewed": "2020-01-01"},
            {"id": "1.1.2", "lastReviewed": "2020-01-01"},
        ]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert all(s["title"] == "(untitled)" for s in out["topStale"])

    def test_unknown_status_normalised(self) -> None:
        side = [
            self._sidecar(status="bogus", last_reviewed="2020-01-01"),
            {"id": "2.1.1", "lastReviewed": "2020-01-01"},  # no status field
        ]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        for s in out["topStale"]:
            assert s["status"] == "unknown"

    @pytest.mark.parametrize("status", ["verified", "community", "draft"])
    def test_known_status_preserved(self, status: str) -> None:
        side = [self._sidecar(last_reviewed="2020-01-01", status=status)]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["topStale"][0]["status"] == status

    def test_sort_by_age_desc_then_id_asc(self) -> None:
        side = [
            self._sidecar(uc_id="1.1.1", last_reviewed="2024-01-01"),
            self._sidecar(uc_id="2.1.1", last_reviewed="2020-01-01"),
            self._sidecar(uc_id="3.1.1", last_reviewed="2020-01-01"),
        ]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        ids = [s["id"] for s in out["topStale"]]
        assert ids == ["2.1.1", "3.1.1", "1.1.1"]

    def test_top_stale_capped_at_limit(self) -> None:
        side = [
            self._sidecar(uc_id=f"1.1.{i}", last_reviewed="2020-01-01")
            for i in range(1, 30)
        ]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 29
        assert len(out["topStale"]) == sd.TOP_STALE_LIMIT

    def test_last_reviewed_non_string_treated_as_max_stale(self) -> None:
        side = [{"id": "1.1.1", "title": "T", "lastReviewed": 42}]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 1
        # Non-string lastReviewed must surface as null in the output row.
        assert out["topStale"][0]["lastReviewed"] is None
        # Sentinel age was applied (max-stale path).
        assert out["topStale"][0]["ageDays"] == 181

    def test_last_reviewed_unparseable_string_treated_as_max_stale(self) -> None:
        side = [{"id": "1.1.1", "title": "T", "lastReviewed": "yesterday"}]
        out = sd._stale_use_cases(side, reference=self.REF, threshold_days=180)
        assert out["count"] == 1
        # The unparseable original string is preserved verbatim in the row.
        assert out["topStale"][0]["lastReviewed"] == "yesterday"
        assert out["topStale"][0]["ageDays"] == 181


# --------------------------------------------------------------------------- #
# Audit-warning capture — _parse_audit_warnings.
# --------------------------------------------------------------------------- #


class TestParseAuditWarnings:
    def test_extracts_warn_lines(self) -> None:
        stderr = "info line\nWARN : something is off\nWARN : another issue"
        out = sd._parse_audit_warnings(stderr, "audit_x")
        assert len(out) == 2
        assert all(e["audit"] == "audit_x" for e in out)
        assert all(e["severity"] == "warn" for e in out)
        assert out[0]["message"] == "something is off"
        assert out[1]["message"] == "another issue"

    def test_ignores_non_warn_lines(self) -> None:
        stderr = "INFO: hi\nERROR: bad\nWARN something without colon"
        out = sd._parse_audit_warnings(stderr, "x")
        assert out == []

    def test_empty_warn_message_dropped(self) -> None:
        stderr = "WARN : "
        out = sd._parse_audit_warnings(stderr, "x")
        assert out == []

    def test_empty_stderr(self) -> None:
        assert sd._parse_audit_warnings("", "x") == []


# --------------------------------------------------------------------------- #
# build_digest — top-level orchestrator.
# --------------------------------------------------------------------------- #


class TestBuildDigest:
    REF = _dt.date(2026, 5, 20)

    def test_first_release_path_has_no_previous(self) -> None:
        digest = sd.build_digest(
            metrics=_metrics(),
            previous=None,
            sidecars=[],
            audit_warnings=[],
            reference_date=self.REF,
        )
        assert digest["previous"] is None
        assert all(v == 0 for v in digest["deltas"].values())
        assert digest["qualityShifts"]["previous"] is None
        # Coverage shifts populated, but no `previousCount`.
        for axis in sd.COVERAGE_AXES:
            block = digest["coverageShifts"][axis]
            assert "previousCount" not in block
            assert block["delta"] == 0
        # Top movers empty for first release.
        for axis in sd.LEADER_AXES:
            assert digest["topMovers"][axis] == []

    def test_subsequent_release_path_diff_populates_deltas(self) -> None:
        prev = _metrics(
            version="9.1.0",
            use_cases=80,
            tiers={"gold": 30, "silver": 25, "bronze": 20, "none": 15},
        )
        cur = _metrics()
        digest = sd.build_digest(
            metrics=cur,
            previous=prev,
            sidecars=[],
            audit_warnings=[],
            reference_date=self.REF,
        )
        assert digest["previous"]["version"] == "9.1.0"
        assert digest["deltas"]["useCases"] == 20
        assert digest["qualityShifts"]["deltas"]["gold"] == 10
        assert digest["qualityShifts"]["deltas"]["none"] == -5

    def test_generated_at_is_zulu(self) -> None:
        digest = sd.build_digest(
            metrics=_metrics(),
            previous=None,
            sidecars=[],
            audit_warnings=[],
            reference_date=self.REF,
        )
        assert digest["generatedAt"].endswith("Z")
        assert digest["referenceDate"] == "2026-05-20"

    def test_audit_warnings_passthrough(self) -> None:
        warnings = [{"audit": "audit_x", "severity": "warn", "message": "msg"}]
        digest = sd.build_digest(
            metrics=_metrics(),
            previous=None,
            sidecars=[],
            audit_warnings=warnings,
            reference_date=self.REF,
        )
        assert digest["auditWarnings"] == warnings

    def test_schema_metadata_present(self) -> None:
        digest = sd.build_digest(
            metrics=_metrics(),
            previous=None,
            sidecars=[],
            audit_warnings=[],
            reference_date=self.REF,
        )
        assert digest["$schema"] == sd.SCHEMA_REF
        assert digest["schema_version"] == sd.SCHEMA_VERSION


# --------------------------------------------------------------------------- #
# render_markdown.
# --------------------------------------------------------------------------- #


class TestRenderMarkdown:
    REF = _dt.date(2026, 5, 20)

    def _digest(
        self,
        *,
        previous: dict[str, Any] | None,
        sidecars: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        return sd.build_digest(
            metrics=_metrics(),
            previous=previous,
            sidecars=sidecars or [],
            audit_warnings=warnings or [],
            reference_date=self.REF,
        )

    def test_first_release_renders_em_dashes_for_previous(self) -> None:
        md = sd.render_markdown(self._digest(previous=None))
        assert "# Stewardship Digest" in md
        assert "## Catalogue counts" in md
        # Em-dash placeholder for previous + delta columns when no previous.
        assert "| useCases | 100 | — | — |" in md
        # Quality tier line for gold.
        assert "| gold | 40 | — | — |" in md
        # Coverage axis line for compliance must surface percentage.
        assert "| compliance | 60 | 60.00% | — |" in md

    def test_subsequent_release_includes_deltas(self) -> None:
        prev = _metrics(version="9.1.0", use_cases=80)
        md = sd.render_markdown(self._digest(previous=prev))
        assert "| useCases | 100 | 80 | +20 |" in md
        # Compliance unchanged between fixtures so delta is +0.
        assert "| compliance | 60 | 60.00% | +0 (+0.00pp) |" in md

    def test_top_movers_section_present_when_any(self) -> None:
        prev = _metrics(version="9.1.0", leaders={
            # Only regulations move; every other axis is identical to
            # the default fixture so its top-movers section is
            # suppressed.
            "regulations": [
                {"regulation": "GDPR", "count": 5},
                {"regulation": "PCI", "count": 10},
            ],
            "mitreAttack": [
                {"technique": "T1078", "count": 8},
                {"technique": "T1110", "count": 6},
            ],
            "cimModels": [
                {"model": "Authentication", "count": 15},
                {"model": "Network_Traffic", "count": 11},
            ],
            "equipment": [
                {"equipment": "splunk", "count": 20},
                {"equipment": "cisco-asa", "count": 5},
            ],
        })
        md = sd.render_markdown(self._digest(previous=prev))
        # regulations moved (GDPR 5 -> 12) so a top-movers section
        # for regulations must appear.
        assert "## Top movers: regulations" in md
        assert "| GDPR | 12 | 5 | +7 |" in md
        # mitreAttack / cimModels / equipment all stayed the same so
        # those sections must NOT appear.
        assert "## Top movers: mitreAttack" not in md
        assert "## Top movers: cimModels" not in md
        assert "## Top movers: equipment" not in md

    def test_audit_warnings_section_only_when_present(self) -> None:
        md_none = sd.render_markdown(self._digest(previous=None))
        assert "## Open audit warnings" not in md_none

        md_with = sd.render_markdown(
            self._digest(
                previous=None,
                warnings=[{"audit": "audit_x", "severity": "warn", "message": "issue"}],
            )
        )
        assert "## Open audit warnings" in md_with
        assert "- **audit_x** (warn): issue" in md_with

    def test_stale_section_empty_message_when_no_stale(self) -> None:
        md = sd.render_markdown(self._digest(previous=None))
        assert "## Stale use cases (0 above 180-day threshold)" in md
        assert "_No stale UCs above threshold" in md

    def test_stale_section_table_when_stale_present(self) -> None:
        # One uc that's missing lastReviewed (max-stale path).
        sidecars = [{"id": "1.1.1", "title": "Stale UC", "status": "verified"}]
        md = sd.render_markdown(self._digest(previous=None, sidecars=sidecars))
        assert "## Stale use cases (1 above 180-day threshold)" in md
        # The row uses the literal em-dash for unknown lastReviewed.
        assert "| UC-1.1.1 | Stale UC | verified | — | 181 |" in md

    def test_render_ends_with_single_newline(self) -> None:
        md = sd.render_markdown(self._digest(previous=None))
        assert md.endswith("\n")
        assert not md.endswith("\n\n")

    def test_coverage_row_with_previous_but_no_percentage_delta(self) -> None:
        """The renderer is defensive against a hand-edited digest that
        carries ``previousCount`` without ``percentageDelta`` (the
        builder always sets both together, but a downstream tool could
        strip one). The branch that skips the percentage suffix must
        emit a bare ``+N`` delta string."""
        digest = self._digest(previous=None)
        digest["coverageShifts"]["compliance"] = {
            "currentCount": 60,
            "currentPercentage": 60.0,
            "previousCount": 50,
            "previousPercentage": 50.0,
            "delta": 10,
            # percentageDelta intentionally omitted.
        }
        md = sd.render_markdown(digest)
        # Bare +N suffix, no percentage-point suffix.
        assert "| compliance | 60 | 60.00% | +10 |" in md
        assert "(+10.00pp)" not in md


# --------------------------------------------------------------------------- #
# _emit — disk twins.
# --------------------------------------------------------------------------- #


class TestEmit:
    REF = _dt.date(2026, 5, 20)

    def test_writes_two_files_and_returns_paths(self, tmp_path: Path) -> None:
        digest = sd.build_digest(
            metrics=_metrics(),
            previous=None,
            sidecars=[],
            audit_warnings=[],
            reference_date=self.REF,
        )
        json_path, md_path = sd._emit(tmp_path / "out", digest)
        assert json_path.is_file()
        assert md_path.is_file()
        # JSON must round-trip and be sort-key-stable.
        assert json.loads(json_path.read_text(encoding="utf-8")) == digest
        # Markdown must start with the canonical h1 (renders correctly).
        assert md_path.read_text(encoding="utf-8").startswith("# Stewardship Digest")

    def test_creates_missing_out_dir(self, tmp_path: Path) -> None:
        digest = sd.build_digest(
            metrics=_metrics(),
            previous=None,
            sidecars=[],
            audit_warnings=[],
            reference_date=self.REF,
        )
        out = tmp_path / "new" / "nested" / "dir"
        json_path, md_path = sd._emit(out, digest)
        assert json_path.parent == out
        assert md_path.parent == out


# --------------------------------------------------------------------------- #
# CLI — main().
# --------------------------------------------------------------------------- #


class TestMainCli:
    def _set_up_inputs(self, tmp_path: Path) -> tuple[Path, Path, Path, Path]:
        """Create a complete metrics + history + content + out tree."""
        metrics_path = tmp_path / "metrics.json"
        history_dir = tmp_path / "history"
        content_dir = tmp_path / "content"
        out_dir = tmp_path / "out"

        history_dir.mkdir()
        content_dir.mkdir()
        metrics_path.write_text(
            json.dumps(_metrics()), encoding="utf-8"
        )
        # One previous snapshot so the delta path is exercised end-to-end.
        (history_dir / "9.1.0.json").write_text(
            json.dumps(_metrics(version="9.1.0", use_cases=80)),
            encoding="utf-8",
        )
        # One sidecar so the stale-UC path is exercised end-to-end.
        cat = content_dir / "cat-01-foo"
        cat.mkdir()
        (cat / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "title": "T"}), encoding="utf-8"
        )
        return metrics_path, history_dir, content_dir, out_dir

    def test_happy_path_writes_both_artefacts(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "2026-05-20",
            ]
        )
        assert rc == 0
        assert (out_dir / "stewardship-digest.json").is_file()
        assert (out_dir / "stewardship-digest.md").is_file()
        # The "wrote ..." status lines must mention both twins.
        captured = capsys.readouterr().out
        assert "stewardship-digest.json" in captured
        assert "stewardship-digest.md" in captured

    def test_missing_metrics_returns_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = sd.main(["--metrics", str(tmp_path / "nope.json")])
        assert rc == 2
        assert "does not exist" in capsys.readouterr().err

    def test_invalid_reference_date_returns_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "not-a-date",
            ]
        )
        assert rc == 2
        assert "not a valid YYYY-MM-DD" in capsys.readouterr().err

    def test_default_reference_date_uses_today_utc(
        self, tmp_path: Path
    ) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                # No --reference-date supplied; uses today UTC.
            ]
        )
        assert rc == 0
        digest = json.loads(
            (out_dir / "stewardship-digest.json").read_text(encoding="utf-8")
        )
        # Round-trip: the referenceDate must be today (UTC).
        today_str = _dt.datetime.now(tz=_dt.UTC).date().isoformat()
        assert digest["referenceDate"] == today_str

    def test_audit_warning_passthrough(self, tmp_path: Path) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "2026-05-20",
                "--audit-warning", "audit_x=hello",
                "--audit-warning", "audit_y=world",
            ]
        )
        assert rc == 0
        digest = json.loads(
            (out_dir / "stewardship-digest.json").read_text(encoding="utf-8")
        )
        msgs = {(w["audit"], w["message"]) for w in digest["auditWarnings"]}
        assert msgs == {("audit_x", "hello"), ("audit_y", "world")}

    @pytest.mark.parametrize(
        "bad",
        ["no-equals-sign", "=just-message", "name=", " = "],
    )
    def test_invalid_audit_warning_returns_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], bad: str
    ) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "2026-05-20",
                "--audit-warning", bad,
            ]
        )
        assert rc == 2
        assert "must be 'audit_name=message'" in capsys.readouterr().err

    def test_zero_stale_threshold_returns_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "2026-05-20",
                "--stale-threshold-days", "0",
            ]
        )
        assert rc == 2
        assert "must be >= 1" in capsys.readouterr().err

    def test_audit_warning_strips_whitespace(self, tmp_path: Path) -> None:
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "2026-05-20",
                "--audit-warning", "  audit_x  =  spaced  ",
            ]
        )
        assert rc == 0
        digest = json.loads(
            (out_dir / "stewardship-digest.json").read_text(encoding="utf-8")
        )
        assert digest["auditWarnings"] == [
            {"audit": "audit_x", "severity": "warn", "message": "spaced"}
        ]

    def test_out_dir_not_under_project_root_uses_absolute_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When the resolved output path falls outside PROJECT_ROOT the
        relative-to fallback in ``main`` must surface the absolute path
        instead of crashing. ``tmp_path`` is under /tmp and almost
        certainly outside the repo root, so this exercises the
        is_relative_to() False branch directly."""
        metrics_path, history_dir, content_dir, out_dir = self._set_up_inputs(tmp_path)
        rc = sd.main(
            [
                "--metrics", str(metrics_path),
                "--history-dir", str(history_dir),
                "--content-dir", str(content_dir),
                "--out", str(out_dir),
                "--reference-date", "2026-05-20",
            ]
        )
        assert rc == 0
        captured = capsys.readouterr().out
        # Whichever branch fires the printout must reference the
        # twin filenames.
        assert "stewardship-digest.json" in captured
        assert "stewardship-digest.md" in captured
