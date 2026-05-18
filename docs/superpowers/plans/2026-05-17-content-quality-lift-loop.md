# Content-Quality Lift Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship four deterministic CLI primitives (`lift-score`, `lift-prompt`, `lift-validate`, `lift-batch`) that, together with an agent-driven orchestration loop, lift the cat-15 composite from Bronze 67.0 to Silver ≥ 75 without touching SPL, compliance, or identity fields.

**Architecture:** Four pure-Python verbs under `src/splunk_uc/tools/lift/`, each with a unit-test suite that runs without Cursor or any AI in the loop. The AI authoring step lives in the orchestration agent layer (Cursor session, `Task` subagent per UC). A strict §5 validation contract enforced by `lift-validate` is the firewall — every committed diff is by construction CI-green.

**Tech Stack:** Python 3.11+ stdlib; `jsonschema` (already in deps); existing `audit-*` verbs invoked as subprocesses; pytest for tests; existing `_registry.py` plug-in pattern.

**Spec:** [`docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`](../specs/2026-05-17-content-quality-lift-loop-design.md). Sections referenced below as "spec §N".

**Worktree:** None — staying on `main` per established project convention (PR-1, PR-2, PR-3 all landed directly on main).

---

## File structure

### Files to create

| Path | Responsibility |
| --- | --- |
| `src/splunk_uc/tools/lift/__init__.py` | empty package marker |
| `src/splunk_uc/tools/lift/_common.py` | shared helpers: sidecar I/O, gap-report dataclass, rubric loader, target-tier resolver |
| `src/splunk_uc/tools/lift/score.py` | `lift-score` verb |
| `src/splunk_uc/tools/lift/prompt.py` | `lift-prompt` verb |
| `src/splunk_uc/tools/lift/validate.py` | `lift-validate` verb (the §5 validation chain) |
| `src/splunk_uc/tools/lift/batch.py` | `lift-batch` verb (work-list generator) |
| `tests/splunk_uc/lift/__init__.py` | empty marker |
| `tests/splunk_uc/lift/test_common.py` | unit tests for `_common.py` |
| `tests/splunk_uc/lift/test_score.py` | unit tests for `lift-score` |
| `tests/splunk_uc/lift/test_prompt.py` | unit tests for `lift-prompt` |
| `tests/splunk_uc/lift/test_validate.py` | unit tests for `lift-validate` |
| `tests/splunk_uc/lift/test_batch.py` | unit tests for `lift-batch` |
| `tests/splunk_uc/lift/fixtures/UC-15-silver-target.json` | minimal exemplar of a Silver-quality UC (for diff-validation tests) |
| `tests/splunk_uc/lift/fixtures/UC-15-bronze-baseline.json` | matching exemplar of a Bronze UC needing lift |

### Files to modify

| Path | Change |
| --- | --- |
| `src/splunk_uc/_registry.py` | register 4 new verbs in a new `lift` category |
| `AGENTS.md` | add the four verbs to "Quick commands" + document the orchestration loop |
| `CHANGELOG.md` | "Added" entry for the lift loop + cat-15 PoC numbers |
| `docs/health-check-2026-progress.md` | drift-ledger entry |
| `docs/scorecard.md` | regenerated (auto) |
| `dist/scorecard.json` | regenerated (auto) |
| `content/cat-15-data-center-physical-infrastructure/UC-15.*.json` | 30 lifted UCs (one commit per UC during the PoC phase) |

---

## Task 1: Shared helpers — `_common.py` + dataclasses

**Files:**
- Create: `src/splunk_uc/tools/lift/__init__.py` (empty)
- Create: `src/splunk_uc/tools/lift/_common.py`
- Create: `tests/splunk_uc/lift/__init__.py` (empty)
- Create: `tests/splunk_uc/lift/test_common.py`

### Step 1: Write the failing tests for `_common.py`

Create `tests/splunk_uc/lift/test_common.py`:

```python
"""Tests for src/splunk_uc/tools/lift/_common.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift._common import (  # noqa: E402
    GapReport,
    TargetTier,
    load_sidecar,
    resolve_sidecar_path,
    score_uc,
)


def test_target_tier_parses_known_values():
    assert TargetTier.from_str("silver") is TargetTier.SILVER
    assert TargetTier.from_str("gold") is TargetTier.GOLD
    assert TargetTier.from_str("gold-v2") is TargetTier.GOLD_V2


def test_target_tier_rejects_unknown():
    import pytest
    with pytest.raises(ValueError, match="unknown tier"):
        TargetTier.from_str("platinum")


def test_resolve_sidecar_path_finds_existing_uc(tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-15.1.1.json"
    sidecar.write_text(json.dumps({"id": "15.1.1", "title": "x"}))
    assert resolve_sidecar_path("UC-15.1.1", content_root=tmp_path / "content") == sidecar


def test_resolve_sidecar_path_raises_for_unknown_uc(tmp_path: Path):
    import pytest
    (tmp_path / "content").mkdir()
    with pytest.raises(FileNotFoundError, match="UC-15.1.1"):
        resolve_sidecar_path("UC-15.1.1", content_root=tmp_path / "content")


def test_load_sidecar_returns_parsed_json(tmp_path: Path):
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_text(json.dumps({"id": "15.1.1", "title": "test"}))
    assert load_sidecar(sidecar) == {"id": "15.1.1", "title": "test"}


def test_score_uc_returns_gap_report_for_short_fields(tmp_path: Path):
    sidecar_data = {
        "id": "15.1.1",
        "title": "Stub",
        "description": "too short",  # under 80 chars
        "value": "also too short",   # under 80 chars
        "dataSources": "tiny",        # under 80 chars
        "detailedImplementation": "x" * 100,  # under 500 chars
        "knownFalsePositives": [],
        "references": [],
        "controlTest": {"positiveScenario": "a", "negativeScenario": "a"},
        "evidence": "",
        "exclusions": "",
        "splunkPillar": "platform",
        "spl": "search index=main",
        "monitoringType": "trend",
        "criticality": 50,
        "difficulty": "medium",
        "app": "splunk_app",
        "implementation": "stub",
    }
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_text(json.dumps(sidecar_data))
    report = score_uc(sidecar, target_tier=TargetTier.SILVER)
    assert isinstance(report, GapReport)
    assert report.uc_id == "15.1.1"
    assert report.current_score < 50
    assert "description" in report.failing_fields
    assert "value" in report.failing_fields
    assert "dataSources" in report.failing_fields
    assert "detailedImplementation" in report.failing_fields
```

### Step 2: Run the tests to verify they fail

Run: `PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_common.py -v`
Expected: All tests fail with `ModuleNotFoundError: splunk_uc.tools.lift._common`.

### Step 3: Implement `_common.py`

Create `src/splunk_uc/tools/lift/_common.py`:

```python
"""Shared helpers for the content-quality lift loop verbs.

See ``docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md``
for the architectural contract. This module is pure-function: no AI
calls, no subprocess dispatch, no network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONTENT_ROOT = REPO_ROOT / "content"


class TargetTier(Enum):
    """Quality tier the lift loop is authoring toward."""

    SILVER = "silver"
    GOLD = "gold"
    GOLD_V2 = "gold-v2"

    @classmethod
    def from_str(cls, value: str) -> TargetTier:
        normalised = value.strip().lower()
        for tier in cls:
            if tier.value == normalised:
                return tier
        raise ValueError(
            f"unknown tier {value!r}; choose from {[t.value for t in cls]}"
        )


@dataclass(frozen=True)
class GapReport:
    """Per-UC gap analysis against a target tier's depth rubric."""

    uc_id: str
    sidecar_path: Path
    target_tier: TargetTier
    current_score: int
    failing_fields: dict[str, str] = field(default_factory=dict)
    # field_name -> human-readable rubric violation

    def to_json(self) -> dict[str, Any]:
        return {
            "uc_id": self.uc_id,
            "sidecar_path": str(self.sidecar_path),
            "target_tier": self.target_tier.value,
            "current_score": self.current_score,
            "failing_fields": dict(self.failing_fields),
        }


def resolve_sidecar_path(
    uc_id: str,
    content_root: Path | None = None,
) -> Path:
    """Locate the sidecar JSON for a given UC-X.Y.Z identifier.

    Searches ``content_root/cat-*/UC-<id>.json``. Raises
    ``FileNotFoundError`` if no match is found.
    """
    root = content_root if content_root is not None else DEFAULT_CONTENT_ROOT
    bare_id = uc_id.removeprefix("UC-")
    for sidecar in root.glob(f"cat-*/UC-{bare_id}.json"):
        return sidecar
    raise FileNotFoundError(f"no sidecar found for {uc_id} under {root}")


def load_sidecar(path: Path) -> dict[str, Any]:
    """Parse a UC sidecar JSON file."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def score_uc(
    sidecar_path: Path,
    target_tier: TargetTier,
) -> GapReport:
    """Score a UC against the target tier's rubric and return a gap report.

    Delegates the actual scoring to the existing ``audit-gold-profile``
    audit, parsing its summary output. For Silver/Gold the v1 audit is
    sufficient; for Gold-v2 the v2 audit is also consulted.
    """
    from splunk_uc.audits import gold_profile  # local import: lazy

    data = load_sidecar(sidecar_path)
    uc_id = str(data.get("id", sidecar_path.stem.removeprefix("UC-")))

    # The audit module exposes ``score_sidecar(data) -> tuple[int, dict[str, str]]``
    # added in Task 1 step 4.
    current_score, failures = gold_profile.score_sidecar(data, tier=target_tier.value)

    return GapReport(
        uc_id=uc_id,
        sidecar_path=sidecar_path,
        target_tier=target_tier,
        current_score=current_score,
        failing_fields=failures,
    )
```

### Step 4: Add `score_sidecar` to the gold-profile audit module

Open `src/splunk_uc/audits/gold_profile.py` and add a public `score_sidecar(data, tier)` function that returns `(int, dict[str, str])`. The function is a thin facade over the existing per-UC scoring loop. Look at the existing `_score_uc` / `_audit_one_uc` (or equivalent) internal function and expose its score + failures as a stable public API. This keeps `_common.py` from re-implementing rubric arithmetic.

If the audit module does not already factor its per-UC scorer into a callable suitable for direct invocation, refactor: move the per-UC scoring into a private function, then expose a public `score_sidecar` wrapper. Verify by re-running `python3 -m splunk_uc audit-gold-profile --check` — same exit code and same output before/after the refactor.

### Step 5: Run the tests to verify they pass

Run: `PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_common.py -v`
Expected: All five tests pass.

### Step 6: Commit

```bash
git add src/splunk_uc/tools/lift/__init__.py \
        src/splunk_uc/tools/lift/_common.py \
        src/splunk_uc/audits/gold_profile.py \
        tests/splunk_uc/lift/__init__.py \
        tests/splunk_uc/lift/test_common.py
git commit -m "feat(lift): shared helpers + gold-profile public scorer

Adds src/splunk_uc/tools/lift/_common.py with the GapReport
dataclass, TargetTier enum, sidecar loader, and the score_uc helper
that delegates to audit-gold-profile via a new public
score_sidecar() facade. Pure-function module — no AI, no subprocess.

Refs: docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md
Task 1 of docs/superpowers/plans/2026-05-17-content-quality-lift-loop.md."
```

---

## Task 2: `lift-score` verb

**Files:**
- Create: `src/splunk_uc/tools/lift/score.py`
- Create: `tests/splunk_uc/lift/test_score.py`
- Modify: `src/splunk_uc/_registry.py` (one `register(Verb(...))` block)

### Step 1: Write the failing tests for `lift-score`

Create `tests/splunk_uc/lift/test_score.py`:

```python
"""Tests for the ``lift-score`` verb."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import score  # noqa: E402


def test_main_prints_human_readable_report_by_default(capsys, tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar_data = {
        "id": "15.1.1",
        "title": "Test UC",
        "description": "short",
        "value": "short",
        "dataSources": "tiny",
        "detailedImplementation": "stub",
        "spl": "search index=main",
        # ... add minimal required fields ...
    }
    (cat / "UC-15.1.1.json").write_text(json.dumps(sidecar_data))
    exit_code = score.main(
        ["UC-15.1.1", "--content-root", str(tmp_path / "content")]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "UC-15.1.1" in captured.out
    assert "current score" in captured.out.lower()
    assert "description" in captured.out  # one of the failing fields


def test_main_emits_json_with_flag(capsys, tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    (cat / "UC-15.1.1.json").write_text(json.dumps({
        "id": "15.1.1", "title": "x", "description": "short",
        "value": "short", "dataSources": "tiny",
        "detailedImplementation": "stub", "spl": "search index=main",
    }))
    exit_code = score.main(
        ["UC-15.1.1", "--json", "--content-root", str(tmp_path / "content")]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["uc_id"] == "15.1.1"
    assert "current_score" in payload
    assert "failing_fields" in payload
```

### Step 2: Run the tests to verify they fail

Run: `PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_score.py -v`
Expected: `ModuleNotFoundError`.

### Step 3: Implement `lift-score`

Create `src/splunk_uc/tools/lift/score.py`:

```python
"""``lift-score`` verb — print depth score + gap report for one UC.

Usage:
    python -m splunk_uc lift-score UC-X.Y.Z
    python -m splunk_uc lift-score UC-X.Y.Z --json
    python -m splunk_uc lift-score UC-X.Y.Z --target-tier gold
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    TargetTier,
    resolve_sidecar_path,
    score_uc,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc lift-score",
        description="Print depth score + gap report for one UC.",
    )
    parser.add_argument("uc_id", help="UC identifier, e.g. UC-15.1.1")
    parser.add_argument(
        "--target-tier",
        default="silver",
        choices=["silver", "gold", "gold-v2"],
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )
    parser.add_argument(
        "--content-root",
        type=Path,
        default=DEFAULT_CONTENT_ROOT,
        help="Override the content root (for tests)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    sidecar = resolve_sidecar_path(args.uc_id, content_root=args.content_root)
    report = score_uc(sidecar, target_tier=TargetTier.from_str(args.target_tier))

    if args.json:
        print(json.dumps(report.to_json(), indent=2, sort_keys=True))
    else:
        print(f"UC: {report.uc_id}")
        print(f"Target tier: {report.target_tier.value}")
        print(f"Current score: {report.current_score}/100")
        print("")
        if report.failing_fields:
            print("Failing fields:")
            for field, reason in sorted(report.failing_fields.items()):
                print(f"  - {field}: {reason}")
        else:
            print("All rubric fields satisfy the target tier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Register the verb

Open `src/splunk_uc/_registry.py` and append after the last existing `register(...)` block:

```python
register(
    Verb(
        name="lift-score",
        module="tools.lift.score",
        help="Print depth score + gap report for one UC.",
        category="lift",
    )
)
```

### Step 5: Run the tests + smoke-test the dispatcher

```bash
PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_score.py -v
PYTHONPATH=src python3 -m splunk_uc lift-score --help
PYTHONPATH=src python3 -m splunk_uc lift-score UC-1.1.1
```

Expected: tests pass; `--help` shows the new verb; the smoke run prints a score for the exemplar UC-1.1.1.

### Step 6: Commit

```bash
git add src/splunk_uc/tools/lift/score.py \
        src/splunk_uc/_registry.py \
        tests/splunk_uc/lift/test_score.py
git commit -m "feat(lift): add lift-score verb

First of four lift-loop CLI primitives. Reads a UC sidecar, scores
it against the chosen target tier's rubric, prints the score and
the list of failing fields. Pure-function: no AI, no subprocess
dispatch, no network.

Refs: spec section 6. Task 2 of the implementation plan."
```

---

## Task 3: `lift-prompt` verb

**Files:**
- Create: `src/splunk_uc/tools/lift/prompt.py`
- Create: `tests/splunk_uc/lift/test_prompt.py`
- Modify: `src/splunk_uc/_registry.py` (one `register(Verb(...))` block)

### Step 1: Write the failing tests

Create `tests/splunk_uc/lift/test_prompt.py`. The prompt is text; tests assert on the **shape** rather than verbatim wording (so the prompt can be tuned without re-baselining tests). At minimum the emitted prompt must:

1. Start with a system-level instruction line.
2. Contain a `# RUBRIC` section that names every field the lift surface (spec §4) is allowed to touch.
3. Contain a `# CURRENT UC SIDECAR` section followed by valid JSON of the loaded sidecar.
4. Contain a `# GAP REPORT` section followed by valid JSON of the gap report.
5. Contain a `# FIREWALL` section that names every firewalled field from spec §4.
6. Contain a `# OUTPUT SHAPE` section that declares the expected JSON diff schema with `uc_id`, `target_tier`, `lifted_fields`.
7. End with an instruction to save the diff to `/tmp/lift-<UC-ID>.diff.json`.

Skeleton:

```python
"""Tests for the ``lift-prompt`` verb."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import prompt  # noqa: E402

FIREWALLED_FIELDS = (
    "spl", "cimSpl", "id", "title", "monitoringType", "splunkPillar",
    "criticality", "difficulty", "compliance", "fixtureRef", "assurance",
    "grandmaExplanation",
)
LIFT_SURFACE_FIELDS = (
    "description", "value", "dataSources", "detailedImplementation",
    "knownFalsePositives", "references", "controlTest", "evidence",
    "exclusions", "visualization", "equipmentModels", "mitreAttack",
)


def test_main_writes_prompt_with_required_sections(capsys, tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    (cat / "UC-15.1.1.json").write_text(json.dumps({
        "id": "15.1.1", "title": "Test", "description": "short",
        "value": "short", "dataSources": "tiny", "spl": "search index=main",
        "detailedImplementation": "stub",
    }))
    exit_code = prompt.main(
        ["UC-15.1.1", "--content-root", str(tmp_path / "content")]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    text = captured.out
    assert "# RUBRIC" in text
    assert "# CURRENT UC SIDECAR" in text
    assert "# GAP REPORT" in text
    assert "# FIREWALL" in text
    assert "# OUTPUT SHAPE" in text
    for field in FIREWALLED_FIELDS:
        assert field in text, f"firewalled field {field!r} missing from prompt"
    for field in LIFT_SURFACE_FIELDS:
        assert field in text, f"lift-surface field {field!r} missing from prompt"
    assert "/tmp/lift-UC-15.1.1.diff.json" in text


def test_prompt_includes_loaded_sidecar_json(capsys, tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar_data = {
        "id": "15.1.1", "title": "Cooling failure",
        "description": "Detect chiller failure", "value": "v",
        "dataSources": "bms", "spl": "search index=bms",
        "detailedImplementation": "stub",
    }
    (cat / "UC-15.1.1.json").write_text(json.dumps(sidecar_data))
    prompt.main(["UC-15.1.1", "--content-root", str(tmp_path / "content")])
    text = capsys.readouterr().out
    # Extract the JSON block under "# CURRENT UC SIDECAR" and assert it round-trips.
    match = re.search(
        r"# CURRENT UC SIDECAR\s*\n```json\s*\n(.*?)\n```",
        text, re.DOTALL,
    )
    assert match is not None
    assert json.loads(match.group(1))["id"] == "15.1.1"
```

### Step 2: Run the tests to verify they fail

`PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_prompt.py -v` → ModuleNotFoundError.

### Step 3: Implement `lift-prompt`

Create `src/splunk_uc/tools/lift/prompt.py`. Use a module-level `PROMPT_TEMPLATE` string with `{...}` format slots for the loaded sidecar JSON, the gap-report JSON, and the UC id. Embed the RUBRIC / FIREWALL / OUTPUT SHAPE sections as **literal text** in the template — they are part of the spec, not dynamically derived, and keeping them literal makes test assertions stable.

Structure of `main`:

```python
def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    sidecar = resolve_sidecar_path(args.uc_id, content_root=args.content_root)
    report = score_uc(sidecar, target_tier=TargetTier.from_str(args.target_tier))
    sidecar_json = json.dumps(load_sidecar(sidecar), indent=2, sort_keys=True)
    gap_json = json.dumps(report.to_json(), indent=2, sort_keys=True)
    print(PROMPT_TEMPLATE.format(
        uc_id=args.uc_id,
        target_tier=args.target_tier,
        sidecar_json=sidecar_json,
        gap_json=gap_json,
    ))
    return 0
```

The `PROMPT_TEMPLATE` (literal text, exact content):

```
You are a Splunk content-quality author. Your job: lift the depth of
the use case below to the target tier without violating the firewall.

# RUBRIC (target tier: {target_tier})

* `description`: >= 80 chars, shares <= 60% word stems with `value`.
* `value`: >= 80 chars, distinct from `description`.
* `dataSources`: >= 80 chars; must contain a Splunkbase ID, a sourcetype, and a named extracted field.
* `detailedImplementation`: >= 500 chars (Silver) / >= 1500 chars (Gold-v2); >= 6 distinct product-specific indicators (sourcetype=, index=, /api/, modular input, time bound, RBAC role, etc.).
* `knownFalsePositives`: >= 4 distinct named scenarios; each must reference a system/process by name AND a distinguish or suppress pattern.
* `references`: >= 4 entries with non-empty `url` and `title`. Prefer high-provenance sources (vendor docs, official Splunk docs).
* `controlTest.positiveScenario` and `negativeScenario`: differ by >= 30 chars.
* `evidence`: >= 30 chars.
* `exclusions`: >= 30 chars.
* `visualization`: populate if missing.
* `equipmentModels`: populate if a known model matches the data sources.
* `mitreAttack[]`: populate ONLY when `splunkPillar` is `security`, the field is currently null/empty, and you can name a specific technique ID that validates against `audit-mitre-taxonomy`.

# CURRENT UC SIDECAR

```json
{sidecar_json}
```

# GAP REPORT

```json
{gap_json}
```

# FIREWALL — DO NOT TOUCH

* `spl`, `cimSpl` — never. SPL changes are out of scope for this loop.
* `id`, `title` — never. Identity is immutable.
* `monitoringType`, `splunkPillar` — never. Classification stays.
* `criticality`, `difficulty` — never. Classification stays.
* `compliance` — never. Regulatory mappings are too sensitive for this loop.
* `fixtureRef`, `assurance` — never. Sample-data is a separate workflow.
* `grandmaExplanation` — never. A dedicated generator owns this field.

# OUTPUT SHAPE

Return a unified JSON diff with this exact structure:

```json
{{
  "uc_id": "{uc_id}",
  "target_tier": "{target_tier}",
  "lifted_fields": {{
    "<field_name>": "<full replacement value>"
  }}
}}
```

Rules:
* `lifted_fields` keys are restricted to the lift surface above.
* Field values are FULL replacements, not patches. The diff replaces
  the entire current value.
* Do NOT invent vendors/products that do not appear in the original
  UC's `dataSources` or `app`.
* Do NOT change SPL. Do NOT change classification.
* Save the diff to `/tmp/lift-{uc_id}.diff.json` and return only that
  path. Do nothing else.
```

### Step 4: Register the verb

In `_registry.py`:

```python
register(
    Verb(
        name="lift-prompt",
        module="tools.lift.prompt",
        help="Emit the AI prompt for one UC (consumed by an orchestration agent).",
        category="lift",
    )
)
```

### Step 5: Run the tests + smoke

```bash
PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_prompt.py -v
PYTHONPATH=src python3 -m splunk_uc lift-prompt UC-1.1.1 | head -40
```

Expected: tests pass; smoke prints the rubric + sidecar JSON sections.

### Step 6: Commit

```bash
git add src/splunk_uc/tools/lift/prompt.py \
        src/splunk_uc/_registry.py \
        tests/splunk_uc/lift/test_prompt.py
git commit -m "feat(lift): add lift-prompt verb

Second lift-loop CLI primitive. Emits the deterministic AI prompt
for one UC: rubric excerpt + UC JSON + gap report + firewall +
expected output diff shape. Orchestration agent feeds this to a
Task subagent.

Refs: spec section 6. Task 3 of the implementation plan."
```

---

## Task 4: `lift-validate` verb — the §5 validation chain

**Files:**
- Create: `src/splunk_uc/tools/lift/validate.py`
- Create: `tests/splunk_uc/lift/test_validate.py`
- Create: `tests/splunk_uc/lift/fixtures/UC-15-silver-target.json`
- Create: `tests/splunk_uc/lift/fixtures/UC-15-bronze-baseline.json`
- Modify: `src/splunk_uc/_registry.py`

This task carries the most code because the §5 contract is non-trivial. Implement carefully.

### Step 1: Add the fixture files

Create `tests/splunk_uc/lift/fixtures/UC-15-bronze-baseline.json` — a real Bronze-quality UC sidecar copied verbatim from `content/cat-15-data-center-physical-infrastructure/UC-15.1.1.json` (whichever UC currently scores lowest in cat-15 per `lift-score`). Do not modify it. This is the baseline a lift attempt starts from.

Create `tests/splunk_uc/lift/fixtures/UC-15-silver-target.json` — the same UC with the lifted fields filled in to Silver-tier thresholds (description ≥ 80 chars, value ≥ 80 chars, dataSources ≥ 80 chars + Splunkbase<sup class="ref">[<a href="#ref-2">2</a>]</sup> ID + sourcetype + named field, detailedImplementation ≥ 500 chars with 6+ specific indicators, KFP ≥ 4 named scenarios, references ≥ 4, controlTest scenarios differ ≥ 30 chars, evidence + exclusions populated). Write authentic, domain-correct content (this UC is a chiller / HVAC / UPS monitoring use case — use real product names and real sourcetypes). The fixture serves as both a test oracle and a worked example of "what a Silver UC looks like".

### Step 2: Write the failing tests

Create `tests/splunk_uc/lift/test_validate.py`:

```python
"""Tests for the lift-validate verb."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import validate  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _stage_uc(tmp_path: Path, fixture_name: str) -> tuple[Path, Path]:
    """Copy the named fixture into a temp content tree, return (content_root, sidecar)."""
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-15.1.1.json"
    shutil.copy(FIXTURE_DIR / fixture_name, sidecar)
    return tmp_path / "content", sidecar


def _write_diff(tmp_path: Path, uc_id: str, lifted: dict) -> Path:
    diff_path = tmp_path / f"lift-{uc_id}.diff.json"
    diff_path.write_text(json.dumps({
        "uc_id": uc_id.removeprefix("UC-"),
        "target_tier": "silver",
        "lifted_fields": lifted,
    }))
    return diff_path


def test_validate_accepts_proper_silver_lift(tmp_path: Path):
    content_root, sidecar = _stage_uc(tmp_path, "UC-15-bronze-baseline.json")
    silver_data = json.loads(
        (FIXTURE_DIR / "UC-15-silver-target.json").read_text()
    )
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {
        "description": silver_data["description"],
        "value": silver_data["value"],
        "dataSources": silver_data["dataSources"],
        "detailedImplementation": silver_data["detailedImplementation"],
        "knownFalsePositives": silver_data["knownFalsePositives"],
        "references": silver_data["references"],
    })
    exit_code = validate.main([
        "UC-15.1.1", "--diff", str(diff_path),
        "--content-root", str(content_root),
    ])
    assert exit_code == 0
    after = json.loads(sidecar.read_text())
    assert after["description"] == silver_data["description"]
    # SPL stays untouched
    baseline = json.loads(
        (FIXTURE_DIR / "UC-15-bronze-baseline.json").read_text()
    )
    assert after["spl"] == baseline["spl"]


def test_validate_rejects_diff_that_touches_firewalled_field(tmp_path: Path):
    content_root, sidecar = _stage_uc(tmp_path, "UC-15-bronze-baseline.json")
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {
        "spl": "search index=evil",  # firewalled
    })
    exit_code = validate.main([
        "UC-15.1.1", "--diff", str(diff_path),
        "--content-root", str(content_root),
    ])
    assert exit_code == 1
    after = json.loads(sidecar.read_text())
    baseline = json.loads(
        (FIXTURE_DIR / "UC-15-bronze-baseline.json").read_text()
    )
    # Sidecar unchanged on validation failure
    assert after == baseline


def test_validate_rejects_diff_when_post_score_not_strictly_greater(tmp_path: Path):
    # Pre-load with the Silver fixture; apply a trivial no-op lift.
    # Expectation: post-lift score == pre-lift score, validation refuses.
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-15.1.1.json"
    shutil.copy(FIXTURE_DIR / "UC-15-silver-target.json", sidecar)
    data = json.loads(sidecar.read_text())
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {
        "description": data["description"],  # unchanged
    })
    exit_code = validate.main([
        "UC-15.1.1", "--diff", str(diff_path),
        "--content-root", str(tmp_path / "content"),
    ])
    assert exit_code == 1


def test_validate_dry_run_does_not_write_sidecar(tmp_path: Path):
    content_root, sidecar = _stage_uc(tmp_path, "UC-15-bronze-baseline.json")
    silver_data = json.loads(
        (FIXTURE_DIR / "UC-15-silver-target.json").read_text()
    )
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {
        "description": silver_data["description"],
    })
    exit_code = validate.main([
        "UC-15.1.1", "--diff", str(diff_path), "--dry-run",
        "--content-root", str(content_root),
    ])
    assert exit_code == 0
    after = json.loads(sidecar.read_text())
    baseline = json.loads(
        (FIXTURE_DIR / "UC-15-bronze-baseline.json").read_text()
    )
    assert after == baseline  # disk unchanged
```

### Step 3: Run the tests to verify they fail

`PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_validate.py -v` → ModuleNotFoundError.

### Step 4: Implement `lift-validate`

Create `src/splunk_uc/tools/lift/validate.py`. The §5 chain in order:

```python
"""``lift-validate`` verb — apply a diff and run the §5 contract."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    REPO_ROOT,
    TargetTier,
    load_sidecar,
    resolve_sidecar_path,
    score_uc,
)

SRC_DIR = REPO_ROOT / "src"

# Fields the firewall forbids the diff from touching (spec §4).
FIREWALLED_FIELDS = frozenset({
    "spl", "cimSpl", "id", "title",
    "monitoringType", "splunkPillar",
    "criticality", "difficulty",
    "compliance",
    "fixtureRef", "assurance",
    "grandmaExplanation",
})


def _apply_diff(sidecar: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    """Return a new sidecar dict with the diff's lifted_fields applied."""
    out = deepcopy(sidecar)
    for field, new_value in diff.get("lifted_fields", {}).items():
        out[field] = new_value
    return out


def _check_firewall(diff: dict[str, Any]) -> list[str]:
    """Return list of violations: keys in lifted_fields that are firewalled."""
    return sorted(
        set(diff.get("lifted_fields", {}).keys()) & FIREWALLED_FIELDS
    )


def _run_audit(
    audit_verb: str,
    sidecar_path: Path,
) -> tuple[int, str]:
    """Invoke an audit verb on one file; return (exit_code, combined output)."""
    result = subprocess.run(
        [
            sys.executable, "-m", "splunk_uc", audit_verb,
            "--files", str(sidecar_path),
        ],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
    )
    return result.returncode, (result.stdout + result.stderr)


VALIDATION_AUDITS = (
    "audit-uc-structure",
    "audit-spl-hallucinations",
    "audit-spl-grammar",
    "audit-known-fp",
    "audit-monitoring-type",
    "audit-content-quality",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc lift-validate",
        description="Apply an AI-authored diff and run the §5 validation chain.",
    )
    parser.add_argument("uc_id")
    parser.add_argument("--diff", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--content-root", type=Path, default=DEFAULT_CONTENT_ROOT,
    )
    parser.add_argument(
        "--target-tier", default="silver",
        choices=["silver", "gold", "gold-v2"],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    sidecar_path = resolve_sidecar_path(args.uc_id, content_root=args.content_root)
    original = load_sidecar(sidecar_path)
    target_tier = TargetTier.from_str(args.target_tier)

    pre_score = score_uc(sidecar_path, target_tier).current_score

    diff = json.loads(args.diff.read_text())

    # 0. Identity invariants
    expected_id = args.uc_id.removeprefix("UC-")
    if diff.get("uc_id") not in (args.uc_id, expected_id):
        print(f"REFUSE: diff uc_id {diff.get('uc_id')!r} != {args.uc_id!r}")
        return 1

    # 1. Firewall
    violations = _check_firewall(diff)
    if violations:
        print(f"REFUSE: diff touches firewalled fields: {violations}")
        return 1

    # 2-7. Apply in-memory, write to a temp file, run audits.
    lifted = _apply_diff(original, diff)
    # Identity must still be intact
    for immutable in ("id", "title"):
        if lifted.get(immutable) != original.get(immutable):
            print(f"REFUSE: {immutable!r} changed by diff")
            return 1

    # Write to a temp sidecar so the audit subprocesses operate on the
    # would-be content, not the on-disk content.
    tmp_sidecar = sidecar_path.parent / f"{sidecar_path.stem}.lift-tmp.json"
    tmp_sidecar.write_text(json.dumps(lifted, indent=2, sort_keys=False))
    try:
        for audit_verb in VALIDATION_AUDITS:
            code, output = _run_audit(audit_verb, tmp_sidecar)
            if code != 0:
                print(f"REFUSE: {audit_verb} exit={code}\n{output}")
                return 1
        # 9. Score must strictly increase
        post_score = score_uc(tmp_sidecar, target_tier).current_score
        if post_score <= pre_score:
            print(
                f"REFUSE: post-lift score {post_score} not > pre-lift {pre_score}"
            )
            return 1
        if args.dry_run:
            print(f"OK (dry-run): {pre_score} -> {post_score}")
            return 0
        # Commit the lifted sidecar in place
        sidecar_path.write_text(json.dumps(lifted, indent=2))
    finally:
        tmp_sidecar.unlink(missing_ok=True)

    # Regenerate the .md companion so the dist build sees the new content.
    subprocess.run(
        [sys.executable, "-m", "splunk_uc", "generate-md-from-json",
         "--files", str(sidecar_path)],
        check=True,
        env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
    )
    print(f"OK: {pre_score} -> {post_score}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Notes for the implementer:

- The audit subprocesses must run with `PYTHONPATH=src` because that's the convention the existing audits assume; the implementation passes `PYTHONPATH=str(SRC_DIR)` in the subprocess env.
- `_common.py` must export `REPO_ROOT` (Task 1 step 3 already defines it as `Path(__file__).resolve().parents[4]`); add it to the module's effective public API simply by importing it from this module.
- If `generate-md-from-json` does not support a `--files` flag in the current build, drop the per-UC regeneration call from `lift-validate` and run a single `python -m splunk_uc generate-md-from-json` at the end of the batch instead (Task 7 step 6 will then explicitly add the companion .md files alongside the scorecard).

### Step 5: Register and smoke

In `_registry.py`:

```python
register(
    Verb(
        name="lift-validate",
        module="tools.lift.validate",
        help="Apply an AI-authored diff for one UC and run the validation chain.",
        category="lift",
    )
)
```

Smoke:

```bash
PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_validate.py -v
PYTHONPATH=src python3 -m splunk_uc lift-validate --help
```

Expected: 4 tests pass; help text shows.

### Step 6: Commit

```bash
git add src/splunk_uc/tools/lift/validate.py \
        src/splunk_uc/_registry.py \
        tests/splunk_uc/lift/test_validate.py \
        tests/splunk_uc/lift/fixtures/
git commit -m "feat(lift): add lift-validate verb (the firewall)

Third lift-loop CLI primitive. Reads an AI-authored JSON diff,
enforces the spec section 5 validation chain in order: identity ->
firewall -> 6 audit verbs -> score-strictly-increased. Writes the
sidecar only on a passing diff. Pure-function except for the audit
subprocesses; no AI in the loop.

Refs: spec sections 4-5. Task 4 of the implementation plan."
```

---

## Task 5: `lift-batch` verb — work-list generator

**Files:**
- Create: `src/splunk_uc/tools/lift/batch.py`
- Create: `tests/splunk_uc/lift/test_batch.py`
- Modify: `src/splunk_uc/_registry.py`

### Step 1: Write the failing tests

Tests assert that `lift-batch`:

1. Enumerates UCs in the named category folder.
2. Sorts by current depth ascending when `--worst-first` is set (default).
3. Truncates to `--limit N`.
4. Writes a manifest JSON to `--report` (default: `reports/lift-batch-<timestamp>.json`).
5. Returns exit 0 on success.

```python
"""Tests for the lift-batch verb."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import batch  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_batch_emits_manifest_sorted_by_worst_first(tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    # Stage 3 UCs: one Silver (high depth), one Bronze (low depth), one mid.
    shutil.copy(FIXTURE_DIR / "UC-15-silver-target.json", cat / "UC-15.1.1.json")
    shutil.copy(FIXTURE_DIR / "UC-15-bronze-baseline.json", cat / "UC-15.1.2.json")
    # Copy bronze baseline a second time with a different ID; tweak description
    # length so it lands between the two extremes.
    third = json.loads((FIXTURE_DIR / "UC-15-bronze-baseline.json").read_text())
    third["id"] = "15.1.3"
    third["description"] = "x" * 90  # marginally improved
    (cat / "UC-15.1.3.json").write_text(json.dumps(third))

    report_path = tmp_path / "report.json"
    exit_code = batch.main([
        "--category", "cat-15",
        "--limit", "2", "--worst-first",
        "--content-root", str(tmp_path / "content"),
        "--report", str(report_path),
    ])
    assert exit_code == 0
    manifest = json.loads(report_path.read_text())
    assert manifest["category"] == "cat-15"
    assert manifest["target_tier"] == "silver"
    assert len(manifest["ucs"]) == 2
    scores = [u["current_score"] for u in manifest["ucs"]]
    assert scores == sorted(scores)  # ascending, worst first


def test_batch_respects_limit(tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    for i in range(1, 6):
        data = json.loads(
            (FIXTURE_DIR / "UC-15-bronze-baseline.json").read_text()
        )
        data["id"] = f"15.1.{i}"
        (cat / f"UC-15.1.{i}.json").write_text(json.dumps(data))
    report_path = tmp_path / "r.json"
    batch.main([
        "--category", "cat-15", "--limit", "3",
        "--content-root", str(tmp_path / "content"),
        "--report", str(report_path),
    ])
    assert len(json.loads(report_path.read_text())["ucs"]) == 3
```

### Step 2: Run tests to verify they fail

`PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_batch.py -v` → ModuleNotFoundError.

### Step 3: Implement `lift-batch`

Create `src/splunk_uc/tools/lift/batch.py`. Skeleton:

```python
"""``lift-batch`` verb — pick the next N UCs in a category for the lift loop."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT, TargetTier, load_sidecar, score_uc,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m splunk_uc lift-batch")
    p.add_argument("--category", required=True, help="e.g. cat-15")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument(
        "--worst-first", action="store_true", default=True,
        help="Sort target UCs by current depth ascending (default).",
    )
    p.add_argument(
        "--random", action="store_true",
        help="Override --worst-first with random sampling.",
    )
    p.add_argument(
        "--target-tier", default="silver",
        choices=["silver", "gold", "gold-v2"],
    )
    p.add_argument(
        "--report", type=Path, default=None,
        help=("Where to write the manifest. Defaults to "
              "reports/lift-batch-<TIMESTAMP>.json"),
    )
    p.add_argument(
        "--content-root", type=Path, default=DEFAULT_CONTENT_ROOT,
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_tier = TargetTier.from_str(args.target_tier)
    cat_dir = next(args.content_root.glob(f"{args.category}-*"), None)
    if cat_dir is None or not cat_dir.is_dir():
        print(f"ERROR: no category folder matched {args.category!r}")
        return 1
    sidecars = sorted(cat_dir.glob("UC-*.json"))
    if not sidecars:
        print(f"ERROR: no UCs found under {cat_dir}")
        return 1

    scored = []
    for sc in sidecars:
        try:
            report = score_uc(sc, target_tier=target_tier)
        except Exception as exc:  # noqa: BLE001 — best-effort scoring
            print(f"WARN: skipping {sc.name}: {exc}")
            continue
        scored.append({
            "uc_id": f"UC-{report.uc_id}",
            "sidecar_path": str(report.sidecar_path),
            "current_score": report.current_score,
            "failing_fields": list(report.failing_fields.keys()),
        })

    if args.random:
        import random
        random.shuffle(scored)
    else:  # worst-first
        scored.sort(key=lambda u: u["current_score"])
    ucs = scored[: args.limit]

    report_path = args.report
    if report_path is None:
        timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
        report_path = (
            args.content_root.parent / "reports" / f"lift-batch-{timestamp}.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "category": args.category,
        "target_tier": target_tier.value,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "limit": args.limit,
        "selection": "random" if args.random else "worst-first",
        "ucs": ucs,
    }
    report_path.write_text(json.dumps(manifest, indent=2))
    print(f"wrote {report_path}")
    print(f"selected {len(ucs)} UCs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Register and smoke

In `_registry.py`:

```python
register(
    Verb(
        name="lift-batch",
        module="tools.lift.batch",
        help="Pick N UCs from a category sorted by depth for the lift loop.",
        category="lift",
    )
)
```

Smoke:

```bash
PYTHONPATH=src python3 -m pytest tests/splunk_uc/lift/test_batch.py -v
PYTHONPATH=src python3 -m splunk_uc lift-batch --category cat-15 --limit 3 \
    --report /tmp/lift-smoke.json
cat /tmp/lift-smoke.json | jq '.ucs | length'
```

Expected: tests pass; smoke writes a 3-UC manifest.

### Step 5: Commit

```bash
git add src/splunk_uc/tools/lift/batch.py \
        src/splunk_uc/_registry.py \
        tests/splunk_uc/lift/test_batch.py
git commit -m "feat(lift): add lift-batch verb

Fourth lift-loop CLI primitive. Enumerates UCs in a category, scores
each, sorts worst-first (or random), writes a JSON manifest with the
top-N targets. The orchestration agent loop reads this manifest to
drive per-UC subagent dispatch.

Refs: spec section 6. Task 5 of the implementation plan."
```

---

## Task 6: Dispatcher smoke + docs

**Files:**
- Modify: `AGENTS.md` (Quick commands section)

### Step 1: Verify the dispatcher exposes all four verbs

```bash
PYTHONPATH=src python3 -m splunk_uc --help | grep -A 5 '^lift:'
```

Expected: four lines listing `lift-score`, `lift-prompt`, `lift-validate`, `lift-batch` with their help strings.

### Step 2: Update AGENTS.md quick-commands

Open `AGENTS.md`. Find the `## Quick commands` block (search for "make build" or "splunk-uc-help"). Append:

```bash
PYTHONPATH=src python3 -m splunk_uc lift-score UC-X.Y.Z            # gap report for one UC
PYTHONPATH=src python3 -m splunk_uc lift-prompt UC-X.Y.Z           # emit AI prompt for one UC
PYTHONPATH=src python3 -m splunk_uc lift-batch --category cat-NN   # manifest of N UCs sorted by depth
PYTHONPATH=src python3 -m splunk_uc lift-validate UC-X.Y.Z --diff <path>  # apply + validate AI diff
```

Also add to the body: a short subsection titled `### Content-quality lift loop` (place it after `### Per-UC plain language`) that links to the spec and the plan and summarises the 4 verbs + the orchestration loop in ≤ 8 lines.

### Step 3: Commit

```bash
git add AGENTS.md
git commit -m "docs(agents): document the lift loop CLI primitives"
```

---

## Task 7: Run the cat-15 proof-of-concept

This task is run by the orchestration agent (Cursor session using the `dispatching-parallel-agents` skill). It is the work of the lift loop itself.

### Step 1: Generate the work list

```bash
PYTHONPATH=src python3 -m splunk_uc lift-batch \
    --category cat-15 --limit 30 --worst-first \
    --report reports/lift-batch-cat-15-poc.json
```

Expected: a manifest with 30 UCs, the lowest-scoring in cat-15 first.

### Step 2: For each UC in the manifest, run the per-UC loop

Read `reports/lift-batch-cat-15-poc.json`. For each `uc_id` in `ucs[]`:

1. Run `python -m splunk_uc lift-prompt <uc_id> > /tmp/lift-<uc_id>.prompt.txt`.
2. Dispatch a `Task` subagent (`subagent_type=generalPurpose`, `readonly=false`) with the prompt as its body. The subagent's only job is to write the JSON diff to `/tmp/lift-<uc_id>.diff.json` and return that path.
3. Run `python -m splunk_uc lift-validate <uc_id> --diff /tmp/lift-<uc_id>.diff.json`.
4. If validation succeeds, commit:

```bash
git add content/cat-15-*/UC-<id>.json content/cat-15-*/UC-<id>.md
git commit -m "content(cat-15): lift UC-X.Y.Z from depth=NN to depth=MM"
```

Use the `dispatching-parallel-agents` skill to keep up to 4 subagent dispatches in flight. Validate + commit sequentially even though dispatch is parallel.

If validation fails on a given UC, skip it (do not retry blindly) and record the failure in `reports/lift-batch-cat-15-poc.json` (append a `failures[]` array).

### Step 3: Regenerate the scorecard + verify the composite climbed

```bash
PYTHONPATH=src python3 -m splunk_uc generate-scorecard
grep -A 1 'cat-15' docs/scorecard.md | head -4
```

Expected: cat-15 composite ≥ 75.

If composite < 75, the batch did not lift enough UCs. Run another batch with `--limit 20` to lift the next 20 lowest-scoring UCs, then re-run scorecard.

### Step 4: Run the full structural test suite

```bash
PYTHONPATH=src python3 -m pytest tests/build/ tests/scripts/ tests/splunk_uc/ -q
```

Expected: all tests pass (no regressions introduced by the lifted content).

### Step 5: Run the cascade umbrella

```bash
make sync-generated-check
```

Expected: green — no drift in auto-generated files except the regenerated scorecard.

### Step 6: Commit the regenerated scorecard

```bash
git add docs/scorecard.md dist/scorecard.json
git commit -m "content(cat-15): regenerate scorecard after PoC lift batch

cat-15 composite climbs from 67.0 -> <new value> after lift-batch
of 30 UCs. See reports/lift-batch-cat-15-poc.json for the per-UC
score deltas."
```

---

## Task 8: CHANGELOG + drift-ledger entry

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/health-check-2026-progress.md`
- Modify: `VERSION` (optional — only if the PoC counts as a release; ask `@fenre` before bumping per `versioning.mdc`)

### Step 1: Append a CHANGELOG entry

Open `CHANGELOG.md`. Add under the current Unreleased / next-version section:

```markdown
### Added

- **Content-quality lift loop (PR-4).** Four new `splunk_uc` verbs
  (`lift-score`, `lift-prompt`, `lift-validate`, `lift-batch`) +
  an agent-driven orchestration loop using the
  `dispatching-parallel-agents` superpowers skill. Together they
  let a Cursor session systematically lift the depth-dimension of
  UC sidecars against the gold-profile rubric without touching
  SPL, compliance, or identity fields. See
  `docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`
  and `docs/superpowers/plans/2026-05-17-content-quality-lift-loop.md`.

### Changed

- **cat-15 Data Center Physical Infrastructure: Bronze 67.0 → Silver
  <new composite>.** Proof-of-concept run of the lift loop;
  30 UC depth-lift commits. SPL unchanged. Per-UC score deltas in
  `reports/lift-batch-cat-15-poc.json`.
```

### Step 2: Append a drift-ledger entry

Open `docs/health-check-2026-progress.md`. Add a new numbered entry to the drift ledger (next number after the last one — current is #21 from PR-3):

```markdown
**#22 (2026-05-17) — Content-quality lift loop PoC (cat-15).**

Shipped four new `splunk_uc` CLI primitives — `lift-score`,
`lift-prompt`, `lift-validate`, `lift-batch` — and ran the first
proof-of-concept batch against cat-15 Data Center Physical
Infrastructure. 30 UC depth lifts committed (one commit per UC).
cat-15 composite climbed from Bronze 67.0 to Silver
<new value>. SPL, compliance, identity, and classification fields
were firewalled by `lift-validate` and unchanged.

Design + plan: `docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`,
`docs/superpowers/plans/2026-05-17-content-quality-lift-loop.md`.
```

### Step 3: Commit

```bash
git add CHANGELOG.md docs/health-check-2026-progress.md
git commit -m "chore: log lift-loop PR-4 in CHANGELOG + drift ledger"
```

---

## Task 9: Push + watch CI

### Step 1: Pre-push sanity

```bash
git log --oneline -20
make sync-generated-check
PYTHONPATH=src python3 -m pytest tests/build/ tests/scripts/ tests/splunk_uc/ -q
```

Expected: 20 lines of clean commit titles; both gates green.

### Step 2: Push

```bash
git push origin main
```

### Step 3: Watch validate.yml

```bash
gh run watch  # or: gh run list --limit 5 + gh run view <id>
```

Expected: validate.yml + gitleaks + CodeQL + Deploy-to-GitHub-Pages all complete with success.

If any job fails, diagnose using the failing job's logs and ship a fix-up commit. Do not amend.

### Step 4: Update the todo list to all-completed

After CI is green, mark every implementation-plan todo as `completed` in TodoWrite. PR-4 is done.

---

## Self-Review

**Spec coverage (against `docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`):**

| Spec section | Plan task(s) |
| --- | --- |
| §3 architecture | Tasks 1-5 (CLI primitives) + Task 7 (orchestration loop) |
| §4 lift surface + firewall | Task 4 step 4 (FIREWALLED_FIELDS const) + Task 3 (prompt template) |
| §5 validation contract | Task 4 (lift-validate is the chain) |
| §6 CLI surface | Tasks 2, 3, 4, 5 (one verb each) |
| §7 AI authoring + parallelism | Task 7 (PoC run uses dispatching-parallel-agents) |
| §8 PoC target + done criteria | Task 7 (the run) + Task 8 (CHANGELOG / ledger) |
| §11 risks + mitigations | Task 4 (firewall + score-strictly-increased) covers risks 1, 4 |

No spec section is unmentioned.

**Placeholder scan:** no `TBD`, no `TODO`, no "implement later", no "similar to Task N". Concrete commands and concrete code in every step.

**Type consistency:**

- `GapReport.uc_id` is the bare ID (`"15.1.1"`, no `UC-` prefix) — matches `score_sidecar`'s expected return.
- `lift-validate` accepts both prefixed and bare IDs in the diff (`diff["uc_id"] in (args.uc_id, expected_id)`) — explicit.
- `TargetTier` enum values match the CLI `--target-tier` choices in every parser.
- `FIREWALLED_FIELDS` set in `validate.py` and the prompt template's `# FIREWALL` section list the same 12 fields.

**Scope check:** the plan covers one PR (PR-4: ship the verbs + PoC cat-15 + CHANGELOG). Subsequent category lifts (cat-7, cat-6, cat-8, cat-12, then cat-22/cat-10/cat-5) are deliberately deferred to future PRs.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-17-content-quality-lift-loop.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Best fit for Tasks 1-6 (each task is a self-contained code change with a tight test loop).

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Best fit if you want to follow along step-by-step.

Either way, **Task 7 (the cat-15 PoC run) must use parallel subagents** (dispatching-parallel-agents skill) — that's the lift loop itself, with one subagent per UC.

**Which approach?**

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<!-- END-AUTOGENERATED-SOURCES -->
