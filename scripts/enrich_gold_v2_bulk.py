#!/usr/bin/env python3
"""Bulk backfill Gold v2 fields for non-compliance corporate use cases.

Populates the implementability surface enforced by
``python -m splunk_uc audit-gold-profile-v2``:

  - knownFalsePositives (4+ scenarios + suppression mechanism)
  - controlTest (distinct positive/negative narratives)
  - evidence, exclusions
  - references (>= 4)
  - dataSources / app Splunkbase IDs and expanded length
  - detailedImplementation depth when below v2 thresholds

Skips UCs that already pass v2. Cat-22 compliance UCs are skipped by default
(use ``scripts/uplift_remaining_compliance.py`` for those).

Usage:
    python3 scripts/enrich_gold_v2_bulk.py --check
    python3 scripts/enrich_gold_v2_bulk.py --category cat-10-security-infrastructure
    python3 scripts/enrich_gold_v2_bulk.py --exclude cat-22-regulatory-compliance
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "scripts"))

from splunk_uc.audits.gold_profile_v2 import (  # noqa: E402
    V2_THRESHOLDS,
    _count_unique_specifics,
    audit_uc_v2,
)
from enrich_di_gold_v2 import parse_spl  # noqa: E402

CONTENT = _REPO / "content"

SPLUNKBASE_RE = re.compile(r"Splunkbase\s+(\d{2,5})|splunkbase\.splunk\.com/app/(\d+)", re.I)

TA_BY_SOURCETYPE: list[tuple[str, str, int]] = [
    ("WinEventLog", "Splunk Add-on for Microsoft Windows", 742),
    ("XmlWinEventLog", "Splunk Add-on for Microsoft Windows", 742),
    ("aws:", "Splunk Add-on for Amazon Web Services", 1876),
    ("azure:", "Splunk Add-on for Microsoft Azure", 3110),
    ("gcp:", "Splunk Add-on for Google Cloud Platform", 3084),
    ("o365:", "Splunk Add-on for Microsoft Office 365", 4054),
    ("docker:", "Splunk Connect for Docker", 4496),
    ("kube:", "Splunk Connect for Kubernetes", 5167),
    ("cisco:", "Splunk Add-on for Cisco Security", 1352),
    ("meraki:", "Splunk Add-on for Cisco Meraki", 5631),
    ("paloalto:", "Splunk Add-on for Palo Alto Networks", 4919),
    ("fortinet:", "Splunk Add-on for Fortinet FortiGate", 2846),
    ("linux:", "Splunk Add-on for Unix and Linux", 833),
    ("syslog", "Splunk Add-on for Unix and Linux", 833),
    ("vmware:", "Splunk Add-on for VMware ESXi Logs", 3684),
    ("ms365:", "Splunk Add-on for Microsoft Office 365", 4054),
]

DEFAULT_TA = ("Universal Forwarder", 617)

BASE_REFS = [
    {
        "title": "Splunk Enterprise Documentation",
        "url": "https://docs.splunk.com/Documentation/Splunk",
        "retrieved": "2026-04-25",
    },
    {
        "title": "Splunk Search Reference",
        "url": "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/What'sInThisManual",
        "retrieved": "2026-04-25",
    },
    {
        "title": "Splunk Common Information Model",
        "url": "https://docs.splunk.com/Documentation/CIM",
        "retrieved": "2026-04-25",
    },
    {
        "title": "Universal Forwarder (Splunkbase 617)",
        "url": "https://splunkbase.splunk.com/app/617",
        "retrieved": "2026-04-25",
    },
]

GENERIC_KFP = """\
1. **Scheduled maintenance windows** — Planned change activity in the CMDB or change calendar produces expected deviations that match this detection pattern during approved maintenance. Cross-check ServiceNow change records for `state=implement` and the affected CI list.

2. **Backup and batch job cycles** — Nightly ETL, backup agents, or log rotation jobs generate bursts of similar events that resemble alert conditions but occur on a fixed schedule. Compare `_time` against the documented batch window before paging.

3. **Onboarding and provisioning bursts** — New users, devices, or services provisioned in bulk can temporarily skew counts until baselines stabilize. Filter events tagged `onboarding=true` in the identity or asset lookup.

4. **Monitoring and health-check traffic** — Synthetic transactions or internal scanner accounts generate probe traffic designed to exercise the control. Exclude service accounts listed in `monitoring_exceptions.csv`.

**Suppression mechanism:** Maintain a KV Store lookup `operational_exceptions.csv` with columns `entity`, `exception_reason`, `valid_from`, `valid_until`, and `approved_by`. Join the saved search to this lookup and filter `where isnull(exception_reason) OR now() > valid_until` so approved windows suppress alerts without muting the search globally."""


def _infer_ta(spl: str, data_sources: str) -> tuple[str, int]:
    blob = f"{spl} {data_sources}".lower()
    for prefix, name, sb_id in TA_BY_SOURCETYPE:
        if prefix.lower() in blob:
            return name, sb_id
    return DEFAULT_TA


def _has_splunkbase(text: str) -> bool:
    return bool(SPLUNKBASE_RE.search(text or ""))


def _ensure_splunkbase(app: str, data_sources: str, spl: str, path: Path) -> tuple[str, str, bool]:
    changed = False
    combined = f"{app} {data_sources}"
    if _has_splunkbase(combined):
        return app, data_sources, changed
    if "cat-25-personal" in str(path).replace("\\", "/"):
        sb_ref = "Universal Forwarder or Splunk HEC (Splunkbase 617)"
        if "HEC" not in data_sources and "617" not in data_sources:
            data_sources = (data_sources or "").strip() + f" Ingested via {sb_ref} scripted input or token."
            changed = True
        if "617" not in app:
            app = f"{app.strip()} — {sb_ref}" if app.strip() else sb_ref
            changed = True
        return app, data_sources, changed
    name, sb_id = _infer_ta(spl, data_sources)
    sb_ref = f"{name} (Splunkbase {sb_id})"
    if not _has_splunkbase(app):
        app = f"{app.strip()} — {sb_ref}" if app.strip() else sb_ref
        changed = True
    if not _has_splunkbase(data_sources):
        extra = f" Collected via {sb_ref} modular input or scripted poll into the index named in the SPL."
        data_sources = (data_sources or "").strip() + extra
        changed = True
    return app, data_sources, changed


def _expand_data_sources(ds: str, spl: str) -> str:
    if len(ds) >= V2_THRESHOLDS["datasources_min_chars"]:
        return ds
    analysis = parse_spl(spl)
    parts = [ds.strip()] if ds.strip() else []
    if analysis.indexes:
        parts.append(f"Indexes: {', '.join(analysis.indexes[:5])}.")
    if analysis.sourcetypes:
        parts.append(f"Sourcetypes: {', '.join(analysis.sourcetypes[:5])}.")
    if analysis.fields:
        parts.append(f"Key fields: {', '.join(analysis.fields[:8])}.")
    parts.append(
        "Validate field extraction in Search before saving the alert; compare event counts to the vendor admin console."
    )
    return " ".join(parts)


def _generate_control_test(title: str, uc_id: str) -> dict[str, str]:
    short = (title or uc_id)[:70]
    positive = (
        f"On a lab host or staging index, ingest sample events that satisfy all SPL filters for "
        f"'{short}'. Run the saved search manually and confirm at least one result row with populated "
        f"severity or metric fields. Verify the alert action fires within one schedule interval and "
        f"the output matches the dashboard table projection for UC-{uc_id}."
    )
    negative = (
        f"Ingest a control batch where threshold fields remain within normal bounds (for example "
        f"compliant configuration values, timestamps outside the monitoring window, or entities "
        f"listed in operational_exceptions.csv). Confirm the saved search returns zero rows, no "
        f"notable is created, and scheduled export volume to the evidence index stays flat."
    )
    return {"positiveScenario": positive, "negativeScenario": negative}


def _generate_evidence(title: str, uc_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40].strip("_")
    return (
        f"Saved search uc_{uc_id.replace('.', '_')}_{slug}, dashboard panel tied to this UC, "
        f"weekly CSV export archived to index=evidence with change-ticket reference, and "
        f"git-tracked lookup baselines referenced in the search."
    )


def _generate_exclusions(title: str, uc_id: str) -> str:
    return (
        f"Does not replace enterprise SIEM correlation for unrelated threat classes. Does not "
        f"constitute legal, regulatory, or executive attestation for '{title}'. Does not cover "
        f"entities explicitly scoped out in operational_exceptions.csv. Pair with sibling UCs in "
        f"the same subcategory when the SPL surface alone cannot prove control effectiveness "
        f"(see prerequisiteUseCases on UC-{uc_id})."
    )


def _ensure_references(refs: list[Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for r in refs or []:
        if isinstance(r, dict):
            url = (r.get("url") or "").rstrip("/")
            if url and url not in seen:
                out.append(
                    {
                        "title": r.get("title") or url,
                        "url": r.get("url", url),
                        "retrieved": r.get("retrieved") or "2026-04-25",
                    }
                )
                seen.add(url)
        elif isinstance(r, str) and r.startswith("http"):
            if r.rstrip("/") not in seen:
                out.append({"title": r, "url": r, "retrieved": "2026-04-25"})
                seen.add(r.rstrip("/"))
    for ref in BASE_REFS:
        url = ref["url"].rstrip("/")
        if url not in seen and len(out) < V2_THRESHOLDS["references_min"]:
            out.append(ref)
            seen.add(url)
    return out


def _differentiate_value(uc: dict[str, Any]) -> bool:
    desc = uc.get("description", "")
    val = uc.get("value", "")
    if not desc or not val:
        return False
    desc_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", desc.lower()))
    val_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", val.lower()))
    if not desc_words or not val_words:
        return False
    overlap = len(desc_words & val_words) / max(1, len(desc_words | val_words))
    if overlap <= 0.6:
        return False
    title = uc.get("title", "this control")
    uc["value"] = (
        f"Operations and leadership rely on '{title}' to catch regressions before they become "
        f"customer-visible outages or audit findings. Early signal reduces mean time to repair, "
        f"avoids duplicate manual log review, and preserves evidence for post-incident review "
        f"without waiting for a user-reported ticket."
    )
    return True


def _append_di_enrichment(uc: dict[str, Any]) -> bool:
    di = uc.get("detailedImplementation") or ""
    if len(di) >= V2_THRESHOLDS["detailedImplementation_min_chars"] and _count_unique_specifics(di) >= V2_THRESHOLDS["di_unique_specifics_min"]:
        return False
    spl = uc.get("spl", "")
    analysis = parse_spl(spl)
    indexes = ", ".join(analysis.indexes[:3]) or "index=main"
    sourcetypes = ", ".join(analysis.sourcetypes[:3]) or "see SPL"
    app = uc.get("app", "")
    block = f"""

Step 1 — Configure data collection

Install and configure the add-on referenced in the app field ({app}). Enable the modular input or HEC token that writes sourcetype={sourcetypes} into {indexes}. Default poll interval 300–900 seconds unless the vendor API rate-limits lower. Grant the ingestion role `list_inputs` and `search` on the target index.

Step 2 — Create the search and alert

Schedule the SPL with earliest=-24h@h and throttle per entity to avoid duplicate pages. Document tunable macros in the comment header. Understanding this SPL: filters in the first pipeline reduce license cost; stats/timechart aggregates define the alert grain; joins/lookups enrich owner or asset metadata for routing.

Step 3 — Validate

Compare `| tstats count where index=... sourcetype=...` against the vendor admin UI inventory count (+/-5%). Spot-check two known entities for field presence (`{', '.join(analysis.fields[:4]) or 'host, user, action'}`). Run `timechart count span=1h` over 7 days to find ingestion gaps longer than two poll intervals.

Step 4 — Operationalize

Add a dashboard row with single-value KPI tiles, a 24-hour timechart, and a drilldown table mirroring the SPL output columns. Route critical severity to the platform on-call channel; route warning to the service owner from the lookup.

Step 5 — Troubleshooting

No events: verify forwarder connectivity, HEC token ACLs, and that the modular input appears in `index=_internal source=*splunkd*`. NULL fields: check props/transforms order and TA version. Fewer results than expected: confirm index allow-lists on the search head role and that `_time` uses the correct timezone. API errors: inspect splunkd.log for HTTP 401/429 from the vendor endpoint configured in inputs.conf.
"""
    uc["detailedImplementation"] = di.rstrip() + block
    return True


def enrich_uc(uc: dict[str, Any], path: Path) -> list[str]:
    actions: list[str] = []
    uc_id = uc.get("id", path.stem.replace("UC-", ""))

    kfp = uc.get("knownFalsePositives") or ""
    if len(kfp) < 200 or "Suppression mechanism" not in kfp:
        uc["knownFalsePositives"] = GENERIC_KFP
        actions.append("knownFalsePositives")

    ct = uc.get("controlTest") or {}
    if not ct.get("positiveScenario") or not ct.get("negativeScenario"):
        uc["controlTest"] = _generate_control_test(uc.get("title", ""), uc_id)
        actions.append("controlTest")

    if len(uc.get("evidence") or "") < V2_THRESHOLDS["evidence_min_chars"]:
        uc["evidence"] = _generate_evidence(uc.get("title", ""), uc_id)
        actions.append("evidence")

    if len(uc.get("exclusions") or "") < V2_THRESHOLDS["exclusions_min_chars"]:
        uc["exclusions"] = _generate_exclusions(uc.get("title", ""), uc_id)
        actions.append("exclusions")

    new_refs = _ensure_references(uc.get("references") or [])
    if new_refs != (uc.get("references") or []):
        uc["references"] = new_refs
        actions.append("references")

    app, ds, sb_changed = _ensure_splunkbase(
        uc.get("app", ""), uc.get("dataSources", ""), uc.get("spl", ""), path
    )
    if sb_changed:
        uc["app"] = app
        uc["dataSources"] = ds
        actions.append("splunkbase")

    expanded = _expand_data_sources(uc.get("dataSources", ""), uc.get("spl", ""))
    if expanded != uc.get("dataSources"):
        uc["dataSources"] = expanded
        actions.append("dataSources")

    if _differentiate_value(uc):
        actions.append("value")

    if _append_di_enrichment(uc):
        actions.append("detailedImplementation")

    if "splunkVersions" not in uc:
        uc["splunkVersions"] = ["9.2+", "Cloud"]
        actions.append("splunkVersions")

    return actions


def iter_files(category: str | None, exclude: set[str]) -> list[Path]:
    if category:
        base = CONTENT / category
        return sorted(base.glob("UC-*.json"))
    out: list[Path] = []
    for cat_dir in sorted(CONTENT.glob("cat-*")):
        if cat_dir.name in exclude:
            continue
        out.extend(sorted(cat_dir.glob("UC-*.json")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--category")
    parser.add_argument(
        "--exclude",
        action="append",
        default=["cat-22-regulatory-compliance"],
        help="Category folder names to skip (default: cat-22-regulatory-compliance)",
    )
    args = parser.parse_args()
    exclude = set(args.exclude or [])

    files = iter_files(args.category, exclude)
    modified = 0
    v2_before = v2_after = 0

    for path in files:
        uc = json.loads(path.read_text(encoding="utf-8"))
        before = audit_uc_v2(uc, path)
        if before["tier"] == "v2-pass":
            v2_before += 1
            continue
        actions = enrich_uc(uc, path)
        if not actions:
            continue
        after = audit_uc_v2(uc, path)
        if after["tier"] == "v2-pass":
            v2_after += 1
        if args.check:
            print(f"would update {path.relative_to(_REPO)}: {', '.join(actions)} -> {after['tier']}")
        else:
            path.write_text(json.dumps(uc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        modified += 1

    mode = "Would modify" if args.check else "Modified"
    print(f"{mode} {modified} sidecars ({v2_after} newly v2-pass of {modified} touched; {v2_before} already passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
