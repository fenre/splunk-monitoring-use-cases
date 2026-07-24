"""``lift-prompt`` verb — emit the deterministic AI prompt for one UC.

The prompt is consumed by an orchestration agent (Cursor session or
equivalent) that dispatches a ``Task`` subagent per UC. The CLI itself
is pure-function: no AI, no subprocess, no network — it only reads
the sidecar and gap report from disk and prints the rendered prompt
to stdout.

Usage:
    python -m splunk_uc lift-prompt UC-X.Y.Z
    python -m splunk_uc lift-prompt UC-X.Y.Z --target-tier gold-v2 --handcraft
    python -m splunk_uc lift-prompt UC-X.Y.Z --domain-pack personal-hec --anchor-uc UC-25.1.1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from splunk_uc.audits._template_fingerprints import detect_template_flags
from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    TargetTier,
    load_sidecar,
    resolve_sidecar_path,
    score_uc,
)
from splunk_uc.tools.lift._domain_packs import (
    format_pack_excerpt,
    infer_pack_id,
    load_domain_pack,
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

{handcraft_section}
{domain_pack_section}
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
  }},
  "authoring_provenance": {{
    "domain_pack": "{domain_pack_id}",
    "anchor_uc": "{anchor_uc}",
    "template_flags_cleared": ["generic_kfp", "generic_controlTest", "generic_exclusions", "generic_evidence"]
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

HANDCRAFT_SECTION = """# HAND-CRAFT MODE — ANTI-TEMPLATE RULES (mandatory)

The sidecar currently carries bulk-enricher template fingerprints: {template_flags}.

You MUST remove every template fingerprint. Specifically:

* Do NOT reuse CMDB/ServiceNow/operational_exceptions.csv/monitoring_exceptions.csv
  boilerplate unless this UC's SPL and dataSources are enterprise IT ops.
* Do NOT use "On a lab host or staging index" controlTest boilerplate.
* Do NOT use "Does not replace enterprise SIEM correlation" exclusions boilerplate.
* Do NOT use generic `Saved search uc_*` + `index=evidence` evidence stubs.
* Every KFP scenario must name systems/fields from THIS UC's `spl`, `dataSources`, or `app`.
* Lift at least 3 narrative fields with domain-specific prose.
* `authoring_provenance` in the diff is required (for audit trail; not written to sidecar).

"""

DOMAIN_PACK_SECTION = """# DOMAIN PACK REFERENCE ({domain_pack_id})

Adapt scenarios from this pack — customize for the UC title and SPL; never paste verbatim.

{pack_excerpt}

"""


def _build_handcraft_section(flags: list[str]) -> str:
    if not flags:
        return ""
    return HANDCRAFT_SECTION.format(template_flags=", ".join(flags) or "(none detected)")


def _build_domain_pack_section(pack_id: str | None, packs_dir: Path | None) -> tuple[str, str]:
    if not pack_id:
        return "", ""
    pack = load_domain_pack(pack_id, packs_dir=packs_dir)
    if pack is None:
        return "", pack_id
    excerpt = format_pack_excerpt(pack)
    section = DOMAIN_PACK_SECTION.format(domain_pack_id=pack_id, pack_excerpt=excerpt)
    return section, pack_id


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
    parser.add_argument(
        "--handcraft",
        action="store_true",
        help="Inject anti-template rules and template-flag inventory into the prompt.",
    )
    parser.add_argument(
        "--domain-pack",
        default=None,
        help="Domain pack id under data/domain-packs/ (inferred from category when omitted).",
    )
    parser.add_argument(
        "--anchor-uc",
        default=None,
        help="Anchor UC id for provenance metadata (e.g. UC-25.1.1).",
    )
    parser.add_argument(
        "--packs-dir",
        type=Path,
        default=None,
        help="Override domain-packs directory (for tests).",
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

    template_flags = detect_template_flags(sidecar_data) if args.handcraft else []
    handcraft_section = _build_handcraft_section(template_flags) if args.handcraft else ""

    pack_id = args.domain_pack or infer_pack_id(sidecar_path)
    domain_pack_section, resolved_pack = _build_domain_pack_section(pack_id, args.packs_dir)

    sidecar_json = json.dumps(sidecar_data, indent=2, sort_keys=True)
    gap_json = json.dumps(report.to_json(), indent=2, sort_keys=True)
    print(
        PROMPT_TEMPLATE.format(
            uc_id=args.uc_id,
            target_tier=target_tier.value,
            sidecar_json=sidecar_json,
            gap_json=gap_json,
            handcraft_section=handcraft_section,
            domain_pack_section=domain_pack_section,
            domain_pack_id=resolved_pack or "",
            anchor_uc=args.anchor_uc or args.uc_id,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
