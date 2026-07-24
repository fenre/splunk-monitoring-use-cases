#!/usr/bin/env python3
"""Generate cat-21 industry UC JSON sidecars from the expansion taxonomy.

Usage:
    python3 tools/research/generate_industry_ucs.py --dry-run
    python3 tools/research/generate_industry_ucs.py --write
    python3 tools/research/generate_industry_ucs.py --write --subcategory 21.1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
CONTENT = REPO / "content" / "cat-21-industry-verticals"
SCHEMA_REF = "../../schemas/uc.schema.json"

sys.path.insert(0, str(REPO))
from data.industry_expansion import ALL_ENTRIES  # noqa: E402
from data.industry_expansion.taxonomy import TaxonomyEntry  # noqa: E402


def _existing_max_z(subcategory: str) -> int:
    mx = 0
    for p in CONTENT.glob(f"UC-{subcategory}.*.json"):
        z = int(p.stem.split(".")[-1])
        mx = max(mx, z)
    return mx


def _build_spl(entry: TaxonomyEntry) -> str:
    base = f'index={entry.index} sourcetype="{entry.sourcetype}"'
    if entry.spl_filter.strip() == "*":
        filt = ""
    else:
        filt = f" {entry.spl_filter}"
    return (
        f"{base}{filt}\n"
        f"| stats count as event_count dc(host) as distinct_hosts by _time span=1h\n"
        f"| where event_count > 0\n"
        f"| table _time event_count distinct_hosts"
    )


def _build_detailed_implementation(entry: TaxonomyEntry, uc_id: str, spl: str) -> str:
    prereq = entry.prerequisite_uc or "none"
    return f"""Prerequisites
• Splunk Enterprise or Splunk Cloud with permission to search `index={entry.index}`.
• Install and configure: {entry.app}.
• Ensure `{entry.sourcetype}` events are flowing (prerequisite UC: {prereq} when applicable).
• Map `{entry.index}` and field extractions per `docs/guides/industry-verticals.md`.

Step 1 — Configure data collection
{entry.implementation}
Expected sourcetype: `{entry.sourcetype}`. Validate with:
```spl
index={entry.index} sourcetype="{entry.sourcetype}" | stats count by sourcetype
```

Step 2 — Create the search and alert
```spl
{spl}
```

Understanding this SPL
The search scopes `{entry.sourcetype}` in `index={entry.index}` and applies `{entry.spl_filter}` to surface `{entry.title}`. Tune time range and alert threshold to your operational baseline; exclude planned maintenance via asset/schedule lookup.

Step 3 — Validate
Compare result counts to the source system UI (SCADA HMI, EHR interface engine, POS gateway, OSS/BSS console, etc.) for the same time range. Spot-check `{entry.table_fields.split()[0] if entry.table_fields else '_time'}` and asset fields.

Step 4 — Operationalize and troubleshoot
Save as `{uc_id.replace('.', '_')}_alert` with appropriate severity. Dashboard: {entry.visualization}.
Failure modes: (1) empty results — verify HEC/Edge Hub input and index routing; (2) duplicate events — check forwarder acknowledgment; (3) missing fields — review props/transforms; (4) alert fatigue — add CMDB/allow-list exclusions documented in knownFalsePositives.
"""


def _build_compliance(entry: TaxonomyEntry) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if entry.regulation:
        out.append(
            {
                "regulation": entry.regulation,
                "version": "current",
                "clause": entry.regulation_clause or "operational-evidence",
                "mode": "satisfies",
                "assurance": "contributing",
                "assurance_rationale": (
                    f"Saved search evidence for {entry.title} supports "
                    f"{entry.regulation} operational monitoring requirements."
                ),
            }
        )
    return out


def _build_control_test(entry: TaxonomyEntry, uc_id: str) -> dict[str, str]:
    return {
        "positiveScenario": (
            f"Replay sample `{entry.sourcetype}` events matching `{entry.spl_filter}` "
            f"into `index={entry.index}`. Confirm UC-{uc_id} search returns >=1 row and alert fires."
        ),
        "negativeScenario": (
            f"Replay benign `{entry.sourcetype}` traffic without `{entry.spl_filter}` markers. "
            "Confirm the search returns zero rows and alert does not fire."
        ),
    }


def entry_to_uc(entry: TaxonomyEntry, bare_id: str) -> dict[str, Any]:
    spl = _build_spl(entry)
    prereqs = [f"UC-{entry.prerequisite_uc}"] if entry.prerequisite_uc else []

    uc: dict[str, Any] = {
        "$schema": SCHEMA_REF,
        "id": bare_id,
        "title": entry.title,
        "criticality": entry.criticality,
        "difficulty": entry.difficulty,
        "monitoringType": list(entry.monitoring_type),
        "splunkPillar": entry.splunk_pillar,
        "industry": entry.industry,
        "dataSources": f"`index={entry.index}` `sourcetype={entry.sourcetype}`",
        "app": entry.app,
        "spl": spl,
        "description": entry.description,
        "value": entry.value,
        "implementation": entry.implementation,
        "visualization": entry.visualization,
        "cimModels": list(entry.cim_models),
        "references": [
            {
                "title": entry.splunkbase_name,
                "url": f"https://splunkbase.splunk.com/app/{entry.splunkbase_id}",
            },
            {
                "title": entry.vendor_ref_title,
                "url": entry.vendor_ref_url,
            },
        ],
        "knownFalsePositives": entry.known_false_positives,
        "mitreAttack": list(entry.mitre_attack),
        "equipment": list(entry.equipment),
        "equipmentModels": list(entry.equipment_models),
        "securityDomain": entry.security_domain,
        "wave": entry.wave,
        "prerequisiteUseCases": prereqs,
        "detailedImplementation": _build_detailed_implementation(entry, bare_id, spl),
        "grandmaExplanation": (
            f"We watch {entry.industry.lower()} systems for signs of {entry.title.lower()} "
            "so your team can act early instead of learning about problems from customers or regulators."
        ),
        "controlTest": _build_control_test(entry, bare_id),
        "cost": {
            "tier": entry.cost_tier,
            "search_load": "moderate",
            "tstats_eligible": False,
        },
        "splunkbaseApps": [
            {
                "id": entry.splunkbase_id,
                "name": entry.splunkbase_name,
                "role": "primary",
                "requiresSmeReview": True,
            }
        ],
        "status": "community",
    }
    compliance = _build_compliance(entry)
    if compliance:
        uc["compliance"] = compliance
    return uc


def assign_ids(entries: list[TaxonomyEntry]) -> list[tuple[str, TaxonomyEntry]]:
    by_sub: dict[str, list[TaxonomyEntry]] = defaultdict(list)
    for e in entries:
        by_sub[e.subcategory].append(e)

    assigned: list[tuple[str, TaxonomyEntry]] = []
    for sub in sorted(by_sub.keys(), key=lambda x: [int(p) for p in x.split(".")]):
        sub_entries = by_sub[sub]
        start = _existing_max_z(sub) + 1
        for i, entry in enumerate(sub_entries):
            z = start + i
            bare = f"{sub}.{z}"
            assigned.append((bare, entry))
    return assigned


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--subcategory", action="append", default=[])
    args = ap.parse_args(argv)
    if args.write:
        args.dry_run = False

    entries = ALL_ENTRIES
    if args.subcategory:
        allow = set(args.subcategory)
        entries = [e for e in entries if e.subcategory in allow]

    assigned = assign_ids(entries)
    print(f"Would generate {len(assigned)} UCs (ALL_ENTRIES={len(ALL_ENTRIES)})")
    if args.dry_run:
        c = Counter(b.rsplit(".", 1)[0] for b, _ in assigned)
        for k in sorted(c.keys(), key=lambda x: [int(p) for p in x.split(".")]):
            print(f"  {k}: {c[k]}")
        print(f"  TOTAL cat-21 after write: {146 + len(assigned)}")
        return 0

    CONTENT.mkdir(parents=True, exist_ok=True)
    written = 0
    for bare_id, entry in assigned:
        path = CONTENT / f"UC-{bare_id}.json"
        if path.exists():
            print(f"skip existing {path.name}")
            continue
        payload = entry_to_uc(entry, bare_id)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1
    print(f"Wrote {written} new sidecars under {CONTENT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
