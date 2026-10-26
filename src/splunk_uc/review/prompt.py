"""``review-prompt`` verb — emit the deterministic review prompt for one tier.

Pure function: reads sidecars, the deterministic ledger and grounding
documents, prints the prompt. No model calls. ``scripts/uc_review_runner.py``
imports ``build_prompt`` directly; the CLI exists so a maintainer can
inspect or hand-run any prompt.

Usage::

    python -m splunk_uc review-prompt UC-5.1.1 --tier deep
    python -m splunk_uc review-prompt --batch 5.1 --tier triage --limit 8
    python -m splunk_uc review-prompt UC-22.1.4 --tier adjudication --prior reports/uc-review/deep/cat-22-regulatory-compliance/UC-22.1.4.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from splunk_uc.review._grounding import build_grounding, subcategory_id
from splunk_uc.review._ledger import (
    CONTENT_DIR,
    DETERMINISTIC_LEDGER,
    REPO_ROOT,
    RUBRIC_VERSION,
    content_sha256,
    iter_sidecars,
    load_record,
    uc_id_of,
)

RUBRIC_DOC = REPO_ROOT / "docs" / "uc-text-review-rubric.md"
RUBRIC_BEGIN = "<!-- rubric:begin -->"
RUBRIC_END = "<!-- rubric:end -->"

TIER_SETTINGS: dict[str, dict[str, int]] = {
    "triage": {"max_guide_chars": 4000, "sibling_limit": 25},
    "deep": {"max_guide_chars": 14000, "sibling_limit": 60},
    "adjudication": {"max_guide_chars": 14000, "sibling_limit": 40},
}
DEFAULT_BATCH_SIZE = 8
STRIP_FIELDS = ("$schema",)

TIER_INSTRUCTIONS = {
    "triage": """# TASK — TRIAGE REVIEW

Review each of the {count} use cases below against the rubric. Work quickly
but do not guess: when a fact looks wrong and the grounding does not settle
it, record `needs_verification`. Your output decides which UCs get a deep
review, so flag every `correctness` concern you see and lower `confidence`
when you are unsure.""",
    "deep": """# TASK — DEEP CORRECTNESS REVIEW

Review the use case below against the rubric, with particular care for the
`correctness` and `consistency` dimensions. Check every product fact: add-on
names and Splunkbase IDs, sourcetypes, field names, event codes, API paths,
CIM datamodel fit, UI paths, RBAC roles, versions, vendor behaviour. Use the
grounding documents first. If you can browse, confirm facts against vendor or
Splunk documentation and cite the URL in `evidence_url`. A `correctness`
blocker without `evidence_url` or `evidence_ref` will be downgraded to
`needs_verification` automatically.""",
    "adjudication": """# TASK — SECOND-OPINION ADJUDICATION

Another reviewer ({prior_model}, tier `{prior_tier}`) marked the findings
listed under PRIOR BLOCKERS as `blocker`. Re-examine the use case and decide,
for each one, whether it is a real factual error. Produce your own complete
review record. Keep a prior finding (same field and dimension) only if you
independently agree it is wrong; set `adjudicates.agrees` to true when you
agree with every prior blocker and false otherwise. Cite evidence for every
blocker you keep.""",
}

OUTPUT_CONTRACT = """# OUTPUT

Return exactly one fenced ```json block and nothing else. Shape:

```json
{{
  "reviews": [
    {{
      "uc_id": "UC-X.Y.Z",
      "verdict": "ok | polish | rewrite | incorrect",
      "confidence": 0.0,
      "scores": {{"clarity": 1, "specificity": 1, "consistency": 1, "correctness": 1, "grandma_fidelity": 1, "overclaiming": 1}},
      "summary": "One or two sentences on the UC's overall text quality.",
      "findings": [
        {{"field": "...", "dimension": "clarity | specificity | consistency | correctness | grandma_fidelity | overclaiming | spelling", "severity": "blocker | major | minor | needs_verification", "quote": "...", "explanation": "...", "suggested_fix": "...", "evidence_url": "https://... (optional)", "evidence_ref": "docs/guides/... (optional)", "confidence": 0.0}}
      ],
      "firewalled_field_flags": [
        {{"field": "spl | cimSpl | compliance | monitoringType | splunkPillar | criticality | difficulty | title | id | mitreAttack", "issue": "...", "severity": "blocker | major | minor | needs_verification", "evidence_url": "https://... (optional)", "evidence_ref": "docs/... (optional)"}}
      ]{adjudicates}
    }}
  ]
}}
```

Rules:
* One entry in `reviews` per UC, in the order given: {uc_ids}.
* Omit optional keys rather than sending empty strings.
* Do not repeat deterministic findings; they are already recorded.
* Do not propose edits to firewalled fields under `findings`.
* A blocker in `firewalled_field_flags` needs `evidence_url` or `evidence_ref` too (for SPL behaviour, cite the Splunk Search Reference page)."""

ADJUDICATES_SNIPPET = """,
      "adjudicates": {{"tier": "{prior_tier}", "model": "{prior_model}", "agrees": true}}"""


def load_rubric_text(path: Path = RUBRIC_DOC) -> str:
    text = path.read_text(encoding="utf-8")
    try:
        start = text.index(RUBRIC_BEGIN) + len(RUBRIC_BEGIN)
        end = text.index(RUBRIC_END)
    except ValueError as exc:
        raise RuntimeError(f"{path} is missing the rubric markers") from exc
    return text[start:end].strip()


def deterministic_index(
    uc_ids: Iterable[str], *, ledger_path: Path = DETERMINISTIC_LEDGER
) -> dict[str, dict[str, Any]]:
    """Stored deterministic records for ``uc_ids`` (scans the JSONL once)."""
    wanted = set(uc_ids)
    found: dict[str, dict[str, Any]] = {}
    if not wanted or not ledger_path.is_file():
        return found
    needles = {f'"uc_id": "{uid}"': uid for uid in wanted}
    with ledger_path.open(encoding="utf-8") as fh:
        for line in fh:
            match = re.search(r'"uc_id": "UC-[\d.]+"', line)
            if match and match.group(0) in needles:
                found[needles[match.group(0)]] = json.loads(line)
                if len(found) == len(wanted):
                    break
    return found


def deterministic_findings_for(
    path: Path, uc: dict[str, Any], index: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Deterministic record for one UC, recomputed (without clusters) when the ledger is stale."""
    record = index.get(uc_id_of(uc))
    if record and record.get("content_sha256") == content_sha256(uc):
        return record
    from splunk_uc.audits import text_quality

    return text_quality.review_uc(
        path,
        uc,
        skeleton_index=None,
        min_cluster=50,
        spelling=text_quality.load_spelling_dictionary(),
    )


def _compact_deterministic(record: dict[str, Any]) -> list[dict[str, str]]:
    rows = [
        {"field": f["field"], "severity": f["severity"], "check": f.get("check", "")}
        for f in record.get("findings", [])
    ]
    rows += [
        {"field": f["field"], "severity": f["severity"], "check": "firewalled"}
        for f in record.get("firewalled_field_flags", [])
    ]
    return rows


def _sidecar_for_prompt(uc: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in uc.items() if k not in STRIP_FIELDS}


def _prior_blockers(prior: dict[str, Any]) -> list[dict[str, Any]]:
    keep = (
        "field",
        "dimension",
        "severity",
        "quote",
        "explanation",
        "evidence_url",
        "evidence_ref",
    )
    blockers = [
        {k: f[k] for k in keep if k in f}
        for f in prior.get("findings", [])
        if f.get("severity") == "blocker"
    ]
    blockers += [
        {k: f[k] for k in ("field", "issue", "severity", "evidence_url", "evidence_ref") if k in f}
        for f in prior.get("firewalled_field_flags", [])
        if f.get("severity") == "blocker"
    ]
    return blockers


def build_prompt(
    tier: str,
    entries: list[tuple[Path, dict[str, Any]]],
    *,
    ledger_path: Path = DETERMINISTIC_LEDGER,
    prior: dict[str, Any] | None = None,
    max_guide_chars: int | None = None,
    sibling_limit: int | None = None,
) -> str:
    """Render the review prompt for ``entries`` (one UC unless ``tier == 'triage'``)."""
    if tier not in TIER_SETTINGS:
        raise ValueError(f"unknown tier {tier!r}")
    if not entries:
        raise ValueError("no UCs to review")
    if tier != "triage" and len(entries) != 1:
        raise ValueError(f"tier {tier!r} reviews exactly one UC per prompt")
    if tier == "triage" and len({subcategory_id(uc) for _, uc in entries}) != 1:
        raise ValueError("a triage batch must come from a single subcategory")
    if tier == "adjudication" and not prior:
        raise ValueError("adjudication needs the prior record (--prior)")

    settings = TIER_SETTINGS[tier]
    grounding = build_grounding(
        entries,
        max_guide_chars=settings["max_guide_chars"] if max_guide_chars is None else max_guide_chars,
        sibling_limit=settings["sibling_limit"] if sibling_limit is None else sibling_limit,
    )
    uc_ids = [uc_id_of(uc) for _, uc in entries]
    index = deterministic_index(uc_ids, ledger_path=ledger_path)

    prior_model = str((prior or {}).get("model", ""))
    prior_tier = str((prior or {}).get("tier", ""))
    parts = [
        "You are a senior Splunk content reviewer for a public catalogue of monitoring use cases.",
        f"Rubric version {RUBRIC_VERSION}.",
        TIER_INSTRUCTIONS[tier].format(
            count=len(entries), prior_model=prior_model, prior_tier=prior_tier
        ),
        load_rubric_text(),
        "# GROUNDING (repository documents; treat as more reliable than the UC text)",
        "```json\n" + json.dumps(grounding, indent=2, ensure_ascii=False) + "\n```",
    ]
    if prior:
        parts += [
            "# PRIOR BLOCKERS",
            "```json\n"
            + json.dumps(_prior_blockers(prior), indent=2, ensure_ascii=False)
            + "\n```",
        ]
    for path, uc in entries:
        det = deterministic_findings_for(path, uc, index)
        parts += [
            f"# USE CASE {uc_id_of(uc)}",
            "## Deterministic findings (already recorded — do not repeat)",
            "```json\n"
            + json.dumps(_compact_deterministic(det), indent=2, ensure_ascii=False)
            + "\n```",
            "## Sidecar",
            "```json\n"
            + json.dumps(_sidecar_for_prompt(uc), indent=2, ensure_ascii=False)
            + "\n```",
        ]
    adjudicates = (
        ADJUDICATES_SNIPPET.format(prior_tier=prior_tier, prior_model=prior_model)
        if tier == "adjudication"
        else ""
    )
    parts.append(OUTPUT_CONTRACT.format(uc_ids=", ".join(uc_ids), adjudicates=adjudicates))
    return "\n\n".join(parts) + "\n"


def _id_key(uc: dict[str, Any]) -> list[int]:
    return [int(x) for x in str(uc.get("id", "")).split(".") if x.isdigit()]


def iter_batches(
    entries: Iterable[tuple[Path, dict[str, Any]]],
    *,
    size: int = DEFAULT_BATCH_SIZE,
) -> list[list[tuple[Path, dict[str, Any]]]]:
    """Group sidecars into triage batches of at most ``size``, never crossing a subcategory."""
    by_sub: dict[tuple[str, str], list[tuple[Path, dict[str, Any]]]] = {}
    for path, uc in entries:
        by_sub.setdefault((path.parent.name, subcategory_id(uc)), []).append((path, uc))
    batches: list[list[tuple[Path, dict[str, Any]]]] = []
    for key in sorted(
        by_sub, key=lambda k: (k[0], [int(x) for x in k[1].split(".") if x.isdigit()])
    ):
        members = sorted(by_sub[key], key=lambda e: _id_key(e[1]))
        for start in range(0, len(members), size):
            batches.append(members[start : start + size])
    return batches


def resolve_uc(uc_id: str, *, content_dir: Path = CONTENT_DIR) -> tuple[Path, dict[str, Any]]:
    bare = uc_id.removeprefix("UC-")
    matches = list(content_dir.glob(f"cat-*/UC-{bare}.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"cannot resolve {uc_id} under {content_dir}")
    path = matches[0]
    return path, json.loads(path.read_text(encoding="utf-8"))


def select_batch(sub_id: str, *, offset: int, limit: int) -> list[tuple[Path, dict[str, Any]]]:
    cat_num = sub_id.split(".", 1)[0]
    category = f"cat-{int(cat_num):02d}"
    members = [
        (path, uc) for path, uc in iter_sidecars(category=category) if subcategory_id(uc) == sub_id
    ]
    members.sort(key=lambda e: _id_key(e[1]))
    return members[offset : offset + limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc review-prompt",
        description="Emit the review prompt for one tier (no model calls).",
    )
    parser.add_argument("uc_ids", nargs="*", help="UC identifiers, e.g. UC-5.1.1")
    parser.add_argument("--tier", choices=sorted(TIER_SETTINGS), default="triage")
    parser.add_argument("--batch", help="Subcategory id for a triage batch, e.g. 5.1")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--prior", type=Path, help="Prior review record (adjudication tier)")
    parser.add_argument("--ledger", type=Path, default=DETERMINISTIC_LEDGER)
    parser.add_argument("--max-guide-chars", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="Emit {uc_ids, tier, prompt} as JSON")
    args = parser.parse_args(argv)

    try:
        if args.batch:
            entries = select_batch(args.batch, offset=args.offset, limit=args.limit)
        else:
            entries = [resolve_uc(uid) for uid in args.uc_ids]
        prior = load_record(args.prior) if args.prior else None
        prompt = build_prompt(
            args.tier,
            entries,
            ledger_path=args.ledger,
            prior=prior,
            max_guide_chars=args.max_guide_chars,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"review-prompt: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "tier": args.tier,
                    "uc_ids": [uc_id_of(uc) for _, uc in entries],
                    "prompt": prompt,
                },
                ensure_ascii=False,
            )
        )
    else:
        sys.stdout.write(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
