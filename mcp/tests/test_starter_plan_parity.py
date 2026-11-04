"""JS/Python parity for the starter-plan planner.

``tests/fixtures/starter-plan-parity.json`` holds expectations recorded
from ``src/scripts/07-starter-plan.js``. The Python mirror in
:mod:`splunk_uc_mcp.starter_plan` must reproduce them exactly. When node
is available the JS side is re-checked too, so a change to either
implementation without the other fails here.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from splunk_uc_mcp.starter_plan import parse_paste, plan_rollout

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "starter-plan-parity.json"
_JS_CHECK = _REPO_ROOT / "tools" / "audits" / "starter_plan_parity.js"

_OPT_NAMES = {"includeDrafts": "include_drafts", "maxSteps": "max_steps"}


def _fixture() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return data


def _kwargs(opts: dict[str, Any]) -> dict[str, Any]:
    return {_OPT_NAMES.get(k, k): v for k, v in opts.items()}


@pytest.mark.parametrize("case", _fixture()["planCases"], ids=lambda c: c["name"])
def test_plan_case_matches_js(case: dict[str, Any]) -> None:
    got = plan_rollout(_fixture()["index"], **_kwargs(case["opts"]))
    assert got == case["expected"]


@pytest.mark.parametrize("case", _fixture()["pasteCases"], ids=lambda c: c["name"])
def test_paste_case_matches_js(case: dict[str, Any]) -> None:
    assert parse_paste(case["text"]) == case["expected"]


def test_fixture_covers_key_paths() -> None:
    cases = _fixture()["planCases"]
    reasons = {c["expected"]["emptyReason"] for c in cases}
    assert {None, "no-input", "no-match"} <= reasons
    assert any(c["opts"].get("includeDrafts") for c in cases)
    assert any(any(s["difficultyWarning"] for s in c["expected"]["steps"]) for c in cases)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_planner_matches_fixture() -> None:
    proc = subprocess.run(
        ["node", str(_JS_CHECK)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
