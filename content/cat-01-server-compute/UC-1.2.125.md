<!-- AUTO-GENERATED from UC-1.2.125.json — DO NOT EDIT -->

---
id: "1.2.125"
title: "Cluster Shared Volume (CSV) Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.125 · Cluster Shared Volume (CSV) Health

## Description

Cluster Shared Volumes underpin Hyper-V and SQL Server failover clusters. CSV failures cause VM/database unavailability across the cluster.

## Value

CSV space and I/O health under Hyper-V clusters affects every VM on shared storage. Early signals on pause, redirect, or latency avoid multi-tenant brownouts.

## Implementation

Monitor Failover Clustering Operational log for CSV state changes. CSV Offline (5121) is critical — VMs will fail. CSV Redirected (5140) means I/O is going through another node (degraded performance). CSV I/O Paused (5142) freezes all VMs on that volume. Alert immediately on offline and paused states. Monitor CSV latency via Perfmon: Cluster CSV File System counters. Track cluster node membership changes (1069/1070/1135).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Failover Clustering Operational log for CSV state changes. CSV Offline (5121) is critical — VMs will fail. CSV Redirected (5140) means I/O is going through another node (degraded performance). CSV I/O Paused (5142) freezes all VMs on that volume. Alert immediately on offline and paused states. Monitor CSV latency via Perfmon: Cluster CSV File System counters. Track cluster node membership changes (1069/1070/1135).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" EventCode IN (5120, 5121, 5140, 5142, 5143)
| eval Status=case(EventCode=5120,"CSV_Online", EventCode=5121,"CSV_Offline", EventCode=5140,"CSV_Redirected", EventCode=5142,"CSV_IO_Paused", EventCode=5143,"CSV_IO_Resumed", 1=1,"Other")
| stats count latest(_time) as LastEvent by host, VolumeName, Status
| where Status IN ("CSV_Offline", "CSV_Redirected", "CSV_IO_Paused")
| sort -LastEvent
```

Understanding this SPL

**Cluster Shared Volume (CSV) Health** — Cluster Shared Volumes underpin Hyper-V and SQL Server failover clusters. CSV failures cause VM/database unavailability across the cluster.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, VolumeName, Status** so each row reflects one combination of those dimensions.
• Filters the current rows with `where Status IN ("CSV_Offline", "CSV_Redirected", "CSV_IO_Paused")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status dashboard (CSV states), Timechart (state changes), Alert on failures.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" EventCode IN (5120, 5121, 5140, 5142, 5143)
| eval Status=case(EventCode=5120,"CSV_Online", EventCode=5121,"CSV_Offline", EventCode=5140,"CSV_Redirected", EventCode=5142,"CSV_IO_Paused", EventCode=5143,"CSV_IO_Resumed", 1=1,"Other")
| stats count latest(_time) as LastEvent by host, VolumeName, Status
| where Status IN ("CSV_Offline", "CSV_Redirected", "CSV_IO_Paused")
| sort -LastEvent
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.dest span=1h
| where count > 0
```

## Visualization

Status dashboard (CSV states), Timechart (state changes), Alert on failures.

## References

- [Monitor Failover Clustering Operational log for CSV state changes. CSV Offline](https://splunkbase.splunk.com/app/5121)
- [VMs will fail. CSV Redirected](https://splunkbase.splunk.com/app/5140)
- [CSV I/O Paused](https://splunkbase.splunk.com/app/5142)
