#!/usr/bin/env python3
"""Headless runner for the UC text-quality review (Cursor Python SDK).

Dispatches review prompts (``python -m splunk_uc review-prompt``) to models,
validates the replies against ``schemas/v2/uc-review-finding.schema.json``,
and writes one record per UC under ``reports/uc-review/<tier>/<cat>/``.
Records are keyed on content hash and rubric version, so reruns skip UCs that
have not changed. Every model call appends a line (tokens, cost, run id) to
``reports/uc-review/run-log.jsonl``.

Requires ``pip install cursor-sdk`` and ``CURSOR_API_KEY``. ``--dry-run``
needs neither: it renders every prompt and reports sizes.

Subcommands::

    models                       list model IDs / parameters for this account
    status                       record counts per tier and category
    triage   [--category cat-NN] [--subcategory X.Y] [--limit N]
    route    [--category cat-NN] print which UCs the deep tier would take, and why
    deep     [--category cat-NN] [--uc UC-X.Y.Z ...]
    adjudicate [--category cat-NN]
    calibrate select             write the stratified 150-UC calibration set
    calibrate run --tier deep|triage [--model ID]
    calibrate score --candidate-model ID
    export   --tier T --out DIR  write prompts + manifest for an out-of-band model run
    ingest   --manifest DIR/manifest.json --model LABEL
    plan                         write reports/uc-review/full-run-plan.json (sizes, order, commands)

Examples::

    python3 scripts/uc_review_runner.py triage --category cat-15 --dry-run
    python3 scripts/uc_review_runner.py triage --category cat-15
    python3 scripts/uc_review_runner.py deep --category cat-15
    python3 scripts/uc_review_runner.py calibrate run --tier triage --model gemini-3.7-flash@reasoning=medium
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.review import _calibration as calibration
from splunk_uc.review import _runner as runner
from splunk_uc.review._ledger import (
    MODEL_TIERS,
    REVIEW_ROOT,
    iter_sidecars,
    iter_tier_records,
    uc_id_of,
)
from splunk_uc.review.prompt import resolve_uc


def _model(args: argparse.Namespace, tier: str, config: dict[str, Any]) -> runner.ModelSpec:
    if getattr(args, "model", None):
        return runner.ModelSpec.parse(args.model)
    return runner.default_model(tier, config=config)


def _entries(args: argparse.Namespace) -> list[runner.Entry]:
    if getattr(args, "uc", None):
        return [resolve_uc(uid) for uid in args.uc]
    if getattr(args, "uc_list", None):
        payload = json.loads(Path(args.uc_list).read_text(encoding="utf-8"))
        ids = [
            row["uc_id"] if isinstance(row, dict) else row for row in payload.get("ucs", payload)
        ]
        return [resolve_uc(uid) for uid in ids]
    entries = list(iter_sidecars(category=getattr(args, "category", None)))
    sub = getattr(args, "subcategory", None)
    if sub:
        prefix = f"{sub}."
        entries = [(p, uc) for p, uc in entries if str(uc.get("id", "")).startswith(prefix)]
    return entries


def _progress(done: int, total: int, outcome: runner.BatchOutcome) -> None:
    status = ", ".join(sorted({line.get("status", "") for line in outcome.log})) or "-"
    failed = f" failed={len(outcome.failed)}" if outcome.failed else ""
    print(f"[{done}/{total}] wrote={len(outcome.written)}{failed} ({status})", file=sys.stderr)


async def _execute(
    tier: str,
    jobs: list[tuple[list[runner.Entry], dict[str, Any] | None]],
    *,
    model: runner.ModelSpec,
    concurrency: int,
    root: Path,
    dry_run: bool,
) -> runner.BatchOutcome:
    if dry_run:

        class _NoInvoker:
            async def __call__(
                self, prompt: str, *, model: runner.ModelSpec, name: str
            ) -> runner.InvokeResult:
                raise AssertionError("dry run must not invoke a model")

        return await runner.run_jobs(
            _NoInvoker(), tier, jobs, model=model, concurrency=concurrency, root=root, dry_run=True
        )
    async with runner.SdkInvoker(api_key=runner.api_key_from_env()) as invoker:
        return await runner.run_jobs(
            invoker,
            tier,
            jobs,
            model=model,
            concurrency=concurrency,
            root=root,
            dry_run=False,
            on_progress=_progress,
        )


def _report(outcome: runner.BatchOutcome, *, dry_run: bool) -> int:
    if dry_run:
        sizes = [line["prompt_chars"] for line in outcome.log]
        ucs = sum(len(line["uc_ids"]) for line in outcome.log)
        print(
            json.dumps(
                {
                    "calls": len(sizes),
                    "ucs": ucs,
                    "prompt_chars_total": sum(sizes),
                    "prompt_chars_max": max(sizes, default=0),
                    "approx_input_tokens": sum(sizes) // 4,
                },
                indent=2,
            )
        )
        return 0
    usage = Counter()
    cents = 0.0
    for line in outcome.log:
        for key, value in (line.get("usage") or {}).items():
            if key == "charged_cents" and isinstance(value, (int, float)):
                cents += value
            elif isinstance(value, int):
                usage[key] += value
    print(
        json.dumps(
            {
                "written": len(outcome.written),
                "failed": len(outcome.failed),
                "failures": dict(sorted(outcome.failed.items())[:50]),
                "usage": dict(usage),
                "charged_cents": round(cents, 2),
            },
            indent=2,
        )
    )
    return 1 if outcome.failed else 0


def cmd_models(args: argparse.Namespace, config: dict[str, Any]) -> int:
    from cursor_sdk import Cursor

    models = Cursor.models.list(api_key=runner.api_key_from_env())
    for model in models:
        params = ", ".join(
            f"{p.id}={'|'.join(str(v.value) for v in (getattr(p, 'values', None) or []))}"
            for p in (model.parameters or [])
        )
        print(f"{model.id}\t{model.display_name}\t{params}")
    print("\nConfigured defaults (config/uc-review-models.json):", file=sys.stderr)
    for tier in MODEL_TIERS:
        print(f"  {tier}: {runner.default_model(tier, config=config).label}", file=sys.stderr)
    return 0


def cmd_status(args: argparse.Namespace, config: dict[str, Any]) -> int:
    root = Path(args.root)
    totals = Counter(p.parent.name for p, _ in iter_sidecars())
    table: dict[str, dict[str, int]] = {cat: {"ucs": n} for cat, n in sorted(totals.items())}
    verdicts: Counter[str] = Counter()
    for tier in MODEL_TIERS:
        for record in iter_tier_records(tier, root=root):
            cat = record.get("file", "/").split("/")[1]
            table.setdefault(cat, {"ucs": 0})
            table[cat][tier] = table[cat].get(tier, 0) + 1
            verdicts[f"{tier}:{record.get('verdict')}"] += 1
    print(json.dumps({"by_category": table, "verdicts": dict(sorted(verdicts.items()))}, indent=2))
    return 0


def cmd_triage(args: argparse.Namespace, config: dict[str, Any]) -> int:
    return _run_tier(args, config, "triage")


def _routed(
    args: argparse.Namespace, tier: str
) -> list[tuple[runner.Entry, list[str], dict[str, Any] | None]]:
    root = Path(args.root)
    entries = _entries(args)
    if tier == "deep" and (getattr(args, "uc", None) or getattr(args, "all", False)):
        return [
            ((p, uc), ["explicit selection"], None)
            for p, uc in entries
            if runner.needs_review(p, uc, "deep", root=root, force=args.force)
        ]
    return runner.select_for_tier(tier, entries, root=root, force=args.force)


def _jobs(
    args: argparse.Namespace, tier: str, config: dict[str, Any]
) -> list[tuple[list[runner.Entry], dict[str, Any] | None]]:
    if tier == "triage":
        batches = runner.triage_batches(
            _entries(args),
            batch_size=getattr(args, "batch_size", None) or config.get("batch_size", 8),
            root=Path(args.root),
            force=args.force,
        )
        jobs = [(b, None) for b in batches]
    else:
        jobs = [([entry], prior) for entry, _, prior in _routed(args, tier)]
    return jobs[: args.limit] if args.limit else jobs


def cmd_export(args: argparse.Namespace, config: dict[str, Any]) -> int:
    jobs = _jobs(args, args.tier, config)
    if not jobs:
        print(f"export: nothing to review for tier {args.tier}", file=sys.stderr)
        return 0
    manifest = runner.export_jobs(args.tier, jobs, out_dir=Path(args.out), root=Path(args.root))
    print(
        f"Wrote {len(manifest['jobs'])} {args.tier} prompts to {args.out}/ "
        f"({sum(len(j['uc_ids']) for j in manifest['jobs'])} UCs)",
        file=sys.stderr,
    )
    return 0


def cmd_plan(args: argparse.Namespace, config: dict[str, Any]) -> int:
    """Render every outstanding deep prompt (no model calls) and write the full-run plan."""
    from splunk_uc.review.prompt import build_prompt

    root = Path(args.root)
    by_category: dict[str, list[runner.Entry]] = {}
    for path, uc in iter_sidecars():
        by_category.setdefault(path.parent.name, []).append((path, uc))

    rows = []
    for category, entries in by_category.items():
        pending = [
            (p, uc)
            for p, uc in entries
            if runner.needs_review(p, uc, "deep", root=root, force=False)
        ]
        chars = sum(len(build_prompt("deep", [entry])) for entry in pending)
        critical = sum(1 for _, uc in entries if uc.get("criticality") == "critical")
        verified = sum(1 for _, uc in entries if uc.get("status") == "verified")
        rows.append(
            {
                "category": category,
                "ucs": len(entries),
                "deep_reviewed": len(entries) - len(pending),
                "deep_pending": len(pending),
                "critical": critical,
                "verified": verified,
                "prompt_chars": chars,
                "approx_input_tokens": chars // 4,
                "command": f"python3 scripts/uc_review_runner.py deep --all --category {category[:6]}",
            }
        )
    rows.sort(
        key=lambda r: (
            r["category"].startswith("cat-25-"),
            -(r["critical"] + r["verified"]) / max(1, r["ucs"]),
            r["category"],
        )
    )
    total_tokens = sum(r["approx_input_tokens"] for r in rows)
    plan = {
        "$comment": (
            "Full-run plan for the UC review deep tier (scripts/uc_review_runner.py plan). "
            "Order: categories with the highest share of critical + verified UCs first, cat-25 last; "
            "within a category the runner orders UCs critical, verified, high, medium, low. "
            "Token counts are prompt characters / 4 and exclude model output and tool use."
        ),
        "deep_model": runner.default_model("deep", config=config).label,
        "adjudication_model": runner.default_model("adjudication", config=config).label,
        "ucs": sum(r["ucs"] for r in rows),
        "deep_pending": sum(r["deep_pending"] for r in rows),
        "approx_input_tokens": total_tokens,
        "categories": rows,
        "after_each_category": [
            "python3 scripts/uc_review_runner.py adjudicate --category cat-NN",
            "python3 -m splunk_uc generate-uc-review-report",
        ],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {out}: {plan['deep_pending']} UCs pending deep review, "
        f"~{total_tokens / 1e6:.1f}M input tokens",
        file=sys.stderr,
    )
    return 0


def cmd_ingest(args: argparse.Namespace, config: dict[str, Any]) -> int:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    outcome = runner.ingest_replies(manifest, model=runner.ModelSpec.parse(args.model))
    return _report(outcome, dry_run=False)


def cmd_route(args: argparse.Namespace, config: dict[str, Any]) -> int:
    rows = _routed(args, args.tier)
    reasons = Counter(r for _, rs, _ in rows for r in rs)
    payload = {
        "tier": args.tier,
        "count": len(rows),
        "reasons": dict(reasons.most_common()),
        "ucs": [{"uc_id": uc_id_of(e[1]), "reasons": rs} for e, rs, _ in rows],
    }
    print(json.dumps(payload, indent=2))
    return 0


def _run_tier(args: argparse.Namespace, config: dict[str, Any], tier: str) -> int:
    jobs = _jobs(args, tier, config)
    if not jobs:
        print(f"{tier}: nothing to review (all records current)", file=sys.stderr)
        return 0
    outcome = asyncio.run(
        _execute(
            tier,
            jobs,
            model=_model(args, tier, config),
            concurrency=args.concurrency or config["concurrency"][tier],
            root=Path(args.root),
            dry_run=args.dry_run,
        )
    )
    return _report(outcome, dry_run=args.dry_run)


def cmd_deep(args: argparse.Namespace, config: dict[str, Any]) -> int:
    return _run_tier(args, config, "deep")


def cmd_adjudicate(args: argparse.Namespace, config: dict[str, Any]) -> int:
    return _run_tier(args, config, "adjudication")


def _model_slug(spec: runner.ModelSpec) -> str:
    return spec.label.replace("@", "__").replace("=", "-").replace(",", "_").replace("/", "-")


def cmd_calibrate(args: argparse.Namespace, config: dict[str, Any]) -> int:
    cal_root = calibration.CALIBRATION_ROOT
    if args.action == "select":
        selected = calibration.select_calibration_set(
            iter_sidecars(), size=args.size, seed=args.seed, human_sample=args.human_sample
        )
        cal_root.mkdir(parents=True, exist_ok=True)
        calibration.SET_PATH.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
        if not calibration.HUMAN_LABELS_PATH.exists() or args.force:
            calibration.HUMAN_LABELS_PATH.write_text(
                json.dumps(calibration.human_labels_template(selected), indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            f"Wrote {calibration.SET_PATH.relative_to(REPO_ROOT)} ({selected['size']} UCs)",
            file=sys.stderr,
        )
        return 0

    selected = calibration.load_json(calibration.SET_PATH)
    uc_ids = [row["uc_id"] for row in selected["ucs"]]

    if args.action == "run":
        tier = args.tier
        spec = _model(args, tier, config)
        root = cal_root / ("reference" if tier == "deep" else _model_slug(spec))
        entries = [resolve_uc(uid) for uid in uc_ids]
        if tier == "triage":
            jobs = [
                (b, None)
                for b in runner.triage_batches(
                    entries, batch_size=config.get("batch_size", 8), root=root, force=args.force
                )
            ]
        else:
            jobs = [
                ([(p, uc)], None)
                for p, uc in entries
                if runner.needs_review(p, uc, "deep", root=root, force=args.force)
            ]
        outcome = asyncio.run(
            _execute(
                tier,
                jobs,
                model=spec,
                concurrency=args.concurrency or config["concurrency"][tier],
                root=root,
                dry_run=args.dry_run,
            )
        )
        return _report(outcome, dry_run=args.dry_run)

    if args.action == "score":
        spec = runner.ModelSpec.parse(args.candidate_model)
        labels = (
            calibration.load_json(calibration.HUMAN_LABELS_PATH)
            if calibration.HUMAN_LABELS_PATH.is_file()
            else None
        )
        result = calibration.score_candidate(
            reference_root=cal_root / "reference",
            candidate_root=cal_root / _model_slug(spec),
            uc_ids=uc_ids,
            human_labels=labels,
        )
        result["candidate_model"] = spec.label
        out = cal_root / f"score-{_model_slug(spec)}.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uc_review_runner.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root", default=str(REVIEW_ROOT), help="Ledger root (default reports/uc-review)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser, *, scope: bool = True) -> None:
        p.add_argument(
            "--model", help="Model id or id@param=value,... (default: config/uc-review-models.json)"
        )
        p.add_argument("--concurrency", type=int, default=None)
        p.add_argument("--limit", type=int, default=None, help="Stop after N calls")
        p.add_argument(
            "--force", action="store_true", help="Re-review even when records are current"
        )
        p.add_argument("--dry-run", action="store_true", help="Render prompts only; no model calls")
        if scope:
            p.add_argument("--category", help="Category prefix, e.g. cat-15")
            p.add_argument("--subcategory", help="Subcategory id, e.g. 15.1")
            p.add_argument("--uc", nargs="*", help="Explicit UC ids")
            p.add_argument(
                "--uc-list", help="JSON file with a 'ucs' list (e.g. the calibration set)"
            )

    sub.add_parser("models", help="List models available to this API key")
    sub.add_parser("status", help="Record counts per tier and category")

    p = sub.add_parser("triage", help="Fast-model review of every stale UC, batched by subcategory")
    common(p)
    p.add_argument("--batch-size", type=int, default=None)

    p = sub.add_parser("route", help="Show the UCs a tier would take, with reasons")
    common(p)
    p.add_argument("--tier", choices=["deep", "adjudication"], default="deep")

    p = sub.add_parser("deep", help="Heavy-model review of routed UCs")
    common(p)
    p.add_argument(
        "--all", action="store_true", help="Review every selected UC, not only routed ones"
    )

    p = sub.add_parser("adjudicate", help="Second-opinion review of deep-review blockers")
    common(p)

    p = sub.add_parser("export", help="Write prompts + manifest for an out-of-band model run")
    common(p)
    p.add_argument("--tier", choices=list(MODEL_TIERS), required=True)
    p.add_argument(
        "--out", required=True, help="Output directory for prompt files and manifest.json"
    )
    p.add_argument(
        "--all", action="store_true", help="deep tier: every selected UC, not only routed ones"
    )
    p.add_argument("--batch-size", type=int, default=None)

    p = sub.add_parser("plan", help="Render outstanding deep prompts and write the full-run plan")
    p.add_argument("--out", default=str(REVIEW_ROOT / "full-run-plan.json"))

    p = sub.add_parser("ingest", help="Validate and persist reply files from an export manifest")
    p.add_argument("--manifest", required=True)
    p.add_argument("--model", required=True, help="Label of the model that wrote the replies")

    p = sub.add_parser("calibrate", help="Calibration set selection, runs and scoring")
    p.add_argument("action", choices=["select", "run", "score"])
    common(p, scope=False)
    p.add_argument("--tier", choices=["deep", "triage"], default="deep")
    p.add_argument("--size", type=int, default=150)
    p.add_argument("--human-sample", type=int, default=40)
    p.add_argument("--seed", type=int, default=20261026)
    p.add_argument("--candidate-model", help="Model label to score (calibrate score)")
    return parser


COMMANDS = {
    "models": cmd_models,
    "status": cmd_status,
    "triage": cmd_triage,
    "route": cmd_route,
    "deep": cmd_deep,
    "adjudicate": cmd_adjudicate,
    "calibrate": cmd_calibrate,
    "export": cmd_export,
    "ingest": cmd_ingest,
    "plan": cmd_plan,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = runner.load_models_config()
    try:
        return COMMANDS[args.command](args, config)
    except RuntimeError as exc:
        print(f"uc_review_runner: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
