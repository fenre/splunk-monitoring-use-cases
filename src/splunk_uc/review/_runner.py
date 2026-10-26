"""Core of ``scripts/uc_review_runner.py``: dispatch review prompts to models.

Everything here is testable without network access: model calls go through
an ``Invoker`` (``SdkInvoker`` in production, a fake in tests). The runner

* builds prompts with ``splunk_uc.review.prompt.build_prompt``,
* calls the model with bounded concurrency and retry on retryable errors,
* parses the fenced JSON reply, completes each record (identity, content
  hash, tier, model, rubric version, run id), applies the evidence rule,
  and validates it against the finding schema,
* retries once with the validation errors appended, then logs the UC as
  ``review_failed``,
* refuses the result if the agent modified a sidecar it was reviewing,
* writes per-UC records and appends one line per call to the run log.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import email.utils
import json
import os
import re
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from splunk_uc.review._ledger import (
    REVIEW_ROOT,
    apply_evidence_rule,
    category_of,
    content_sha256,
    is_current,
    load_record,
    new_record,
    record_path,
    uc_id_of,
    validate_record,
    write_record,
)
from splunk_uc.review._routing import triage_routing_reasons
from splunk_uc.review.prompt import build_prompt, iter_batches

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS_CONFIG = REPO_ROOT / "config" / "uc-review-models.json"
RUN_LOG_NAME = "run-log.jsonl"
MAX_STARTUP_ATTEMPTS = 4
BACKOFF_SECONDS = (4, 8, 16, 32)
JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)

Entry = tuple[Path, dict[str, Any]]


# --------------------------------------------------------------------------
# Model selection
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelSpec:
    id: str
    params: tuple[tuple[str, str], ...] = ()

    @property
    def label(self) -> str:
        if not self.params:
            return self.id
        return self.id + "@" + ",".join(f"{k}={v}" for k, v in self.params)

    @classmethod
    def parse(cls, raw: str) -> ModelSpec:
        """``id`` or ``id@key=value,key=value`` (the form stored in review records)."""
        model_id, _, rest = raw.partition("@")
        params = tuple(
            tuple(pair.split("=", 1))  # type: ignore[misc]
            for pair in rest.split(",")
            if "=" in pair
        )
        return cls(id=model_id.strip(), params=params)

    @classmethod
    def from_config(cls, node: dict[str, Any]) -> ModelSpec:
        params = tuple(sorted((str(k), str(v)) for k, v in (node.get("params") or {}).items()))
        return cls(id=str(node["id"]), params=params)


def load_models_config(path: Path = MODELS_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_model(tier: str, *, config: dict[str, Any] | None = None) -> ModelSpec:
    cfg = config or load_models_config()
    return ModelSpec.from_config(cfg["tiers"][tier])


# --------------------------------------------------------------------------
# Invokers
# --------------------------------------------------------------------------


@dataclass
class InvokeResult:
    status: str
    text: str = ""
    run_id: str = ""
    agent_id: str = ""
    duration_ms: int | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class StartupError(Exception):
    """A model call that never started (auth, config, network)."""

    def __init__(self, message: str, *, retryable: bool, retry_after: str | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


class Invoker(Protocol):
    async def __call__(self, prompt: str, *, model: ModelSpec, name: str) -> InvokeResult: ...


class SdkInvoker:
    """Production invoker on the Cursor Python SDK (local runtime, one shared bridge)."""

    def __init__(self, *, api_key: str, cwd: Path = REPO_ROOT) -> None:
        self.api_key = api_key
        self.cwd = cwd
        self._client: Any = None

    async def __aenter__(self) -> SdkInvoker:
        from cursor_sdk import AsyncClient, LocalAgentOptions

        self._client = await AsyncClient.launch_bridge(
            workspace=str(self.cwd), local=LocalAgentOptions(cwd=str(self.cwd))
        )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __call__(self, prompt: str, *, model: ModelSpec, name: str) -> InvokeResult:
        from cursor_sdk import (
            AgentOptions,
            AsyncAgent,
            CursorAgentError,
            LocalAgentOptions,
            ModelParameterValue,
            ModelSelection,
        )

        selection = ModelSelection(
            id=model.id, params=[ModelParameterValue(id=k, value=v) for k, v in model.params]
        )
        options = AgentOptions(
            model=selection,
            api_key=self.api_key,
            name=name,
            local=LocalAgentOptions(cwd=str(self.cwd)),
        )
        try:
            result = await AsyncAgent.prompt(prompt, options, client=self._client)
        except CursorAgentError as exc:
            raise StartupError(
                str(exc), retryable=bool(exc.is_retryable), retry_after=exc.retry_after
            ) from exc
        usage: dict[str, Any] = {}
        run_usage = getattr(result, "usage", None)
        tokens = getattr(run_usage, "usage", None)
        cost = getattr(run_usage, "cost", None)
        if tokens is not None:
            usage.update(
                {
                    k: getattr(tokens, k)
                    for k in (
                        "input_tokens",
                        "output_tokens",
                        "cache_read_tokens",
                        "cache_write_tokens",
                        "reasoning_tokens",
                        "total_tokens",
                    )
                    if getattr(tokens, k, None) is not None
                }
            )
        if cost is not None:
            usage["charged_cents"] = getattr(cost, "charged_cents", None)
        error = " ".join(str(x) for x in (result.error_code, result.error_message) if x)
        return InvokeResult(
            status=str(result.status),
            text=str(result.result or ""),
            run_id=str(result.id or ""),
            agent_id=str(result.agent_id or ""),
            duration_ms=result.duration_ms,
            usage=usage,
            error=error,
        )


def retry_delay(attempt: int, retry_after: str | None) -> float:
    """Seconds to wait before retry ``attempt`` (1-based), honouring ``retry_after``."""
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            parsed = email.utils.parsedate_to_datetime(retry_after)
            if parsed is not None:
                now = dt.datetime.now(parsed.tzinfo or dt.UTC)
                return max(0.0, (parsed - now).total_seconds())
    return float(BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)])


async def call_with_retry(
    invoker: Invoker,
    prompt: str,
    *,
    model: ModelSpec,
    name: str,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> InvokeResult:
    attempt = 0
    while True:
        attempt += 1
        try:
            return await invoker(prompt, model=model, name=name)
        except StartupError as exc:
            if not exc.retryable or attempt >= MAX_STARTUP_ATTEMPTS:
                return InvokeResult(status="startup_error", error=str(exc))
            await sleep(retry_delay(attempt, exc.retry_after))


# --------------------------------------------------------------------------
# Parsing and record completion
# --------------------------------------------------------------------------


def extract_reviews(text: str) -> list[dict[str, Any]]:
    """The ``reviews`` list from the model reply (last fenced json block, or bare JSON)."""
    blocks = JSON_FENCE_RE.findall(text)
    candidates = [blocks[-1]] if blocks else [text.strip()]
    for raw in candidates:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"reply is not valid JSON: {exc}") from exc
        if isinstance(payload, dict) and isinstance(payload.get("reviews"), list):
            return [r for r in payload["reviews"] if isinstance(r, dict)]
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]
    raise ValueError("reply has no 'reviews' list")


QUOTE_MAX = 500
SUMMARY_MAX = 800


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


MODEL_KEYS = (
    "verdict",
    "confidence",
    "scores",
    "summary",
    "findings",
    "firewalled_field_flags",
    "adjudicates",
)


def complete_record(
    review: dict[str, Any],
    *,
    path: Path,
    uc: dict[str, Any],
    tier: str,
    model: ModelSpec,
    run_id: str,
    reviewed_at: str,
) -> dict[str, Any]:
    record = new_record(uc=uc, path=path, tier=tier, model=model.label)
    for key in MODEL_KEYS:
        if key in review and review[key] not in (None, ""):
            record[key] = review[key]
    record.setdefault("findings", [])
    record.setdefault("firewalled_field_flags", [])
    for finding in record["findings"]:
        if isinstance(finding, dict) and isinstance(finding.get("quote"), str):
            finding["quote"] = _clip(finding["quote"], QUOTE_MAX)
    if isinstance(record.get("summary"), str):
        record["summary"] = _clip(record["summary"], SUMMARY_MAX)
    if tier != "adjudication":
        record.pop("adjudicates", None)
    if run_id:
        record["run_id"] = run_id
    record["reviewed_at"] = reviewed_at
    record = apply_evidence_rule(record)
    if "verdict" in record:
        record["verdict"] = derive_verdict(record)
    return record


def derive_verdict(record: dict[str, Any]) -> str:
    """The rubric's verdict rule, applied after the evidence rule so downgrades count."""
    severities = {f.get("severity") for f in record.get("findings", [])}
    severities |= {f.get("severity") for f in record.get("firewalled_field_flags", [])}
    if "blocker" in severities:
        return "incorrect"
    if "major" in severities:
        return "rewrite"
    if severities & {"minor", "needs_verification"}:
        return "polish"
    scores = record.get("scores") or {}
    if scores and all(isinstance(v, int) and v >= 4 for v in scores.values()):
        return "ok"
    return "polish"


@dataclass
class BatchOutcome:
    written: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    log: list[dict[str, Any]] = field(default_factory=list)


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _shas(entries: Sequence[Entry]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path, _ in entries}


def records_from_reply(
    text: str,
    entries: Sequence[Entry],
    *,
    tier: str,
    model: ModelSpec,
    run_id: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    """Valid records keyed by UC id, plus validation errors per UC id."""
    reviews = extract_reviews(text)
    by_id = {str(r.get("uc_id", "")): r for r in reviews}
    reviewed_at = _now()
    good: dict[str, dict[str, Any]] = {}
    bad: dict[str, list[str]] = {}
    for path, uc in entries:
        uc_id = uc_id_of(uc)
        review = by_id.get(uc_id)
        if review is None:
            bad[uc_id] = ["no review returned for this UC"]
            continue
        record = complete_record(
            review,
            path=path,
            uc=uc,
            tier=tier,
            model=model,
            run_id=run_id,
            reviewed_at=reviewed_at,
        )
        errors = validate_record(record)
        if errors:
            bad[uc_id] = errors
        else:
            good[uc_id] = record
    return good, bad


def repair_prompt(prompt: str, errors: dict[str, list[str]]) -> str:
    lines = ["", "# YOUR PREVIOUS REPLY FAILED VALIDATION", ""]
    for uc_id, errs in sorted(errors.items()):
        lines.append(f"* {uc_id}: " + "; ".join(errs[:6]))
    lines.append("")
    lines.append(
        "Return the complete corrected JSON for every UC, following the OUTPUT section exactly."
    )
    return prompt + "\n".join(lines) + "\n"


async def review_batch(
    invoker: Invoker,
    tier: str,
    entries: Sequence[Entry],
    *,
    model: ModelSpec,
    root: Path = REVIEW_ROOT,
    prior: dict[str, Any] | None = None,
    dry_run: bool = False,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> BatchOutcome:
    """Review one batch (triage) or one UC (deep / adjudication) and persist the records."""
    outcome = BatchOutcome()
    prompt = build_prompt(tier, list(entries), prior=prior)
    uc_ids = [uc_id_of(uc) for _, uc in entries]
    if dry_run:
        outcome.log.append(
            {
                "tier": tier,
                "model": model.label,
                "uc_ids": uc_ids,
                "status": "dry_run",
                "prompt_chars": len(prompt),
            }
        )
        return outcome

    before = _shas(entries)
    name = f"uc-review-{tier}-{uc_ids[0]}"
    pending: dict[str, dict[str, Any]] = {}
    errors: dict[str, list[str]] = {}
    current_prompt = prompt
    for attempt in (1, 2):
        result = await call_with_retry(invoker, current_prompt, model=model, name=name, sleep=sleep)
        log_line: dict[str, Any] = {
            "ts": _now(),
            "tier": tier,
            "model": model.label,
            "uc_ids": uc_ids,
            "attempt": attempt,
            "status": result.status,
            "run_id": result.run_id,
            "agent_id": result.agent_id,
            "duration_ms": result.duration_ms,
            "usage": result.usage,
            "prompt_chars": len(current_prompt),
        }
        if result.error:
            log_line["error"] = result.error[:500]
        if result.status != "finished":
            outcome.log.append(log_line)
            errors = {uid: [f"run status {result.status}: {result.error}"] for uid in uc_ids}
            break
        try:
            good, errors = records_from_reply(
                result.text, entries, tier=tier, model=model, run_id=result.run_id
            )
        except ValueError as exc:
            good, errors = {}, {uid: [str(exc)] for uid in uc_ids if uid not in pending}
        pending.update(good)
        errors = {uid: errs for uid, errs in errors.items() if uid not in pending}
        log_line["valid"] = sorted(good)
        log_line["invalid"] = sorted(errors)
        outcome.log.append(log_line)
        if not errors:
            break
        current_prompt = repair_prompt(prompt, errors)

    after = _shas(entries)
    modified = [str(p) for p in before if before[p] != after[p]]
    if modified:
        for path, data in before.items():
            path.write_bytes(data)
        for uid in uc_ids:
            outcome.failed[uid] = "agent modified a sidecar under review; restored and discarded"
        outcome.log.append(
            {
                "ts": _now(),
                "tier": tier,
                "uc_ids": uc_ids,
                "status": "sidecar_modified",
                "files": modified,
            }
        )
        return outcome

    for path, uc in entries:
        uc_id = uc_id_of(uc)
        record = pending.get(uc_id)
        if record is None:
            outcome.failed[uc_id] = (
                "review_failed: " + "; ".join(errors.get(uc_id, ["unknown"]))[:400]
            )
            continue
        write_record(record_path(tier, category_of(path), uc_id, root=root), record)
        outcome.written.append(uc_id)
    return outcome


def append_run_log(lines: Iterable[dict[str, Any]], *, root: Path = REVIEW_ROOT) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with (root / RUN_LOG_NAME).open("a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------
# Selection: staleness, priority order, routing
# --------------------------------------------------------------------------

CRITICALITY_RANK = {"critical": 0, "high": 2, "medium": 3, "low": 4}


def priority_key(uc: dict[str, Any], path: Path) -> tuple[int, int, str]:
    """Lower sorts first: critical, then verified, then high/medium/low; cat-25 last."""
    rank = CRITICALITY_RANK.get(str(uc.get("criticality")), 5)
    if uc.get("status") == "verified" and rank > 1:
        rank = 1
    last = 1 if category_of(path).startswith("cat-25-") else 0
    return (last, rank, category_of(path))


def needs_review(path: Path, uc: dict[str, Any], tier: str, *, root: Path, force: bool) -> bool:
    if force:
        return True
    existing = load_record(record_path(tier, category_of(path), uc_id_of(uc), root=root))
    return not is_current(existing, sha=content_sha256(uc))


def triage_batches(
    entries: Iterable[Entry], *, batch_size: int, root: Path, force: bool
) -> list[list[Entry]]:
    stale = [(p, uc) for p, uc in entries if needs_review(p, uc, "triage", root=root, force=force)]
    batches = iter_batches(stale, size=batch_size)
    batches.sort(key=lambda b: min(priority_key(uc, p) for p, uc in b))
    return batches


def deep_routing_reasons(
    uc: dict[str, Any], path: Path, triage: dict[str, Any] | None
) -> list[str]:
    reasons: list[str] = []
    if uc.get("criticality") == "critical":
        reasons.append("criticality=critical")
    if uc.get("status") == "verified":
        reasons.append("status=verified")
    if category_of(path).startswith("cat-22-") and uc.get("compliance"):
        reasons.append("cat-22 compliance claim")
    reasons += triage_routing_reasons(triage)
    return reasons


def adjudication_reasons(path: Path, deep: dict[str, Any] | None) -> list[str]:
    if not deep:
        return []
    blockers = [f for f in deep.get("findings", []) if f.get("severity") == "blocker"]
    blockers += [
        f for f in deep.get("firewalled_field_flags", []) if f.get("severity") == "blocker"
    ]
    if not blockers:
        return []
    reasons: list[str] = []
    if category_of(path).startswith("cat-22-"):
        reasons.append("cat-22 blocker")
    low = [
        f
        for f in blockers
        if isinstance(f.get("confidence"), (int, float)) and f["confidence"] < 0.6
    ]
    if low or (isinstance(deep.get("confidence"), (int, float)) and deep["confidence"] < 0.6):
        reasons.append("low-confidence blocker")
    return reasons


def select_for_tier(
    tier: str,
    entries: Iterable[Entry],
    *,
    root: Path,
    force: bool,
) -> list[tuple[Entry, list[str], dict[str, Any] | None]]:
    """``(entry, reasons, prior)`` for every UC the tier should (re-)review."""
    out: list[tuple[Entry, list[str], dict[str, Any] | None]] = []
    for path, uc in entries:
        uc_id = uc_id_of(uc)
        category = category_of(path)
        if tier == "deep":
            triage = load_record(record_path("triage", category, uc_id, root=root))
            reasons = deep_routing_reasons(uc, path, triage)
            prior = None
        elif tier == "adjudication":
            prior = load_record(record_path("deep", category, uc_id, root=root))
            if prior and prior.get("content_sha256") != content_sha256(uc):
                continue
            reasons = adjudication_reasons(path, prior)
        else:
            raise ValueError(f"select_for_tier does not handle {tier!r}")
        if reasons and needs_review(path, uc, tier, root=root, force=force):
            out.append(((path, uc), reasons, prior))
    out.sort(key=lambda row: priority_key(row[0][1], row[0][0]))
    return out


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


async def run_jobs(
    invoker: Invoker,
    tier: str,
    jobs: Sequence[tuple[list[Entry], dict[str, Any] | None]],
    *,
    model: ModelSpec,
    concurrency: int,
    root: Path,
    dry_run: bool,
    on_progress: Callable[[int, int, BatchOutcome], None] | None = None,
) -> BatchOutcome:
    total = BatchOutcome()
    semaphore = asyncio.Semaphore(max(1, concurrency))
    done = 0
    lock = asyncio.Lock()

    async def one(entries: list[Entry], prior: dict[str, Any] | None) -> None:
        nonlocal done
        async with semaphore:
            outcome = await review_batch(
                invoker, tier, entries, model=model, root=root, prior=prior, dry_run=dry_run
            )
        async with lock:
            total.written += outcome.written
            total.failed.update(outcome.failed)
            total.log += outcome.log
            if not dry_run:
                append_run_log(outcome.log, root=root)
            done += 1
            if on_progress:
                on_progress(done, len(jobs), outcome)

    await asyncio.gather(*(one(entries, prior) for entries, prior in jobs))
    return total


# --------------------------------------------------------------------------
# File-based hand-off (export prompts, ingest replies)
# --------------------------------------------------------------------------


def export_jobs(
    tier: str,
    jobs: Sequence[tuple[list[Entry], dict[str, Any] | None]],
    *,
    out_dir: Path,
    root: Path,
) -> dict[str, Any]:
    """Write one prompt file per job plus ``manifest.json`` for out-of-band model runs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (entries, prior) in enumerate(jobs, start=1):
        uc_ids = [uc_id_of(uc) for _, uc in entries]
        job_id = f"{tier}-{index:04d}-{uc_ids[0]}"
        prompt_file = out_dir / f"{job_id}.prompt.md"
        prompt_file.write_text(build_prompt(tier, list(entries), prior=prior), encoding="utf-8")
        rows.append(
            {
                "job": job_id,
                "uc_ids": uc_ids,
                "files": [str(p) for p, _ in entries],
                "prompt": str(prompt_file),
                "reply": str(out_dir / f"{job_id}.reply.md"),
            }
        )
    manifest = {"tier": tier, "root": str(root), "jobs": rows}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def ingest_replies(
    manifest: dict[str, Any],
    *,
    model: ModelSpec,
    root: Path | None = None,
) -> BatchOutcome:
    """Validate and persist reply files listed in an ``export_jobs`` manifest."""
    tier = manifest["tier"]
    ledger_root = root or Path(manifest["root"])
    outcome = BatchOutcome()
    for job in manifest["jobs"]:
        entries: list[Entry] = []
        for raw in job["files"]:
            path = Path(raw)
            entries.append((path, json.loads(path.read_text(encoding="utf-8"))))
        reply_path = Path(job["reply"])
        log_line: dict[str, Any] = {
            "ts": _now(),
            "tier": tier,
            "model": model.label,
            "uc_ids": job["uc_ids"],
            "status": "ingested",
            "run_id": f"file:{job['job']}",
            "usage": {},
        }
        if not reply_path.is_file():
            for uid in job["uc_ids"]:
                outcome.failed[uid] = "no reply file"
            log_line["status"] = "missing_reply"
            outcome.log.append(log_line)
            continue
        try:
            good, errors = records_from_reply(
                reply_path.read_text(encoding="utf-8"),
                entries,
                tier=tier,
                model=model,
                run_id=f"file:{job['job']}",
            )
        except ValueError as exc:
            good, errors = {}, {uid: [str(exc)] for uid in job["uc_ids"]}
        for path, uc in entries:
            uc_id = uc_id_of(uc)
            if uc_id in good:
                write_record(
                    record_path(tier, category_of(path), uc_id, root=ledger_root), good[uc_id]
                )
                outcome.written.append(uc_id)
            else:
                outcome.failed[uc_id] = (
                    "review_failed: " + "; ".join(errors.get(uc_id, ["unknown"]))[:400]
                )
        log_line["valid"] = sorted(good)
        log_line["invalid"] = sorted(errors)
        outcome.log.append(log_line)
    append_run_log(outcome.log, root=ledger_root)
    return outcome


def api_key_from_env() -> str:
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "CURSOR_API_KEY is not set. Create a user or service-account key in the "
            "Cursor dashboard (Integrations) and export it, or add it as a Cloud Agent secret."
        )
    return key
