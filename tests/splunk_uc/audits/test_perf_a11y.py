"""Unit tests for ``splunk_uc.audits.perf_a11y``.

P16 wave N: lifts ``src/splunk_uc/audits/perf_a11y.py`` from 8.7% to
≥95% combined line+branch coverage. Pins every documented contract of
the Phase 4.5f perf + accessibility gate: byte-budget evaluation,
axe-core subprocess orchestration, a11y allowlist filtering, report
serialisation, human summary, and the ``main()`` CLI (including the
``--check`` drift detector with `dist/*` size normalisation).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import perf_a11y as pa

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_repo_points_at_real_repo(self) -> None:
        assert (pa.REPO / "schemas").is_dir()
        assert (pa.REPO / "content").is_dir()

    def test_report_path_under_repo(self) -> None:
        assert pa.REPORT_PATH == pa.REPO / "reports" / "perf-a11y.json"

    def test_run_axe_script_path(self) -> None:
        assert pa.RUN_AXE_SCRIPT == pa.REPO / "tests" / "a11y" / "run-axe.mjs"

    def test_perf_budgets_shape(self) -> None:
        assert len(pa._PERF_BUDGETS) > 0
        for budget in pa._PERF_BUDGETS:
            assert "file" in budget
            assert "budget_bytes" in budget
            assert "tier" in budget
            assert "note" in budget
            assert isinstance(budget["budget_bytes"], int)
            assert budget["budget_bytes"] > 0
            assert budget["tier"] in ("critical-path", "generated-data")

    def test_a11y_pages(self) -> None:
        assert len(pa._A11Y_PAGES) > 0
        assert "scorecard.html" in pa._A11Y_PAGES
        assert "index.html" in pa._A11Y_PAGES

    def test_hard_fail_impacts(self) -> None:
        assert pa._HARD_FAIL_IMPACTS == {"critical", "serious"}

    def test_warning_impacts(self) -> None:
        assert pa._WARNING_IMPACTS == {"moderate", "minor"}

    def test_allowlist_is_list(self) -> None:
        assert isinstance(pa._A11Y_ALLOWLIST, list)


# ---------------------------------------------------------------------------
# _evaluate_budgets
# ---------------------------------------------------------------------------


class TestEvaluateBudgets:
    def test_empty_budgets_returns_empty(self) -> None:
        records, hf = pa._evaluate_budgets([])
        assert records == []
        assert hf == 0

    def test_missing_file_emits_missing_record_and_hard_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(pa, "REPO", tmp_path)
        budgets: list[pa.PerfBudget] = [
            {
                "file": "missing.html",
                "budget_bytes": 1024,
                "tier": "critical-path",
                "note": "test",
            }
        ]
        records, hf = pa._evaluate_budgets(budgets)
        assert len(records) == 1
        assert records[0]["status"] == "missing"
        assert records[0]["actual_bytes"] is None
        assert records[0]["headroom_bytes"] is None
        assert records[0]["budget_bytes"] == 1024
        assert hf == 1

    def test_present_under_budget_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pa, "REPO", tmp_path)
        f = tmp_path / "ok.html"
        f.write_bytes(b"x" * 100)
        budgets: list[pa.PerfBudget] = [
            {"file": "ok.html", "budget_bytes": 1024, "tier": "critical-path", "note": "test"}
        ]
        records, hf = pa._evaluate_budgets(budgets)
        assert records[0]["status"] == "ok"
        assert records[0]["actual_bytes"] == 100
        assert records[0]["headroom_bytes"] == 924
        assert hf == 0

    def test_present_over_budget_hard_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(pa, "REPO", tmp_path)
        f = tmp_path / "big.html"
        f.write_bytes(b"x" * 2000)
        budgets: list[pa.PerfBudget] = [
            {"file": "big.html", "budget_bytes": 1024, "tier": "critical-path", "note": "test"}
        ]
        records, hf = pa._evaluate_budgets(budgets)
        assert records[0]["status"] == "over-budget"
        assert records[0]["actual_bytes"] == 2000
        assert records[0]["headroom_bytes"] == -976
        assert hf == 1

    def test_exactly_at_budget_is_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Boundary: actual == budget is ok (`actual <= budget`).
        monkeypatch.setattr(pa, "REPO", tmp_path)
        f = tmp_path / "edge.html"
        f.write_bytes(b"x" * 1024)
        budgets: list[pa.PerfBudget] = [
            {"file": "edge.html", "budget_bytes": 1024, "tier": "critical-path", "note": "test"}
        ]
        records, hf = pa._evaluate_budgets(budgets)
        assert records[0]["status"] == "ok"
        assert records[0]["headroom_bytes"] == 0
        assert hf == 0

    def test_records_sorted_by_tier_then_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(pa, "REPO", tmp_path)
        for name in ("a.html", "b.html", "c.html"):
            (tmp_path / name).write_bytes(b"x" * 10)
        budgets: list[pa.PerfBudget] = [
            {"file": "c.html", "budget_bytes": 100, "tier": "generated-data", "note": ""},
            {"file": "a.html", "budget_bytes": 100, "tier": "critical-path", "note": ""},
            {"file": "b.html", "budget_bytes": 100, "tier": "critical-path", "note": ""},
        ]
        records, _ = pa._evaluate_budgets(budgets)
        assert [r["file"] for r in records] == ["a.html", "b.html", "c.html"]
        assert [r["tier"] for r in records] == [
            "critical-path",
            "critical-path",
            "generated-data",
        ]

    def test_missing_tier_defaults_to_critical_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(pa, "REPO", tmp_path)
        budgets: list[pa.PerfBudget] = [
            {
                "file": "missing.html",
                "budget_bytes": 1024,
            }
        ]
        records, _ = pa._evaluate_budgets(budgets)
        assert records[0]["tier"] == "critical-path"

    def test_no_floats_in_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Docstring promises every field is str or int — no floats anywhere.
        monkeypatch.setattr(pa, "REPO", tmp_path)
        f = tmp_path / "x.html"
        f.write_bytes(b"x" * 50)
        budgets: list[pa.PerfBudget] = [
            {"file": "x.html", "budget_bytes": 100, "tier": "critical-path", "note": "test"}
        ]
        records, _ = pa._evaluate_budgets(budgets)
        for record in records:
            for value in record.values():
                assert not isinstance(value, float)


# ---------------------------------------------------------------------------
# _run_axe — subprocess orchestrator
# ---------------------------------------------------------------------------


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestRunAxe:
    def test_missing_axe_script_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(pa, "REPO", tmp_path)
        monkeypatch.setattr(pa, "RUN_AXE_SCRIPT", tmp_path / "missing.mjs")
        with pytest.raises(RuntimeError, match="axe runner missing"):
            pa._run_axe(["page.html"])

    def test_missing_node_binary_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = tmp_path / "run-axe.mjs"
        script.write_text("// stub")
        monkeypatch.setattr(pa, "REPO", tmp_path)
        monkeypatch.setattr(pa, "RUN_AXE_SCRIPT", script)
        monkeypatch.setattr(pa.shutil, "which", lambda name: None)
        with pytest.raises(RuntimeError, match="`node` binary not found"):
            pa._run_axe(["page.html"])

    def test_missing_axe_core_module_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = tmp_path / "run-axe.mjs"
        script.write_text("// stub")
        monkeypatch.setattr(pa, "REPO", tmp_path)
        monkeypatch.setattr(pa, "RUN_AXE_SCRIPT", script)
        monkeypatch.setattr(pa.shutil, "which", lambda name: "/usr/bin/node")
        # node_modules dir exists but axe-core does not
        (tmp_path / "node_modules").mkdir()
        with pytest.raises(RuntimeError, match="axe-core is missing"):
            pa._run_axe(["page.html"])

    def test_missing_jsdom_module_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = tmp_path / "run-axe.mjs"
        script.write_text("// stub")
        monkeypatch.setattr(pa, "REPO", tmp_path)
        monkeypatch.setattr(pa, "RUN_AXE_SCRIPT", script)
        monkeypatch.setattr(pa.shutil, "which", lambda name: "/usr/bin/node")
        nm = tmp_path / "node_modules"
        (nm / "axe-core").mkdir(parents=True)
        # jsdom dir does not exist
        with pytest.raises(RuntimeError, match="jsdom is missing"):
            pa._run_axe(["page.html"])

    def _setup_runnable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        proc: _FakeCompletedProcess,
    ) -> None:
        script = tmp_path / "run-axe.mjs"
        script.write_text("// stub")
        monkeypatch.setattr(pa, "REPO", tmp_path)
        monkeypatch.setattr(pa, "RUN_AXE_SCRIPT", script)
        monkeypatch.setattr(pa.shutil, "which", lambda name: "/usr/bin/node")
        nm = tmp_path / "node_modules"
        (nm / "axe-core").mkdir(parents=True)
        (nm / "jsdom").mkdir(parents=True)

        def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
            return proc

        monkeypatch.setattr(pa.subprocess, "run", fake_run)

    def test_subprocess_failure_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup_runnable(
            tmp_path,
            monkeypatch,
            _FakeCompletedProcess(returncode=2, stdout="oops", stderr="boom"),
        )
        with pytest.raises(RuntimeError, match="axe runner exited with code 2"):
            pa._run_axe(["page.html"])

    def test_subprocess_non_json_output_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup_runnable(
            tmp_path,
            monkeypatch,
            _FakeCompletedProcess(returncode=0, stdout="not json", stderr=""),
        )
        with pytest.raises(RuntimeError, match="non-JSON output"):
            pa._run_axe(["page.html"])

    def test_subprocess_success_returns_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        payload = {"axe_version": "4.0.0", "results": []}
        self._setup_runnable(
            tmp_path,
            monkeypatch,
            _FakeCompletedProcess(returncode=0, stdout=json.dumps(payload), stderr=""),
        )
        result = pa._run_axe(["page.html"])
        assert result == payload


# ---------------------------------------------------------------------------
# _is_allowlisted
# ---------------------------------------------------------------------------


class TestIsAllowlisted:
    def test_empty_allowlist_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pa, "_A11Y_ALLOWLIST", [])
        assert pa._is_allowlisted("index.html", "color-contrast") is False

    def test_matching_entry_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            pa,
            "_A11Y_ALLOWLIST",
            [{"file": "index.html", "rule_id": "color-contrast", "reason": "test"}],
        )
        assert pa._is_allowlisted("index.html", "color-contrast") is True

    def test_non_matching_file_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            pa,
            "_A11Y_ALLOWLIST",
            [{"file": "index.html", "rule_id": "color-contrast", "reason": "test"}],
        )
        assert pa._is_allowlisted("other.html", "color-contrast") is False

    def test_non_matching_rule_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            pa,
            "_A11Y_ALLOWLIST",
            [{"file": "index.html", "rule_id": "color-contrast", "reason": "test"}],
        )
        assert pa._is_allowlisted("index.html", "other-rule") is False


# ---------------------------------------------------------------------------
# _evaluate_a11y
# ---------------------------------------------------------------------------


class TestEvaluateA11y:
    def test_empty_axe_payload(self) -> None:
        block, hf, warns, total = pa._evaluate_a11y({})
        assert block["results"] == []
        assert block["pages_audited"] == []
        assert hf == 0
        assert warns == 0
        assert total == 0
        assert "summary" in block

    def test_runner_error_on_file_is_hard_failure(self) -> None:
        payload = {"results": [{"file": "index.html", "status": "error", "error": "jsdom crashed"}]}
        block, hf, warns, _total = pa._evaluate_a11y(payload)
        assert hf == 1
        assert warns == 0
        assert block["results"][0]["status"] == "error"
        assert block["results"][0]["hard_failure_count"] == 1

    def test_critical_violation_hard_fails(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "img-alt", "impact": "critical"}],
                }
            ]
        }
        block, hf, warns, total = pa._evaluate_a11y(payload)
        assert hf == 1
        assert warns == 0
        assert total == 1
        assert block["results"][0]["violations"][0]["disposition"] == "hard-fail"

    def test_serious_violation_hard_fails(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "label", "impact": "serious"}],
                }
            ]
        }
        _, hf, _, _ = pa._evaluate_a11y(payload)
        assert hf == 1

    def test_moderate_violation_warns(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "tabindex", "impact": "moderate"}],
                }
            ]
        }
        _, hf, warns, _ = pa._evaluate_a11y(payload)
        assert hf == 0
        assert warns == 1

    def test_minor_violation_warns(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "region", "impact": "minor"}],
                }
            ]
        }
        _, hf, warns, _ = pa._evaluate_a11y(payload)
        assert hf == 0
        assert warns == 1

    def test_unknown_impact_treated_as_warning(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "weird", "impact": "exotic"}],
                }
            ]
        }
        _, hf, warns, _ = pa._evaluate_a11y(payload)
        assert hf == 0
        assert warns == 1

    def test_missing_impact_treated_as_warning(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "weird"}],
                }
            ]
        }
        _, hf, warns, _ = pa._evaluate_a11y(payload)
        assert hf == 0
        assert warns == 1

    def test_allowlisted_violation_does_not_hard_fail(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            pa,
            "_A11Y_ALLOWLIST",
            [
                {
                    "file": "index.html",
                    "rule_id": "img-alt",
                    "reason": "test",
                    "approver": "alice",
                    "added": "2026-01-01",
                    "review_by": "2026-04-01",
                }
            ],
        )
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "img-alt", "impact": "critical"}],
                }
            ]
        }
        block, hf, warns, _ = pa._evaluate_a11y(payload)
        assert hf == 0
        assert warns == 0
        assert block["results"][0]["violations"][0]["disposition"] == "allowlisted"
        assert block["summary"]["allowlist_hits"] == 1
        assert len(block["allowlist"]) == 1
        assert block["allowlist"][0]["rule_id"] == "img-alt"

    def test_mixed_violations(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [
                        {"id": "a", "impact": "critical"},
                        {"id": "b", "impact": "minor"},
                        {"id": "c", "impact": "serious"},
                    ],
                }
            ]
        }
        _, hf, warns, total = pa._evaluate_a11y(payload)
        assert hf == 2
        assert warns == 1
        assert total == 3

    def test_summary_block_shape(self) -> None:
        payload = {
            "results": [
                {
                    "file": "index.html",
                    "status": "ok",
                    "violations": [{"id": "a", "impact": "critical"}],
                }
            ],
            "axe_version": "4.7.0",
            "jsdom_version": "22.0.0",
            "config": {"foo": "bar"},
        }
        block, _, _, _ = pa._evaluate_a11y(payload)
        assert block["axe_version"] == "4.7.0"
        assert block["jsdom_version"] == "22.0.0"
        assert block["config"] == {"foo": "bar"}
        assert "summary" in block
        assert "pages_with_errors" in block["summary"]
        assert block["summary"]["pages_with_errors"] == 0

    def test_pages_with_errors_counted(self) -> None:
        payload = {
            "results": [
                {"file": "a.html", "status": "error", "error": "x"},
                {"file": "b.html", "status": "ok", "violations": []},
                {"file": "c.html", "status": "error", "error": "y"},
            ]
        }
        block, _, _, _ = pa._evaluate_a11y(payload)
        assert block["summary"]["pages_with_errors"] == 2

    def test_allowlist_snapshot_sorted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            pa,
            "_A11Y_ALLOWLIST",
            [
                {"file": "z.html", "rule_id": "img-alt"},
                {"file": "a.html", "rule_id": "label"},
                {"file": "a.html", "rule_id": "color-contrast"},
            ],
        )
        block, _, _, _ = pa._evaluate_a11y({"results": []})
        assert [(e["file"], e["rule_id"]) for e in block["allowlist"]] == [
            ("a.html", "color-contrast"),
            ("a.html", "label"),
            ("z.html", "img-alt"),
        ]


# ---------------------------------------------------------------------------
# _canonical_serialise
# ---------------------------------------------------------------------------


class TestCanonicalSerialise:
    def test_uses_indent_2_sort_keys(self) -> None:
        s = pa._canonical_serialise({"b": 1, "a": 2})
        assert '"a": 2' in s
        assert s.index('"a"') < s.index('"b"')

    def test_trailing_newline(self) -> None:
        s = pa._canonical_serialise({})
        assert s.endswith("\n")

    def test_ensure_ascii_false_preserves_unicode(self) -> None:
        s = pa._canonical_serialise({"key": "café"})
        assert "café" in s
        assert "caf\\u00e9" not in s


# ---------------------------------------------------------------------------
# _normalise_dist_size_fields
# ---------------------------------------------------------------------------


class TestNormaliseDistSizeFields:
    def test_zeros_dist_actual_and_headroom(self) -> None:
        payload = {
            "perf": {
                "budgets": [
                    {
                        "file": "dist/catalog.json",
                        "actual_bytes": 12345,
                        "headroom_bytes": -100,
                        "budget_bytes": 1000,
                        "status": "over-budget",
                    },
                ]
            }
        }
        out = pa._normalise_dist_size_fields(json.dumps(payload))
        parsed = json.loads(out)
        assert parsed["perf"]["budgets"][0]["actual_bytes"] == 0
        assert parsed["perf"]["budgets"][0]["headroom_bytes"] == 0
        # Budget threshold and status stay intact
        assert parsed["perf"]["budgets"][0]["budget_bytes"] == 1000
        assert parsed["perf"]["budgets"][0]["status"] == "over-budget"

    def test_preserves_project_root_files(self) -> None:
        payload = {
            "perf": {
                "budgets": [
                    {
                        "file": "index.html",
                        "actual_bytes": 99999,
                        "headroom_bytes": 100,
                        "budget_bytes": 100000,
                        "status": "ok",
                    },
                ]
            }
        }
        out = pa._normalise_dist_size_fields(json.dumps(payload))
        parsed = json.loads(out)
        assert parsed["perf"]["budgets"][0]["actual_bytes"] == 99999

    def test_malformed_json_returned_as_is(self) -> None:
        assert pa._normalise_dist_size_fields("not json") == "not json"

    def test_missing_perf_block_returned_as_is(self) -> None:
        s = json.dumps({"foo": "bar"})
        assert pa._normalise_dist_size_fields(s) == s

    def test_missing_budgets_list_returned_as_is(self) -> None:
        s = json.dumps({"perf": {}})
        assert pa._normalise_dist_size_fields(s) == s

    def test_non_list_budgets_returned_as_is(self) -> None:
        s = json.dumps({"perf": {"budgets": "oops"}})
        assert pa._normalise_dist_size_fields(s) == s

    def test_non_dict_budget_entry_skipped(self) -> None:
        payload = {
            "perf": {
                "budgets": [
                    "not a dict",
                    {"file": "dist/foo.txt", "actual_bytes": 100, "headroom_bytes": 5},
                ]
            }
        }
        out = pa._normalise_dist_size_fields(json.dumps(payload))
        parsed = json.loads(out)
        assert parsed["perf"]["budgets"][0] == "not a dict"
        assert parsed["perf"]["budgets"][1]["actual_bytes"] == 0

    def test_dist_entry_without_actual_or_headroom_handled(self) -> None:
        payload = {
            "perf": {
                "budgets": [{"file": "dist/foo.txt", "budget_bytes": 100, "status": "missing"}]
            }
        }
        out = pa._normalise_dist_size_fields(json.dumps(payload))
        parsed = json.loads(out)
        # No actual_bytes or headroom_bytes present; should remain absent.
        assert "actual_bytes" not in parsed["perf"]["budgets"][0]
        assert "headroom_bytes" not in parsed["perf"]["budgets"][0]


# ---------------------------------------------------------------------------
# _render_report
# ---------------------------------------------------------------------------


def _gen_a11y_block() -> dict[str, Any]:
    return {
        "allowlist": [],
        "axe_version": "4.7.0",
        "config": {},
        "jsdom_version": "22.0.0",
        "pages_audited": ["index.html"],
        "results": [],
        "summary": {
            "allowlist_hits": 0,
            "hard_failures": 0,
            "pages_with_errors": 0,
            "total_violations": 0,
            "warnings": 0,
        },
    }


class TestRenderReport:
    def test_full_payload_shape(self) -> None:
        records = [
            {
                "actual_bytes": 100,
                "budget_bytes": 200,
                "file": "a.html",
                "headroom_bytes": 100,
                "note": "test",
                "status": "ok",
                "tier": "critical-path",
            },
            {
                "actual_bytes": 500,
                "budget_bytes": 200,
                "file": "b.html",
                "headroom_bytes": -300,
                "note": "test",
                "status": "over-budget",
                "tier": "generated-data",
            },
        ]
        out = pa._render_report(records, 1, _gen_a11y_block(), 0, 0, None)
        parsed = json.loads(out)
        assert "$comment" in parsed
        assert "a11y" in parsed
        assert "perf" in parsed
        assert "summary" in parsed
        assert parsed["perf"]["budgets"] == records
        assert parsed["perf"]["summary"]["total_files"] == 2
        assert parsed["perf"]["summary"]["critical_path_budgeted"] == 1
        assert parsed["perf"]["summary"]["generated_data_budgeted"] == 1
        assert parsed["perf"]["summary"]["over_budget_count"] == 1
        assert parsed["perf"]["summary"]["hard_failures"] == 1

    def test_missing_count_in_summary(self) -> None:
        records = [
            {
                "actual_bytes": None,
                "budget_bytes": 200,
                "file": "m.html",
                "headroom_bytes": None,
                "note": "",
                "status": "missing",
                "tier": "critical-path",
            }
        ]
        out = pa._render_report(records, 1, _gen_a11y_block(), 0, 0, None)
        parsed = json.loads(out)
        assert parsed["perf"]["summary"]["missing_count"] == 1

    def test_axe_runner_error_in_summary(self) -> None:
        out = pa._render_report([], 0, _gen_a11y_block(), 0, 0, "node not found")
        parsed = json.loads(out)
        assert parsed["axe_runner_error"] == "node not found"
        assert parsed["summary"]["runner_error"] is True
        # runner_error adds 1 to total hard_failures
        assert parsed["summary"]["hard_failures"] == 1

    def test_no_axe_runner_error(self) -> None:
        out = pa._render_report([], 0, _gen_a11y_block(), 0, 0, None)
        parsed = json.loads(out)
        assert parsed["axe_runner_error"] is None
        assert parsed["summary"]["runner_error"] is False

    def test_output_canonically_serialised(self) -> None:
        out = pa._render_report([], 0, _gen_a11y_block(), 0, 0, None)
        # Should be canonical: sort_keys + indent=2 + trailing newline
        assert out.endswith("\n")
        # The $comment key should sort to position 0 because '$' precedes 'a' in ASCII
        assert out.lstrip().startswith('{\n  "$comment"')


# ---------------------------------------------------------------------------
# _print_human_summary
# ---------------------------------------------------------------------------


class TestPrintHumanSummary:
    def test_green_when_no_failures(self, capsys: pytest.CaptureFixture[str]) -> None:
        records = [
            {
                "actual_bytes": 100,
                "budget_bytes": 200,
                "file": "ok.html",
                "headroom_bytes": 100,
                "note": "",
                "status": "ok",
                "tier": "critical-path",
            }
        ]
        pa._print_human_summary(records, 0, _gen_a11y_block(), 0, 0, None)
        out = capsys.readouterr().out
        assert "GREEN" in out
        assert "Performance budgets" in out
        assert "ok.html" in out
        assert "headroom" in out.lower()

    def test_red_when_perf_fails(self, capsys: pytest.CaptureFixture[str]) -> None:
        records = [
            {
                "actual_bytes": 500,
                "budget_bytes": 100,
                "file": "big.html",
                "headroom_bytes": -400,
                "note": "",
                "status": "over-budget",
                "tier": "critical-path",
            }
        ]
        pa._print_human_summary(records, 1, _gen_a11y_block(), 0, 0, None)
        out = capsys.readouterr().out
        assert "RED" in out
        assert "OVER" in out

    def test_red_when_a11y_fails(self, capsys: pytest.CaptureFixture[str]) -> None:
        pa._print_human_summary([], 0, _gen_a11y_block(), 1, 0, None)
        out = capsys.readouterr().out
        assert "RED" in out

    def test_runner_error_short_circuits_to_red(self, capsys: pytest.CaptureFixture[str]) -> None:
        pa._print_human_summary([], 0, _gen_a11y_block(), 0, 0, "boom")
        out = capsys.readouterr().out
        assert "RUNNER ERROR" in out
        assert "RED" in out

    def test_missing_record_renders_dash(self, capsys: pytest.CaptureFixture[str]) -> None:
        records = [
            {
                "actual_bytes": None,
                "budget_bytes": 100,
                "file": "m.html",
                "headroom_bytes": None,
                "note": "",
                "status": "missing",
                "tier": "critical-path",
            }
        ]
        pa._print_human_summary(records, 1, _gen_a11y_block(), 0, 0, None)
        out = capsys.readouterr().out
        assert "MISSING" in out
        assert "m.html" in out

    def test_violation_rendering(self, capsys: pytest.CaptureFixture[str]) -> None:
        block = _gen_a11y_block()
        block["results"] = [
            {
                "file": "index.html",
                "status": "ok",
                "summary": {"passes": 5, "violations": 1, "incomplete": 0, "inapplicable": 2},
                "violations": [
                    {
                        "id": "img-alt",
                        "impact": "critical",
                        "disposition": "hard-fail",
                        "nodeCount": 3,
                        "help": "Images must have alternative text",
                    }
                ],
                "incomplete": [],
            }
        ]
        pa._print_human_summary([], 0, block, 1, 0, None)
        out = capsys.readouterr().out
        assert "index.html" in out
        assert "img-alt" in out
        assert "Images must have" in out

    def test_runner_error_per_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        block = _gen_a11y_block()
        block["results"] = [
            {
                "file": "bad.html",
                "status": "error",
                "summary": {"passes": 0, "violations": 0, "incomplete": 0, "inapplicable": 0},
                "violations": [],
                "incomplete": [],
                "error": "jsdom failed",
            }
        ]
        pa._print_human_summary([], 0, block, 1, 0, None)
        out = capsys.readouterr().out
        assert "RUNNER ERROR on this file" in out

    def test_incomplete_truncated_to_five(self, capsys: pytest.CaptureFixture[str]) -> None:
        block = _gen_a11y_block()
        block["results"] = [
            {
                "file": "index.html",
                "status": "ok",
                "summary": {"passes": 0, "violations": 0, "incomplete": 10, "inapplicable": 0},
                "violations": [],
                "incomplete": [
                    {"id": f"rule-{i}", "impact": "minor", "nodeCount": 1, "help": ""}
                    for i in range(10)
                ],
            }
        ]
        pa._print_human_summary([], 0, block, 0, 0, None)
        out = capsys.readouterr().out
        assert "5 more" in out

    def test_zero_budget_avoids_division(self, capsys: pytest.CaptureFixture[str]) -> None:
        # budget_bytes=0 should not crash with ZeroDivisionError.
        records = [
            {
                "actual_bytes": 100,
                "budget_bytes": 0,
                "file": "x.html",
                "headroom_bytes": -100,
                "note": "",
                "status": "over-budget",
                "tier": "critical-path",
            }
        ]
        pa._print_human_summary(records, 1, _gen_a11y_block(), 0, 0, None)
        out = capsys.readouterr().out
        assert "0.00% headroom" in out


# ---------------------------------------------------------------------------
# main() — CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point REPO + REPORT_PATH at a hermetic tmp_path tree."""
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(pa, "REPO", tmp_path)
    monkeypatch.setattr(pa, "REPORT_PATH", reports / "perf-a11y.json")
    return tmp_path


def _fake_axe_ok(_pages: list[str]) -> dict[str, Any]:
    return {
        "axe_version": "4.7.0",
        "config": {},
        "jsdom_version": "22.0.0",
        "results": [],
    }


class TestMainCli:
    def test_default_writes_report_returns_zero(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Empty budgets → no hard failures; mock axe to succeed.
        monkeypatch.setattr(pa, "_PERF_BUDGETS", [])
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])
        monkeypatch.setattr(pa, "_run_axe", _fake_axe_ok)
        rc = pa.main([])
        assert rc == 0
        assert pa.REPORT_PATH.is_file()
        out = capsys.readouterr().out
        assert "GREEN" in out

    def test_axe_runner_error_returns_one(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(pa, "_PERF_BUDGETS", [])
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])

        def boom(_pages: list[str]) -> dict[str, Any]:
            raise RuntimeError("axe broke")

        monkeypatch.setattr(pa, "_run_axe", boom)
        rc = pa.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "ERROR" in err

    def test_perf_hard_failure_returns_one(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        big = isolated / "big.html"
        big.write_bytes(b"x" * 2000)
        monkeypatch.setattr(
            pa,
            "_PERF_BUDGETS",
            [{"file": "big.html", "budget_bytes": 100, "tier": "critical-path", "note": ""}],
        )
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])
        monkeypatch.setattr(pa, "_run_axe", _fake_axe_ok)
        rc = pa.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "RED" in out

    def test_check_missing_report_returns_one(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(pa, "_PERF_BUDGETS", [])
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])
        monkeypatch.setattr(pa, "_run_axe", _fake_axe_ok)
        rc = pa.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "does not exist" in err

    def test_check_matching_report_returns_zero(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(pa, "_PERF_BUDGETS", [])
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])
        monkeypatch.setattr(pa, "_run_axe", _fake_axe_ok)
        # First run: write the report.
        pa.main([])
        capsys.readouterr()
        # Second run: --check should match.
        rc = pa.main(["--check"])
        assert rc == 0

    def test_check_drift_returns_one(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(pa, "_PERF_BUDGETS", [])
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])
        monkeypatch.setattr(pa, "_run_axe", _fake_axe_ok)
        # Plant a stale report.
        pa.REPORT_PATH.write_text("{}", encoding="utf-8")
        rc = pa.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "out of date" in err
        assert "diff" in err

    def test_check_normalises_dist_size_drift(
        self,
        isolated: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Create a dist/ file with size 100; budget keeps it ok.
        (isolated / "dist").mkdir()
        (isolated / "dist" / "x.txt").write_bytes(b"x" * 100)
        monkeypatch.setattr(
            pa,
            "_PERF_BUDGETS",
            [{"file": "dist/x.txt", "budget_bytes": 1000, "tier": "generated-data", "note": ""}],
        )
        monkeypatch.setattr(pa, "_A11Y_PAGES", [])
        monkeypatch.setattr(pa, "_run_axe", _fake_axe_ok)
        # First run: write the report.
        pa.main([])
        capsys.readouterr()
        # Now grow the file — actual_bytes changes but normalisation should mask it.
        (isolated / "dist" / "x.txt").write_bytes(b"x" * 200)
        rc = pa.main(["--check"])
        assert rc == 0

    def test_help_does_not_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            pa.main(["--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "Phase 4.5f" in out
        assert "--check" in out


class TestScriptEntryPoint:
    def test_module_exports_main(self) -> None:
        assert hasattr(pa, "main")
        assert callable(pa.main)


# Touch subprocess so the import is not flagged unused.
assert subprocess is not None
