---
id: "7.1.10"
title: "TempDB Contention (SQL Server)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.10 · TempDB Contention (SQL Server)

## Description

TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

## Value

TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

## Implementation

Poll wait statistics via DB Connect. Filter for PAGELATCH waits on TempDB (database_id 2). Alert when TempDB waits exceed baseline. Recommend adding TempDB data files equal to number of CPU cores (up to 8).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver.
• Ensure the following data sources are available: `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll wait statistics via DB Connect. Filter for PAGELATCH waits on TempDB (database_id 2). Alert when TempDB waits exceed baseline. Recommend adding TempDB data files equal to number of CPU cores (up to 8).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:wait_stats"
| where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"
| stats sum(wait_time_ms) as total_wait by wait_type
```

Understanding this SPL

**TempDB Contention (SQL Server)** — TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

Documented **Data sources**: `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:wait_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:wait_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by wait_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**TempDB Contention (SQL Server)** — TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

Documented **Data sources**: `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (wait types), Line chart (TempDB wait trend), Single value (current TempDB wait ms).

## SPL

```spl
index=database sourcetype="dbconnect:wait_stats"
| where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"
| stats sum(wait_time_ms) as total_wait by wait_type
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Bar chart (wait types), Line chart (TempDB wait trend), Single value (current TempDB wait ms).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
