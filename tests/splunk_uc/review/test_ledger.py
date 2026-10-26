"""Tests for the UC review findings ledger and its schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.review import _ledger as ledger  # noqa: E402

UC_PATH = REPO_ROOT / "content" / "cat-05-network-infrastructure" / "UC-5.1.1.json"


def _model_record(**overrides: object) -> dict[str, object]:
    uc = json.loads(UC_PATH.read_text(encoding="utf-8"))
    record = ledger.new_record(uc=uc, path=UC_PATH, tier="deep", model="claude-opus-5-5-high")
    record.update(
        {
            "verdict": "incorrect",
            "confidence": 0.8,
            "scores": dict.fromkeys(ledger.SCORE_DIMENSIONS, 3),
            "findings": [
                {
                    "field": "cimModels",
                    "dimension": "correctness",
                    "severity": "blocker",
                    "explanation": "Interface link-state syslog is not Network_Traffic.",
                    "evidence_url": "https://docs.splunk.com/Documentation/CIM/latest/User/NetworkTraffic",
                }
            ],
        }
    )
    record.update(overrides)
    return record


def test_content_sha_is_key_order_independent() -> None:
    a = {"id": "1.1.1", "title": "x", "spl": "index=main"}
    b = {"spl": "index=main", "title": "x", "id": "1.1.1"}
    assert ledger.content_sha256(a) == ledger.content_sha256(b)
    assert ledger.content_sha256(a) != ledger.content_sha256({**a, "title": "y"})


def test_new_record_shape() -> None:
    uc = json.loads(UC_PATH.read_text(encoding="utf-8"))
    record = ledger.new_record(uc=uc, path=UC_PATH, tier="deterministic", model="deterministic:x")
    assert record["uc_id"] == "UC-5.1.1"
    assert record["file"] == "content/cat-05-network-infrastructure/UC-5.1.1.json"
    assert ledger.validate_record(record) == []


def test_model_record_valid() -> None:
    assert ledger.validate_record(_model_record()) == []


def test_model_tier_requires_scores_and_verdict() -> None:
    record = _model_record()
    del record["scores"]
    del record["verdict"]
    errors = ledger.validate_record(record)
    assert any("scores" in e for e in errors)
    assert any("verdict" in e for e in errors)


def test_partial_scores_rejected() -> None:
    errors = ledger.validate_record(_model_record(scores={"clarity": 3}))
    assert errors


def test_schema_enforces_evidence_on_correctness_blockers() -> None:
    record = _model_record()
    del record["findings"][0]["evidence_url"]  # type: ignore[index]
    assert ledger.validate_record(record)


def test_apply_evidence_rule_downgrades_unsupported_blockers() -> None:
    record = _model_record()
    del record["findings"][0]["evidence_url"]  # type: ignore[index]
    record["firewalled_field_flags"] = [
        {"field": "spl", "issue": "Threshold contradicts the description.", "severity": "blocker"}
    ]
    fixed = ledger.apply_evidence_rule(record)
    assert fixed["findings"][0]["severity"] == "needs_verification"
    assert fixed["firewalled_field_flags"][0]["severity"] == "needs_verification"
    assert ledger.validate_record(fixed) == []
    assert record["findings"][0]["severity"] == "blocker"  # type: ignore[index]


def test_apply_evidence_rule_keeps_supported_blockers() -> None:
    fixed = ledger.apply_evidence_rule(_model_record())
    assert fixed["findings"][0]["severity"] == "blocker"


def test_is_current_respects_sha_and_rubric() -> None:
    record = _model_record()
    sha = record["content_sha256"]
    assert ledger.is_current(record, sha=sha)
    assert not ledger.is_current(record, sha="0" * 64)
    assert not ledger.is_current({**record, "rubric_version": "0.9"}, sha=sha)
    assert not ledger.is_current(None, sha=sha)


def test_record_round_trip_and_iteration(tmp_path: Path) -> None:
    record = _model_record()
    path = ledger.record_path("deep", "cat-05-network-infrastructure", "UC-5.1.1", root=tmp_path)
    ledger.write_record(path, record)
    assert ledger.load_record(path) == record
    assert list(ledger.iter_tier_records("deep", root=tmp_path)) == [record]


def test_iter_deterministic_jsonl(tmp_path: Path) -> None:
    rows = [{"uc_id": "UC-1.1.1"}, {"uc_id": "UC-1.1.2"}]
    (tmp_path / "deterministic.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    assert list(ledger.iter_tier_records("deterministic", root=tmp_path)) == rows


def test_iter_sidecars_by_category() -> None:
    paths = [p for p, _ in ledger.iter_sidecars(category="cat-15")]
    assert paths
    assert all("cat-15-" in str(p) for p in paths)
