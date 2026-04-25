<!-- AUTO-GENERATED from UC-6.3.20.json — DO NOT EDIT -->

---
id: "6.3.20"
title: "Backup Target Capacity and Growth Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.20 · Backup Target Capacity and Growth Rate

## Description

Backup destination (disk, dedup appliance, object storage) that fills up causes backup failures and retention gaps. Tracking growth and remaining capacity prevents surprise outages.

## Value

Backup destination (disk, dedup appliance, object storage) that fills up causes backup failures and retention gaps. Tracking growth and remaining capacity prevents surprise outages.

## Implementation

Poll backup target capacity (vendor API or filesystem/object metrics). Ingest used and total. Alert at 85% (warning) and 95% (critical). Compute week-over-week growth rate for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Backup vendor API, storage array metrics, S3/CloudWatch.
• Ensure the following data sources are available: Backup catalog size, target filesystem capacity, object storage metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll backup target capacity (vendor API or filesystem/object metrics). Ingest used and total. Alert at 85% (warning) and 95% (critical). Compute week-over-week growth rate for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype=backup_capacity
| eval used_pct=round(used_bytes/capacity_bytes*100, 1)
| stats latest(used_pct) as pct, latest(used_bytes) as used by target_name
| where pct > 85
| table target_name pct used capacity_bytes
```

Understanding this SPL

**Backup Target Capacity and Growth Rate** — Backup destination (disk, dedup appliance, object storage) that fills up causes backup failures and retention gaps. Tracking growth and remaining capacity prevents surprise outages.

Documented **Data sources**: Backup catalog size, target filesystem capacity, object storage metrics. **App/TA** (typical add-on context): Backup vendor API, storage array metrics, S3/CloudWatch. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: backup_capacity. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype=backup_capacity. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by target_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Backup Target Capacity and Growth Rate**): table target_name pct used capacity_bytes


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Gauge per target, Line chart (usage % over time), Table (target, %, growth rate).

## SPL

```spl
index=backup sourcetype=backup_capacity
| eval used_pct=round(used_bytes/capacity_bytes*100, 1)
| stats latest(used_pct) as pct, latest(used_bytes) as used by target_name
| where pct > 85
| table target_name pct used capacity_bytes
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Gauge per target, Line chart (usage % over time), Table (target, %, growth rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
