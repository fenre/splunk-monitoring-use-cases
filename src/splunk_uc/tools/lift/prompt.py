"""``lift-prompt`` verb — emit the deterministic AI prompt for one UC.

The prompt is consumed by an orchestration agent (Cursor session or
equivalent) that dispatches a ``Task`` subagent per UC. The CLI itself
is pure-function: no AI, no subprocess, no network — it only reads
the sidecar and gap report from disk and prints the rendered prompt
to stdout.

Usage:
    python -m splunk_uc lift-prompt UC-X.Y.Z
    python -m splunk_uc lift-prompt UC-X.Y.Z --target-tier gold
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    TargetTier,
    load_sidecar,
    resolve_sidecar_path,
    score_uc,
)

PROMPT_TEMPLATE = """You are a Splunk content-quality author. Your job: lift the depth of
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
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc lift-prompt",
        description=(
            "Emit the deterministic AI prompt for one UC. The output is "
            "consumed by an orchestration agent that dispatches a Task "
            "subagent per UC."
        ),
    )
    parser.add_argument("uc_id", help="UC identifier, e.g. UC-15.1.1")
    parser.add_argument(
        "--target-tier",
        default="silver",
        choices=["silver", "gold", "gold-v2"],
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
    try:
        sidecar_path = resolve_sidecar_path(args.uc_id, content_root=args.content_root)
        target_tier = TargetTier.from_str(args.target_tier)
        report = score_uc(sidecar_path, target_tier=target_tier)
        sidecar_data = load_sidecar(sidecar_path)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"lift-prompt: {exc}", file=sys.stderr)
        return 1

    sidecar_json = json.dumps(sidecar_data, indent=2, sort_keys=True)
    gap_json = json.dumps(report.to_json(), indent=2, sort_keys=True)
    print(
        PROMPT_TEMPLATE.format(
            uc_id=args.uc_id,
            target_tier=target_tier.value,
            sidecar_json=sidecar_json,
            gap_json=gap_json,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
