"""Tests for the UC review runner core and calibration scoring (no network)."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.review import _calibration as calibration  # noqa: E402
from splunk_uc.review import _runner as runner  # noqa: E402
from splunk_uc.review._ledger import (  # noqa: E402
    SCORE_DIMENSIONS,
    content_sha256,
    record_path,
    validate_record,
    write_record,
)

SRC_UC = REPO_ROOT / "content" / "cat-15-data-center-physical-infrastructure"
MODEL = runner.ModelSpec(id="fake-model", params=(("reasoning", "high"),))


def _copy_ucs(tmp_path: Path, *names: str) -> list[runner.Entry]:
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True, exist_ok=True)
    entries = []
    for name in names:
        dst = cat / f"{name}.json"
        shutil.copy(SRC_UC / f"{name}.json", dst)
        entries.append((dst, json.loads(dst.read_text(encoding="utf-8"))))
    return entries


def _review(uc_id: str, **extra: Any) -> dict[str, Any]:
    review = {
        "uc_id": uc_id,
        "verdict": "rewrite",
        "confidence": 0.7,
        "scores": dict.fromkeys(SCORE_DIMENSIONS, 3),
        "summary": "Templated prose.",
        "findings": [
            {
                "field": "value",
                "dimension": "specificity",
                "severity": "major",
                "explanation": "Generic value statement.",
            }
        ],
        "firewalled_field_flags": [],
    }
    review.update(extra)
    return review


def _reply(*reviews: dict[str, Any]) -> str:
    return "Here you go.\n```json\n" + json.dumps({"reviews": list(reviews)}) + "\n```\n"


class FakeInvoker:
    def __init__(self, *results: Any) -> None:
        self.results = list(results)
        self.prompts: list[str] = []

    async def __call__(self, prompt: str, *, model: runner.ModelSpec, name: str) -> runner.InvokeResult:
        self.prompts.append(prompt)
        item = self.results.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item):
            item = item()
        if isinstance(item, runner.InvokeResult):
            return item
        return runner.InvokeResult(
            status="finished",
            text=item,
            run_id=f"run-{len(self.prompts)}",
            usage={"input_tokens": 100, "output_tokens": 10, "charged_cents": 1.5},
        )


async def _no_sleep(_: float) -> None:
    return None


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_review_batch_writes_valid_records(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1", "UC-15.1.2")
    invoker = FakeInvoker(_reply(_review("UC-15.1.1"), _review("UC-15.1.2")))
    outcome = _run(
        runner.review_batch(invoker, "triage", entries, model=MODEL, root=tmp_path / "ledger", sleep=_no_sleep)
    )
    assert outcome.written == ["UC-15.1.1", "UC-15.1.2"]
    assert outcome.failed == {}
    path = record_path("triage", "cat-15-data-center-physical-infrastructure", "UC-15.1.1", root=tmp_path / "ledger")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["model"] == "fake-model@reasoning=high"
    assert record["run_id"] == "run-1"
    assert record["content_sha256"] == content_sha256(entries[0][1])
    assert validate_record(record) == []
    assert outcome.log[0]["usage"]["charged_cents"] == 1.5


def test_review_batch_repairs_missing_uc(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1", "UC-15.1.2")
    invoker = FakeInvoker(_reply(_review("UC-15.1.1")), _reply(_review("UC-15.1.2")))
    outcome = _run(
        runner.review_batch(invoker, "triage", entries, model=MODEL, root=tmp_path / "ledger", sleep=_no_sleep)
    )
    assert sorted(outcome.written) == ["UC-15.1.1", "UC-15.1.2"]
    assert "FAILED VALIDATION" in invoker.prompts[1]
    assert "UC-15.1.2: no review returned" in invoker.prompts[1]
    assert [line["attempt"] for line in outcome.log] == [1, 2]


def test_review_batch_gives_up_after_one_repair(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    bad = _review("UC-15.1.1", verdict="great")
    invoker = FakeInvoker(_reply(bad), "not json at all")
    outcome = _run(
        runner.review_batch(invoker, "deep", entries, model=MODEL, root=tmp_path / "ledger", sleep=_no_sleep)
    )
    assert outcome.written == []
    assert outcome.failed["UC-15.1.1"].startswith("review_failed")


def test_evidence_rule_applied_before_validation(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    review = _review(
        "UC-15.1.1",
        verdict="incorrect",
        findings=[
            {
                "field": "dataSources",
                "dimension": "correctness",
                "severity": "blocker",
                "explanation": "Sourcetype does not exist in the named add-on.",
            }
        ],
    )
    invoker = FakeInvoker(_reply(review))
    _run(runner.review_batch(invoker, "deep", entries, model=MODEL, root=tmp_path / "l", sleep=_no_sleep))
    path = record_path("deep", "cat-15-data-center-physical-infrastructure", "UC-15.1.1", root=tmp_path / "l")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["findings"][0]["severity"] == "needs_verification"


def test_retryable_startup_error_is_retried(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    slept: list[float] = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)

    invoker = FakeInvoker(
        runner.StartupError("rate limited", retryable=True, retry_after="2"),
        _reply(_review("UC-15.1.1")),
    )
    outcome = _run(runner.review_batch(invoker, "deep", entries, model=MODEL, root=tmp_path / "l", sleep=sleep))
    assert outcome.written == ["UC-15.1.1"]
    assert slept == [2.0]


def test_non_retryable_startup_error_fails(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    invoker = FakeInvoker(runner.StartupError("bad key", retryable=False))
    outcome = _run(runner.review_batch(invoker, "deep", entries, model=MODEL, root=tmp_path / "l", sleep=_no_sleep))
    assert outcome.written == []
    assert "startup_error" in outcome.failed["UC-15.1.1"]
    assert outcome.log[0]["status"] == "startup_error"


def test_run_error_status_fails(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    invoker = FakeInvoker(runner.InvokeResult(status="error", error="model crashed"))
    outcome = _run(runner.review_batch(invoker, "deep", entries, model=MODEL, root=tmp_path / "l", sleep=_no_sleep))
    assert "model crashed" in outcome.failed["UC-15.1.1"]


def test_sidecar_modification_is_reverted_and_discarded(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    path = entries[0][0]
    original = path.read_bytes()

    def tamper() -> str:
        path.write_text("{}", encoding="utf-8")
        return _reply(_review("UC-15.1.1"))

    invoker = FakeInvoker(tamper)
    outcome = _run(runner.review_batch(invoker, "deep", entries, model=MODEL, root=tmp_path / "l", sleep=_no_sleep))
    assert path.read_bytes() == original
    assert outcome.written == []
    assert "modified a sidecar" in outcome.failed["UC-15.1.1"]


def test_dry_run_never_invokes(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1")
    outcome = _run(
        runner.review_batch(FakeInvoker(), "deep", entries, model=MODEL, root=tmp_path / "l", dry_run=True)
    )
    assert outcome.log[0]["status"] == "dry_run"
    assert outcome.log[0]["prompt_chars"] > 1000


def test_run_jobs_appends_run_log(tmp_path: Path) -> None:
    entries = _copy_ucs(tmp_path, "UC-15.1.1", "UC-15.1.2")
    invoker = FakeInvoker(_reply(_review("UC-15.1.1")), _reply(_review("UC-15.1.2")))
    total = _run(
        runner.run_jobs(
            invoker,
            "deep",
            [([entries[0]], None), ([entries[1]], None)],
            model=MODEL,
            concurrency=2,
            root=tmp_path / "l",
            dry_run=False,
        )
    )
    assert sorted(total.written) == ["UC-15.1.1", "UC-15.1.2"]
    lines = (tmp_path / "l" / runner.RUN_LOG_NAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_needs_review_skips_current_records(tmp_path: Path) -> None:
    (path, uc), = _copy_ucs(tmp_path, "UC-15.1.1")
    root = tmp_path / "l"
    assert runner.needs_review(path, uc, "triage", root=root, force=False)
    write_record(
        record_path("triage", path.parent.name, "UC-15.1.1", root=root),
        {"uc_id": "UC-15.1.1", "content_sha256": content_sha256(uc), "rubric_version": "1.0"},
    )
    assert not runner.needs_review(path, uc, "triage", root=root, force=False)
    assert runner.needs_review(path, uc, "triage", root=root, force=True)


def test_triage_batches_priority_and_cat25_last(tmp_path: Path) -> None:
    root = tmp_path / "l"
    a = (Path("/x/content/cat-25-personal-hobbyist-monitoring/UC-25.1.1.json"), {"id": "25.1.1", "criticality": "critical"})
    b = (Path("/x/content/cat-15-data-center-physical-infrastructure/UC-15.1.1.json"), {"id": "15.1.1", "criticality": "low"})
    c = (Path("/x/content/cat-15-data-center-physical-infrastructure/UC-15.2.1.json"), {"id": "15.2.1", "criticality": "critical"})
    batches = runner.triage_batches([a, b, c], batch_size=8, root=root, force=True)
    assert [batch[0][1]["id"] for batch in batches] == ["15.2.1", "15.1.1", "25.1.1"]


def test_deep_routing_reasons() -> None:
    path = Path("/x/content/cat-22-regulatory-compliance/UC-22.1.1.json")
    uc = {"criticality": "high", "status": "verified", "compliance": [{"regulation": "GDPR"}]}
    triage = {
        "confidence": 0.5,
        "findings": [{"dimension": "correctness", "severity": "major"}],
        "firewalled_field_flags": [],
    }
    reasons = runner.deep_routing_reasons(uc, path, triage)
    assert reasons == [
        "status=verified",
        "cat-22 compliance claim",
        "triage correctness finding",
        "triage confidence < 0.6",
    ]
    assert runner.deep_routing_reasons({"criticality": "low"}, Path("/x/content/cat-01-a/UC-1.1.1.json"), None) == []


def test_adjudication_reasons() -> None:
    p22 = Path("/x/content/cat-22-regulatory-compliance/UC-22.1.1.json")
    p5 = Path("/x/content/cat-05-network-infrastructure/UC-5.1.1.json")
    blocker = {"severity": "blocker", "confidence": 0.9}
    assert runner.adjudication_reasons(p22, {"findings": [blocker], "confidence": 0.9}) == ["cat-22 blocker"]
    assert runner.adjudication_reasons(p5, {"findings": [blocker], "confidence": 0.9}) == []
    assert runner.adjudication_reasons(p5, {"findings": [{**blocker, "confidence": 0.4}]}) == [
        "low-confidence blocker"
    ]
    assert runner.adjudication_reasons(p5, {"findings": [{"severity": "major"}]}) == []


def test_extract_reviews_variants() -> None:
    assert runner.extract_reviews('{"reviews": [{"uc_id": "UC-1.1.1"}]}') == [{"uc_id": "UC-1.1.1"}]
    assert runner.extract_reviews('```json\n[{"uc_id": "UC-1.1.1"}]\n```') == [{"uc_id": "UC-1.1.1"}]
    with pytest.raises(ValueError):
        runner.extract_reviews("no json here")
    with pytest.raises(ValueError):
        runner.extract_reviews('{"other": 1}')


def test_retry_delay() -> None:
    assert runner.retry_delay(1, None) == 4.0
    assert runner.retry_delay(9, None) == 32.0
    assert runner.retry_delay(1, "7") == 7.0
    assert runner.retry_delay(1, "Wed, 21 Oct 2015 07:28:00 GMT") == 0.0


def test_model_spec_round_trip() -> None:
    spec = runner.ModelSpec.parse("claude-opus-5-5@reasoning=high")
    assert spec == runner.ModelSpec(id="claude-opus-5-5", params=(("reasoning", "high"),))
    assert runner.ModelSpec.parse(spec.label) == spec
    assert runner.default_model("deep").id


def test_calibration_select_is_stratified_and_deterministic() -> None:
    from splunk_uc.review._ledger import iter_sidecars

    entries = list(iter_sidecars(category="cat-1"))
    first = calibration.select_calibration_set(entries, size=40, min_verified=5, human_sample=10, seed=7)
    second = calibration.select_calibration_set(entries, size=40, min_verified=5, human_sample=10, seed=7)
    assert first == second
    assert first["size"] == 40
    assert len({row["category"] for row in first["ucs"]}) >= 5
    assert sum(1 for row in first["ucs"] if row["status"] == "verified") >= 5
    assert len(first["human_spot_check"]) == 10
    template = calibration.human_labels_template(first)
    assert set(template["labels"]) == set(first["human_spot_check"])


def _write(root: Path, tier: str, uc_id: str, findings: list[dict[str, Any]]) -> None:
    write_record(
        record_path(tier, "cat-05-network-infrastructure", uc_id, root=root),
        {"uc_id": uc_id, "findings": findings, "firewalled_field_flags": []},
    )


def test_calibration_score(tmp_path: Path) -> None:
    ref, cand = tmp_path / "ref", tmp_path / "cand"
    _write(ref, "deep", "UC-5.1.1", [
        {"field": "value", "dimension": "specificity", "severity": "major"},
        {"field": "cimModels", "dimension": "correctness", "severity": "blocker"},
    ])
    _write(cand, "triage", "UC-5.1.1", [
        {"field": "value", "dimension": "specificity", "severity": "major"},
        {"field": "app", "dimension": "correctness", "severity": "blocker"},
    ])
    result = calibration.score_candidate(reference_root=ref, candidate_root=cand)
    assert result["recall"] == 0.5
    assert result["false_blocker_rate"] == 1.0
    assert result["passed"] is False

    labels = {"labels": {"UC-5.1.1": {"checked": True, "reject": [{"field": "cimModels", "dimension": "correctness"}], "add": [{"field": "app", "dimension": "correctness"}]}}}
    result = calibration.score_candidate(reference_root=ref, candidate_root=cand, human_labels=labels)
    assert result["recall"] == 1.0
    assert result["false_blocker_rate"] == 0.0
    assert result["passed"] is True


def _load_cli() -> Any:
    spec = importlib.util.spec_from_file_location("uc_review_runner", REPO_ROOT / "scripts" / "uc_review_runner.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_cli_dry_run_triage(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    cli = _load_cli()
    rc = cli.main(["--root", str(tmp_path), "triage", "--subcategory", "15.1", "--category", "cat-15", "--dry-run", "--limit", "1"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["calls"] == 1
    assert payload["ucs"] == 8


def test_cli_requires_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    cli = _load_cli()
    rc = cli.main(["--root", str(tmp_path), "deep", "--uc", "UC-15.1.1"])
    assert rc == 1
    assert "CURSOR_API_KEY" in capsys.readouterr().err
