#!/usr/bin/env python3
"""Generate cat-04 cloud UC JSON sidecars from the expansion taxonomy.

Usage:
    python3 tools/research/generate_cloud_ucs.py --dry-run
    python3 tools/research/generate_cloud_ucs.py --write
    python3 tools/research/generate_cloud_ucs.py --write --subcategory 4.1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
CONTENT = REPO / "content" / "cat-04-cloud-infrastructure"
SCHEMA_REF = "../../schemas/uc.schema.json"

sys.path.insert(0, str(REPO))
from data.cloud_expansion import ALL_ENTRIES, crawl_uc_ids  # noqa: E402
from data.cloud_expansion.taxonomy import TaxonomyEntry  # noqa: E402


def _existing_max_z(subcategory: str) -> int:
    prefix = subcategory.replace(".", r"\.")
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
        f"| table {entry.table_fields}\n"
        f"| sort -_time"
    )


def _build_cim_spl(entry: TaxonomyEntry) -> str:
    if not entry.cim_models:
        return ""
    model = entry.cim_models[0]
    if model == "Change":
        return (
            "| tstats `summariesonly` count\n"
            f"  from datamodel=Change.All_Changes\n"
            "  where All_Changes.action=*\n"
            "  by All_Changes.user All_Changes.action All_Changes.object span=1h\n"
            "| sort -count"
        )
    if model == "Authentication":
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Authentication.Authentication\n"
            "  by Authentication.user Authentication.src Authentication.action span=1h\n"
            "| sort -count"
        )
    return ""


def _build_detailed_implementation(entry: TaxonomyEntry, uc_id: str, spl: str) -> str:
    prereq = entry.prerequisite_uc or "none"
    return f"""Prerequisites
• Splunk Enterprise or Splunk Cloud with permission to search `index={entry.index}`.
• Install and configure: {entry.app}.
• Ensure `{entry.sourcetype}` events are flowing (prerequisite UC: {prereq} when applicable).
• Map `{entry.index}` and field extractions per `docs/guides/aws.md`, `docs/guides/azure.md`, or `docs/guides/gcp.md` as appropriate.

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
The search scopes `{entry.sourcetype}` in `index={entry.index}` and applies `{entry.spl_filter}` to surface `{entry.title}`. Tune time range and alert threshold to your change cadence; exclude break-glass principals via a lookup.

Step 3 — Validate
Compare result counts to the vendor console (CloudTrail Event history, Azure Activity Log, GCP Logs Explorer, or service-native UI). Spot-check `{entry.table_fields.split()[0] if entry.table_fields else '_time'}` and actor fields. Confirm CIM acceleration only after TA field mappings are verified.

Step 4 — Operationalize and troubleshoot
Save as `{uc_id.replace('.', '_')}_alert` with appropriate severity. Dashboard: {entry.visualization}.
Failure modes: (1) empty results — verify TA input and index routing; (2) duplicate events — check S3/SQS duplication; (3) missing fields — upgrade `{entry.app}` and review `props.conf` aliases; (4) alert fatigue — add CMDB/allow-list exclusions documented in knownFalsePositives.
"""


def _build_compliance(entry: TaxonomyEntry) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if entry.cis_control:
        out.append(
            {
                "regulation": "CIS-AWS",
                "version": "v3.0",
                "clause": entry.cis_control,
                "mode": "detects-violation-of",
                "assurance": "partial",
                "assurance_rationale": (
                    f"CloudTrail detection of {entry.title} contributes to CIS control "
                    f"{entry.cis_control} audit logging and change monitoring."
                ),
            }
        )
    if entry.nist_control:
        out.append(
            {
                "regulation": "NIST-800-53",
                "version": "Rev.5",
                "clause": entry.nist_control,
                "mode": "satisfies",
                "assurance": "contributing",
                "assurance_rationale": (
                    f"Saved search evidence for {entry.nist_control} when alert outputs are archived."
                ),
            }
        )
    return out


def _build_control_test(entry: TaxonomyEntry, uc_id: str) -> dict[str, str]:
    return {
        "positiveScenario": (
            f"Replay or inject sample `{entry.sourcetype}` events matching `{entry.spl_filter}` "
            f"into `index={entry.index}`. Confirm UC-{uc_id} search returns >=1 row and alert fires."
        ),
        "negativeScenario": (
            f"Replay benign `{entry.sourcetype}` traffic without `{entry.spl_filter}` markers. "
            "Confirm the search returns zero rows and alert does not fire."
        ),
    }


def entry_to_uc(entry: TaxonomyEntry, bare_id: str) -> dict[str, Any]:
    spl = _build_spl(entry)
    cim_spl = _build_cim_spl(entry)
    prereqs = [f"UC-{entry.prerequisite_uc}"] if entry.prerequisite_uc else []

    uc: dict[str, Any] = {
        "$schema": SCHEMA_REF,
        "id": bare_id,
        "title": entry.title,
        "criticality": entry.criticality,
        "difficulty": entry.difficulty,
        "monitoringType": list(entry.monitoring_type),
        "splunkPillar": entry.splunk_pillar,
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
                "title": entry.vendor_ref_title or "Vendor documentation",
                "url": entry.vendor_ref_url,
            },
        ],
        "knownFalsePositives": entry.known_false_positives
        or "Approved change windows; documented automation service principals; sandbox accounts excluded via lookup.",
        "mitreAttack": list(entry.mitre_attack) if entry.mitre_attack else ["T1078.004"],
        "equipment": list(entry.equipment),
        "equipmentModels": list(entry.equipment_models),
        "securityDomain": entry.security_domain,
        "wave": entry.wave,
        "prerequisiteUseCases": prereqs,
        "detailedImplementation": _build_detailed_implementation(entry, bare_id, spl),
        "grandmaExplanation": (
            f"We watch for {entry.title.lower()} in your cloud audit logs so the team catches "
            "important changes early instead of finding out from auditors or customers."
        ),
        "controlTest": _build_control_test(entry, bare_id),
        "cost": {
            "tier": entry.cost_tier,
            "search_load": "moderate",
            "tstats_eligible": bool(cim_spl),
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
    if cim_spl:
        uc["cimSpl"] = cim_spl
        uc["dataModelAcceleration"] = (
            f"Enable acceleration for {', '.join(entry.cim_models)} after TA field mappings are verified."
        )
    return uc


ORIGINAL_MAX = {"4.1": 77, "4.2": 57, "4.3": 40, "4.4": 32, "4.5": 15, "4.6": 6}


def _generated_count() -> int:
    total = len(list(CONTENT.glob("UC-*.json")))
    original = sum(ORIGINAL_MAX.values())
    return max(0, total - original)


def assign_ids(entries: list[TaxonomyEntry], *, append: bool = False) -> list[tuple[str, TaxonomyEntry]]:
    if append:
        skip = _generated_count()
        entries = entries[skip:]

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
    ap.add_argument("--append", action="store_true", help="Only write taxonomy rows not yet on disk")
    ap.add_argument("--subcategory", action="append", default=[])
    args = ap.parse_args(argv)
    if args.write:
        args.dry_run = False

    entries = ALL_ENTRIES
    if args.subcategory:
        allow = set(args.subcategory)
        entries = [e for e in entries if e.subcategory in allow]

    assigned = assign_ids(entries, append=args.append)
    print(f"Would generate {len(assigned)} UCs")
    if args.dry_run:
        from collections import Counter

        c = Counter(b.split(".")[0] + "." + b.split(".")[1] for b, _ in assigned)
        for k in sorted(c.keys(), key=lambda x: [int(p) for p in x.split(".")]):
            print(f"  {k}: {c[k]}")
        return 0

    CONTENT.mkdir(parents=True, exist_ok=True)
    for bare_id, entry in assigned:
        path = CONTENT / f"UC-{bare_id}.json"
        if path.exists():
            print(f"skip existing {path.name}")
            continue
        payload = entry_to_uc(entry, bare_id)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote new sidecars under {CONTENT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
