---
id: "6.4.13"
title: "NFS Export Capacity and Client Load"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.4.13 · NFS Export Capacity and Client Load

## Description

Export-level capacity and NFS operations/sec highlight hot exports and approaching full filesystems on NAS heads.

## Value

Export-level capacity and NFS operations/sec highlight hot exports and approaching full filesystems on NAS heads.

## Implementation

Poll export statistics from NAS API or aggregated nfsd metrics. Alert on high used % or abnormal ops vs baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: NetApp/Isilon API, Linux `nfsstat`, `exportfs -v` metrics.
• Ensure the following data sources are available: Per-export bytes used, NFS op counters.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll export statistics from NAS API or aggregated nfsd metrics. Alert on high used % or abnormal ops vs baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="nas:nfs_export"
| eval used_pct=round(used_bytes/capacity_bytes*100,1)
| timechart span=5m sum(ops_per_sec) as ops, avg(used_pct) as pct by export_path, host
| where pct > 85 OR ops > 10000
```

Understanding this SPL

**NFS Export Capacity and Client Load** — Export-level capacity and NFS operations/sec highlight hot exports and approaching full filesystems on NAS heads.

Documented **Data sources**: Per-export bytes used, NFS op counters. **App/TA** (typical add-on context): NetApp/Isilon API, Linux `nfsstat`, `exportfs -v` metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: nas:nfs_export. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="nas:nfs_export". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by export_path, host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where pct > 85 OR ops > 10000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (export, used %, ops/s), Line chart (ops and capacity trend), Bar chart (top exports by ops).

## SPL

```spl
index=storage sourcetype="nas:nfs_export"
| eval used_pct=round(used_bytes/capacity_bytes*100,1)
| timechart span=5m sum(ops_per_sec) as ops, avg(used_pct) as pct by export_path, host
| where pct > 85 OR ops > 10000
```

## Visualization

Table (export, used %, ops/s), Line chart (ops and capacity trend), Bar chart (top exports by ops).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
