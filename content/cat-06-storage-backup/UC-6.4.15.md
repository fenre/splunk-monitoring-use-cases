<!-- AUTO-GENERATED from UC-6.4.15.json — DO NOT EDIT -->

---
id: "6.4.15"
title: "File Server Capacity Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.4.15 · File Server Capacity Trending

## Description

Volume-level free space trending on Windows file servers prevents user and application outages from full disks.

## Value

Volume-level free space trending on Windows file servers prevents user and application outages from full disks.

## Implementation

Collect % Free Space every 5–15m. Alert at 15% (warning) and 10% (critical). Use `predict` on large shares for procurement lead time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (PerfDisk), scripted `Get-Volume`.
• Ensure the following data sources are available: Logical disk free MB/%, WMI volume metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect % Free Space every 5–15m. Alert at 15% (warning) and 10% (critical). Use `predict` on large shares for procurement lead time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype="Perfmon:LogicalDisk" counter="% Free Space"
| timechart span=1h latest(InstanceValue) as free_pct by host, instance
| where free_pct < 15
```

Understanding this SPL

**File Server Capacity Trending** — Volume-level free space trending on Windows file servers prevents user and application outages from full disks.

Documented **Data sources**: Logical disk free MB/%, WMI volume metrics. **App/TA** (typical add-on context): `Splunk_TA_windows` (PerfDisk), scripted `Get-Volume`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: Perfmon:LogicalDisk. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype="Perfmon:LogicalDisk". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host, instance** — ideal for trending and alerting on this use case.
• Filters the current rows with `where free_pct < 15` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare host or array-reported free space and used percentage for the same volume and time range in Server Manager, the array management console, or your NAS UI—whichever owns the LUN or share.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Pair alerts with the file-server or security team runbook and change calendar. Consider visualizations: Line chart (free % trend), Gauge (current free %), Table (volumes below threshold).

## SPL

```spl
index=os sourcetype="Perfmon:LogicalDisk" counter="% Free Space"
| timechart span=1h latest(InstanceValue) as free_pct by host, instance
| where free_pct < 15
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

Line chart (free % trend), Gauge (current free %), Table (volumes below threshold).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
