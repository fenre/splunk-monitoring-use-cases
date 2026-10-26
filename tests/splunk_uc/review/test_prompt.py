"""Tests for the review-prompt verb and its grounding bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.review import _grounding as grounding  # noqa: E402
from splunk_uc.review import prompt as rp  # noqa: E402
from splunk_uc.review._ledger import content_sha256  # noqa: E402

UC_PATH = REPO_ROOT / "content" / "cat-05-network-infrastructure" / "UC-5.1.1.json"


def _entry(path: Path = UC_PATH) -> tuple[Path, dict]:
    return path, json.loads(path.read_text(encoding="utf-8"))


def _json_block_after(prompt: str, heading: str) -> object:
    section = prompt.split(heading, 1)[1]
    return json.loads(section.split("```json\n", 1)[1].split("\n```", 1)[0])


def test_rubric_markers_present_and_embedded() -> None:
    rubric = rp.load_rubric_text()
    assert rubric.startswith("## Rubric")
    assert "needs_verification" in rubric
    assert rubric in rp.build_prompt("deep", [_entry()], ledger_path=Path("/nonexistent"))


def test_deep_prompt_sections(tmp_path: Path) -> None:
    prompt = rp.build_prompt("deep", [_entry()], ledger_path=tmp_path / "missing.jsonl")
    assert "# TASK — DEEP CORRECTNESS REVIEW" in prompt
    assert "# USE CASE UC-5.1.1" in prompt
    assert '"$schema"' not in prompt.split("## Sidecar", 1)[1]
    ground = _json_block_after(prompt, "# GROUNDING")
    assert ground["guide"] == "docs/guides/cisco-networks.md"
    assert ground["guide_excerpt"]
    assert {s["id"] for s in ground["splunkbase"]} >= {"1352"}
    assert all(s["id"] != "UC-5.1.1" for s in ground["siblings"])
    det = _json_block_after(prompt, "## Deterministic findings (already recorded")
    assert any(row["check"] == "premium_app_pillar_mismatch" for row in det)
    assert prompt.rstrip().endswith("Do not propose edits to firewalled fields under `findings`.")


def test_stored_deterministic_record_used_when_current(tmp_path: Path) -> None:
    _, uc = _entry()
    ledger = tmp_path / "det.jsonl"
    stored = {
        "uc_id": "UC-5.1.1",
        "content_sha256": content_sha256(uc),
        "findings": [{"field": "value", "severity": "minor", "check": "stored_marker"}],
        "firewalled_field_flags": [],
    }
    ledger.write_text(json.dumps(stored, sort_keys=True) + "\n", encoding="utf-8")
    prompt = rp.build_prompt("deep", [_entry()], ledger_path=ledger)
    det = _json_block_after(prompt, "## Deterministic findings (already recorded")
    assert det == [{"field": "value", "severity": "minor", "check": "stored_marker"}]


def test_stale_deterministic_record_is_recomputed(tmp_path: Path) -> None:
    ledger = tmp_path / "det.jsonl"
    stale = {
        "uc_id": "UC-5.1.1",
        "content_sha256": "0" * 64,
        "findings": [{"field": "value", "severity": "minor", "check": "stored_marker"}],
        "firewalled_field_flags": [],
    }
    ledger.write_text(json.dumps(stale, sort_keys=True) + "\n", encoding="utf-8")
    prompt = rp.build_prompt("deep", [_entry()], ledger_path=ledger)
    det = _json_block_after(prompt, "## Deterministic findings (already recorded")
    assert all(row["check"] != "stored_marker" for row in det)


def test_triage_batch_contract() -> None:
    entries = rp.select_batch("15.1", offset=0, limit=3)
    assert len(entries) == 3
    prompt = rp.build_prompt("triage", entries, ledger_path=Path("/nonexistent"))
    ids = [f"UC-{uc['id']}" for _, uc in entries]
    for uc_id in ids:
        assert f"# USE CASE {uc_id}" in prompt
    assert f"in the order given: {', '.join(ids)}" in prompt


def test_triage_rejects_mixed_subcategories() -> None:
    mixed = rp.select_batch("15.1", offset=0, limit=1) + rp.select_batch("15.2", offset=0, limit=1)
    with pytest.raises(ValueError, match="single subcategory"):
        rp.build_prompt("triage", mixed, ledger_path=Path("/nonexistent"))


def test_deep_rejects_multiple_ucs() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        rp.build_prompt("deep", rp.select_batch("15.1", offset=0, limit=2))


def test_adjudication_requires_prior_and_lists_blockers() -> None:
    with pytest.raises(ValueError, match="prior"):
        rp.build_prompt("adjudication", [_entry()])
    prior = {
        "tier": "deep",
        "model": "claude-opus-5-5-high",
        "findings": [
            {
                "field": "cimModels",
                "dimension": "correctness",
                "severity": "blocker",
                "explanation": "Link-state syslog is not Network_Traffic.",
                "evidence_ref": "docs/guides/cisco-networks.md",
            },
            {"field": "value", "dimension": "specificity", "severity": "major", "explanation": "generic"},
        ],
        "firewalled_field_flags": [],
    }
    prompt = rp.build_prompt("adjudication", [_entry()], prior=prior, ledger_path=Path("/nonexistent"))
    blockers = _json_block_after(prompt, "# PRIOR BLOCKERS")
    assert [b["field"] for b in blockers] == ["cimModels"]
    assert '"adjudicates": {"tier": "deep", "model": "claude-opus-5-5-high", "agrees": true}' in prompt


def test_iter_batches_never_cross_subcategory() -> None:
    entries = rp.select_batch("15.1", offset=0, limit=10) + rp.select_batch("15.2", offset=0, limit=3)
    batches = rp.iter_batches(entries, size=4)
    assert [len(b) for b in batches] == [4, 4, 2, 3]
    for batch in batches:
        assert len({grounding.subcategory_id(uc) for _, uc in batch}) == 1


def test_guide_excerpt_prefers_keyword_sections(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    guide = tmp_path / "guide.md"
    guide.write_text(
        "## Intro\nGeneral text.\n\n## Syslog\ncisco:ios cisco:ios LINEPROTO\n\n## Other\nNothing.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(grounding, "REPO_ROOT", tmp_path)
    excerpt = grounding.guide_excerpt("guide.md", {"cisco:ios"}, max_chars=1000)
    assert "## Syslog" in excerpt
    assert "## Other" not in excerpt


def test_cli_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    rc = rp.main(["UC-5.1.1", "--tier", "deep", "--json", "--ledger", "/nonexistent"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["uc_ids"] == ["UC-5.1.1"]
    assert payload["tier"] == "deep"


def test_cli_unknown_uc(capsys: pytest.CaptureFixture[str]) -> None:
    assert rp.main(["UC-999.9.9", "--tier", "deep"]) == 1
    assert "cannot resolve" in capsys.readouterr().err
